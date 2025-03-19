from typing import Type, Optional
from pydantic import BaseModel
from langchain.tools import BaseTool
import sqlite3
from data.loader import get_sqlite_database_path
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema.runnable.base import Runnable
from langchain_openai import ChatOpenAI
from chatbot.chains.base import PromptTemplate, generate_prompt_templates
from langchain import callbacks
from langchain.schema import StrOutputParser





class PuttingPlayerInStarting11Input(BaseModel):
    player_name: str
    action: Optional[str] = "add"  # Default action is "add", can be "remove"

class PuttingPlayerInStarting11(BaseTool):
    name: str = "PuttingPlayerInStarting11Tool"  # Name of the tool
    description: str = (
        "Allows a user to add or remove a player from the starting eleven. "
        "If adding, ensures that no more than 11 players are in the starting eleven."
    )
    args_schema: Type[BaseModel] = PuttingPlayerInStarting11Input  # Input schema for the tool
    return_direct: bool = True

    def _run(self, user_id: int, player_name: str, action: Optional[str] = "add") -> str:
        """Add or remove a player from the starting eleven based on the action."""
        db_path = get_sqlite_database_path()
        
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Step 1: Get the player_id from the player_name
            cursor.execute("SELECT player_id, name FROM players_fantasy")
            players = cursor.fetchall()
            
            if player_name == "Unknown player":
                return f"You didn't introduce the name of anyone in your team"
            
            else:
                player_id = next(player[0] for player in players if player[1] == player_name)

            # Step 2: Check if the player is on the user's team
            cursor.execute(
                "SELECT on_team, starting_eleven FROM user_team WHERE user_id = ? AND player_id = ?",
                (user_id, player_id),
            )
            result = cursor.fetchone()

            on_team, starting_eleven = result

            if action == "add":
                # Step 3: Ensure that no more than 11 players are in the starting eleven
                cursor.execute(
                    "SELECT COUNT(*) FROM user_team WHERE user_id = ? AND starting_eleven = 1",
                    (user_id,)
                )
                starting_eleven_count = cursor.fetchone()[0]

                if starting_eleven_count >= 11:
                    return "Error: You cannot have more than 11 players in the starting eleven."

                # Step 4: If the player is not already in the starting eleven, add them
                if starting_eleven == 1:
                    return f"Player '{player_name}' is already in the starting eleven."

                cursor.execute(
                    "UPDATE user_team SET starting_eleven = 1 WHERE user_id = ? AND player_id = ?",
                    (user_id, player_id),
                )
                conn.commit()
                return f"Player '{player_name}' has been successfully added to the starting eleven."

            elif action == "remove":
                # Step 5: If removing, ensure the player is in the starting eleven
                if starting_eleven == 0:
                    return f"Player '{player_name}' is not in the starting eleven."

                cursor.execute(
                    "UPDATE user_team SET starting_eleven = 0 WHERE user_id = ? AND player_id = ?",
                    (user_id, player_id),
                )
                conn.commit()
                return f"Player '{player_name}' has been successfully removed from the starting eleven."

            else:
                return "Error: Invalid action. Use 'add' to add a player or 'remove' to remove a player."

        except sqlite3.OperationalError as e:
            return f"Error: {str(e)}"
        finally:
            cursor.close()
            conn.close()


class PlayerInStarting11ChainExecutor(Runnable):
    """Chain that gets the information needed for the tool to work and allows the tool to work"""    
    def __init__(self, llm, user_id, memory=False):
        """Initialize the player in starting 11 executor chain."""

        super().__init__()

        self.tool = PuttingPlayerInStarting11()
        self.user_id = user_id
        self.llm = llm
        db_path = get_sqlite_database_path()
        self.db = sqlite3.connect(db_path)
        self.name_list = self.query_as_list("""
            SELECT p.name, p.team, p.position, p.expected_points_next_game
            FROM players_fantasy p
            JOIN user_team ut ON p.player_id = ut.player_id
            WHERE ut.user_id = ? AND ut.on_team = 1
            ORDER BY p.expected_points_next_game DESC
        """, user_id= self.user_id)

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            Your task is to identify to which player the user is referring to, to do so you will have access to a list with all the names
            You should also check if the user wants to remove or add a player to his starting 11, 'remove' and 'add' are the only 2 allowed for action

            Here is the list all players in the user's team:
            {names_list}
            
            Here is the user input:
            {customer_input}
            
            Focus:
            0. Only outputting 'add' or 'remove' for action
            1. Try to find the player name that is more similar to the one the user gave
            2. If you can't find a name corresponding, output Unknown player
            
            {format_instructions}
            """,
            human_template="Customer Query: {customer_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = PydanticOutputParser(pydantic_object=PuttingPlayerInStarting11Input)
        self.format_instructions = self.output_parser.get_format_instructions()

        self.chain = self.prompt | self.llm | self.output_parser

    def query_as_list(self, query, user_id):
        """
        Executes the SQL query and formats the result as a list.
        """
        cursor = self.db.cursor()
        cursor.execute(query, (user_id,))
        res = cursor.fetchall()
        return res
    
    def invoke(self, user_input) -> str:
        # Extract inputs from the user input string
        inputs = self.chain.invoke(
            {
                "customer_input": user_input["customer_input"],
                "names_list": self.name_list,
                "format_instructions": self.format_instructions,
            },)
        
        # Use the PuttingPlayerInStarting11 tool to check and update the starting_eleven
        result = self.tool._run(user_id=self.user_id, player_name=inputs.player_name, action=inputs.action)

        # Return the result of the operation
        return result 
    
class PlayerInStarting11ChainFinal(Runnable):
    """Chain that generates a message telling the user if his change in the starting team was successful or not"""    
    def __init__(self, llm, user_id, memory=True):
        """Initialize the player in starting 11 final chain."""

        super().__init__()

        self.user_id = user_id
        self.llm = llm
        
        self.chain_helper = PlayerInStarting11ChainExecutor(user_id=self.user_id, llm = self.llm)

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            Your task is to tell the user the result of the process of the changes to his starting 11

            Here is the output yielding the result of the Chains:
            {output}
            
            Here is the user input:
            {customer_input}
            
            Focus:
            1. Rewrite the output so it's more user understandable
            2. Be friendly and informative
            
            Chat History:
            {chat_history}
            """,
            human_template="Customer Query: {customer_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = StrOutputParser()

        self.chain = self.prompt | self.llm | self.output_parser
        
    def invoke(self, inputs, config):
            output = self.chain_helper.invoke({"customer_input": inputs["customer_input"]})
            with callbacks.collect_runs() as cb:
                inputs["output"] = output
                                
                result = self.chain.invoke(inputs, config=config)
                
                return result

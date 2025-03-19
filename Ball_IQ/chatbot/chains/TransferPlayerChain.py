from typing import Type, Optional, Dict
from pydantic import BaseModel
from langchain.tools import BaseTool
import sqlite3
from data.loader import get_sqlite_database_path
from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable.base import Runnable
from langchain_openai import ChatOpenAI
from chatbot.chains.base import PromptTemplate, generate_prompt_templates
from langchain import callbacks
from langchain.schema import StrOutputParser



class TransferPlayerInput(BaseModel):
    player_out_name: Optional[str] = None  # Make player_out_name optional
    player_in_name: str

class TransferPlayerTool(BaseTool):
    name: str = "TransferPlayerTool"  # Tool name should be descriptive
    description: str = (
        "Allows a user to transfer a player out of their team and add a new player to their team. "
        "The user_id and player names must be provided, and player names will be validated against the "
        "players_fantasy table. Ensures the user does not exceed their budget during the transfer."
    )
    args_schema: Type[BaseModel] = TransferPlayerInput
    return_direct: bool = True

    def _run(user_id: int, player_out_name: Optional[str], player_in_name: str) -> str:
        db_path = get_sqlite_database_path()
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        try:
            # Get the user's current budget
            cursor.execute(
                "SELECT budget FROM users WHERE user_id = ?",
                (user_id,),
            )
            user_budget = cursor.fetchone()
            if user_budget is None:
                return f"Your user does not exist."
            user_budget = user_budget[0]

            if player_out_name:
                # Handle player out
                # Get the price of the outgoing player
                cursor.execute(
                    "SELECT player_id, price FROM players_fantasy WHERE name = ?",
                    (player_out_name,),
                )
                player_out_data = cursor.fetchone()
                if player_out_data is None:
                    return f"{player_out_name}' does not exist in the fantasy player list."
                player_out_id, player_out_price = player_out_data

                # Validate that the outgoing player is on the user's team
                cursor.execute(
                    "SELECT player_id FROM user_team WHERE user_id = ? AND player_id = ? AND on_team = 1",
                    (user_id, player_out_id),
                )
                if cursor.fetchone() is None:
                    return f"'{player_out_name}' is not currently on your team."

                # Calculate the net budget impact of the transfer
                cursor.execute(
                    "SELECT price FROM players_fantasy WHERE name = ?",
                    (player_in_name,),
                )
                player_in_data = cursor.fetchone()
                if player_in_data is None:
                    return f"'{player_in_name}' does not exist in the fantasy player list."
                player_in_price = player_in_data[0]

                budget_after_transfer = user_budget + player_out_price - player_in_price

                # Validate that the user can afford the incoming player
                if budget_after_transfer < 0:
                    return (
                        f"Insufficient budget to add '{player_in_name}' to the team. "
                        f"Your budget is after selling is {(user_budget + player_out_price):.2f} and the player costs {player_in_price:.2f}."
                    )

                # Remove the outgoing player (set on_team and starting_eleven to 0)
                cursor.execute(
                    "UPDATE user_team SET on_team = 0, starting_eleven = 0 WHERE user_id = ? AND player_id = ?",
                    (user_id, player_out_id),
                )
            else:
                # If no player_out_name is provided, just add the incoming player
                # Check if the user already has 15 players on the team
                cursor.execute(
                    "SELECT COUNT(*) FROM user_team WHERE user_id = ? AND on_team = 1",
                    (user_id,),
                )
                on_team_count = cursor.fetchone()[0]
                if on_team_count >= 15:
                    return f"Cannot add '{player_in_name}' to the team. You already have 15 players on your team."

                # Calculate the net budget impact of the transfer
                cursor.execute(
                    "SELECT price FROM players_fantasy WHERE name = ?",
                    (player_in_name,),
                )
                player_in_data = cursor.fetchone()
                if player_in_data is None:
                    return f"Player '{player_in_name}' does not exist in the fantasy player list."
                player_in_price = player_in_data[0]

                budget_after_transfer = user_budget - player_in_price

                # Validate that the user can afford the incoming player
                if budget_after_transfer < 0:
                    return (
                        f"Insufficient budget to add '{player_in_name}' to the team. "
                        f"Your current budget is {user_budget:.2f}, and the player costs {player_in_price:.2f}."
                    )

            # Add the incoming player to the team
            cursor.execute(
                "SELECT player_id FROM players_fantasy WHERE name = ?",
                (player_in_name,),
            )
            player_in_id = cursor.fetchone()[0]

            # Check if the player is already in the user's team
            cursor.execute(
                "SELECT player_id FROM user_team WHERE user_id = ? AND player_id = ?",
                (user_id, player_in_id),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO user_team (user_id, player_id, on_team, starting_eleven) VALUES (?, ?, 1, 0)",
                    (user_id, player_in_id),
                )
            else:
                cursor.execute(
                    "UPDATE user_team SET on_team = 1 WHERE user_id = ? AND player_id = ?",
                    (user_id, player_in_id),
                )

            # Update the user's budget
            cursor.execute(
                "UPDATE users SET budget = ? WHERE user_id = ?",
                (budget_after_transfer, user_id),
            )

            connection.commit()

        except sqlite3.OperationalError as e:
            return f"An error occurred while processing the transfer: {e}"
        finally:
            cursor.close()
            connection.close()

        # Return the result
        if player_out_name:
            return (
                f"Player '{player_out_name}' has been removed from your team. "
                f"Player '{player_in_name}' has been successfully added to the team. "
                f"Remaining budget: {budget_after_transfer:.2f}"
            )
        else:
            return (
                f"Player '{player_in_name}' has been successfully added to the team. "
                f"Remaining budget: {budget_after_transfer:.2f}"
            )

class TransferPlayerChain(Runnable):
    """Chain that gets the necessary inputs for the tool from the user query and allows the tool to work."""

    def __init__(self, llm, user_id, memory = False, transfer_tool = TransferPlayerTool):
        """Initialize the transfer player reasoning chain."""

        super().__init__()
        self.transfer_tool = transfer_tool
        self.user_id = user_id
        self.llm = llm
        db_path = get_sqlite_database_path()
        self.db = sqlite3.connect(db_path)
        self.name_list = self.query_as_list("""
            SELECT p.name
            FROM players_fantasy p
            JOIN user_team ut ON p.player_id = ut.player_id
            WHERE ut.user_id = ? AND ut.on_team = 1
        """, user_id= self.user_id)
        self.all_players_names = self.query_as_list_all_names("""SELECT p.name FROM players_fantasy p""")

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            Your task is to get information out of an user input, you want to get the name of the player that the user wants to bring into his team
            and the name of the player the user wants to take out of his team
            
            Here is the list all players in the user's team:
            {names_list}
            
            Here are all the players names:
            {all_players}
            
            Here is the customer input:
            {customer_input}
            
            Focus:
            0. If the user provides 2 players in his input, you can check which is the incoming player by checking which of them doesn't appear on the list of players
            that are in his team
            1. Try to find the players names that are more similar to the one the user gave
            3. If the user doesn't provide incoming player assign 'None' to it
            
            
            {format_instructions}
            """,
            human_template="Customer Query: {customer_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = PydanticOutputParser(pydantic_object=TransferPlayerInput)
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
    
    def query_as_list_all_names(self, query):
        """Retrieve a query as a list"""
        cursor = self.db.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        return list(set(res))

    
    def invoke(self, inputs, config = None) -> str:
        """ 
        Validates and executes the transfer using the TransferPlayerTool.
        """ 
        # Parse and validate input 
        transfer_info = self.chain.invoke(
            {
                "customer_input": inputs["customer_input"],
                "names_list": self.name_list,
                "all_players": self.all_players_names,
                "format_instructions": self.format_instructions,
            },
        )
        if transfer_info.player_in_name == 'None':
            return f"You always need to state a player to bring to your team"
        # Use the TransferPlayerTool to perform the transfer 
        else:
            result = self.transfer_tool._run(user_id=self.user_id, 
                                        player_out_name=transfer_info.player_out_name,
                                        player_in_name=transfer_info.player_in_name,)
            return result

class TransferPlayerChainFinal(Runnable):
    """Chain that generates a message to tell if the transfer was successful or not"""

    def __init__(self, llm, user_id, memory=True):
        """Initialize the transfer player response chain."""

        super().__init__()

        self.user_id = user_id
        self.llm = llm
        
        self.chain_helper = TransferPlayerChain(user_id=self.user_id, llm = self.llm)
        
        

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            Your task is to tell the user the result of the process of the changes to his team

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

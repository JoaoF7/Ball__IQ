from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable.base import Runnable
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from chatbot.chains.base import PromptTemplate, generate_prompt_templates
from data.loader import *
import sqlite3
from langchain import callbacks
from langchain.schema import StrOutputParser



class RecommendPlayers(Runnable):
    """Chain that generates a response to customer queries about recommending players to his team."""
    def __init__(self, llm, user_id, memory=True):
        """Initialize the recommend players chain."""

        super().__init__()

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
        self.all_players_names = self.query_as_list_all_names("""SELECT p.name, p.team, p.position, p.price, p.expected_points_next_game 
                                                            FROM players_fantasy p""")

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            Your task is to recommend players to the user, to recommend take into consideration the expected_points_next_game
            You should not recommend players that already are in the users team and be careful with budget constraints made by the user

            Here is the list all players in the user's team:
            {names_list}
            
            Here are all the players and their info about expected_points_next_game, and price:
            {all_players}
            
            Here is the customer input:
            {customer_input}
            
            Focus:
            0. In order to make the best recommendations focus on recommending the players with more expected_points_next_game
            1. Do not recommend already in the users team
            2. Be careful with user budget restrictions, the sum of the price of the recommended players should not be above the budget
            3. Be careful with user number of players recommended, only recommend the number he asks for
            4. By default recommend two or three players
            5. Be careful with position restrictions, if a user defines a position he wants you should respect it
            6. In the output be sure to mention, the player's name, price, team, position and expected_points_next_game
            7. Be informal and think like you are exchanging texts with the user
            8. Only recommend players that are in the all players list
            9. The information provided should be done fully following the information provided in the section: all the players and their info about expected_points_next_game, and price:
            10. The  Expected Points Next Game should be the number under the column expected_points_next_game
            Chat History:
            {chat_history}
            """,
            human_template="Customer Query: {customer_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = StrOutputParser()


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

    
    def invoke(self, inputs, config):
        with callbacks.collect_runs() as cb:
                inputs["names_list"] = self.name_list
                inputs["all_players"] = self.all_players_names
                return self.chain.invoke(inputs, config=config)

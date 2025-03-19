from langchain.schema import StrOutputParser
from langchain.schema.runnable.base import Runnable
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from chatbot.chains.base import PromptTemplate, generate_prompt_templates
from data.loader import *
import sqlite3
from langchain import callbacks

class OptimizeLineup(Runnable):
    """Chain that generates a response to customer queries about optimizing his lineup."""    
    def __init__(self, llm, user_id, memory=True):
        """Initialize the optimize lineup chain."""

        super().__init__()

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
            Your task is to identify the best players in the users team and tell him how to make the best of them.
            You choose tell him a tactic to use or simply follow the one he says, to compare players you should focus on the 
            expected_points_next_game

            Here is the list all players in the user's team:
            {names_list}
            
            Here is the user input:
            {customer_input}
            
            Focus:
            0. Focus on the values under the expected_points_next_game
            1. Check if a user defines a tactic he wants you to use if not you choose the one that will yield in most points for his team, by summing the expected_points_next_game of all the players you recommend
            2. Tell users the name, team, position, expected points
            3. Be accurate and informal
            4. Don't use bullet points, provide the message as if you were exchanging texts with the user
            5. You should provide always 11 players, unless the user specifies otherwise, like wanting a specific number of players from a certain position
            6. The most common tactics asked are 433, which means you need to provide 4 defenders, 3 midfielders and 3 forwards, 442 which means you need to provide 4 defenders, 4 midfielders and 2 forwards and lastly 343 which means you need to provide 3 defenders, 4 midfielders and 3 forwards
            7. Always provide a goalkeeper
            6. By default you should suggest 4 defenders, 4 midfielders and 2 forwards
            
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

    
    def invoke(self, inputs, config):
        with callbacks.collect_runs() as cb:
            inputs["names_list"] = self.name_list
            return self.chain.invoke(inputs, config=config)

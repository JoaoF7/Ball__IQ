from langchain.schema.runnable.base import Runnable
from langchain_community.utilities.sql_database import SQLDatabase
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from chatbot.chains.base import PromptTemplate, generate_prompt_templates
from data.loader import *
import sqlite3
from langchain import callbacks
from langchain.schema import StrOutputParser


class ViewPlayerStats(Runnable):
    """Chain that generates a response to customer queries about the stats of a certain player."""
    def __init__(self, llm, memory=True):
        """Initialize the view players chain."""
        super().__init__()

        self.llm = llm
        db_path = get_sqlite_database_path()
        self.db = sqlite3.connect(db_path)
        self.list_stats_players = self.query_as_list_all("""
                SELECT 
                    ps.goals, ps.assists, ps.yellow_cards, ps.red_cards, 
                    ps.penalties_defended, ps.own_goals, ps.clean_sheets, 
                    ps.saves, ps.starts, ps.penalties_missed, 
                    pf.price_evolution, pf.form_rank, pf.name
                FROM player_stats ps
                INNER JOIN players_fantasy pf ON ps.player_id = pf.player_id""")

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            Your task is to identify to which player the user wants to know the stats about and provide him with those stats

            Here is the list all players names and stats:
            {stats_players}
            
            Here is the user input:
            {customer_input}
            
            Focus:
            1. Focus on providing all the stats for the user
            2. If the user asks for a specific stats provide him only with those only 
            3. Provide an overall summary on the player and how their stats look like compared to the average
            4. Be informal, friendly and informative
            5. Don't say Hey there
            6. Give trustworthy stats, get them from the list and don't create anything else
            7. Don't say the player ID
            8. If the user doesn't ask for a specific stat, the stats provided should be 6 out of the 10 that you think are more useful: goals, assists, yellow_cards, red_cards, penalties_defended, own_goals, clean_sheets, saves, starts, penalties_missed, 
            9. These show always: price_evolution, pf.form_rank, this values should be exactly the same as the ones provided in the list all players names and stats
            
            Chat History:
            {chat_history}
            """,
            human_template="Customer Query: {customer_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = StrOutputParser()

        self.chain = self.prompt | self.llm | self.output_parser

    
    def query_as_list_all(self, query):
        """Retrieve a query as a list"""
        cursor = self.db.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        return list(set(res))

    
    def invoke(self, inputs, config):
        with callbacks.collect_runs() as cb:
                inputs["stats_players"] = self.list_stats_players                                
                return self.chain.invoke(inputs, config=config)


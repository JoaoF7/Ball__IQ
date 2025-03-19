from langchain.schema import StrOutputParser
from langchain.schema.runnable.base import Runnable
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from chatbot.chains.base import PromptTemplate, generate_prompt_templates
from data.loader import *
import sqlite3
from langchain import callbacks

class CheckUpcomingFixtures(Runnable):
    """Chain that generates a response to customer queries about upcoming fixtures."""
    def __init__(self, llm, memory=True):
        """Initialize the check upcoming fixtures chain."""
        super().__init__()

        self.llm = llm
        db_path = get_sqlite_database_path()
        self.db = sqlite3.connect(db_path)
        self.name_list = self.query_as_list("SELECT name, team FROM players_fantasy")
        self.fixtures = self.query_as_list("SELECT * From fixtures")

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            Your task is to identify the matches a certain player will play accordingly to what player is in the user input.

            Here is the list all players:
            {names_list}

            Here is a list of all matches and the teams playing:
            {fixtures}
            
            Here is the user input:
            {customer_input}
            
            Focus:
            0. If a user wants a specific number of fixtures provide that name, otherwise only provide the next 2 fixtures
            1. Check if the user defines a week that he wants, if not the default is week 20, you can check the week of the fixtures under column week
            2. The teams playing the matches can be seen in the columns away_team and home_team
            3. Focus on accuracy, present real matches and real dates as weeks as weeks
            4. Be accurate and informal
            8. Don't use bullet points, provide the message as if you were exchanging texts with the user
            9. Don't greet the user

            Chat History:
            {chat_history}
                        """,
            human_template="Customer Query: {customer_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = StrOutputParser()

        self.chain = self.prompt | self.llm | self.output_parser

    def query_as_list(self, query):
        """Retrieve a query as a list"""
        cursor = self.db.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        return list(set(res))
    
    def invoke(self, inputs, config):
            with callbacks.collect_runs() as cb:
                inputs["names_list"] = self.name_list
                inputs["fixtures"] = self.fixtures
                                
                result = self.chain.invoke(inputs, config=config)
                
                return result
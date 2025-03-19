from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable.base import Runnable
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from chatbot.chains.base import PromptTemplate, generate_prompt_templates
from data.loader import *
from langchain import callbacks
from langchain.schema import StrOutputParser




class Chitchat(Runnable):
    """Chain that generates a response to customer queries about chitchat."""
    def __init__(self, llm, memory=True):
        """Initialize the chitchat chain."""
        super().__init__()

        self.llm = llm

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            You need to reply to an user chitchat message
            
            
            Here is the user input:
            {customer_input}
            
            Focus:
            1. Be friendly
            2. Be informal
            3. Answer the user the best you can or do what he wants
            4. Try to ask the user to ask for things related to EPL fantasy football as that is what you are designed to answer
            
            
            Chat History:
            {chat_history}
            """,
            human_template="Customer Query: {customer_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = StrOutputParser()

        self.chain = self.prompt | self.llm | self.output_parser
    
    def invoke(self, inputs, config):
        with callbacks.collect_runs() as cb:
            return self.chain.invoke(inputs, config=config)


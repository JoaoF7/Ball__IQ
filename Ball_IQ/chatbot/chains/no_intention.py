from langchain.schema import StrOutputParser
from langchain.schema.runnable.base import Runnable
from pydantic import BaseModel, ValidationError
from langchain_openai import ChatOpenAI
from chatbot.chains.base import PromptTemplate, generate_prompt_templates
from data.loader import *
from langchain import callbacks


class DealwithNoneIntention(Runnable):
    """Chain that deals with intentions that the router couldn't define."""    
    def __init__(self, llm, memory=True):
        """Initialize the deal with none intention chain."""        
        super().__init__()

        self.llm = llm

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            You need to check what possible intention the user is referencing to
            
            List of intentions:
            {list_of_intentions}
            
            Here is the user input:
            {customer_input}
            
            Focus:
            1. Retrieve the intention associated with the user input
            2. The output should just be one of the possible intentions, only that
            3. Don't put it in a list            
            
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


from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain.schema.runnable.base import Runnable
import sqlite3
from data.loader import get_sqlite_database_path
from langchain.output_parsers import PydanticOutputParser
from chatbot.chains.base import PromptTemplate, generate_prompt_templates
from langchain_openai import ChatOpenAI
from langchain import callbacks
from langchain.schema import StrOutputParser



# Tool 1: View Points Tool
class PointsInput(BaseModel):
    action: str = "view"
    points: Optional[float] = None

class PointsOutput(BaseModel):
    message: str

class ViewPointsTool(BaseTool):
    name: str = "ViewPointsTool"
    description: str = "Retrieve the current points for a user based on their user ID."
    args_schema: Type[BaseModel] = PointsInput
    

    def _run(self, user_id: int) -> str:
        db_path = get_sqlite_database_path()
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if result is None:
                return f"Error: User with ID {user_id} does not exist."
            points = result[0]
            return f"User {user_id} currently has {points} points."
        except sqlite3.OperationalError as e:
            return f"Error: {str(e)}"
        finally:
            cursor.close()
            connection.close()

# Tool 2: Update Points Tool
class UpdatePointsTool(BaseTool):
    name: str = "UpdatePointsTool"
    description: str = "Update the points for a user based on their user ID and the new points value."
    args_schema: Type[BaseModel] = PointsInput
    

    def _run(self, user_id: int, new_points: int) -> str:
        db_path = get_sqlite_database_path()
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        try:
            cursor.execute("UPDATE users SET points = ? WHERE user_id = ?", (new_points, user_id))
            if cursor.rowcount == 0:
                return f"Error: User with ID {user_id} does not exist."
            connection.commit()
            return f"Successfully updated user {user_id}'s points to {new_points}."
        except sqlite3.OperationalError as e:
            return f"Error: {str(e)}"
        finally:
            cursor.close()
            connection.close()

# Runnable Setup
class PointsRunnableReasoning(Runnable):
    """Chain that gets the inputs needed for the tools to work."""   
    def __init__(self, llm, memory=False):
        """Initialize the points reasoning chain."""

        super().__init__()

        self.llm = llm
        prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            Your task is to figure out where the user wants to view or update his team points, and to check to what value to update them
            
            Here is the user input:
            {customer_input}
            
            Focus:
            1. Check if the action is either 'view' or 'update'
            2. If it is 'update' the points should be the value introduced by the user
            3. If it is 'view' the points should be None

            {format_instructions}
            """,
            human_template="Customer Query: {customer_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = PydanticOutputParser(pydantic_object=PointsInput)
        self.format_instructions = self.output_parser.get_format_instructions()

        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, user_input) -> str:
        # Extract inputs from the user input string
        return self.chain.invoke(
            {
                "customer_input": user_input["customer_input"],
                "format_instructions": self.format_instructions,
            },)
class PointsRunnableResponse(Runnable):
        """Chain that tells the user their point or if the update was successful."""

        def __init__(self, llm, user_id, memory=True):
            """Initialize the product information response chain."""
            super().__init__()
            self.user_id = user_id
            self.view_points_tool = ViewPointsTool()
            self.update_points_tool = UpdatePointsTool()
            self.llm = llm
            self.reasoning_chain = PointsRunnableReasoning(llm)
            # Define the prompt template for customer service interaction
            prompt_template = PromptTemplate(
            system_template=""" 
            You are a part of a company about fantasy football. 
            Your task is to tell the user their points or the status of their update. To do so you'll have
            the help from an output from a tool
            
            Here is the output of the tool:
            {output_of_tool}
            
            
            Focus:
            1. Be friendly and informative
            2. Be informal

            Chat History:
            {chat_history}
            """,
            human_template="Output of tool: {output_of_tool}",
        )

            self.prompt = generate_prompt_templates(prompt_template, memory=memory)
            self.output_parser = StrOutputParser()
        
            # Chain to combine the prompt with LLM processing
            self.chain = self.prompt | self.llm | self.output_parser

        def invoke(self, inputs, config):
                """Invoke the product information response chain."""
                results = self.reasoning_chain.invoke({"customer_input": inputs["customer_input"]})
                if results.action == "view":
                    tool_output = self.view_points_tool._run(user_id=self.user_id)
                    with callbacks.collect_runs() as cb:
                        inputs["output_of_tool"] = tool_output
                        return self.chain.invoke(inputs, config=config)
                    
                elif results.action == "update":
                    tool_output = self.update_points_tool._run(user_id=self.user_id, new_points= results.points)
                    with callbacks.collect_runs() as cb:
                        inputs["output_of_tool"] = tool_output
                        return self.chain.invoke(inputs, config=config)
    

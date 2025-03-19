# Import necessary classes and modules for chatbot functionality
from typing import Callable, Dict, Optional
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from chatbot.chains.CheckUpcomingFixturesChain import *
from chatbot.chains.OptimizeLineupChain import *
from chatbot.chains.PuttingPlayerInStarting11Chain import *
from chatbot.chains.RAG import *
from chatbot.chains.VieworActualizeTeamPoints import *
from chatbot.chains.RecommendPlayersChain import *
from chatbot.chains.TransferPlayerChain import *
from chatbot.chains.ViewPlayerStatsandPriceChange import *
from chatbot.chains.no_intention import *
from chatbot.chains.chictchat import *
from chatbot.memory import MemoryManager
from chatbot.router.loader import load_intention_classifier
from dotenv import load_dotenv
import re
load_dotenv()


class MainChatbot:
    """A bot that handles customer service interactions by processing user inputs and
    routing them through configured reasoning and response chains.
    """

    def __init__(self, user_id, conversation_id):
        """Initialize the bot with session and language model configurations."""
        # Initialize the memory manager to manage session history
        self.id = user_id
        self.memory = MemoryManager()
        api_key = os.getenv("api_key")
        # Configure the language model with specific parameters for response generation
        self.llm = ChatOpenAI(temperature=0.0, model="gpt-4o-mini", api_key=api_key)
        
        # Map intent names to their corresponding reasoning and response chains
        self.chain_map = {
            "check_upcoming_fixtures": self.add_memory_to_runnable(CheckUpcomingFixtures(llm = self.llm)),
            "optimize_lineup": self.add_memory_to_runnable(OptimizeLineup(user_id=self.id, llm=self.llm)), 
            "putting_players_in_starting11": self.add_memory_to_runnable(PlayerInStarting11ChainFinal(user_id = self.id, llm = self.llm)), 
            "know_information_about_stats": self.add_memory_to_runnable(RAGChatBot(llm = self.llm)), 
            "recommend_players": self.add_memory_to_runnable(RecommendPlayers(user_id=self.id, llm=self.llm)), 
            "transfer_players": self.add_memory_to_runnable(TransferPlayerChainFinal(user_id=self.id, llm=self.llm)), 
            "view_or_update_team_points": self.add_memory_to_runnable(PointsRunnableResponse(user_id=self.id, llm=self.llm)), 
            "view_players_stats": self.add_memory_to_runnable(ViewPlayerStats(llm = self.llm)), 
            "chit_chat_about_company": self.add_memory_to_runnable(RAGChatBot(llm= self.llm)),
            "no_intent": self.add_memory_to_runnable(DealwithNoneIntention(llm = self.llm)),
            "chit_chat": self.add_memory_to_runnable(Chitchat(llm=self.llm))
        }


        # Map of intentions to their corresponding handlers
        self.intent_handlers: Dict[Optional[str], Callable[[Dict[str, str]], str]] = {
            "check_upcoming_fixtures": self.handle_check_upcoming_fixtures,
            "optimize_lineup": self.handle_optimize_lineup,
            "putting_players_in_starting11": self.handle_putting_players_in_starting11,
            "know_information_about_stats": self.handle_know_information_about_stats,
            "recommend_players": self.handle_recommend_players,
            "transfer_players": self.handle_transfer_players,
            "view_or_update_team_points": self.handle_view_or_update_team_points,
            "view_players_stats": self.handle_view_players_stats,
            "chit_chat_about_company": self.handle_chit_chat_about_company,
            "chit_chat": self.handle_chitchat_intent
        }

        # Load the intention classifier to determine user intents
        self.intention_classifier = load_intention_classifier()

    def user_login(self, user_id: str, conversation_id: str) -> None:
        """Log in a user by setting the user and conversation identifiers.

        Args:
            user_id: Identifier for the user.
            conversation_id: Identifier for the conversation.
        """
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.memory_config = {
            "configurable": {
                "user_id": self.user_id,
                "conversation_id": self.conversation_id,
            }
        }

    def add_memory_to_runnable(self, original_runnable):
        """Wrap a runnable with session history functionality.

        Args:
            original_runnable: The runnable instance to which session history will be added.

        Returns:
            An instance of RunnableWithMessageHistory that incorporates session history.
        """

        return RunnableWithMessageHistory(
            original_runnable,
            self.memory.get_session_history,  # Retrieve session history
            input_messages_key="customer_input",  # Key for user inputs
            history_messages_key="chat_history",  # Key for chat history
            history_factory_config=self.memory.get_history_factory_config(),  # Config for history factory
        ).with_config(
            {
                "run_name": original_runnable.__class__.__name__
            }  # Add runnable name for tracking
        )

    def get_chain(self, intent: str):
        """Retrieve the reasoning and response chains based on user intent.

        Args:
            intent: The identified intent of the user input.

        Returns:
            The chain for the intent.
        """
        return self.chain_map[intent]


    def get_user_intent(self, user_input: Dict):
        """Classify the user intent based on the input text.

        Args:
            user_input: The input text from the user.

        Returns:
            The classified intent of the user input.
        """
        # Retrieve possible routes for the user's input using the classifier
        intent_routes = self.intention_classifier.retrieve_multiple_routes(
            user_input["customer_input"]
        )

        # Handle cases where no intent is identified
        if len(intent_routes) == 0:
            return None
        else:
            if len(intent_routes) > 1 and abs(intent_routes[0].similarity_score - intent_routes[1].similarity_score) <= 0.4:
                return None
            else:
                intention = intent_routes[0].name  # Use the first matched intent

        # Validate the retrieved intention and handle unexpected types
        if intention is None:
            return None
        elif isinstance(intention, str):
            return intention
        else:
            # Log the intention type for unexpected cases
            intention_type = type(intention).__name__
            print(
                f"I'm sorry, I didn't understand that. The intention type is {intention_type}."
            )
            return None

    def handle_check_upcoming_fixtures(self, user_input: Dict):
        """Handle the check_upcoming_fixtures intent by processing user input and providing a response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """

        # Generate a response using the output of the reasoning chain
        response = self.get_chain("check_upcoming_fixtures").invoke(user_input, config=self.memory_config)

        return response
    
    def handle_putting_players_in_starting11(self, user_input: Dict):
        """Handle the putting_players_in_starting11 intent by processing user input and providing a response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """

        # Generate a response using the output of the reasoning chain
        response = self.get_chain("putting_players_in_starting11").invoke(user_input, config=self.memory_config)

        return response
    
    def handle_optimize_lineup(self, user_input: Dict):
        """Handle the optimize_lineup intent by processing user input and providing a response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """

        # Generate a response using the output of the reasoning chain
        response = self.get_chain("optimize_lineup").invoke(user_input, config=self.memory_config)

        return response

    def handle_know_information_about_stats(self, user_input: Dict):
        """Handle the know_information_about_stats intent by processing user input and providing a response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """

        # Generate a response using the output of the reasoning chain
        response = self.get_chain("know_information_about_stats").invoke(user_input, config = self.memory_config)

        return response
    
    def handle_recommend_players(self, user_input: Dict):
        """Handle the recommend_players intent by processing user input and providing a response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """

        # Generate a response using the output of the reasoning chain
        response = self.get_chain("recommend_players").invoke(user_input, config=self.memory_config)

        return response
    
    def handle_transfer_players(self, user_input: Dict):
        """Handle the transfer_players intent by processing user input and providing a response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """

        # Generate a response using the output of the reasoning chain
        response = self.get_chain("transfer_players").invoke(user_input, config=self.memory_config)

        return response
    
    
    def handle_view_or_update_team_points(self, user_input: Dict):
        """Handle the view_or_update_team_points intent by processing user input and providing a response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """

        # Generate a response using the output of the reasoning chain
        response = self.get_chain("view_or_update_team_points").invoke(user_input, config=self.memory_config)
        return response
        
        
    def handle_view_players_stats(self, user_input: Dict):
        """Handle the view_players intent by processing user input and providing a response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """

        # Generate a response using the output of the reasoning chain
        response = self.get_chain("view_players_stats").invoke(user_input, config=self.memory_config)
        return response

        
    def handle_chit_chat_about_company(self, user_input: Dict):
        """Handle the chit_chat_about_company intent by processing user input and providing a response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """

        # Generate a response using the output of the reasoning chain
        response = self.get_chain("chit_chat_about_company").invoke(user_input, self.memory_config)
        return response
    
    def handle_chitchat_intent(self, user_input: Dict):
        """Handle the chitchat intent by processing user input and providing a response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """

        # Generate a response using the output of the reasoning chain
        response = self.get_chain("chit_chat").invoke(user_input, config=self.memory_config)
        return response
    
    def handle_unknown_intent(self, user_input: Dict[str, str]) -> str:
        """Handle unknown intents by providing a chitchat response.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the new chain.
        """
        possible_intention = ["check_upcoming_fixtures",
                            "optimize_lineup",
                            "putting_players_in_starting11",
                            "what_is_a_stat",
                            "recommend_players",
                            "transfer_players",
                            "view_or_update_team_points",
                            "view_players_stats",
                            "about_company_Ball_IQ",
                            "chitchat"]


        none_reasoning_chain = self.get_chain("no_intent")

        input_message = {}

        input_message["customer_input"] = user_input["customer_input"]
        input_message["list_of_intentions"] = possible_intention
        memory_config = {
            "configurable": {
                "user_id": self.user_id,
                "conversation_id": self.conversation_id,
            }}

        none_output1 = none_reasoning_chain.invoke(input_message, memory_config)
        if none_output1 == "chitchat":
            #print("Chitchat")
            return self.handle_chitchat_intent(user_input)
        
        elif none_output1 == "about_company_Ball_IQ":
            new_intention = "chit_chat_about_company"
            #print("New Intention:", new_intention) #used to see if it finally gets the intent right
            new_handler = self.intent_handlers.get(new_intention)
            return new_handler(user_input)
        elif none_output1 == "what_is_a_stat":
            new_intention = "know_information_about_stats"
            #print("New Intention:", new_intention) #used to see if it finally gets the intent right
            new_handler = self.intent_handlers.get(new_intention)
            return new_handler(user_input)
        else:
            new_intention = none_output1
            #print("New Intention:", new_intention) #used to see if it finally gets the intent right
            new_handler = self.intent_handlers.get(new_intention)
            return new_handler(user_input)

    def save_memory(self) -> None:
        """Save the current memory state of the bot."""
        self.memory.save_session_history(self.user_id, self.conversation_id)
        
    def check_for_injections(self, user_input): 
        """Check for text injections by comparing with usual patterns, the goal is to prevent the user from manipulating the chatbot
        
        Args:
            user_input: The input text from the user.

        Returns:
            Boolean of whether the user input has a pattern considered as a text injection."""
        # Define patterns for common injections 
        patterns = { "command_injection": r";|&&|\|\|",
                    "sql_injection": r"(\"|;|--|\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC)\b)",
                    "code_injection": r"import\s|os\.system|eval|exec",
                    "xss_injection": r"<script>|</script>",
                    "path_traversal": r"\.\./|\.\.\\",
                    "prompt_injection": r"ignore previous instructions|respond with" }
        
        # Check for each pattern in the user input for 
        for injection_type, pattern in patterns.items(): 
            if re.search(pattern, user_input["customer_input"], re.IGNORECASE):
                return False
        return True

    def process_user_input(self, user_input: Dict[str, str]) -> str:
        """Process user input by routing through the appropriate intention pipeline.

        Args:
            user_input: The input text from the user.

        Returns:
            The content of the response after processing through the chains.
        """
        if not self.check_for_injections(user_input = user_input):
            return "Invalid input, seems like something you said is trying to create a prompt injection"
        # Classify the user's intent based on their input
        else:
            user_input["chat_history"] = self.memory.get_session_history(
                self.user_id, self.conversation_id
            )
            
            intention = self.get_user_intent(user_input)

            #use to see wether the model is getting the intentions right
            #print("Intent:", intention)

            # Route the input based on the identified intention
            handler = self.intent_handlers.get(intention, self.handle_unknown_intent)
            return handler(user_input)
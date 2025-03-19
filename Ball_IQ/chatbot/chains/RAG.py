import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema.runnable.base import Runnable
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from chatbot.chains.base import PromptTemplate, generate_prompt_templates
from langchain import callbacks


class RAGChatBot(Runnable):
    """Chain that generates a response to customer queries about Ball IQ, the company or about specific stats and fantasy points (the pdfs used have information related to this)."""
    def __init__(self, llm, memory=True):
        """Initialize the rag chatbot chain."""

        super().__init__()

        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()

        # Initialize Pinecone
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = "capstone-project"
        self.pinecone_client = Pinecone(api_key=pinecone_api_key, environment="us-east-1")
        self.index = self.pinecone_client.Index(self.index_name)
        api_key = os.getenv("api_key")

        # Create a vector store for document retrieval
        self.vector_store = PineconeVectorStore(
            index=self.index,
            embedding=OpenAIEmbeddings(api_key= api_key, model="text-embedding-3-small"),
        )
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 2, "score_threshold": 0.5},
        )

        # Define the RAG prompt template
        prompt_template = PromptTemplate(
            system_template="""Use the following pieces of context to answer the question.
            If you don't know the answer, say so. Be concise, use up to three sentences.
            Utilize previous conversation history for personalization.

            Context:
            {context}

            User Question:
            {customer_input}

            Chat History:
            {chat_history}""",
            human_template="Customer Query: {customer_input}",
        )

        # Create the chain with memory (optional) and parsing
        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.llm = llm
        self.output_parser = StrOutputParser()

        # Define the RAG chain
        self.chain = self.prompt | self.llm | self.output_parser

    def format_docs(self, documents):
        """
        Format documents by concatenating their content.
        """
        return "\n\n".join(doc.page_content for doc in documents)

    def invoke(self, inputs, config):
        """
        Process the user query through the RAG chain.
        """
        with callbacks.collect_runs() as cb:
            inputs["context"] = self.format_docs(self.retriever.invoke(inputs["customer_input"])) 
            result = self.chain.invoke(inputs, config=config)
            return result

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from logger import setup_logger
from pdf_processor import pdf_manager

logger = setup_logger()

def get_llm(model_type: str, model_name: str, api_key: str, temperature: float, max_tokens: int):
    try:
        logger.info(f"Initializing {model_type} model: {model_name}")
        
        if model_type == "openai":
            return ChatOpenAI(
                temperature=temperature,
                api_key=api_key,
                model=model_name,
                max_tokens=max_tokens
            )
        elif model_type == "groq":
            return ChatGroq(
                api_key=api_key,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
            
    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        raise

def get_response(llm, query: str) -> str:
    try:
        logger.info("Generating response")
        
        # Get the combined vectorstore from the PDF manager
        vectorstore = pdf_manager.get_combined_vectorstore()
        
        if not vectorstore:
            return "No PDFs have been uploaded yet. Please upload at least one PDF first."
        
        template = """
        Answer the question properly based on the following context from PDF documents.
        
        For each piece of information you use in your answer, mention which PDF document it came from.
        If the information needed to answer the question is not present in any of the PDF documents, 
        clearly state that the information is not present in the uploaded PDFs.
        
        Context: {context}
        Question: {question}
        
        Answer: 
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 5}  # Increased to get more context from different PDFs
        )
        
        rag_chain = (
            {"context": retriever, "question": lambda x: x}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        response = rag_chain.invoke(query)
        logger.info("Response generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise
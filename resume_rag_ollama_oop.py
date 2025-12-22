"""Resume RAG System using Ollama with OOP design."""

import os
from typing import Optional, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate


class ResumeRAG:
    """RAG system for querying resume documents using Ollama models."""
    
    def __init__(
        self,
        pdf_path: str,
        chat_model: str = "gpt-oss:20b",
        embedding_model: str = "nomic-embed-text",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        temperature: float = 0.0
    ):
        """
        Initialize Resume RAG system.
        
        Args:
            pdf_path: Path to the PDF resume file
            chat_model: Ollama model for chat/QA
            embedding_model: Ollama model for embeddings
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
            temperature: LLM temperature (0 for deterministic)
        """
        self.pdf_path = pdf_path
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.temperature = temperature
        
        self.vectorstore = None
        self.qa_chain = None
        
    def load_and_process_document(self) -> None:
        """Load PDF and create vector store with embeddings."""
        print("Loading PDF...")
        loader = PyPDFLoader(self.pdf_path)
        docs = loader.load()
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        splits = text_splitter.split_documents(docs)
        
        # Create embeddings and vector store
        print("Creating embeddings...")
        embeddings = OllamaEmbeddings(model=self.embedding_model)
        self.vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
        
    def setup_qa_chain(self) -> None:
        """Configure the RAG QA chain with LLM and prompt."""
        if self.vectorstore is None:
            raise ValueError("Must call load_and_process_document() first")
        
        # Configure LLM
        llm = ChatOllama(model=self.chat_model, temperature=self.temperature)
        
        # Define strict grounding prompt
        template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer based ONLY on the context provided, just say that you don't know. 
Do not try to make up an answer or use outside knowledge.

Context: {context}

Question: {question}

Helpful Answer:"""
        
        rag_prompt = PromptTemplate.from_template(template)
        
        # Create QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=self.vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": rag_prompt}
        )
        
    def query(self, question: str) -> str:
        """
        Query the resume with a question.
        
        Args:
            question: Question to ask about the resume
            
        Returns:
            Answer from the RAG system
        """
        if self.qa_chain is None:
            raise ValueError("Must call setup_qa_chain() first")
        
        response = self.qa_chain.invoke(question)
        return response['result']
    
    def interactive_mode(self) -> None:
        """Run interactive Q&A session."""
        if self.qa_chain is None:
            raise ValueError("Must call setup_qa_chain() first")
        
        print("\n" + "="*60)
        print("Resume RAG System - Interactive Mode")
        print("="*60)
        print(f"Chat Model: {self.chat_model}")
        print(f"Embedding Model: {self.embedding_model}")
        print("Type 'quit' to exit")
        print("="*60 + "\n")
        
        while True:
            query = input("\nAsk a question about the resume: ")
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not query.strip():
                print("Please enter a valid question.")
                continue
            
            try:
                answer = self.query(query)
                print(f"\nAnswer: {answer}")
            except Exception as e:
                print(f"\nError: {str(e)}")


def main():
    """Main entry point for the application."""
    # Configuration
    pdf_path = "C:/resume/resume.pdf"
    chat_model_name = "gpt-oss:20b"
    embedding_model_name = "nomic-embed-text"
    
    # Initialize RAG system
    rag_system = ResumeRAG(
        pdf_path=pdf_path,
        chat_model=chat_model_name,
        embedding_model=embedding_model_name
    )
    
    # Load document and setup
    rag_system.load_and_process_document()
    rag_system.setup_qa_chain()
    
    # Run interactive mode
    rag_system.interactive_mode()


if __name__ == "__main__":
    main()

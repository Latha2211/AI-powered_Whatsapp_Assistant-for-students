"""
RAG Engine using LangChain + FAISS Vector Store
Handles document chunking, embedding, and retrieval
"""

import os
import pickle
from typing import List, Dict, Optional, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger("rag_engine")


class RAGEngine:
    """RAG Engine for FAQ and document retrieval"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.vector_store = None
        self.qa_chain = None
        self.faq_index_path = "data/faiss_index"
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def load_faq_data(self, faq_df: pd.DataFrame) -> List[Document]:
        """Convert FAQ DataFrame to LangChain Documents with chunking"""
        try:
            documents = []
            
            for _, row in faq_df.iterrows():
                # Combine question and answer
                text = f"Question: {row['Question']}\n\nAnswer: {row['Answer']}"
                
                # Create metadata
                metadata = {
                    "question": row['Question'],
                    "category": row.get('Category', 'general'),
                    "interface": row.get('Interface', 'general'),
                    "source": "FAQ Database"
                }
                
                # Chunk the text
                chunks = self.text_splitter.split_text(text)
                
                # Create documents for each chunk
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        page_content=chunk,
                        metadata={**metadata, "chunk_id": i}
                    )
                    documents.append(doc)
            
            logger.info(f"✅ Loaded {len(documents)} document chunks from {len(faq_df)} FAQs")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Error loading FAQ data: {e}")
            return []
    
    def create_vector_store(self, documents: List[Document]) -> bool:
        """Create FAISS vector store from documents"""
        try:
            logger.info("🔄 Creating FAISS vector store...")
            
            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            
            # Save to disk
            os.makedirs(self.faq_index_path, exist_ok=True)
            self.vector_store.save_local(self.faq_index_path)
            
            logger.info(f"✅ FAISS vector store created and saved to {self.faq_index_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating vector store: {e}")
            return False
    
    def load_vector_store(self) -> bool:
        """Load existing FAISS vector store"""
        try:
            if not os.path.exists(self.faq_index_path):
                logger.warning(f"⚠️ FAISS index not found at {self.faq_index_path}")
                return False
            
            self.vector_store = FAISS.load_local(
                self.faq_index_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            logger.info("✅ FAISS vector store loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading vector store: {e}")
            return False
    
    def setup_qa_chain(self, salutation: str = "Student"):
        """Setup RetrievalQA chain with custom prompt"""
        
        prompt_template = f"""You are an AI assistant for Texila American University, helping students with their queries.

Use the following context to answer the student's question. If you don't find relevant information in the context, politely inform the student.

Context:
{{context}}

Student Question: {{question}}

Instructions:
- Address the student as "{salutation}"
- Be professional, friendly, and concise
- Provide accurate information based on the context
- If unsure, admit it and suggest contacting support
- Use bullet points for clarity when listing multiple items

Answer:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}  # Retrieve top 4 relevant chunks
            ),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
        
        logger.info("✅ QA chain configured")
    
    def query(
        self, 
        question: str, 
        salutation: str = "Student",
        interface: Optional[str] = None
    ) -> Tuple[str, float, List[str]]:
        """
        Query the RAG system
        
        Returns:
            (answer, confidence_score, source_questions)
        """
        try:
            if not self.vector_store:
                logger.error("❌ Vector store not initialized")
                return "I'm having technical difficulties. Please try again.", 0.0, []
            
            # Setup QA chain with salutation
            self.setup_qa_chain(salutation)
            
            # Get retriever results with scores
            retriever = self.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": 4,
                    "score_threshold": 0.65
                }
            )
            
            # Retrieve relevant documents
            relevant_docs = retriever.get_relevant_documents(question)
            
            if not relevant_docs:
                logger.info(f"⚠️ No relevant documents found for: {question[:50]}...")
                return (
                    f"{salutation}, I couldn't find specific information about your query. "
                    "Could you rephrase or provide more details?",
                    0.0,
                    []
                )
            
            # Filter by interface if provided
            if interface:
                relevant_docs = [
                    doc for doc in relevant_docs 
                    if doc.metadata.get('interface', '').lower() == interface.lower()
                ]
            
            # Run QA chain
            result = self.qa_chain({"query": question})
            
            # Extract answer and sources
            answer = result['result']
            source_docs = result.get('source_documents', [])
            
            # Calculate confidence (average similarity of top docs)
            # Using inverse distance as proxy for similarity
            confidence = min(len(relevant_docs) / 4.0, 1.0) * 0.9  # Max 0.9
            
            # Extract source questions
            source_questions = list(set([
                doc.metadata.get('question', '') 
                for doc in source_docs 
                if doc.metadata.get('question')
            ]))[:3]  # Top 3 unique sources
            
            logger.info(f"✅ Query processed | Confidence: {confidence:.2f} | Sources: {len(source_questions)}")
            
            return answer, confidence, source_questions
            
        except Exception as e:
            logger.error(f"❌ Error in query: {e}")
            return (
                f"{salutation}, I encountered an error processing your question. "
                "Please try again or contact support.",
                0.0,
                []
            )
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add new documents to existing vector store"""
        try:
            if not self.vector_store:
                logger.error("❌ Vector store not initialized")
                return False
            
            # Add documents
            self.vector_store.add_documents(documents)
            
            # Save updated store
            self.vector_store.save_local(self.faq_index_path)
            
            logger.info(f"✅ Added {len(documents)} new documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding documents: {e}")
            return False
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 4,
        interface: Optional[str] = None
    ) -> List[Dict]:
        """
        Perform similarity search and return results with metadata
        
        Returns:
            List of dicts with content, metadata, and score
        """
        try:
            if not self.vector_store:
                return []
            
            # Search with scores
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results:
                # Filter by interface if specified
                if interface and doc.metadata.get('interface', '').lower() != interface.lower():
                    continue
                
                formatted_results.append({
                    'content': doc.page_content,
                    'question': doc.metadata.get('question', ''),
                    'category': doc.metadata.get('category', ''),
                    'interface': doc.metadata.get('interface', ''),
                    'score': float(score),
                    'confidence': max(0, 1 - score)  # Convert distance to similarity
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Error in similarity search: {e}")
            return []


# Singleton instance
_rag_engine_instance = None

def get_rag_engine() -> RAGEngine:
    """Get or create RAG engine singleton"""
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance

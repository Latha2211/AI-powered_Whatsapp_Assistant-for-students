"""
Message Processor - Handles WhatsApp message processing with RAG
"""

import re
from typing import Dict, Optional, Tuple, List
from datetime import datetime

from src.rag.rag_engine import get_rag_engine
from src.database.student_repository import StudentRepository
from src.utils.logger import setup_logger
from src.utils.message_helpers import (
    is_pure_greeting,
    is_satisfied_response,
    is_paypal_query,
    is_publication_query,
    is_remittance_query,
    extract_question_from_message
)

logger = setup_logger("message_processor")


class MessageProcessor:
    """Process incoming WhatsApp messages using RAG"""
    
    def __init__(self):
        self.rag_engine = get_rag_engine()
        self.student_repo = StudentRepository()
    
    def process_text_message(
        self,
        message: str,
        contact_id: str,
        contact_name: str,
        salutation: str = "Student",
        chat_context: List[Dict] = None
    ) -> Dict:
        """
        Process text message and generate response using RAG
        
        Returns:
            Dict with response, message_type, confidence, sources
        """
        try:
            # Clean and normalize message
            message_clean = message.strip()
            
            # Route to specialized handlers
            if is_pure_greeting(message_clean):
                return self._handle_greeting(salutation)
            
            if is_satisfied_response(message_clean):
                return self._handle_acknowledgment(salutation)
            
            if is_paypal_query(message_clean):
                return self._handle_paypal_query(salutation)
            
            if is_publication_query(message_clean):
                return self._handle_publication_query(salutation, message_clean)
            
            if is_remittance_query(message_clean):
                return self._handle_remittance_query(salutation)
            
            # Check for student-specific queries (fees, academic)
            if self._is_student_specific_query(message_clean):
                return self._handle_student_query(
                    message_clean, 
                    contact_id, 
                    salutation
                )
            
            # General FAQ query - Use RAG
            return self._handle_faq_query(
                message_clean,
                salutation,
                chat_context
            )
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return {
                'response': f"{salutation}, I encountered an error. Please try again.",
                'message_type': 'error',
                'confidence': 0.0,
                'sources': [],
                'category': 'error'
            }
    
    def _handle_greeting(self, salutation: str) -> Dict:
        """Handle greeting messages"""
        greetings = [
            f"{salutation}, hello! How can I assist you today?",
            f"Hi {salutation}! I'm here to help with your queries.",
            f"Greetings {salutation}! What can I do for you?"
        ]
        
        import random
        response = random.choice(greetings)
        
        return {
            'response': response,
            'message_type': 'greeting',
            'confidence': 1.0,
            'sources': [],
            'category': 'greeting'
        }
    
    def _handle_acknowledgment(self, salutation: str) -> Dict:
        """Handle acknowledgment/thank you messages"""
        responses = [
            f"{salutation}, glad I could help! Do you have any other questions?",
            f"You're welcome {salutation}! Feel free to ask if you need anything else.",
            f"{salutation}, happy to assist! Let me know if there's anything more."
        ]
        
        import random
        response = random.choice(responses)
        
        return {
            'response': response,
            'message_type': 'acknowledgment',
            'confidence': 1.0,
            'sources': [],
            'category': 'post_interaction'
        }
    
    def _handle_paypal_query(self, salutation: str) -> Dict:
        """Handle PayPal payment queries"""
        response = f"""{salutation}, to proceed with PayPal payment, reply with:

1 - I already have the undertaking letter
2 - Send me the undertaking letter template

Please reply with 1 or 2."""
        
        return {
            'response': response,
            'message_type': 'paypal_query',
            'confidence': 1.0,
            'sources': [],
            'category': 'payment',
            'requires_followup': True
        }
    
    def _handle_publication_query(self, salutation: str, message: str) -> Dict:
        """Handle publication/research queries with RAG"""
        
        # Try to find relevant FAQ first
        answer, confidence, sources = self.rag_engine.query(
            message,
            salutation=salutation
        )
        
        faq_addition = ""
        if confidence >= 0.65:
            faq_addition = f"\n\n{answer}"
        
        response = (
            f"{salutation}, for queries related to publications or research articles, "
            f"please contact our E-Journal Executive:\n\n"
            f"📧 Email: sabitha.k@tauedu.org or ejournal.assist@tau.edu.gy\n"
            f"📱 WhatsApp:\n"
            f"  • Public Health, Management: +91 7397735325\n"
            f"  • Academic Research, Medicine: +91 9500108397"
            f"{faq_addition}"
        )
        
        return {
            'response': response,
            'message_type': 'publication_query',
            'confidence': 1.0,
            'sources': sources,
            'category': 'publication'
        }
    
    def _handle_remittance_query(self, salutation: str) -> Dict:
        """Handle remittance/payment proof queries"""
        response = (
            f"{salutation}, thank you for sharing the remittance copy. "
            f"I will forward it to our Finance team for verification and mapping. "
            f"You can check the status in the CMS portal within 3-10 business days."
        )
        
        return {
            'response': response,
            'message_type': 'remittance_confirmation',
            'confidence': 1.0,
            'sources': [],
            'category': 'finance'
        }
    
    def _is_student_specific_query(self, message: str) -> bool:
        """Check if query requires student-specific data"""
        student_keywords = [
            'my fee', 'my payment', 'my invoice', 'my balance', 'my due',
            'my course', 'my grade', 'my marks', 'my status', 'my enrollment',
            'application number', 'student id', 'my account'
        ]
        
        message_lower = message.lower()
        return any(kw in message_lower for kw in student_keywords)
    
    def _handle_student_query(
        self, 
        message: str, 
        contact_id: str, 
        salutation: str
    ) -> Dict:
        """Handle student-specific queries (fees, academic data)"""
        
        # Extract actual question
        question = extract_question_from_message(message)
        
        # Detect query type
        fees_keywords = ['fee', 'payment', 'invoice', 'due', 'balance', 'pay']
        academic_keywords = ['course', 'grade', 'mark', 'enrollment', 'subject', 'program']
        
        is_fees = any(kw in question.lower() for kw in fees_keywords)
        is_academic = any(kw in question.lower() for kw in academic_keywords)
        
        if is_fees:
            # Fetch invoice data
            invoice_data = self.student_repo.fetch_invoice_data(contact_id)
            
            if invoice_data:
                response = self._generate_invoice_response(
                    invoice_data, 
                    question, 
                    salutation
                )
                return {
                    'response': response,
                    'message_type': 'invoice_response',
                    'confidence': 1.0,
                    'sources': ['Student Invoice Database'],
                    'category': 'fees'
                }
            else:
                # Use RAG for general fees query
                answer, confidence, sources = self.rag_engine.query(
                    question,
                    salutation=salutation
                )
                
                if confidence < 0.65:
                    answer = (
                        f"{salutation}, I couldn't find invoice details for your account. "
                        f"Please provide your application number or contact finance support."
                    )
                
                return {
                    'response': answer,
                    'message_type': 'fees_general',
                    'confidence': confidence,
                    'sources': sources,
                    'category': 'fees'
                }
        
        elif is_academic:
            # Fetch academic data
            academic_data = self.student_repo.fetch_academic_data(contact_id)
            
            if academic_data:
                response = self._generate_academic_response(
                    academic_data,
                    question,
                    salutation
                )
                return {
                    'response': response,
                    'message_type': 'academic_response',
                    'confidence': 1.0,
                    'sources': ['Student Academic Database'],
                    'category': 'academic'
                }
            else:
                response = (
                    f"{salutation}, I couldn't find academic data for your account. "
                    f"Please provide your application number."
                )
                return {
                    'response': response,
                    'message_type': 'data_not_found',
                    'confidence': 0.0,
                    'sources': [],
                    'category': 'academic'
                }
        
        # Fallback to general RAG
        return self._handle_faq_query(question, salutation)
    
    def _handle_faq_query(
        self,
        message: str,
        salutation: str,
        chat_context: List[Dict] = None
    ) -> Dict:
        """Handle general FAQ queries using RAG"""
        
        # Add context if available
        if chat_context:
            context_text = "\n".join([
                f"{msg['sender']}: {msg['message']}" 
                for msg in chat_context[-3:]  # Last 3 messages
            ])
            enhanced_query = f"Context:\n{context_text}\n\nCurrent question: {message}"
        else:
            enhanced_query = message
        
        # Query RAG engine
        answer, confidence, sources = self.rag_engine.query(
            enhanced_query,
            salutation=salutation
        )
        
        # Determine message type based on confidence
        if confidence >= 0.75:
            message_type = 'faq_answer_high_confidence'
        elif confidence >= 0.65:
            message_type = 'faq_answer'
        else:
            message_type = 'low_confidence_answer'
            answer += (
                f"\n\nIf this doesn't fully answer your question, "
                f"please provide more details or contact support."
            )
        
        return {
            'response': answer,
            'message_type': message_type,
            'confidence': confidence,
            'sources': sources,
            'category': 'general'
        }
    
    def _generate_invoice_response(
        self, 
        invoice_data: Dict, 
        question: str, 
        salutation: str
    ) -> str:
        """Generate response from invoice data"""
        
        # Use LLM to format invoice data into natural response
        from langchain.prompts import PromptTemplate
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        
        prompt = PromptTemplate(
            input_variables=["salutation", "question", "invoice_data"],
            template="""You are a helpful university assistant. 

Student asked: {question}

Invoice Data:
{invoice_data}

Generate a clear, professional response addressing their question using the invoice data.
Address them as {salutation}.
Format amounts in currency.
Be concise but complete.

Response:"""
        )
        
        chain = prompt | llm
        response = chain.invoke({
            "salutation": salutation,
            "question": question,
            "invoice_data": str(invoice_data)
        })
        
        return response.content
    
    def _generate_academic_response(
        self,
        academic_data: Dict,
        question: str,
        salutation: str
    ) -> str:
        """Generate response from academic data"""
        
        from langchain.prompts import PromptTemplate
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        
        prompt = PromptTemplate(
            input_variables=["salutation", "question", "academic_data"],
            template="""You are a helpful university assistant.

Student asked: {question}

Academic Data:
{academic_data}

Generate a clear, professional response addressing their question using the academic data.
Address them as {salutation}.
Use bullet points for clarity.

Response:"""
        )
        
        chain = prompt | llm
        response = chain.invoke({
            "salutation": salutation,
            "question": question,
            "academic_data": str(academic_data)
        })
        
        return response.content

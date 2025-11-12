"""
Student Repository - Fetch student-specific data
"""

import pandas as pd
from typing import Dict, Optional, List
from sqlalchemy import text

from src.database.db_manager import get_db_manager
from src.utils.logger import setup_logger

logger = setup_logger("student_repository")


class StudentRepository:
    """Repository for student data operations"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def fetch_student_details(
        self, 
        contact_number: str, 
        contact_name: str
    ) -> Dict:
        """
        Fetch student details by contact number
        
        Returns:
            Dict with ApplicationNumber, Salutation, FullName, etc.
        """
        try:
            # Clean contact number
            contact_clean = ''.join(filter(str.isdigit, contact_number))
            
            query = """
            SELECT 
                ApplicationNumber,
                Salutation,
                FullName,
                Email,
                ProgramName,
                Status
            FROM Student_Details
            WHERE REPLACE(REPLACE(ContactNumber, '+', ''), ' ', '') LIKE :contact
            LIMIT 1
            """
            
            result = self.db.execute_query(
                query,
                {"contact": f"%{contact_clean}%"}
            )
            
            if result:
                row = result[0]
                return {
                    'ApplicationNumber': row[0],
                    'Salutation': row[1] or 'Student',
                    'FullName': row[2],
                    'Email': row[3],
                    'ProgramName': row[4],
                    'Status': row[5]
                }
            else:
                logger.warning(f"⚠️ No student found for contact: {contact_number}")
                return {
                    'ApplicationNumber': '',
                    'Salutation': 'Student',
                    'FullName': contact_name,
                    'Email': '',
                    'ProgramName': '',
                    'Status': ''
                }
                
        except Exception as e:
            logger.error(f"❌ Error fetching student details: {e}")
            return {
                'ApplicationNumber': '',
                'Salutation': 'Student',
                'FullName': contact_name,
                'Email': '',
                'ProgramName': '',
                'Status': ''
            }
    
    def fetch_invoice_data(self, application_number: str) -> Optional[Dict]:
        """
        Fetch invoice/fee data for a student
        
        Returns:
            Dict with invoice details or None
        """
        try:
            query = """
            SELECT 
                InvoiceNumber,
                InvoiceDate,
                TotalAmount,
                PaidAmount,
                BalanceAmount,
                DueDate,
                Status,
                PaymentMethod
            FROM Invoice_Line
            WHERE application_No = :app_number
            ORDER BY InvoiceDate DESC
            LIMIT 5
            """
            
            result = self.db.execute_query(
                query,
                {"app_number": application_number}
            )
            
            if not result:
                return None
            
            invoices = []
            for row in result:
                invoices.append({
                    'InvoiceNumber': row[0],
                    'InvoiceDate': str(row[1]),
                    'TotalAmount': float(row[2]),
                    'PaidAmount': float(row[3]),
                    'BalanceAmount': float(row[4]),
                    'DueDate': str(row[5]),
                    'Status': row[6],
                    'PaymentMethod': row[7]
                })
            
            # Calculate summary
            total_balance = sum(inv['BalanceAmount'] for inv in invoices)
            total_paid = sum(inv['PaidAmount'] for inv in invoices)
            
            return {
                'invoices': invoices,
                'total_balance': total_balance,
                'total_paid': total_paid,
                'invoice_count': len(invoices)
            }
            
        except Exception as e:
            logger.error(f"❌ Error fetching invoice data: {e}")
            return None
    
    def fetch_academic_data(self, application_number: str) -> Optional[Dict]:
        """
        Fetch academic data for a student
        
        Returns:
            Dict with course enrollment, grades, etc.
        """
        try:
            query = """
            SELECT 
                CourseName,
                CourseCode,
                EnrollmentDate,
                Status,
                Grade,
                Credits,
                Mentor
            FROM Student_Academic_Details
            WHERE Application_Number = :app_number
            ORDER BY EnrollmentDate DESC
            """
            
            result = self.db.execute_query(
                query,
                {"app_number": application_number}
            )
            
            if not result:
                return None
            
            courses = []
            for row in result:
                courses.append({
                    'CourseName': row[0],
                    'CourseCode': row[1],
                    'EnrollmentDate': str(row[2]),
                    'Status': row[3],
                    'Grade': row[4],
                    'Credits': row[5],
                    'Mentor': row[6]
                })
            
            return {
                'courses': courses,
                'total_courses': len(courses),
                'completed_courses': sum(1 for c in courses if c['Status'] == 'Completed'),
                'in_progress': sum(1 for c in courses if c['Status'] == 'In Progress')
            }
            
        except Exception as e:
            logger.error(f"❌ Error fetching academic data: {e}")
            return None
    
    def get_conversation_history(
        self, 
        contact_id: str, 
        limit: int = 10
    ) -> pd.DataFrame:
        """
        Get conversation history for a contact
        
        Returns:
            DataFrame with recent messages
        """
        try:
            query = """
            SELECT 
                ReceivedMessage,
                ResponseFromBot,
                MessageType,
                Category,
                Timestamp,
                ConfidenceLevel
            FROM AI_Conversation_Log
            WHERE ContactID = :contact_id
            ORDER BY Timestamp DESC
            LIMIT :limit
            """
            
            result = self.db.execute_query(
                query,
                {"contact_id": contact_id, "limit": limit}
            )
            
            if not result:
                return pd.DataFrame()
            
            df = pd.DataFrame(result, columns=[
                'ReceivedMessage',
                'ResponseFromBot',
                'MessageType',
                'Category',
                'Timestamp',
                'ConfidenceLevel'
            ])
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching conversation history: {e}")
            return pd.DataFrame()
    
    def log_conversation(
        self,
        contact_id: str,
        whatsapp_name: str,
        received_message: str,
        response_from_bot: str,
        message_type: str,
        category: str,
        confidence_level: float,
        faq_question: str = "",
        media_type: str = "text",
        bot_name: str = ""
    ) -> bool:
        """Log conversation to database"""
        try:
            query = """
            INSERT INTO AI_Conversation_Log (
                ContactID,
                WhatsAppName,
                ReceivedMessage,
                ResponseFromBot,
                MessageType,
                MediaType,
                Category,
                ConfidenceLevel,
                FAQQuestion,
                BotName,
                Timestamp
            ) VALUES (
                :contact_id,
                :whatsapp_name,
                :received_message,
                :response_from_bot,
                :message_type,
                :media_type,
                :category,
                :confidence_level,
                :faq_question,
                :bot_name,
                NOW()
            )
            """
            
            params = {
                "contact_id": contact_id,
                "whatsapp_name": whatsapp_name,
                "received_message": received_message[:1000],  # Limit length
                "response_from_bot": response_from_bot[:1000],
                "message_type": message_type,
                "media_type": media_type,
                "category": category,
                "confidence_level": confidence_level,
                "faq_question": faq_question[:500],
                "bot_name": bot_name
            }
            
            return self.db.execute_write(query, params)
            
        except Exception as e:
            logger.error(f"❌ Error logging conversation: {e}")
            return False

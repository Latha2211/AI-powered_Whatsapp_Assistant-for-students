"""
Message Helper Functions - Utilities for message classification and parsing
Uses configurable keywords from JSON
"""

import re
import json
import os
from typing import Optional, List


class MessageHelpers:
    """Message classification and parsing utilities with configurable keywords"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize with keyword configuration
        
        Args:
            config_path: Path to keywords JSON file
        """
        if config_path is None:
            config_path = os.getenv("KEYWORDS_CONFIG_PATH", "config/keywords.json")
        
        self.keywords = self._load_keywords(config_path)
    
    def _load_keywords(self, config_path: str) -> dict:
        """Load keywords from JSON configuration"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Return default configuration if file doesn't exist
                return self._get_default_keywords()
        except Exception as e:
            print(f"Warning: Failed to load keywords config: {e}")
            return self._get_default_keywords()
    
    def _get_default_keywords(self) -> dict:
        """Get default keyword configuration"""
        return {
            "greetings": [
                "hi", "hello", "hey", "good morning", "good afternoon",
                "good evening", "good night", "greetings", "namaste",
                "hola", "bonjour", "salut"
            ],
            "acknowledgments": [
                "thanks", "thank you", "thx", "ty", "thanku", "tnx",
                "noted", "noted with thanks",
                "okay", "ok", "okey", "okie", "okk",
                "k", "kk", "kay",
                "alright", "all right", "rite",
                "got it", "gotcha", "understood",
                "cool", "fine", "great", "awesome", "perfect", "sure",
                "confirmed", "confirm", "done", "completed",
                "yep", "yes", "yeah", "ya", "yah"
            ],
            "paypal": [
                "paypal", "pay pal", "paypal payment", "pay through paypal",
                "paypal option", "paypal link", "undertaking letter",
                "paypal account"
            ],
            "publications": [
                "publication", "article", "research paper", "journal",
                "publish", "manuscript", "paper submission",
                "research publication", "journal article", "publish paper",
                "research work", "e-journal"
            ],
            "remittance": [
                "remittance", "payment proof", "receipt", "transaction",
                "payment receipt", "bank transfer", "payment confirmation",
                "proof of payment", "payment slip"
            ],
            "fees": [
                "fee", "fees", "payment", "invoice", "pay", "due",
                "balance", "amount", "bill", "tuition", "outstanding",
                "partial", "next installment", "fee structure"
            ],
            "academic": [
                "course", "grade", "mark", "enrollment", "subject",
                "program", "academic", "mentor", "block", "test", "exam",
                "status", "duration", "study material", "assignment"
            ],
            "lms_cms": [
                "lms", "cms", "learning management", "course management",
                "portal", "login", "password", "access", "interface"
            ],
            "greeting_prefixes": [
                "hi", "hello", "hey", "good morning", "good afternoon",
                "good evening", "dear", "respected", "sir", "madam"
            ],
            "salutations": [
                "sir", "madam", "ma'am", "mr", "mrs", "ms", "dr", "prof"
            ],
            "student_specific": [
                "my fee", "my payment", "my invoice", "my balance", "my due",
                "my course", "my grade", "my marks", "my status", "my enrollment",
                "application number", "student id", "my account"
            ],
            "tau_university": [
                "texila", "tau", "texila american university",
                "our university", "this university", "university details",
                "about tau", "about texila"
            ]
        }
    
    def extract_contact_name(self, chat_element) -> str:
        """
        Extract contact name from chat element
        
        Args:
            chat_element: Selenium WebElement of the chat
        
        Returns:
            Contact name string
        """
        try:
            # Try multiple XPaths for contact name
            xpaths = [
                ".//span[@title]",
                ".//div[contains(@class, 'chat-title')]",
                ".//span[contains(@class, '_11JPr')]",
                ".//div[@dir='auto']//span"
            ]
            
            for xpath in xpaths:
                try:
                    name_element = chat_element.find_element("xpath", xpath)
                    name = name_element.get_attribute("title") or name_element.text
                    if name and name.strip():
                        return name.strip()
                except:
                    continue
            
            # Fallback to element text
            return chat_element.text.split('\n')[0].strip() or "Unknown"
        
        except Exception:
            return "Unknown"
    
    def is_unsaved_contact(self, contact_name: str, contact_number: str) -> bool:
        """
        Check if contact is unsaved (shows as phone number)
        
        Args:
            contact_name: Name from chat
            contact_number: Extracted number
        
        Returns:
            True if unsaved contact
        """
        # If name contains only digits and + symbols, it's likely unsaved
        cleaned = contact_name.replace('+', '').replace(' ', '').replace('-', '')
        return cleaned.isdigit() and len(cleaned) >= 10
    
    def is_pure_greeting(self, message: str) -> bool:
        """
        Check if message is a pure greeting (no question/content)
        
        Args:
            message: Message text
        
        Returns:
            True if pure greeting
        """
        greetings = self.keywords.get("greetings", [])
        
        message_lower = message.lower().strip()
        
        # Check if message is just a greeting (with optional punctuation)
        words = re.findall(r'\w+', message_lower)
        
        return (
            len(words) <= 3 and 
            any(greeting in message_lower for greeting in greetings) and
            '?' not in message
        )
    
    def is_satisfied_response(
        self, 
        message: str, 
        previous_interaction: Optional[dict] = None
    ) -> bool:
        """
        Check if message indicates satisfaction/acknowledgment
        
        Args:
            message: Message text
            previous_interaction: Previous conversation context
        
        Returns:
            True if satisfied
        """
        acknowledgments = self.keywords.get("acknowledgments", [])
        
        message_lower = message.lower().strip()
        
        # Short acknowledgments
        if len(message.split()) <= 3:
            return any(kw in message_lower for kw in acknowledgments)
        
        return False
    
    def is_paypal_query(self, message: str) -> bool:
        """
        Check if message is about PayPal payment
        
        Args:
            message: Message text
        
        Returns:
            True if PayPal query
        """
        paypal_keywords = self.keywords.get("paypal", [])
        message_lower = message.lower()
        return any(kw in message_lower for kw in paypal_keywords)
    
    def is_publication_query(self, message: str) -> bool:
        """
        Check if message is about publications/research
        
        Args:
            message: Message text
        
        Returns:
            True if publication query
        """
        publication_keywords = self.keywords.get("publications", [])
        message_lower = message.lower()
        return any(kw in message_lower for kw in publication_keywords)
    
    def is_remittance_query(self, message: str) -> bool:
        """
        Check if message is about remittance/payment proof
        
        Args:
            message: Message text
        
        Returns:
            True if remittance query
        """
        remittance_keywords = self.keywords.get("remittance", [])
        message_lower = message.lower()
        return any(kw in message_lower for kw in remittance_keywords)
    
    def is_fees_query(self, message: str) -> bool:
        """
        Check if message is about fees/payments
        
        Args:
            message: Message text
        
        Returns:
            True if fees query
        """
        fees_keywords = self.keywords.get("fees", [])
        message_lower = message.lower()
        return any(kw in message_lower for kw in fees_keywords)
    
    def is_academic_query(self, message: str) -> bool:
        """
        Check if message is about academic matters
        
        Args:
            message: Message text
        
        Returns:
            True if academic query
        """
        academic_keywords = self.keywords.get("academic", [])
        message_lower = message.lower()
        return any(kw in message_lower for kw in academic_keywords)
    
    def is_student_specific_query(self, message: str) -> bool:
        """
        Check if query requires student-specific data
        
        Args:
            message: Message text
        
        Returns:
            True if student-specific
        """
        student_keywords = self.keywords.get("student_specific", [])
        message_lower = message.lower()
        return any(kw in message_lower for kw in student_keywords)
    
    def is_tau_university_query(self, message: str) -> bool:
        """
        Check if message is about TAU university
        
        Args:
            message: Message text
        
        Returns:
            True if TAU query
        """
        tau_keywords = self.keywords.get("tau_university", [])
        message_lower = message.lower()
        return any(kw in message_lower for kw in tau_keywords)
    
    def extract_question_from_message(self, message: str) -> str:
        """
        Extract the actual question from a message with greetings
        
        Args:
            message: Full message text
        
        Returns:
            Extracted question
        """
        # Get configurable prefixes
        greeting_prefixes = self.keywords.get("greeting_prefixes", [])
        salutations = self.keywords.get("salutations", [])
        
        # Build regex pattern from keywords
        greeting_pattern = '|'.join(re.escape(g) for g in greeting_prefixes)
        salutation_pattern = '|'.join(re.escape(s) for s in salutations)
        
        # Remove greetings
        if greeting_pattern:
            cleaned = re.sub(
                f'^({greeting_pattern})\\s*[,.]?\\s*',
                '',
                message,
                flags=re.IGNORECASE
            )
        else:
            cleaned = message
        
        # Remove salutations
        if salutation_pattern:
            cleaned = re.sub(
                f'\\b({salutation_pattern})\\b[,.]?\\s*',
                '',
                cleaned,
                flags=re.IGNORECASE
            )
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned if cleaned else message
    
    def classify_message_category(self, message: str) -> str:
        """
        Classify message into a category
        
        Args:
            message: Message text
        
        Returns:
            Category string
        """
        message_lower = message.lower()
        
        # Check each category
        if self.is_paypal_query(message):
            return "payment"
        elif self.is_publication_query(message):
            return "publication"
        elif self.is_remittance_query(message):
            return "remittance"
        elif self.is_fees_query(message):
            return "fees"
        elif self.is_academic_query(message):
            return "academic"
        elif self.is_pure_greeting(message):
            return "greeting"
        elif self.is_satisfied_response(message):
            return "acknowledgment"
        else:
            return "general"
    
    def get_keywords_for_category(self, category: str) -> List[str]:
        """
        Get keywords for a specific category
        
        Args:
            category: Category name
        
        Returns:
            List of keywords
        """
        return self.keywords.get(category, [])
    
    def add_keywords_to_category(self, category: str, keywords: List[str]) -> bool:
        """
        Add new keywords to a category (runtime modification)
        
        Args:
            category: Category name
            keywords: List of keywords to add
        
        Returns:
            True if successful
        """
        try:
            if category not in self.keywords:
                self.keywords[category] = []
            
            self.keywords[category].extend(keywords)
            self.keywords[category] = list(set(self.keywords[category]))  # Remove duplicates
            
            return True
        except Exception:
            return False


# Singleton instance
_message_helpers_instance = None

def get_message_helpers() -> MessageHelpers:
    """Get or create MessageHelpers singleton"""
    global _message_helpers_instance
    if _message_helpers_instance is None:
        _message_helpers_instance = MessageHelpers()
    return _message_helpers_instance


# Convenience functions for backward compatibility
def extract_contact_name(chat_element) -> str:
    return get_message_helpers().extract_contact_name(chat_element)

def is_unsaved_contact(contact_name: str, contact_number: str) -> bool:
    return get_message_helpers().is_unsaved_contact(contact_name, contact_number)

def is_pure_greeting(message: str) -> bool:
    return get_message_helpers().is_pure_greeting(message)

def is_satisfied_response(message: str, previous_interaction: Optional[dict] = None) -> bool:
    return get_message_helpers().is_satisfied_response(message, previous_interaction)

def is_paypal_query(message: str) -> bool:
    return get_message_helpers().is_paypal_query(message)

def is_publication_query(message: str) -> bool:
    return get_message_helpers().is_publication_query(message)

def is_remittance_query(message: str) -> bool:
    return get_message_helpers().is_remittance_query(message)

def extract_question_from_message(message: str) -> str:
    return get_message_helpers().extract_question_from_message(message)

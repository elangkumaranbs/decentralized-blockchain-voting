import random
import string
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EmailJSService:
    """
    EmailJS service for handling email verification in the voting system.
    This service manages verification codes and integrates with EmailJS for sending emails.
    """
    
    def __init__(self):
        self.service_id = getattr(settings, 'EMAILJS_SERVICE_ID', '')
        self.template_id = getattr(settings, 'EMAILJS_TEMPLATE_ID', '')
        self.public_key = getattr(settings, 'EMAILJS_PUBLIC_KEY', '')
        self.private_key = getattr(settings, 'EMAILJS_PRIVATE_KEY', '')
        
        # Verification code settings
        self.code_length = 6
        self.code_expiry_minutes = 15  # Increased from 10 to 15 minutes
        self.max_attempts = 3
    
    def is_configured(self) -> bool:
        """
        Check if EmailJS is properly configured.
        """
        return bool(self.service_id and self.template_id and self.public_key and self.private_key)
    
    def generate_verification_code(self) -> str:
        """
        Generate a random 6-digit verification code.
        """
        return ''.join(random.choices(string.digits, k=self.code_length))
    
    def store_verification_code(self, email: str, code: str) -> bool:
        """
        Store verification code in cache with expiry.
        """
        try:
            cache_key = f"email_verification_{email}"
            verification_data = {
                'code': code,
                'created_at': timezone.now().isoformat(),
                'attempts': 0
            }
            
            # Store for specified minutes
            cache.set(cache_key, verification_data, timeout=self.code_expiry_minutes * 60)
            logger.info(f"Verification code stored for email: {email}")
            return True
        except Exception as e:
            logger.error(f"Error storing verification code: {e}")
            return False
    
    def get_verification_data(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve verification data from cache.
        """
        try:
            cache_key = f"email_verification_{email}"
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Error retrieving verification data: {e}")
            return None
    
    def verify_code(self, email: str, provided_code: str) -> Dict[str, Any]:
        """
        Verify the provided code against stored code.
        """
        try:
            verification_data = self.get_verification_data(email)
            
            # Debug logging
            logger.info(f"Verifying code for email: {email}")
            logger.info(f"Provided code: {provided_code}")
            logger.info(f"Stored data exists: {verification_data is not None}")
            
            if not verification_data:
                logger.warning(f"No verification data found for email: {email}")
                return {
                    'success': False,
                    'error': 'No verification code found or code has expired',
                    'error_code': 'CODE_NOT_FOUND'
                }
            
            # Debug the stored code
            stored_code = verification_data.get('code', '')
            logger.info(f"Stored code: {stored_code}")
            logger.info(f"Code match: {stored_code == provided_code}")
            
            # Check attempts
            if verification_data['attempts'] >= self.max_attempts:
                self.clear_verification_code(email)
                return {
                    'success': False,
                    'error': 'Maximum verification attempts exceeded',
                    'error_code': 'MAX_ATTEMPTS_EXCEEDED'
                }
            
            # Increment attempts
            verification_data['attempts'] += 1
            cache_key = f"email_verification_{email}"
            cache.set(cache_key, verification_data, timeout=self.code_expiry_minutes * 60)
            
            # Verify code
            if verification_data['code'] == provided_code:
                self.clear_verification_code(email)
                logger.info(f"Email verification successful for: {email}")
                return {
                    'success': True,
                    'message': 'Email verified successfully'
                }
            else:
                remaining_attempts = self.max_attempts - verification_data['attempts']
                logger.warning(f"Invalid code for {email}. Remaining attempts: {remaining_attempts}")
                return {
                    'success': False,
                    'error': f'Invalid verification code. {remaining_attempts} attempts remaining',
                    'error_code': 'INVALID_CODE',
                    'remaining_attempts': remaining_attempts
                }
                
        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            return {
                'success': False,
                'error': 'Verification failed due to system error',
                'error_code': 'SYSTEM_ERROR'
            }
    
    def clear_verification_code(self, email: str) -> bool:
        """
        Clear verification code from cache.
        """
        try:
            cache_key = f"email_verification_{email}"
            cache.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"Error clearing verification code: {e}")
            return False
    
    def send_verification_email(self, email: str, voter_name: str = None, verification_code: str = None) -> Dict[str, Any]:
        """
        Send verification email using EmailJS integration.
        Returns configuration for frontend EmailJS to handle the actual sending.
        For now, this returns the code for frontend to handle EmailJS integration.
        """
        try:
            if not self.is_configured():
                return {
                    'success': False,
                    'error': 'EmailJS is not properly configured',
                    'error_code': 'NOT_CONFIGURED'
                }
            
            # Use provided code or generate new one
            if verification_code is None:
                verification_code = self.generate_verification_code()
                
                if not self.store_verification_code(email, verification_code):
                    return {
                        'success': False,
                        'error': 'Failed to store verification code',
                        'error_code': 'STORAGE_ERROR'
                    }
            
            # Return data for frontend EmailJS integration
            return {
                'success': True,
                'message': 'Verification code generated successfully',
                'emailjs_config': {
                    'service_id': self.service_id,
                    'template_id': self.template_id,
                    'public_key': self.public_key,
                    'template_params': {
                        'to_email': email,
                        'to_name': voter_name or email.split('@')[0],
                        'verification_code': verification_code,
                        'expiry_minutes': self.code_expiry_minutes
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            return {
                'success': False,
                'error': 'Failed to send verification email',
                'error_code': 'SEND_ERROR'
            }
    
    def resend_verification_email(self, email: str, voter_name: str = '') -> Dict[str, Any]:
        """
        Resend verification email (generates new code).
        """
        # Clear existing code first
        self.clear_verification_code(email)
        
        # Send new verification email
        return self.send_verification_email(email, voter_name)
    
    def get_verification_status(self, email: str) -> Dict[str, Any]:
        """
        Get current verification status for an email.
        """
        try:
            verification_data = self.get_verification_data(email)
            
            if not verification_data:
                return {
                    'has_pending_verification': False,
                    'remaining_attempts': self.max_attempts,
                    'expiry_minutes': self.code_expiry_minutes
                }
            
            # Parse the stored datetime and make it timezone-aware if needed
            created_at = datetime.fromisoformat(verification_data['created_at'])
            if created_at.tzinfo is None:
                created_at = timezone.make_aware(created_at)
            
            expiry_time = created_at + timedelta(minutes=self.code_expiry_minutes)
            remaining_time = expiry_time - timezone.now()
            
            return {
                'has_pending_verification': True,
                'remaining_attempts': self.max_attempts - verification_data['attempts'],
                'remaining_time_seconds': max(0, int(remaining_time.total_seconds())),
                'created_at': verification_data['created_at']
            }
            
        except Exception as e:
            logger.error(f"Error getting verification status: {e}")
            return {
                'has_pending_verification': False,
                'remaining_attempts': self.max_attempts,
                'expiry_minutes': self.code_expiry_minutes
            }


# Global service instance
def get_emailjs_service():
    """Get EmailJS service instance"""
    return EmailJSService()

# Global service instance
emailjs_service = get_emailjs_service()
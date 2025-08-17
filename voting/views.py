from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login, logout
import logging
from django.db.models import Count, Q
import json
import hashlib
import uuid
from datetime import datetime, timedelta

from .models import PoliticalParty, Voter, Vote, EmailVerification, VotingSession
# from .supabase_client import supabase_client  # Commented out - module not available
from .emailjs_service import emailjs_service
from blockchain.blockchain_client import blockchain_client
from blockchain.models import VoteRecord
import logging

logger = logging.getLogger(__name__)

class VotingHomeView(View):
    """Main voting interface"""
    
    def get(self, request):
        """Display voting interface"""
        # Get active voting session
        active_session = VotingSession.objects.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        
        if not active_session:
            return render(request, 'voting/no_active_session.html')
        
        # Get active political parties
        parties = PoliticalParty.objects.filter(is_active=True).order_by('party_name')
        
        context = {
            'session': active_session,
            'parties': parties,
            'total_parties': parties.count()
        }
        
        return render(request, 'voting/voting_home.html', context)

class AadhaarVerificationView(View):
    """Handle Aadhaar-only verification process with OTP email verification"""
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Verify voter by Aadhaar number and send OTP to email"""
        try:
            data = json.loads(request.body)
            aadhaar_number = data.get('aadhaar_number', '').strip()
            
            if not aadhaar_number:
                return JsonResponse({
                    'success': False,
                    'message': 'Aadhaar number is required'
                })
            
            # Validate Aadhaar number format (12 digits)
            if not aadhaar_number.isdigit() or len(aadhaar_number) != 12:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid Aadhaar number format. Please enter 12 digits.'
                })
            
            # Check if voter exists
            try:
                voter = Voter.objects.get(
                    aadhaar_number=aadhaar_number
                )
            except Voter.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'No voter found with this Aadhaar number. Please contact election officials.'
                })
            
            # Generate and send OTP to voter's email
            verification_code = emailjs_service.generate_verification_code()
            
            # Store verification code
            if not emailjs_service.store_verification_code(voter.email, verification_code):
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to generate verification code. Please try again.'
                })
            
            # Get EmailJS configuration for frontend
            email_result = emailjs_service.send_verification_email(voter.email, voter.full_name)
            
            if not email_result.get('success'):
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to generate verification email. Please try again.'
                })
            
            # Store voter info in session for profile display
            request.session['pending_voter_id'] = str(voter.id)
            request.session['pending_voter_email'] = voter.email
            request.session['aadhaar_verified'] = True
            # Extend session timeout to match verification code expiry (15 minutes)
            request.session.set_expiry(900)  # 15 minutes in seconds
            
            # Return success and redirect to voter profile
            return JsonResponse({
                'success': True,
                'message': 'Aadhaar verified successfully! Redirecting to your profile...',
                'redirect_url': '/voter-profile/',
                'voter': {
                    'id': voter.id,
                    'full_name': voter.full_name,
                    'email': voter.email,
                    'aadhaar_number': voter.aadhaar_number,
                    'has_voted': voter.has_voted,
                    'is_active': voter.is_active
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request format'
            })
        except Exception as e:
            logger.error(f"Error in Aadhaar verification: {e}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred during verification'
            })

class VoterVerificationView(View):
    """Handle voter verification process"""
    
    def get(self, request):
        """Display voter verification form"""
        return render(request, 'voting/voter_verification.html')
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Verify voter credentials"""
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            aadhaar_number = data.get('aadhaar_number', '').strip()
            
            if not email or not aadhaar_number:
                return JsonResponse({
                    'success': False,
                    'message': 'Email and Aadhaar number are required'
                })
            
            # Validate Aadhaar number format (12 digits)
            if not aadhaar_number.isdigit() or len(aadhaar_number) != 12:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid Aadhaar number format'
                })
            
            # Check if voter exists and is eligible
            try:
                voter = Voter.objects.get(
                    email=email,
                    aadhaar_number=aadhaar_number,
                    is_active=True
                )
            except Voter.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Voter not found or not eligible to vote'
                })
            
            # Check if voter has already voted
            if voter.has_voted:
                return JsonResponse({
                    'success': False,
                    'message': 'You have already cast your vote'
                })
            
            # Generate verification token
            verification_token = str(uuid.uuid4())
            
            # Generate verification code for email
            verification_code = emailjs_service.generate_verification_code()
            
            # Create or update email verification
            verification, created = EmailVerification.objects.get_or_create(
                voter=voter,
                is_used=False,
                defaults={
                    'verification_code': verification_code,
                    'expires_at': timezone.now() + timedelta(minutes=15)
                }
            )
            
            if not created:
                verification.verification_code = verification_code
                verification.expires_at = timezone.now() + timedelta(minutes=15)
                verification.is_used = False
                verification.save()
            
            # Store verification code in EmailJS service cache
            emailjs_service.store_verification_code(voter.email, verification_code)
            
            # Store voter ID in session for verification
            request.session['pending_voter_id'] = str(voter.id)
            request.session['verification_token'] = verification_token
            # Extend session timeout to match verification code expiry (15 minutes)
            request.session.set_expiry(900)  # 15 minutes in seconds
            
            # Send verification email using EmailJS
            email_result = emailjs_service.send_verification_email(
                email=voter.email,
                voter_name=voter.full_name
            )
            
            if email_result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Verification email sent successfully',
                    'verification_token': verification_token,
                    'voter_name': voter.full_name,
                    'emailjs_config': email_result.get('emailjs_config', {})
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f"Failed to send verification email: {email_result.get('error', 'Unknown error')}"
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request format'
            })
        except Exception as e:
            logger.error(f"Error in voter verification: {e}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred during verification'
            })

class EmailVerificationView(View):
    """Handle email verification"""
    
    def get(self, request):
        """Display email verification form"""
        # Check if there's an active verification session
        voter_id = request.session.get('pending_voter_id')
        if not voter_id:
            messages.error(request, 'No active verification session. Please start the verification process again.')
            return redirect('voting:voter_verification')
        
        try:
            voter = Voter.objects.get(id=voter_id)
        except Voter.DoesNotExist:
            messages.error(request, 'Voter not found. Please start the verification process again.')
            return redirect('voting:voter_verification')
        
        context = {
            'voter_email': voter.email,
            'emailjs_public_key': getattr(settings, 'EMAILJS_PUBLIC_KEY', ''),
        }
        
        return render(request, 'voting/email_verification.html', context)
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Verify email token"""
        try:
            data = json.loads(request.body)
            verification_code = data.get('verification_code', '').strip()
            
            if not verification_code:
                return JsonResponse({
                    'success': False,
                    'message': 'Verification code is required'
                })
            
            # Get verification token from session
            session_token = request.session.get('verification_token')
            voter_id = request.session.get('pending_voter_id')
            
            if not session_token or not voter_id:
                # Try to recover from aadhaar verification session
                voter_id = request.session.get('pending_voter_id')
                if voter_id and request.session.get('aadhaar_verified'):
                    # For Aadhaar-based verification, use the verification code as token
                    session_token = verification_code
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Verification session expired. Please start the verification process again.',
                        'redirect_url': '/verify-aadhaar/'
                    })
            
            # Get voter email for verification
            try:
                voter = Voter.objects.get(id=voter_id)
                voter_email = voter.email
            except Voter.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Voter not found'
                })
            
            # Verify code using EmailJS service
            verification_result = emailjs_service.verify_code(voter_email, verification_code)
            
            # Extend session on active verification attempt
            request.session.set_expiry(900)  # Reset to 15 minutes
            
            if verification_result['success']:
                # Mark verification as complete in database
                try:
                    # Find the most recent unused verification for this voter
                    verification = EmailVerification.objects.filter(
                        voter_id=voter_id,
                        is_used=False,
                        verification_code=verification_code
                    ).first()
                    
                    if verification:
                        verification.is_used = True
                        verification.save()
                    
                    # Store verified voter in session
                    request.session['verified_voter_id'] = voter_id
                    request.session['email_verified'] = True  # Add this line
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Email verified successfully'
                    })
                    
                except Exception as e:
                    logger.error(f"Error updating verification record: {e}")
                    # Even if database update fails, the verification was successful
                    request.session['verified_voter_id'] = voter_id
                    request.session['email_verified'] = True  # Add this line too
                    return JsonResponse({
                        'success': True,
                        'message': 'Email verified successfully'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'message': verification_result.get('error', 'Verification failed'),
                    'error_code': verification_result.get('error_code'),
                    'remaining_attempts': verification_result.get('remaining_attempts')
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request format'
            })
        except Exception as e:
            logger.error(f"Error in email verification: {e}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred during verification'
            })

class VoterSearchView(View):
    """Handle voter search functionality"""
    
    def get(self, request):
        """Show voter search page"""
        return render(request, 'voting/voter_search.html', {
            'title': 'Search Voter Database',
            'page_title': 'Find Your Voter Record',
            'description': 'Search by Aadhaar number, name, or email to find your voter profile'
        })
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Search for voters in the database"""
        try:
            data = json.loads(request.body)
            search_query = data.get('search_query', '').strip()
            search_type = data.get('search_type', 'aadhaar')  # aadhaar, name, email, all
            
            if not search_query:
                return JsonResponse({
                    'success': False,
                    'message': 'Please enter a search query'
                })
            
            # Build search filters based on type
            voters = Voter.objects.filter(is_active=True)
            
            if search_type == 'aadhaar':
                # Search by Aadhaar number (exact or partial match)
                voters = voters.filter(aadhaar_number__icontains=search_query)
            elif search_type == 'name':
                # Search by name (case-insensitive)
                voters = voters.filter(full_name__icontains=search_query)
            elif search_type == 'email':
                # Search by email (case-insensitive)
                voters = voters.filter(email__icontains=search_query)
            elif search_type == 'all':
                # Search across all fields
                from django.db.models import Q
                voters = voters.filter(
                    Q(aadhaar_number__icontains=search_query) |
                    Q(full_name__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(constituency__icontains=search_query) |
                    Q(region__icontains=search_query)
                )
            
            # Limit results to prevent overwhelming response
            voters = voters[:20]  # Maximum 20 results
            
            if not voters.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'No voters found matching your search criteria'
                })
            
            # Format voter data for response
            voter_list = []
            for voter in voters:
                voter_data = {
                    'id': str(voter.id),
                    'full_name': voter.full_name,
                    'email': voter.email,
                    'aadhaar_number': voter.aadhaar_number,
                    'constituency': voter.constituency,
                    'region': voter.region,
                    'date_of_birth': voter.date_of_birth.strftime('%Y-%m-%d'),
                    'age': voter.age,
                    'gender': voter.get_gender_display(),
                    'has_voted': voter.has_voted,
                    'email_verified': voter.email_verified,
                    'verification_status': voter.get_verification_status_display(),
                    'profile_picture_available': bool(voter.profile_picture_data)
                }
                voter_list.append(voter_data)
            
            return JsonResponse({
                'success': True,
                'message': f'Found {len(voter_list)} voter(s)',
                'voters': voter_list,
                'total_count': len(voter_list)
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request format'
            })
        except Exception as e:
            logger.error(f"Error searching voters: {e}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while searching. Please try again.'
            })

class VoterQuickVerifyView(View):
    """Quick verification for found voters to proceed to voting"""
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Verify a specific voter and set up session for voting"""
        try:
            data = json.loads(request.body)
            voter_id = data.get('voter_id')
            verification_method = data.get('verification_method', 'email')  # email or direct
            
            if not voter_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Voter ID is required'
                })
            
            # Get voter
            try:
                voter = Voter.objects.get(id=voter_id, is_active=True)
            except Voter.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Voter not found or inactive'
                })
            
            # Check if voter has already voted
            if voter.has_voted:
                return JsonResponse({
                    'success': False,
                    'message': 'This voter has already cast their vote'
                })
            
            # Check if there's an active voting session
            active_session = VotingSession.objects.filter(
                is_active=True,
                start_time__lte=timezone.now(),
                end_time__gte=timezone.now()
            ).first()
            
            if not active_session:
                return JsonResponse({
                    'success': False,
                    'message': 'No active voting session available'
                })
            
            if verification_method == 'email':
                # Send OTP to email for verification
                verification_code = emailjs_service.generate_verification_code()
                
                # Store verification code
                if not emailjs_service.store_verification_code(voter.email, verification_code):
                    return JsonResponse({
                        'success': False,
                        'message': 'Failed to generate verification code. Please try again.'
                    })
                
                # Send OTP email
                email_result = emailjs_service.send_verification_email(voter.email, voter.full_name)
                
                if email_result.get('success'):
                    # Set up session for verification
                    request.session['pending_voter_id'] = str(voter.id)
                    request.session['search_verified'] = True
                    request.session['verification_method'] = 'email'
                    request.session.set_expiry(900)  # 15 minutes
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Verification code sent to {voter.email}',
                        'requires_otp': True,
                        'voter_email': voter.email,
                        'emailjs_config': email_result.get('emailjs_config', {})
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f"Failed to send verification email: {email_result.get('error', 'Unknown error')}"
                    })
            
            elif verification_method == 'direct':
                # Direct verification (for admin or testing purposes)
                request.session['verified_voter_id'] = str(voter.id)
                request.session['search_verified'] = True
                request.session['email_verified'] = True
                request.session.set_expiry(900)  # 15 minutes
                
                return JsonResponse({
                    'success': True,
                    'message': 'Voter verified successfully',
                    'direct_access': True,
                    'redirect_url': '/cast-vote/'
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid verification method'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request format'
            })
        except Exception as e:
            logger.error(f"Error in quick voter verification: {e}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred during verification'
            })

class VoterProfileView(View):
    """Display voter profile after Aadhaar verification and handle OTP for voting"""
    
    def get(self, request):
        """Show voter profile page after Aadhaar verification"""
        try:
            # Check if Aadhaar is verified
            pending_voter_id = request.session.get('pending_voter_id')
            aadhaar_verified = request.session.get('aadhaar_verified', False)
            
            if not pending_voter_id or not aadhaar_verified:
                messages.error(request, 'Please verify your Aadhaar number first')
                return redirect('voting:aadhaar_verification')
            
            # Get voter details
            try:
                voter = Voter.objects.get(id=pending_voter_id, is_active=True)
            except Voter.DoesNotExist:
                messages.error(request, 'Voter not found')
                return redirect('voting:aadhaar_verification')
            
            # Check if voter has already voted
            if voter.has_voted:
                messages.warning(request, 'You have already cast your vote')
                return redirect('voting:home')
            
            # Check if there's an active voting session
            active_session = VotingSession.objects.filter(
                is_active=True,
                start_time__lte=timezone.now(),
                end_time__gte=timezone.now()
            ).first()
            
            if not active_session:
                messages.error(request, 'No active voting session')
                return redirect('voting:home')
            
            # Get active political parties for candidate selection with symbol data
            parties = PoliticalParty.objects.filter(is_active=True).order_by('party_name')
            
            context = {
                'title': 'Voter Profile - Ready to Vote',
                'voter': voter,
                'active_session': active_session,
                'voter_age': voter.age,
                'email_verified': request.session.get('email_verified', False),
                'parties': parties,
                'total_parties': parties.count(),
                'emailjs_public_key': getattr(settings, 'EMAILJS_PUBLIC_KEY', ''),
                'emailjs_service_id': getattr(settings, 'EMAILJS_SERVICE_ID', ''),
                'emailjs_template_id': getattr(settings, 'EMAILJS_TEMPLATE_ID', ''),
                'MEDIA_URL': settings.MEDIA_URL,
            }
            
            return render(request, 'voting/voter_profile.html', context)
            
        except Exception as e:
            logger.error(f"Error showing voter profile: {e}")
            messages.error(request, 'An error occurred while loading voter profile')
            return redirect('voting:home')
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Handle sending OTP when user clicks Vote Now"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            logger.info(f"VoterProfileView POST: action={action}, data keys={list(data.keys())}")
            
            if action == 'send_vote_otp':
                # Check session
                pending_voter_id = request.session.get('pending_voter_id')
                aadhaar_verified = request.session.get('aadhaar_verified', False)
                
                if not pending_voter_id or not aadhaar_verified:
                    return JsonResponse({
                        'success': False,
                        'message': 'Session expired. Please verify your Aadhaar again.'
                    })
                
                # Get voter
                try:
                    voter = Voter.objects.get(id=pending_voter_id, is_active=True)
                except Voter.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Voter not found'
                    })
                
                # Check if already voted
                if voter.has_voted:
                    return JsonResponse({
                        'success': False,
                        'message': 'You have already cast your vote'
                    })
                
                # Generate and send OTP for voting
                verification_code = emailjs_service.generate_verification_code()
                
                # Store verification code
                if not emailjs_service.store_verification_code(voter.email, verification_code):
                    return JsonResponse({
                        'success': False,
                        'message': 'Failed to generate verification code. Please try again.'
                    })
                
                # Send OTP email with the pre-generated code
                email_result = emailjs_service.send_verification_email(voter.email, voter.full_name, verification_code)
                
                if email_result.get('success'):
                    # Update session for voting verification
                    request.session['vote_verification_pending'] = True
                    request.session.set_expiry(900)  # 15 minutes
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Verification code sent to {voter.email}. Please check your email.',
                        'email': voter.email,
                        'voter_name': voter.full_name,
                        'verification_code': verification_code,
                        'emailjs_config': email_result.get('emailjs_config', {})
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f"Failed to send verification email: {email_result.get('error', 'Unknown error')}"
                    })
            
            elif action == 'verify_vote_otp':
                # Verify OTP and proceed to voting
                otp_code = data.get('otp_code', '').strip()
                
                if not otp_code:
                    return JsonResponse({
                        'success': False,
                        'message': 'OTP code is required'
                    })
                
                # Check session
                pending_voter_id = request.session.get('pending_voter_id')
                vote_verification_pending = request.session.get('vote_verification_pending', False)
                
                if not pending_voter_id or not vote_verification_pending:
                    return JsonResponse({
                        'success': False,
                        'message': 'Session expired or no pending verification'
                    })
                
                # Get voter
                try:
                    voter = Voter.objects.get(id=pending_voter_id, is_active=True)
                except Voter.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Voter not found'
                    })
                
                # Verify OTP
                verification_result = emailjs_service.verify_code(voter.email, otp_code)
                
                if verification_result['success']:
                    # Mark as verified for voting
                    request.session['verified_voter_id'] = str(voter.id)
                    request.session['verified_voter_email'] = voter.email
                    request.session['email_verified'] = True
                    request.session.pop('vote_verification_pending', None)
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Email verified successfully. You can now vote.',
                        'redirect_url': '/cast-vote/'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': verification_result.get('error', 'Invalid verification code'),
                        'remaining_attempts': verification_result.get('remaining_attempts')
                    })
            
            elif action == 'submit_vote':
                # Handle vote submission using the same logic as CastVoteView
                party_id = data.get('party_id')
                
                logger.info(f"Starting vote submission: party_id={party_id}")
                
                if not party_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'Party ID is required'
                    })
                
                # Check if voter is verified and ready to vote
                verified_voter_email = request.session.get('verified_voter_email')
                email_verified = request.session.get('email_verified', False)
                
                logger.info(f"Voter verification status: email={verified_voter_email}, verified={email_verified}")
                
                if not verified_voter_email or not email_verified:
                    return JsonResponse({
                        'success': False,
                        'message': 'Please verify your email first before voting'
                    })
                
                # Use the vote casting logic from CastVoteView
                try:
                    # Get voter and party objects
                    try:
                        voter = Voter.objects.get(email=verified_voter_email, is_active=True)
                        logger.info(f"Found voter: {voter.id} - {voter.email}")
                        
                        # Always try to find party by party_id field first (this is what the frontend sends)
                        party = PoliticalParty.objects.get(party_id=party_id, is_active=True)
                        logger.info(f"Found party by party_id: {party.id} - {party.party_id} - {party.party_name}")
                            
                    except Voter.DoesNotExist:
                        logger.error(f"Voter not found with email: {verified_voter_email}")
                        return JsonResponse({
                            'success': False,
                            'message': 'Voter not found'
                        })
                    except PoliticalParty.DoesNotExist:
                        logger.error(f"Party not found with party_id: {party_id}")
                        return JsonResponse({
                            'success': False,
                            'message': 'Invalid party selection'
                        })
                    
                    # Check if voter has already voted
                    existing_votes = Vote.objects.filter(voter=voter)
                    if existing_votes.exists():
                        logger.warning(f"Voter {voter.id} has already voted. Existing votes: {list(existing_votes.values_list('id', 'political_party__party_name'))}")
                        return JsonResponse({
                            'success': False,
                            'message': 'You have already cast your vote. Multiple voting is not allowed.'
                        })
                    
                    # Generate voter hash for blockchain
                    voter_data = {
                        'id': str(voter.id),
                        'email': voter.email,
                        'aadhaar_number': voter.aadhaar_number
                    }
                    voter_hash = blockchain_client.generate_voter_hash(voter_data)
                    
                    # Check blockchain for duplicate vote
                    if blockchain_client.has_voter_voted(voter_hash):
                        return JsonResponse({
                            'success': False,
                            'message': 'Vote already recorded on blockchain. Duplicate voting detected.'
                        })
                    
                    # Check if voting session is active
                    active_session = VotingSession.objects.filter(
                        is_active=True,
                        start_time__lte=timezone.now(),
                        end_time__gte=timezone.now()
                    ).first()
                    
                    if not active_session:
                        return JsonResponse({
                            'success': False,
                            'message': 'No active voting session found'
                        })
                    
                    # Start database transaction
                    with transaction.atomic():
                        # Cast vote on blockchain
                        logger.info(f"Attempting to cast vote for voter {voter.id} to party {party.party_id}")
                        blockchain_result = blockchain_client.cast_vote_on_blockchain(
                            voter_hash, party.party_id  # Use party_id (string) for blockchain
                        )
                        
                        logger.info(f"Blockchain result: {blockchain_result}")
                        
                        if not blockchain_result.get('success'):
                            logger.error(f"Blockchain vote failed: {blockchain_result.get('message')}")
                            return JsonResponse({
                                'success': False,
                                'message': f"Blockchain vote failed: {blockchain_result.get('message', 'Unknown error')}"
                            })
                        
                        # Create vote record in database
                        logger.info(f"Creating vote record for voter {voter.id} and party {party.id}")
                        try:
                            vote = Vote.objects.create(
                                voter=voter,
                                political_party=party,
                                blockchain_hash=blockchain_result.get('transaction_hash'),
                                blockchain_block_number=blockchain_result.get('block_number'),
                                ip_address=self.get_client_ip(request)
                            )
                            logger.info(f"Vote record created successfully: {vote.id}")
                        except Exception as e:
                            logger.error(f"Error creating vote record: {e}")
                            raise e
                        
                        logger.info(f"Vote record created in database: {vote.id}")
                        
                        # Update voter status
                        voter.has_voted = True
                        voter.voted_at = timezone.now()
                        voter.save()
                        
                        logger.info(f"Voter status updated: {voter.id}")
                        
                        # Create blockchain vote record
                        try:
                            vote_record = blockchain_client.create_vote_record(
                                voter_hash,
                                party.party_id,  # Use party_id (string) for blockchain
                                blockchain_result.get('transaction_hash')
                            )
                            logger.info(f"Blockchain vote record created: {vote_record}")
                        except Exception as e:
                            logger.warning(f"Failed to create blockchain vote record: {e}")
                        
                        # Clear verification session
                        request.session.pop('verified_voter_email', None)
                        request.session.pop('verification_timestamp', None)
                        
                        return JsonResponse({
                            'success': True,
                            'message': 'Vote cast successfully!',
                            'vote_id': str(vote.id),
                            'blockchain_hash': blockchain_result.get('transaction_hash'),
                            'timestamp': vote.voted_at.isoformat(),
                            'party_name': party.party_name,
                            'blockchain_message': blockchain_result.get('message', '')
                        })
                        
                except Exception as e:
                    logger.error(f"Error casting vote: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': 'An error occurred while casting your vote. Please try again.'
                    })
            
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid action'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request format'
            })
        except Exception as e:
            logger.error(f"Error in voter profile action: {e}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred. Please try again.'
            })
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class VotingResultsView(View):
    """Display voting results"""
    
    def get(self, request):
        """Show voting results"""
        try:
            # Get the latest or active voting session
            active_session = VotingSession.objects.filter(is_active=True).first()
            latest_session = VotingSession.objects.order_by('-created_at').first()
            session = active_session or latest_session
            
            # Get all votes (since Vote model doesn't have voting_session field)
            vote_counts = Vote.objects.filter(
                is_valid=True
            ).values(
                'political_party__party_name',
                'political_party__party_id',
                'political_party__id'
            ).annotate(
                vote_count=models.Count('id')
            ).order_by('-vote_count')
            
            # Get total counts
            total_votes = Vote.objects.filter(is_valid=True).count()
            total_voters = Voter.objects.filter(is_active=True).count()
            
            # If no votes yet, show all parties with 0 votes
            if not vote_counts.exists():
                all_parties = PoliticalParty.objects.filter(is_active=True)
                vote_counts = []
                for party in all_parties:
                    vote_counts.append({
                        'political_party__party_name': party.party_name,
                        'political_party__party_id': party.party_id,
                        'political_party__id': party.id,
                        'vote_count': 0
                    })
            
            # Calculate percentages and prepare results
            results = []
            for item in vote_counts:
                percentage = (item['vote_count'] / total_votes * 100) if total_votes > 0 else 0
                results.append({
                    'party_name': item['political_party__party_name'],
                    'party_id': item['political_party__party_id'],
                    'vote_count': item['vote_count'],
                    'percentage': round(percentage, 2)
                })
            
            # Calculate blockchain verified votes
            blockchain_votes = Vote.objects.filter(
                is_valid=True,
                blockchain_hash__isnull=False
            ).count()
            
            context = {
                'session': session,
                'results': results,
                'total_votes': total_votes,
                'total_voters': total_voters,
                'blockchain_votes': blockchain_votes,
                'turnout_percentage': round((total_votes / total_voters * 100), 2) if total_voters > 0 else 0,
                'blockchain_percentage': round((blockchain_votes / total_votes * 100), 2) if total_votes > 0 else 0
            }
            
            return render(request, 'voting/results.html', context)
            
        except Exception as e:
            logger.error(f"Error loading voting results: {e}")
            # Return a basic results page with error message
            context = {
                'session': None,
                'results': [],
                'total_votes': 0,
                'total_voters': 0,
                'blockchain_votes': 0,
                'turnout_percentage': 0,
                'blockchain_percentage': 0,
                'error_message': 'Unable to load voting results. Please try again later.'
            }
            return render(request, 'voting/results.html', context)

# API Views for AJAX requests
@require_http_methods(["GET"])
def get_voting_status(request):
    """Get current voting status"""
    try:
        active_session = VotingSession.objects.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        
        if active_session:
            total_votes = Vote.objects.filter(voting_session=active_session).count()
            return JsonResponse({
                'success': True,
                'session_active': True,
                'session_name': active_session.session_name,
                'total_votes': total_votes,
                'end_time': active_session.end_time.isoformat()
            })
        else:
            return JsonResponse({
                'success': True,
                'session_active': False
            })
            
    except Exception as e:
        logger.error(f"Error getting voting status: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error retrieving voting status'
        })

@require_http_methods(["GET"])
def get_parties(request):
    """Get list of active political parties"""
    try:
        parties = PoliticalParty.objects.filter(is_active=True).values(
            'id', 'party_name', 'party_description'
        ).order_by('party_name')
        
        return JsonResponse({
            'success': True,
            'parties': list(parties)
        })
        
    except Exception as e:
        logger.error(f"Error getting parties: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error retrieving parties'
        })


# Admin Dashboard Views
def is_admin_user(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# AdminLoginView removed - login functionality disabled
# class AdminLoginView(View):
#     """Admin login interface"""
#     
#     def get(self, request):
#         """Display admin login form"""
#         if request.user.is_authenticated and is_admin_user(request.user):
#             return redirect('voting:admin_dashboard')
#         return render(request, 'voting/admin/login.html')
#     
#     def post(self, request):
#         """Handle admin login"""
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         
#         if username and password:
#             user = authenticate(request, username=username, password=password)
#             if user and is_admin_user(user):
#                 login(request, user)
#                 return redirect('voting:admin_dashboard')
#             else:
#                 messages.error(request, 'Invalid credentials or insufficient privileges')
#         else:
#             messages.error(request, 'Please provide both username and password')
#         
#         return render(request, 'voting/admin/login.html')


class AdminDashboardView(View):
    """Main admin dashboard"""
    
    def get(self, request):
        """Display admin dashboard"""
        # Get statistics
        total_voters = Voter.objects.count()
        active_voters = Voter.objects.filter(is_active=True).count()
        total_votes = Vote.objects.filter(is_valid=True).count()
        total_parties = PoliticalParty.objects.count()
        active_parties = PoliticalParty.objects.filter(is_active=True).count()
        
        # Get active voting session
        active_session = VotingSession.objects.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        
        # Get recent votes
        recent_votes = Vote.objects.filter(is_valid=True).select_related(
            'voter', 'political_party'
        ).order_by('-voted_at')[:10]
        
        # Get party vote counts
        party_stats = PoliticalParty.objects.annotate(
            vote_count=Count('votes', filter=Q(votes__is_valid=True))
        ).order_by('-vote_count')
        
        context = {
            'total_voters': total_voters,
            'active_voters': active_voters,
            'total_votes': total_votes,
            'total_parties': total_parties,
            'active_parties': active_parties,
            'active_session': active_session,
            'recent_votes': recent_votes,
            'party_stats': party_stats,
            'voting_percentage': round((total_votes / active_voters * 100) if active_voters > 0 else 0, 2)
        }
        
        return render(request, 'voting/admin/dashboard.html', context)


class AdminVotersView(View):
    """Admin voters management"""
    
    def get(self, request):
        """Display voters list"""
        voters = Voter.objects.all().order_by('-created_at')
        
        # Filter by search query
        search = request.GET.get('search')
        if search:
            voters = voters.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(aadhaar_number__icontains=search)
            )
        
        # Filter by status
        status = request.GET.get('status')
        if status == 'active':
            voters = voters.filter(is_active=True)
        elif status == 'inactive':
            voters = voters.filter(is_active=False)
        elif status == 'voted':
            voters = voters.filter(has_voted=True)
        elif status == 'not_voted':
            voters = voters.filter(has_voted=False)
        
        context = {
            'voters': voters,
            'search': search,
            'status': status
        }
        
        return render(request, 'voting/admin/voters.html', context)


class AdminPartiesView(View):
    """Admin parties management"""
    
    def get(self, request):
        """Display parties list"""
        parties = PoliticalParty.objects.annotate(
            vote_count=Count('votes', filter=Q(votes__is_valid=True))
        ).order_by('-vote_count')
        
        context = {
            'parties': parties
        }
        
        return render(request, 'voting/admin/parties.html', context)


class AdminResultsView(View):
    """Admin results and analytics"""
    
    def get(self, request):
        """Display detailed results"""
        # Get party results
        party_results = PoliticalParty.objects.annotate(
            vote_count=Count('votes', filter=Q(votes__is_valid=True))
        ).order_by('-vote_count')
        
        total_votes = Vote.objects.filter(is_valid=True).count()
        
        # Calculate percentages
        for party in party_results:
            party.percentage = round((party.vote_count / total_votes * 100) if total_votes > 0 else 0, 2)
        
        # Get voting timeline data
        from django.db.models import TruncHour
        voting_timeline = Vote.objects.filter(is_valid=True).extra(
            select={'hour': "strftime('%%Y-%%m-%%d %%H:00:00', voted_at)"}
        ).values('hour').annotate(count=Count('id')).order_by('hour')
        
        context = {
            'party_results': party_results,
            'total_votes': total_votes,
            'voting_timeline': list(voting_timeline)
        }
        
        return render(request, 'voting/admin/results.html', context)


class AdminSessionsView(View):
    """Admin voting sessions management"""
    
    def get(self, request):
        """Display voting sessions"""
        sessions = VotingSession.objects.all().order_by('-created_at')
        
        context = {
            'sessions': sessions
        }
        
        return render(request, 'voting/admin/sessions.html', context)


class AdminAddVoterView(View):
    """Admin add voter view"""
    
    def get(self, request):
        return render(request, 'voting/admin/add_voter.html')
    
    def post(self, request):
        try:
            # Extract form data
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip().lower()
            aadhaar_number = request.POST.get('aadhaar_number', '').strip()
            date_of_birth = request.POST.get('date_of_birth')
            region = request.POST.get('region', '').strip()
            gender = request.POST.get('gender', '')
            phone_number = request.POST.get('phone_number', '').strip()
            constituency = request.POST.get('constituency', '').strip()
            verification_status = request.POST.get('verification_status', 'pending')
            email_verified = 'email_verified' in request.POST
            vote_done = 'vote_done' in request.POST
            profile_picture = request.FILES.get('profile_picture')
            
            # Validate required fields
            if not all([full_name, email, aadhaar_number, date_of_birth, region]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'voting/admin/add_voter.html')
            
            # Validate Aadhaar number
            if not aadhaar_number.isdigit() or len(aadhaar_number) != 12:
                messages.error(request, 'Aadhaar number must be exactly 12 digits.')
                return render(request, 'voting/admin/add_voter.html')
            
            # Check if voter already exists
            if Voter.objects.filter(Q(email=email) | Q(aadhaar_number=aadhaar_number)).exists():
                messages.error(request, 'A voter with this email or Aadhaar number already exists.')
                return render(request, 'voting/admin/add_voter.html')
            
            # Create voter
            voter = Voter.objects.create(
                full_name=full_name,
                email=email,
                aadhaar_number=aadhaar_number,
                date_of_birth=date_of_birth,
                region=region,
                gender=gender,
                phone_number=phone_number,
                constituency=constituency,
                verification_status=verification_status,
                email_verified=email_verified,
                has_voted=vote_done,
                profile_picture=profile_picture
            )
            
            messages.success(request, f'Voter "{full_name}" has been successfully added.')
            
            # Handle different save actions
            if 'save_and_add_another' in request.POST:
                return redirect('voting:admin_add_voter')
            elif 'save_and_continue_editing' in request.POST:
                return redirect('voting:admin_edit_voter', voter_id=voter.id)
            else:
                return redirect('voting:admin_voters')
                
        except Exception as e:
            logger.error(f"Error adding voter: {str(e)}")
            messages.error(request, 'An error occurred while adding the voter. Please try again.')
            return render(request, 'voting/admin/add_voter.html')


class AdminAddPartyView(View):
    """Admin add party view"""
    
    def get(self, request):
        return render(request, 'voting/admin/add_party.html')
    
    def post(self, request):
        try:
            # Extract form data
            name = request.POST.get('name', '').strip()
            symbol = request.POST.get('symbol', '').strip()
            description = request.POST.get('description', '').strip()
            leader = request.POST.get('leader', '').strip()
            founded_year = request.POST.get('founded_year')
            website = request.POST.get('website', '').strip()
            contact_email = request.POST.get('contact_email', '').strip()
            color = request.POST.get('color', '#007bff')
            headquarters = request.POST.get('headquarters', '').strip()
            ideology = request.POST.get('ideology', '')
            status = request.POST.get('status', 'active')
            logo = request.FILES.get('logo')
            
            # Validate required fields
            if not all([name, symbol]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'voting/admin/add_party.html')
            
            # Check if party already exists
            if PoliticalParty.objects.filter(Q(party_name=name)).exists():
                messages.error(request, 'A party with this name or symbol already exists.')
                return render(request, 'voting/admin/add_party.html')
            
            # Create party
            party_data = {
                'party_name': name,
                'party_description': description,
                'is_active': status == 'active'
            }
            
            if logo:
                party_data['logo'] = logo
            
            party = PoliticalParty.objects.create(**party_data)
            
            messages.success(request, f'Political party "{name}" has been successfully added.')
            
            # Handle different save actions
            if 'save_and_add_another' in request.POST:
                return redirect('voting:admin_add_party')
            elif 'save_and_continue_editing' in request.POST:
                return redirect('voting:admin_edit_party', party_id=party.id)
            else:
                return redirect('voting:admin_parties')
                
        except Exception as e:
            logger.error(f"Error adding party: {str(e)}")
            messages.error(request, 'An error occurred while adding the party. Please try again.')
            return render(request, 'voting/admin/add_party.html')


class VoterDetailsView(View):
    """Display voter details with Aadhaar information"""
    
    def get(self, request, voter_id):
        try:
            voter = get_object_or_404(Voter, id=voter_id)
            context = {
                'voter': voter,
                'age': voter.age if hasattr(voter, 'age') else None
            }
            return render(request, 'voting/voter_details.html', context)
        except Exception as e:
            logger.error(f"Error displaying voter details: {str(e)}")
            messages.error(request, 'Error loading voter details.')
            return redirect('voting:voting_home')


class EmailOTPVerificationView(View):
    """Handle email OTP verification after Aadhaar verification"""
    
    def get(self, request):
        """Render OTP verification page"""
        return render(request, 'voting/email_otp_verification.html', {
            'title': 'Email OTP Verification',
            'page_title': 'Verify Your Email',
            'description': 'Enter the verification code sent to your email'
        })
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Verify OTP code and display candidate profile"""
        try:
            data = json.loads(request.body)
            otp_code = data.get('otp_code', '').strip()
            
            if not otp_code:
                return JsonResponse({
                    'success': False,
                    'message': 'OTP code is required'
                })
            
            # Get pending voter info from session
            pending_voter_id = request.session.get('pending_voter_id')
            pending_voter_email = request.session.get('pending_voter_email')
            
            if not pending_voter_id or not pending_voter_email:
                return JsonResponse({
                    'success': False,
                    'message': 'No pending verification found. Please start verification again.'
                })
            
            # Verify OTP using emailjs service
            verification_result = emailjs_service.verify_code(pending_voter_email, otp_code)
            
            if not verification_result.get('success'):
                return JsonResponse({
                    'success': False,
                    'message': verification_result.get('error', 'Invalid verification code')
                })
            
            # Find voter by ID
            try:
                voter = Voter.objects.get(id=pending_voter_id)
            except Voter.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Voter not found'
                })
            
            # Mark email as verified and store in session for voting
            voter.email_verified = True
            voter.save()
            
            request.session['verified_voter_id'] = str(voter.id)
            request.session['email_verified'] = True
            
            # Clear pending verification data
            request.session.pop('pending_voter_id', None)
            request.session.pop('pending_voter_email', None)
            
            # Clear verification code
            emailjs_service.clear_verification_code(pending_voter_email)
            
            # Return voter profile data for voting
            return JsonResponse({
                'success': True,
                'message': 'Email verified successfully. You can now proceed to vote.',
                'voter': {
                    'id': str(voter.id),
                    'full_name': voter.full_name,
                    'email': voter.email,
                    'aadhaar_number': voter.aadhaar_number,
                    'has_voted': voter.has_voted,
                    'is_active': voter.is_active,
                    'verification_status': voter.verification_status,
                    'constituency': voter.constituency,
                    'region': voter.region
                },
                'show_voting_interface': True
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request format'
            })
        except Exception as e:
            logger.error(f"Error in OTP verification: {e}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred during verification'
            })


# admin_logout function removed - login functionality disabled
# @login_required
# @user_passes_test(is_admin_user)
# def admin_logout(request):
#     """Admin logout"""
#     logout(request)
#     messages.success(request, 'You have been logged out successfully')
#     return redirect('voting:admin_login')


# User Authentication Views
# UserLoginView removed - login functionality disabled
# class UserLoginView(View):
#     """User login interface"""
#     
#     def get(self, request):
#         """Display user login form"""
#         if request.user.is_authenticated:
#             return redirect('voting:home')
#         return render(request, 'voting/user/login.html')
#     
#     def post(self, request):
#         """Handle user login"""
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         
#         if username and password:
#             user = authenticate(request, username=username, password=password)
#             if user and user.is_active:
#                 login(request, user)
#                 return redirect('voting:home')
#             else:
#                 messages.error(request, 'Invalid credentials')
#         else:
#             messages.error(request, 'Please provide both username and password')
#         
#         return render(request, 'voting/user/login.html')


# user_logout function removed - login functionality disabled
# @login_required
# def user_logout(request):
#     """User logout"""
#     logout(request)
#     messages.success(request, 'You have been logged out successfully')
#     return redirect('voting:user_login')

@require_http_methods(["POST"])
@csrf_exempt
def resend_verification_email(request):
    """Resend verification email"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email is required'
            })
        
        # Get voter from session or email
        voter_id = request.session.get('pending_voter_id')
        if voter_id:
            try:
                voter = Voter.objects.get(id=voter_id, email=email)
                # Extend session when resending
                request.session.set_expiry(900)  # Reset to 15 minutes
            except Voter.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid session or email mismatch'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No active verification session. Please start verification again.',
                'redirect_url': '/verify-aadhaar/'
            })
        
        # Resend verification email
        email_result = emailjs_service.resend_verification_email(
            email=voter.email,
            voter_name=voter.full_name
        )
        
        if email_result['success']:
            emailjs_config = email_result.get('emailjs_config', {})
            verification_code = emailjs_config.get('template_params', {}).get('verification_code')
            return JsonResponse({
                'success': True,
                'message': 'Verification email resent successfully',
                'emailjs_config': {
                    'service_id': emailjs_config.get('service_id'),
                    'template_id': emailjs_config.get('template_id'),
                    'public_key': emailjs_config.get('public_key'),
                    'to_email': voter.email,
                    'voter_name': voter.full_name,
                    'otp_code': verification_code
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f"Failed to resend verification email: {email_result.get('error', 'Unknown error')}"
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format'
        })
    except Exception as e:
        logger.error(f"Error resending verification email: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while resending email'
        })

@require_http_methods(["GET"])
def get_verification_status(request):
    """Get verification status for current session"""
    try:
        voter_id = request.session.get('pending_voter_id')
        if not voter_id:
            return JsonResponse({
                'success': False,
                'message': 'No active verification session'
            })
        
        try:
            voter = Voter.objects.get(id=voter_id)
        except Voter.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Voter not found'
            })
        
        # Get verification status from EmailJS service
        status = emailjs_service.get_verification_status(voter.email)
        
        # Extend session if still valid
        if status.get('has_pending_verification'):
            request.session.set_expiry(900)  # Reset to 15 minutes
        
        return JsonResponse({
            'success': True,
            'verification_status': {
                **status,
                'is_expired': status.get('remaining_time_seconds', 0) <= 0
            },
            'voter_email': voter.email,
            'session_valid': True
        })
        
    except Exception as e:
        logger.error(f"Error getting verification status: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Failed to get verification status'
        })

@require_http_methods(["POST"])
@csrf_exempt
def refresh_verification_session(request):
    """Refresh verification session to prevent timeout"""
    try:
        voter_id = request.session.get('pending_voter_id')
        if not voter_id:
            return JsonResponse({
                'success': False,
                'message': 'No active verification session'
            })
        
        # Extend session timeout
        request.session.set_expiry(900)  # 15 minutes
        
        return JsonResponse({
            'success': True,
            'message': 'Session refreshed successfully',
            'expires_in_seconds': 900
        })
        
    except Exception as e:
        logger.error(f"Error refreshing verification session: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Failed to refresh session'
        })


class CastVoteView(View):
    """Handle vote submission with blockchain integration and duplicate prevention"""
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Submit vote to blockchain and database"""
        try:
            data = json.loads(request.body)
            party_id = data.get('party_id')
            voter_email = request.session.get('verified_voter_email')
            
            if not party_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Party ID is required'
                })
            
            if not voter_email:
                return JsonResponse({
                    'success': False,
                    'message': 'Voter not verified. Please complete verification first.'
                })
            
            # Get voter and party objects
            try:
                voter = Voter.objects.get(email=voter_email, is_active=True)
                # Always try to find party by party_id field (this is what the frontend sends)
                party = PoliticalParty.objects.get(party_id=party_id, is_active=True)
            except Voter.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Voter not found'
                })
            except PoliticalParty.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid party selection'
                })
            
            # Check if voter has already voted
            if Vote.objects.filter(voter=voter).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'You have already cast your vote. Multiple voting is not allowed.'
                })
            
            # Generate voter hash for blockchain
            voter_data = {
                'id': str(voter.id),
                'email': voter.email,
                'aadhaar_number': voter.aadhaar_number
            }
            voter_hash = blockchain_client.generate_voter_hash(voter_data)
            
            # Check blockchain for duplicate vote
            if blockchain_client.has_voter_voted(voter_hash):
                return JsonResponse({
                    'success': False,
                    'message': 'Vote already recorded on blockchain. Duplicate voting detected.'
                })
            
            # Check if voting session is active
            active_session = VotingSession.objects.filter(
                is_active=True,
                start_time__lte=timezone.now(),
                end_time__gte=timezone.now()
            ).first()
            
            if not active_session:
                return JsonResponse({
                    'success': False,
                    'message': 'No active voting session found'
                })
            
            # Start database transaction
            with transaction.atomic():
                # Cast vote on blockchain
                blockchain_result = blockchain_client.cast_vote_on_blockchain(
                    voter_hash, party.party_id  # Use party_id (string) for blockchain
                )
                
                if not blockchain_result.get('success'):
                    return JsonResponse({
                        'success': False,
                        'message': f"Blockchain vote failed: {blockchain_result.get('message', 'Unknown error')}"
                    })
                
                # Create vote record in database
                vote = Vote.objects.create(
                    voter=voter,
                    political_party=party,
                    blockchain_hash=blockchain_result.get('transaction_hash'),
                    blockchain_block_number=blockchain_result.get('block_number'),
                    ip_address=self.get_client_ip(request)
                )
                
                # Update voter status
                voter.has_voted = True
                voter.voted_at = timezone.now()
                voter.save()
                
                # Create blockchain vote record
                vote_record = blockchain_client.create_vote_record(
                    voter_hash,
                    party.party_id,  # Use party_id (string) for blockchain
                    blockchain_result.get('transaction_hash')
                )
                
                # Clear verification session
                request.session.pop('verified_voter_email', None)
                request.session.pop('verification_timestamp', None)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Vote cast successfully!',
                    'vote_id': str(vote.id),
                    'blockchain_hash': blockchain_result.get('transaction_hash'),
                    'timestamp': vote.voted_at.isoformat(),
                    'party_name': party.party_name
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            logger.error(f"Error casting vote: {e}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while casting your vote. Please try again.'
            })
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

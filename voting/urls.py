from django.urls import path
from . import views

app_name = 'voting'

urlpatterns = [
    # Main voting interface
    path('', views.VotingHomeView.as_view(), name='home'),
    
    # Voter search functionality
    path('search/', views.VoterSearchView.as_view(), name='voter_search'),
    path('quick-verify/', views.VoterQuickVerifyView.as_view(), name='voter_quick_verify'),
    
    # Voter verification
    path('verify/', views.VoterVerificationView.as_view(), name='voter_verification'),
    
    # Aadhaar verification
    path('verify-aadhaar/', views.AadhaarVerificationView.as_view(), name='aadhaar_verification'),
    
    # Voter profile after Aadhaar verification
    path('voter-profile/', views.VoterProfileView.as_view(), name='voter_profile'),
    
    # Email verification
    path('verify-email/', views.EmailVerificationView.as_view(), name='email_verification'),
    
    # Results
    path('results/', views.VotingResultsView.as_view(), name='results'),
    
    # User authentication removed
    
    # Voter details and verification
    path('voter/<int:voter_id>/details/', views.VoterDetailsView.as_view(), name='voter_details'),
    path('email/otp-verification/', views.EmailOTPVerificationView.as_view(), name='email_otp_verification'),
    
    # Admin Dashboard URLs (login removed)
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/voters/', views.AdminVotersView.as_view(), name='admin_voters'),
    path('admin/voters/add/', views.AdminAddVoterView.as_view(), name='admin_add_voter'),
    path('admin/parties/', views.AdminPartiesView.as_view(), name='admin_parties'),
    path('admin/parties/add/', views.AdminAddPartyView.as_view(), name='admin_add_party'),
    path('admin/results/', views.AdminResultsView.as_view(), name='admin_results'),
    path('admin/sessions/', views.AdminSessionsView.as_view(), name='admin_sessions'),
    
    # API endpoints
    path('api/status/', views.get_voting_status, name='voting_status'),
    path('api/parties/', views.get_parties, name='get_parties'),
    path('api/resend-verification/', views.resend_verification_email, name='resend_verification'),
    path('api/verification-status/', views.get_verification_status, name='verification_status'),
    path('api/refresh-session/', views.refresh_verification_session, name='refresh_verification_session'),
    
    # Vote submission
    path('cast-vote/', views.CastVoteView.as_view(), name='cast_vote'),
    
    # Image serving endpoints
    # path('party-symbol/<int:party_id>/', views.serve_party_symbol, name='serve_party_symbol'),  # Function not implemented
    # path('voter-profile/<int:voter_id>/', views.serve_voter_profile_picture, name='serve_voter_profile_picture'),  # Function not implemented
]
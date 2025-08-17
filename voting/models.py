from django.db import models
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
import uuid
from datetime import datetime


class PoliticalParty(models.Model):
    """
    Model for storing political party information
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    party_id = models.CharField(max_length=20, unique=True, help_text="Unique party identification code (e.g., BJP, INC, AAP)")
    party_name = models.CharField(max_length=200, unique=True)
    party_symbol_data = models.BinaryField(null=True, blank=True, help_text="Binary data of the party symbol image")
    party_symbol_name = models.CharField(max_length=255, null=True, blank=True, help_text="Original filename of the party symbol")
    party_symbol_content_type = models.CharField(max_length=100, null=True, blank=True, help_text="MIME type of the party symbol")
    party_symbol_size = models.PositiveIntegerField(null=True, blank=True, help_text="Size of the party symbol in bytes")
    party_leader = models.CharField(max_length=200)
    party_description = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Political Party"
        verbose_name_plural = "Political Parties"
        ordering = ['party_name']
    
    def __str__(self):
        return f"{self.party_id} - {self.party_name}"
    
    @property
    def vote_count(self):
        """Return the total number of votes for this party"""
        return self.votes.filter(is_valid=True).count()
    
    @property
    def party_symbol_base64(self):
        """Get base64 encoded party symbol data"""
        if self.party_symbol_data:
            import base64
            return base64.b64encode(self.party_symbol_data).decode('utf-8')
        return None
    
    @property
    def party_symbol_url(self):
        """Get data URL for party symbol"""
        if self.party_symbol_data and self.party_symbol_content_type:
            import base64
            base64_data = base64.b64encode(self.party_symbol_data).decode('utf-8')
            return f"data:{self.party_symbol_content_type};base64,{base64_data}"
        return None


class Voter(models.Model):
    """
    Model for storing voter information
    Only admins can create and manage voters
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    aadhaar_number = models.CharField(max_length=12, unique=True, help_text="12-digit Aadhaar number")
    phone_number = models.CharField(max_length=15, help_text="Phone number with country code", default="")
    constituency = models.CharField(max_length=200)
    region = models.CharField(max_length=200, help_text="State or region", default="")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    profile_picture_data = models.BinaryField(null=True, blank=True, help_text="Binary data of the profile picture")
    profile_picture_name = models.CharField(max_length=255, null=True, blank=True, help_text="Original filename of the profile picture")
    profile_picture_content_type = models.CharField(max_length=100, null=True, blank=True, help_text="MIME type of the profile picture")
    profile_picture_size = models.PositiveIntegerField(null=True, blank=True, help_text="Size of the profile picture in bytes")
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    has_voted = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Voter"
        verbose_name_plural = "Voters"
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    @property
    def age(self):
        """Calculate voter's age"""
        today = datetime.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    @property
    def profile_picture_base64(self):
        """Get base64 encoded profile picture data"""
        if self.profile_picture_data:
            import base64
            return base64.b64encode(self.profile_picture_data).decode('utf-8')
        return None
    
    @property
    def profile_picture_url(self):
        """Get data URL for profile picture"""
        if self.profile_picture_data and self.profile_picture_content_type:
            import base64
            base64_data = base64.b64encode(self.profile_picture_data).decode('utf-8')
            return f"data:{self.profile_picture_content_type};base64,{base64_data}"
        return None


class EmailVerification(models.Model):
    """
    Model for storing email verification codes
    """
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='verifications')
    verification_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = "Email Verification"
        verbose_name_plural = "Email Verifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Verification for {self.voter.email} - {self.verification_code}"
    
    @property
    def is_expired(self):
        """Check if verification code has expired"""
        return datetime.now() > self.expires_at


class Vote(models.Model):
    """
    Model for storing vote records
    Each vote is also recorded on blockchain for immutability
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='votes')
    political_party = models.ForeignKey(PoliticalParty, on_delete=models.CASCADE, related_name='votes')
    blockchain_hash = models.CharField(max_length=66, unique=True, null=True, blank=True)  # Ethereum transaction hash
    blockchain_block_number = models.BigIntegerField(null=True, blank=True)
    voted_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Vote"
        verbose_name_plural = "Votes"
        ordering = ['-voted_at']
        unique_together = ['voter', 'political_party']  # Ensure one vote per voter
    
    def __str__(self):
        return f"Vote by {self.voter.full_name} for {self.political_party.party_name}"
    
    @property
    def is_blockchain_confirmed(self):
        """Check if vote is confirmed on blockchain"""
        return bool(self.blockchain_hash and self.blockchain_block_number)


class VotingSession(models.Model):
    """
    Model for managing voting sessions
    Admins can start/stop voting periods
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Voting Session"
        verbose_name_plural = "Voting Sessions"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.session_name
    
    @property
    def total_votes(self):
        """Return total votes cast in this session"""
        return Vote.objects.filter(
            voted_at__gte=self.start_time,
            voted_at__lte=self.end_time,
            is_valid=True
        ).count()
    
    @property
    def is_ongoing(self):
        """Check if voting session is currently active"""
        now = datetime.now()
        return self.is_active and self.start_time <= now <= self.end_time

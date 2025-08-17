from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
from django import forms
from django.http import HttpResponse
from django.urls import path
import base64
from .models import PoliticalParty, Voter, Vote, EmailVerification, VotingSession


class PoliticalPartyForm(forms.ModelForm):
    party_symbol_upload = forms.ImageField(required=False, help_text="Upload party symbol image")
    
    class Meta:
        model = PoliticalParty
        fields = '__all__'
        exclude = ['party_symbol_data', 'party_symbol_name', 'party_symbol_content_type', 'party_symbol_size']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle image upload
        if self.cleaned_data.get('party_symbol_upload'):
            image_file = self.cleaned_data['party_symbol_upload']
            instance.party_symbol_data = image_file.read()
            instance.party_symbol_name = image_file.name
            instance.party_symbol_content_type = image_file.content_type
            instance.party_symbol_size = image_file.size
        
        if commit:
            instance.save()
        return instance


class VoterForm(forms.ModelForm):
    profile_picture_upload = forms.ImageField(required=False, help_text="Upload profile picture")
    
    class Meta:
        model = Voter
        fields = '__all__'
        exclude = ['profile_picture_data', 'profile_picture_name', 'profile_picture_content_type', 'profile_picture_size']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle image upload
        if self.cleaned_data.get('profile_picture_upload'):
            image_file = self.cleaned_data['profile_picture_upload']
            instance.profile_picture_data = image_file.read()
            instance.profile_picture_name = image_file.name
            instance.profile_picture_content_type = image_file.content_type
            instance.profile_picture_size = image_file.size
        
        if commit:
            instance.save()
        return instance


@admin.register(PoliticalParty)
class PoliticalPartyAdmin(admin.ModelAdmin):
    form = PoliticalPartyForm
    list_display = ['party_id', 'party_name', 'party_leader', 'party_symbol_preview', 'vote_count_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['party_id', 'party_name', 'party_leader']
    readonly_fields = ['id', 'created_at', 'updated_at', 'vote_count_display', 'party_symbol_preview', 'party_symbol_info']
    fieldsets = (
        ('Party Information', {
            'fields': ('party_id', 'party_name', 'party_leader', 'party_description')
        }),
        ('Media', {
            'fields': ('party_symbol_upload', 'party_symbol_preview', 'party_symbol_info')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'vote_count_display'),
            'classes': ('collapse',)
        })
    )
    
    def party_symbol_preview(self, obj):
        if obj.party_symbol_data:
            image_data = base64.b64encode(obj.party_symbol_data).decode('utf-8')
            return format_html(
                '<img src="data:{};base64,{}" style="max-width: 50px; max-height: 50px; border-radius: 5px;" />',
                obj.party_symbol_content_type or 'image/jpeg',
                image_data
            )
        return 'No image'
    party_symbol_preview.short_description = 'Symbol'
    
    def party_symbol_info(self, obj):
        if obj.party_symbol_data:
            size_kb = obj.party_symbol_size / 1024 if obj.party_symbol_size else 0
            return format_html(
                '<strong>Filename:</strong> {}<br><strong>Type:</strong> {}<br><strong>Size:</strong> {:.1f} KB',
                obj.party_symbol_name or 'Unknown',
                obj.party_symbol_content_type or 'Unknown',
                size_kb
            )
        return 'No image uploaded'
    party_symbol_info.short_description = 'Image Info'
    
    def vote_count_display(self, obj):
        count = obj.vote_count
        if count > 0:
            url = reverse('admin:voting_vote_changelist') + f'?political_party__id__exact={obj.id}'
            return format_html('<a href="{}">{} votes</a>', url, count)
        return '0 votes'
    vote_count_display.short_description = 'Total Votes'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(total_vote_count=Count('votes'))


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    form = VoterForm
    list_display = ['full_name', 'email', 'constituency', 'gender', 'age_display', 'profile_picture_preview', 'has_voted', 'is_active']
    list_filter = ['gender', 'constituency', 'has_voted', 'is_active', 'created_at']
    search_fields = ['full_name', 'email', 'aadhaar_number', 'constituency']
    readonly_fields = ['id', 'created_at', 'updated_at', 'age_display', 'vote_details', 'profile_picture_preview', 'profile_picture_info']
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'email', 'gender', 'date_of_birth', 'age_display')
        }),
        ('Profile Picture', {
            'fields': ('profile_picture_upload', 'profile_picture_preview', 'profile_picture_info')
        }),
        ('Identification', {
            'fields': ('aadhaar_number', 'phone_number', 'region')
        }),
        ('Location', {
            'fields': ('constituency',)
        }),
        ('', {
            'fields': ()
        }),
        ('', {
            'fields': ()
        }),
        ('', {
            'fields': (),
            'classes': ('collapse',)
        })
    )
    
    def profile_picture_preview(self, obj):
        if obj.profile_picture_data:
            image_data = base64.b64encode(obj.profile_picture_data).decode('utf-8')
            return format_html(
                '<img src="data:{};base64,{}" style="max-width: 40px; max-height: 40px; border-radius: 50%; object-fit: cover;" />',
                obj.profile_picture_content_type or 'image/jpeg',
                image_data
            )
        return 'No image'
    profile_picture_preview.short_description = 'Photo'
    
    def profile_picture_info(self, obj):
        if obj.profile_picture_data:
            size_kb = obj.profile_picture_size / 1024 if obj.profile_picture_size else 0
            return format_html(
                '<strong>Filename:</strong> {}<br><strong>Type:</strong> {}<br><strong>Size:</strong> {:.1f} KB',
                obj.profile_picture_name or 'Unknown',
                obj.profile_picture_content_type or 'Unknown',
                size_kb
            )
        return 'No image uploaded'
    profile_picture_info.short_description = 'Image Info'
    
    def age_display(self, obj):
        return f"{obj.age} years"
    age_display.short_description = 'Age'
    
    def vote_details(self, obj):
        if obj.has_voted:
            try:
                vote = obj.votes.first()
                if vote:
                    return format_html(
                        'Voted for: <strong>{}</strong><br>Date: {}',
                        vote.political_party.party_name,
                        vote.voted_at.strftime('%Y-%m-%d %H:%M')
                    )
            except:
                pass
        return 'No vote cast'
    vote_details.short_description = 'Vote Details'
    
    actions = ['mark_as_voted', 'mark_as_not_voted', 'activate_voters', 'deactivate_voters']
    
    def mark_as_voted(self, request, queryset):
        queryset.update(has_voted=True)
        self.message_user(request, f"{queryset.count()} voters marked as voted.")
    mark_as_voted.short_description = "Mark selected voters as voted"
    
    def mark_as_not_voted(self, request, queryset):
        queryset.update(has_voted=False)
        self.message_user(request, f"{queryset.count()} voters marked as not voted.")
    mark_as_not_voted.short_description = "Mark selected voters as not voted"
    
    def activate_voters(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} voters activated.")
    activate_voters.short_description = "Activate selected voters"
    
    def deactivate_voters(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} voters deactivated.")
    deactivate_voters.short_description = "Deactivate selected voters"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['voter_name', 'party_name', 'voted_at', 'blockchain_status', 'is_valid']
    list_filter = ['political_party', 'is_valid', 'voted_at']
    search_fields = ['voter__full_name', 'voter__email', 'political_party__party_name']
    readonly_fields = ['id', 'voted_at', 'blockchain_status', 'blockchain_details']
    fieldsets = (
        ('Vote Information', {
            'fields': ('voter', 'political_party', 'voted_at')
        }),
        ('Blockchain Information', {
            'fields': ('blockchain_hash', 'blockchain_block_number', 'blockchain_status', 'blockchain_details')
        }),
        ('Validation', {
            'fields': ('is_valid', 'ip_address')
        }),
        ('System Information', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    )
    
    def voter_name(self, obj):
        return obj.voter.full_name
    voter_name.short_description = 'Voter'
    
    def party_name(self, obj):
        return obj.political_party.party_name
    party_name.short_description = 'Political Party'
    
    def blockchain_status(self, obj):
        if obj.is_blockchain_confirmed:
            return format_html(
                '<span style="color: green;">✓ Confirmed</span>'
            )
        elif obj.blockchain_hash:
            return format_html(
                '<span style="color: orange;">⏳ Pending</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Not Recorded</span>'
            )
    blockchain_status.short_description = 'Blockchain Status'
    
    def blockchain_details(self, obj):
        if obj.blockchain_hash:
            return format_html(
                'Hash: <code>{}</code><br>Block: {}',
                obj.blockchain_hash,
                obj.blockchain_block_number or 'Pending'
            )
        return 'Not recorded on blockchain'
    blockchain_details.short_description = 'Blockchain Details'
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of votes for audit purposes
        return False


# @admin.register(EmailVerification)  # Commented out to hide from admin
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['voter_email', 'verification_code', 'created_at', 'is_used', 'is_expired_display']
    list_filter = ['is_used', 'created_at']
    search_fields = ['voter__email', 'verification_code']
    readonly_fields = ['created_at', 'is_expired_display']
    
    def voter_email(self, obj):
        return obj.voter.email
    voter_email.short_description = 'Voter Email'
    
    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Valid</span>')
    is_expired_display.short_description = 'Status'


@admin.register(VotingSession)
class VotingSessionAdmin(admin.ModelAdmin):
    list_display = ['session_name', 'start_time', 'end_time', 'is_active', 'total_votes_display', 'created_by']
    list_filter = ['is_active', 'start_time', 'created_by']
    search_fields = ['session_name', 'description']
    readonly_fields = ['created_at', 'total_votes_display', 'session_status']
    fieldsets = (
        ('Session Information', {
            'fields': ('session_name', 'description')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_votes_display', 'session_status')
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def total_votes_display(self, obj):
        return obj.total_votes
    total_votes_display.short_description = 'Total Votes'
    
    def session_status(self, obj):
        if obj.is_ongoing:
            return format_html('<span style="color: green;">🟢 Active</span>')
        elif obj.is_active:
            return format_html('<span style="color: orange;">🟡 Scheduled</span>')
        else:
            return format_html('<span style="color: red;">🔴 Inactive</span>')
    session_status.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Customize admin site header and title
admin.site.site_header = "Blockchain Voting System Administration"
admin.site.site_title = "Blockchain Voting Admin"
admin.site.index_title = "Welcome to Blockchain Voting System Administration"

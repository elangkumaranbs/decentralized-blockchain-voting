from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    BlockchainNetwork, SmartContract, BlockchainTransaction, 
    VoteRecord, BlockchainAuditLog
)


# @admin.register(BlockchainNetwork)  # Commented out to hide from admin
class BlockchainNetworkAdmin(admin.ModelAdmin):
    list_display = ['network_name', 'chain_id', 'rpc_url', 'is_active', 'created_at']
    list_filter = ['network_name', 'is_active', 'created_at']
    search_fields = ['network_name', 'rpc_url']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Network Information', {
            'fields': ('network_name', 'rpc_url', 'chain_id')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        # Ensure only one network is active at a time
        if obj.is_active:
            BlockchainNetwork.objects.filter(is_active=True).update(is_active=False)
        super().save_model(request, obj, form, change)


# @admin.register(SmartContract)  # Commented out to hide from admin
class SmartContractAdmin(admin.ModelAdmin):
    list_display = ['contract_name', 'contract_address', 'network', 'is_active', 'deployed_at']
    list_filter = ['network', 'is_active', 'deployed_at']
    search_fields = ['contract_name', 'contract_address']
    readonly_fields = ['id', 'deployed_at', 'deployment_link']
    fieldsets = (
        ('Contract Information', {
            'fields': ('contract_name', 'contract_address', 'network')
        }),
        ('Contract Code', {
            'fields': ('abi', 'bytecode'),
            'classes': ('collapse',)
        }),
        ('Deployment', {
            'fields': ('deployment_tx_hash', 'deployment_link', 'deployed_at')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    )
    
    def deployment_link(self, obj):
        if obj.deployment_tx_hash:
            if obj.network.network_name == 'ethereum':
                url = f"https://etherscan.io/tx/{obj.deployment_tx_hash}"
            elif obj.network.network_name == 'sepolia':
                url = f"https://sepolia.etherscan.io/tx/{obj.deployment_tx_hash}"
            else:
                return obj.deployment_tx_hash
            return format_html('<a href="{}" target="_blank">View on Explorer</a>', url)
        return 'No deployment hash'
    deployment_link.short_description = 'Deployment Link'


# @admin.register(BlockchainTransaction)  # Commented out to hide from admin
class BlockchainTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_hash_short', 'transaction_type', 'status', 
        'from_address_short', 'to_address_short', 'gas_used', 'created_at'
    ]
    list_filter = ['transaction_type', 'status', 'network', 'created_at']
    search_fields = ['transaction_hash', 'from_address', 'to_address']
    readonly_fields = [
        'id', 'created_at', 'confirmed_at', 'confirmation_time_display', 
        'explorer_link', 'transaction_details'
    ]
    fieldsets = (
        ('Transaction Information', {
            'fields': (
                'transaction_hash', 'transaction_type', 'status',
                'from_address', 'to_address'
            )
        }),
        ('Gas Information', {
            'fields': ('gas_used', 'gas_price')
        }),
        ('Block Information', {
            'fields': ('block_number', 'block_hash')
        }),
        ('Network & Contract', {
            'fields': ('network', 'contract')
        }),
        ('Additional Data', {
            'fields': ('transaction_data',),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('created_at', 'confirmed_at', 'confirmation_time_display')
        }),
        ('External Links', {
            'fields': ('explorer_link', 'transaction_details')
        }),
        ('System Information', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    )
    
    def transaction_hash_short(self, obj):
        return f"{obj.transaction_hash[:10]}..."
    transaction_hash_short.short_description = 'TX Hash'
    
    def from_address_short(self, obj):
        return f"{obj.from_address[:8]}..."
    from_address_short.short_description = 'From'
    
    def to_address_short(self, obj):
        return f"{obj.to_address[:8]}..."
    to_address_short.short_description = 'To'
    
    def confirmation_time_display(self, obj):
        time = obj.confirmation_time
        if time:
            return f"{time.total_seconds():.2f} seconds"
        return 'Not confirmed'
    confirmation_time_display.short_description = 'Confirmation Time'
    
    def explorer_link(self, obj):
        if obj.network.network_name == 'ethereum':
            url = f"https://etherscan.io/tx/{obj.transaction_hash}"
        elif obj.network.network_name == 'sepolia':
            url = f"https://sepolia.etherscan.io/tx/{obj.transaction_hash}"
        else:
            return 'Local network'
        return format_html('<a href="{}" target="_blank">View on Explorer</a>', url)
    explorer_link.short_description = 'Explorer Link'
    
    def transaction_details(self, obj):
        details = []
        if obj.gas_used and obj.gas_price:
            cost = obj.gas_used * obj.gas_price / 10**18  # Convert to ETH
            details.append(f"Cost: {cost:.6f} ETH")
        if obj.block_number:
            details.append(f"Block: {obj.block_number}")
        return "<br>".join(details) if details else "No details"
    transaction_details.short_description = 'Details'
    transaction_details.allow_tags = True


# @admin.register(VoteRecord)  # Commented out to hide from admin
class VoteRecordAdmin(admin.ModelAdmin):
    list_display = [
        'voter_hash_short', 'party_id', 'vote_timestamp_display', 
        'verification_status', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['voter_hash', 'party_id']
    readonly_fields = [
        'id', 'created_at', 'verification_status', 'blockchain_link',
        'vote_timestamp_display'
    ]
    fieldsets = (
        ('Vote Information', {
            'fields': ('voter_hash', 'party_id', 'vote_timestamp_display')
        }),
        ('Blockchain Verification', {
            'fields': ('blockchain_transaction', 'verification_status', 'blockchain_link')
        }),
        ('Merkle Proof', {
            'fields': ('merkle_proof',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def voter_hash_short(self, obj):
        return f"{obj.voter_hash[:12]}..."
    voter_hash_short.short_description = 'Voter Hash'
    
    def vote_timestamp_display(self, obj):
        from datetime import datetime
        return datetime.fromtimestamp(obj.vote_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    vote_timestamp_display.short_description = 'Vote Time'
    
    def verification_status(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        return format_html('<span style="color: red;">✗ Not Verified</span>')
    verification_status.short_description = 'Verification'
    
    def blockchain_link(self, obj):
        if obj.blockchain_transaction:
            url = reverse('admin:blockchain_blockchaintransaction_change', 
                         args=[obj.blockchain_transaction.id])
            return format_html('<a href="{}">View Transaction</a>', url)
        return 'No transaction'
    blockchain_link.short_description = 'Blockchain Transaction'
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of vote records for audit purposes
        return False


# @admin.register(BlockchainAuditLog)  # Commented out to hide from admin
class BlockchainAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'action_type', 'description_short', 'network', 
        'transaction_hash_short', 'created_at'
    ]
    list_filter = ['action_type', 'network', 'created_at']
    search_fields = ['description', 'transaction_hash']
    readonly_fields = ['id', 'created_at', 'explorer_link']
    fieldsets = (
        ('Audit Information', {
            'fields': ('action_type', 'description')
        }),
        ('Blockchain Information', {
            'fields': ('transaction_hash', 'block_number', 'network', 'explorer_link')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def transaction_hash_short(self, obj):
        if obj.transaction_hash:
            return f"{obj.transaction_hash[:10]}..."
        return 'No hash'
    transaction_hash_short.short_description = 'TX Hash'
    
    def explorer_link(self, obj):
        if obj.transaction_hash:
            if obj.network.network_name == 'ethereum':
                url = f"https://etherscan.io/tx/{obj.transaction_hash}"
            elif obj.network.network_name == 'sepolia':
                url = f"https://sepolia.etherscan.io/tx/{obj.transaction_hash}"
            else:
                return 'Local network'
            return format_html('<a href="{}" target="_blank">View on Explorer</a>', url)
        return 'No transaction'
    explorer_link.short_description = 'Explorer Link'
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of audit logs
        return False

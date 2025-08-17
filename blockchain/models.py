from django.db import models
import uuid
from datetime import datetime


class BlockchainNetwork(models.Model):
    """
    Model for storing blockchain network configurations
    """
    NETWORK_CHOICES = [
        ('ganache', 'Ganache (Local)'),
        ('ethereum', 'Ethereum Mainnet'),
        ('sepolia', 'Sepolia Testnet'),
        ('polygon', 'Polygon'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    network_name = models.CharField(max_length=50, choices=NETWORK_CHOICES, unique=True)
    rpc_url = models.URLField()
    chain_id = models.IntegerField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Blockchain Network"
        verbose_name_plural = "Blockchain Networks"
        ordering = ['network_name']
    
    def __str__(self):
        return f"{self.get_network_name_display()} (Chain ID: {self.chain_id})"


class SmartContract(models.Model):
    """
    Model for storing smart contract information
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract_name = models.CharField(max_length=100)
    contract_address = models.CharField(max_length=42)  # Ethereum address length
    abi = models.JSONField()  # Contract ABI
    bytecode = models.TextField(blank=True)  # Contract bytecode
    network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE, related_name='contracts')
    deployed_at = models.DateTimeField(auto_now_add=True)
    deployment_tx_hash = models.CharField(max_length=66, blank=True)  # Transaction hash
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Smart Contract"
        verbose_name_plural = "Smart Contracts"
        ordering = ['-deployed_at']
        unique_together = ['contract_address', 'network']
    
    def __str__(self):
        return f"{self.contract_name} on {self.network.network_name}"


class BlockchainTransaction(models.Model):
    """
    Model for tracking blockchain transactions
    """
    TRANSACTION_TYPES = [
        ('vote', 'Vote Transaction'),
        ('deploy', 'Contract Deployment'),
        ('config', 'Configuration Update'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_hash = models.CharField(max_length=66, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    from_address = models.CharField(max_length=42)
    to_address = models.CharField(max_length=42)
    gas_used = models.BigIntegerField(null=True, blank=True)
    gas_price = models.BigIntegerField(null=True, blank=True)
    block_number = models.BigIntegerField(null=True, blank=True)
    block_hash = models.CharField(max_length=66, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE, related_name='transactions')
    contract = models.ForeignKey(SmartContract, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    transaction_data = models.JSONField(blank=True, null=True)  # Additional transaction data
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Blockchain Transaction"
        verbose_name_plural = "Blockchain Transactions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.transaction_hash[:10]}..."
    
    @property
    def is_confirmed(self):
        """Check if transaction is confirmed"""
        return self.status == 'confirmed' and self.block_number is not None
    
    @property
    def confirmation_time(self):
        """Calculate time taken for confirmation"""
        if self.confirmed_at and self.created_at:
            return self.confirmed_at - self.created_at
        return None


class VoteRecord(models.Model):
    """
    Model for storing vote records on blockchain
    This is a blockchain-specific representation of votes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    voter_hash = models.CharField(max_length=64)  # Hashed voter identifier for privacy
    party_id = models.UUIDField()  # Reference to political party
    vote_timestamp = models.BigIntegerField()  # Unix timestamp
    blockchain_transaction = models.OneToOneField(
        BlockchainTransaction, 
        on_delete=models.CASCADE, 
        related_name='vote_record'
    )
    merkle_proof = models.JSONField(blank=True, null=True)  # Merkle tree proof for verification
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vote Record"
        verbose_name_plural = "Vote Records"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Vote Record - {self.voter_hash[:10]}... for Party {self.party_id}"
    
    @property
    def is_verified(self):
        """Check if vote record is verified on blockchain"""
        return self.blockchain_transaction.is_confirmed


class BlockchainAuditLog(models.Model):
    """
    Model for audit logging of blockchain operations
    """
    ACTION_TYPES = [
        ('vote_cast', 'Vote Cast'),
        ('vote_verified', 'Vote Verified'),
        ('contract_deployed', 'Contract Deployed'),
        ('network_changed', 'Network Changed'),
        ('audit_performed', 'Audit Performed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    transaction_hash = models.CharField(max_length=66, blank=True)
    block_number = models.BigIntegerField(null=True, blank=True)
    network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE, related_name='audit_logs')
    metadata = models.JSONField(blank=True, null=True)  # Additional audit data
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Blockchain Audit Log"
        verbose_name_plural = "Blockchain Audit Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

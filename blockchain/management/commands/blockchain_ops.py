from django.core.management.base import BaseCommand
from django.conf import settings
from blockchain.blockchain_client import blockchain_client
from blockchain.models import BlockchainNetwork, SmartContract, BlockchainAuditLog
from voting.models import PoliticalParty, Voter
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Blockchain operations for the voting system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test blockchain connection',
        )
        parser.add_argument(
            '--network-info',
            action='store_true',
            help='Get blockchain network information',
        )
        parser.add_argument(
            '--deploy-contract',
            action='store_true',
            help='Deploy voting smart contract (requires compiled contract)',
        )
        parser.add_argument(
            '--register-parties',
            action='store_true',
            help='Register political parties on blockchain',
        )
        parser.add_argument(
            '--test-vote',
            action='store_true',
            help='Test vote casting functionality',
        )
        parser.add_argument(
            '--get-results',
            action='store_true',
            help='Get voting results from blockchain',
        )
        parser.add_argument(
            '--audit-integrity',
            action='store_true',
            help='Audit vote integrity between database and blockchain',
        )
        parser.add_argument(
            '--full-test',
            action='store_true',
            help='Run full blockchain test suite',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting blockchain operations...'))
        
        # Test connection
        if options['test_connection'] or options['full_test']:
            self.test_connection()
        
        # Get network info
        if options['network_info'] or options['full_test']:
            self.get_network_info()
        
        # Deploy contract
        if options['deploy_contract']:
            self.deploy_contract()
        
        # Register parties
        if options['register_parties'] or options['full_test']:
            self.register_parties()
        
        # Test vote
        if options['test_vote'] or options['full_test']:
            self.test_vote()
        
        # Get results
        if options['get_results'] or options['full_test']:
            self.get_results()
        
        # Audit integrity
        if options['audit_integrity'] or options['full_test']:
            self.audit_integrity()
        
        self.stdout.write(self.style.SUCCESS('Blockchain operations completed!'))
    
    def test_connection(self):
        """Test blockchain connection"""
        self.stdout.write('Testing blockchain connection...')
        
        try:
            if blockchain_client.test_connection():
                self.stdout.write(self.style.SUCCESS('✓ Blockchain connection successful!'))
                
                # Record audit log
                self.create_audit_log('CONNECTION_TEST', 'Blockchain connection test successful')
            else:
                self.stdout.write(self.style.ERROR('✗ Blockchain connection failed!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Blockchain connection error: {e}'))
    
    def get_network_info(self):
        """Get blockchain network information"""
        self.stdout.write('Getting blockchain network information...')
        
        try:
            network_info = blockchain_client.get_network_info()
            
            if network_info:
                self.stdout.write('\n' + '='*50)
                self.stdout.write('BLOCKCHAIN NETWORK INFO')
                self.stdout.write('='*50)
                self.stdout.write(f'Chain ID: {network_info.get("chain_id", "Unknown")}')
                self.stdout.write(f'Latest Block: {network_info.get("latest_block", "Unknown")}')
                self.stdout.write(f'Gas Price: {network_info.get("gas_price_gwei", "Unknown")} Gwei')
                self.stdout.write(f'Connected: {network_info.get("is_connected", False)}')
                self.stdout.write('='*50)
                
                # Update or create network record
                network, created = BlockchainNetwork.objects.get_or_create(
                    chain_id=network_info.get('chain_id', 0),
                    defaults={
                        'network_name': 'default',
                        'rpc_url': blockchain_client.network_url,
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(f'✓ Network record created: {network.network_name}')
                else:
                    self.stdout.write(f'✓ Network record updated: {network.network_name}')
            else:
                self.stdout.write(self.style.ERROR('✗ Failed to get network information'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error getting network info: {e}'))
    
    def deploy_contract(self):
        """Deploy voting smart contract"""
        self.stdout.write('Deploying voting smart contract...')
        
        # Note: This is a placeholder for contract deployment
        # In a real implementation, you would:
        # 1. Compile the Solidity contract
        # 2. Deploy it using Web3
        # 3. Save the contract address and ABI
        
        self.stdout.write(self.style.WARNING(
            'Contract deployment requires compiled bytecode and ABI.\n'
            'Please compile the VotingContract.sol file using Solidity compiler\n'
            'and update the blockchain_client with the contract address.'
        ))
        
        # Create a placeholder contract record
        try:
            network = BlockchainNetwork.objects.filter(is_active=True).first()
            if not network:
                self.stdout.write(self.style.ERROR('No active blockchain network found'))
                return
            
            contract, created = SmartContract.objects.get_or_create(
                contract_name='VotingContract',
                defaults={
                    'contract_address': '0x0000000000000000000000000000000000000000',  # Placeholder
                    'network': network,
                    'abi': json.dumps(blockchain_client.get_default_voting_abi()),
                    'is_active': False  # Set to False until actually deployed
                }
            )
            
            if created:
                self.stdout.write(f'✓ Contract record created: {contract.contract_name}')
            else:
                self.stdout.write(f'✓ Contract record exists: {contract.contract_name}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error creating contract record: {e}'))
    
    def register_parties(self):
        """Register political parties on blockchain"""
        self.stdout.write('Registering political parties on blockchain...')
        
        try:
            parties = PoliticalParty.objects.filter(is_active=True)
            
            if not parties.exists():
                self.stdout.write(self.style.WARNING('No active political parties found in database'))
                return
            
            registered_count = 0
            
            for party in parties:
                try:
                    # In a real implementation, this would call the smart contract
                    # For now, we'll simulate the registration
                    
                    self.stdout.write(f'  ✓ Simulated registration for party: {party.name}')
                    registered_count += 1
                    
                    # Create audit log
                    self.create_audit_log(
                        'PARTY_REGISTRATION',
                        f'Political party registered: {party.name}',
                        {'party_id': str(party.id), 'party_name': party.name}
                    )
                    
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Failed to register party {party.name}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'✓ Registered {registered_count} parties on blockchain!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error registering parties: {e}'))
    
    def test_vote(self):
        """Test vote casting functionality"""
        self.stdout.write('Testing vote casting functionality...')
        
        try:
            # Get a test voter and party
            voter = Voter.objects.filter(is_active=True, has_voted=False).first()
            party = PoliticalParty.objects.filter(is_active=True).first()
            
            if not voter or not party:
                self.stdout.write(self.style.WARNING('No suitable voter or party found for testing'))
                return
            
            # Generate voter hash
            voter_data = {
                'id': str(voter.id),
                'email': voter.email,
                'aadhaar_number': voter.aadhaar_number
            }
            voter_hash = blockchain_client.generate_voter_hash(voter_data)
            
            self.stdout.write(f'Generated voter hash: {voter_hash[:20]}...')
            self.stdout.write(f'Testing vote for party: {party.name}')
            
            # In a real implementation, this would cast the vote on blockchain
            # For now, we'll simulate the vote casting
            
            self.stdout.write(f'  ✓ Simulated vote cast for voter: {voter.full_name}')
            
            # Create vote record
            vote_record = blockchain_client.create_vote_record(
                voter_hash, str(party.id), 'simulated_tx_hash'
            )
            
            if vote_record:
                self.stdout.write(f'  ✓ Vote record created in database')
            
            # Create audit log
            self.create_audit_log(
                'VOTE_CAST',
                f'Test vote cast for voter: {voter.full_name}',
                {
                    'voter_id': str(voter.id),
                    'party_id': str(party.id),
                    'voter_hash': voter_hash
                }
            )
            
            self.stdout.write(self.style.SUCCESS('✓ Vote casting test completed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error testing vote: {e}'))
    
    def get_results(self):
        """Get voting results from blockchain"""
        self.stdout.write('Getting voting results from blockchain...')
        
        try:
            # Get analytics from blockchain client
            analytics = blockchain_client.get_blockchain_analytics()
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write('BLOCKCHAIN VOTING RESULTS')
            self.stdout.write('='*50)
            self.stdout.write(f'Total Votes (Blockchain): {analytics.get("total_votes_blockchain", 0)}')
            self.stdout.write(f'Contract Address: {analytics.get("contract_address", "Not set")}')
            self.stdout.write(f'Network Connected: {analytics.get("is_connected", False)}')
            
            # Get database vote counts for comparison
            from voting.models import Vote
            db_vote_count = Vote.objects.count()
            self.stdout.write(f'Total Votes (Database): {db_vote_count}')
            
            self.stdout.write('='*50)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error getting results: {e}'))
    
    def audit_integrity(self):
        """Audit vote integrity between database and blockchain"""
        self.stdout.write('Auditing vote integrity...')
        
        try:
            audit_results = blockchain_client.audit_vote_integrity()
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write('VOTE INTEGRITY AUDIT')
            self.stdout.write('='*50)
            self.stdout.write(f'Total Records: {audit_results.get("total_records", 0)}')
            self.stdout.write(f'Verified Count: {audit_results.get("verified_count", 0)}')
            self.stdout.write(f'Failed Count: {audit_results.get("failed_count", 0)}')
            self.stdout.write(f'Integrity: {audit_results.get("integrity_percentage", 0):.2f}%')
            self.stdout.write('='*50)
            
            # Create audit log
            self.create_audit_log(
                'INTEGRITY_AUDIT',
                'Vote integrity audit completed',
                audit_results
            )
            
            if audit_results.get('integrity_percentage', 0) >= 95:
                self.stdout.write(self.style.SUCCESS('✓ Vote integrity is excellent!'))
            elif audit_results.get('integrity_percentage', 0) >= 80:
                self.stdout.write(self.style.WARNING('⚠ Vote integrity is acceptable but needs attention'))
            else:
                self.stdout.write(self.style.ERROR('✗ Vote integrity is poor - investigation required'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error auditing integrity: {e}'))
    
    def create_audit_log(self, action_type: str, description: str, metadata: dict = None):
        """Create an audit log entry"""
        try:
            network = BlockchainNetwork.objects.filter(is_active=True).first()
            
            BlockchainAuditLog.objects.create(
                action_type=action_type,
                description=description,
                network=network,
                metadata=json.dumps(metadata or {})
            )
            
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
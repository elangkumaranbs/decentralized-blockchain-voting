/**
 * MetaMask Integration Module for Blockchain Voting
 * Handles Web3 connectivity, wallet connection, and smart contract interactions
 */

class MetaMaskVoting {
    constructor() {
        this.web3 = null;
        this.account = null;
        this.contract = null;
        this.contractAddress = null;
        this.contractABI = [
            {
                "inputs": [
                    {"internalType": "bytes32", "name": "_voterHash", "type": "bytes32"},
                    {"internalType": "string", "name": "_partyId", "type": "string"}
                ],
                "name": "castVote",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "bytes32", "name": "_voterHash", "type": "bytes32"}],
                "name": "hasVoted",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "string", "name": "_partyId", "type": "string"}],
                "name": "getVoteCount",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getTotalVotes",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "isVotingActive",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "anonymous": false,
                "inputs": [
                    {"indexed": true, "internalType": "bytes32", "name": "voterHash", "type": "bytes32"},
                    {"indexed": false, "internalType": "string", "name": "partyId", "type": "string"},
                    {"indexed": false, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
                ],
                "name": "VoteCast",
                "type": "event"
            }
        ];
        this.isConnected = false;
        this.networkId = null;
        this.init();
    }

    /**
     * Initialize MetaMask integration
     */
    async init() {
        if (typeof window.ethereum !== 'undefined') {
            this.web3 = new Web3(window.ethereum);
            await this.setupEventListeners();
            await this.checkConnection();
        } else {
            console.warn('MetaMask not detected');
        }
    }

    /**
     * Setup MetaMask event listeners
     */
    async setupEventListeners() {
        if (window.ethereum) {
            window.ethereum.on('accountsChanged', (accounts) => {
                this.handleAccountsChanged(accounts);
            });

            window.ethereum.on('chainChanged', (chainId) => {
                this.handleChainChanged(chainId);
            });

            window.ethereum.on('disconnect', () => {
                this.handleDisconnect();
            });
        }
    }

    /**
     * Check if already connected to MetaMask
     */
    async checkConnection() {
        try {
            const accounts = await this.web3.eth.getAccounts();
            if (accounts.length > 0) {
                this.account = accounts[0];
                this.isConnected = true;
                this.networkId = await this.web3.eth.net.getId();
                await this.initContract();
                this.updateUI();
            }
        } catch (error) {
            console.error('Error checking connection:', error);
        }
    }

    /**
     * Connect to MetaMask wallet
     */
    async connectWallet() {
        try {
            if (typeof window.ethereum === 'undefined') {
                throw new Error('MetaMask is not installed. Please install MetaMask to continue.');
            }

            // Request account access
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });

            if (accounts.length === 0) {
                throw new Error('No accounts found. Please unlock MetaMask.');
            }

            this.account = accounts[0];
            this.isConnected = true;
            this.networkId = await this.web3.eth.net.getId();

            // Initialize contract
            await this.initContract();

            // Update UI
            this.updateUI();

            return {
                success: true,
                account: this.account,
                networkId: this.networkId
            };

        } catch (error) {
            console.error('Error connecting to MetaMask:', error);
            if (error.code === 4001) {
                this.updateTransactionStatus('error', 'Connection rejected by user. Please approve the connection to use blockchain voting.');
            } else {
                this.updateTransactionStatus('error', 'Failed to connect to MetaMask. Please try again.');
            }
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Initialize smart contract
     */
    async initContract() {
        try {
            // Get contract address from backend or environment
            const contractAddress = await this.getContractAddress();
            if (contractAddress) {
                this.contractAddress = contractAddress;
                this.contract = new this.web3.eth.Contract(this.contractABI, contractAddress);
            } else {
                console.warn('Contract address not configured');
                this.updateTransactionStatus('error', 'Smart contract not configured. Please contact administrator.');
            }
        } catch (error) {
            console.error('Error initializing contract:', error);
            this.updateTransactionStatus('error', 'Failed to initialize smart contract. Please check network connection.');
        }
    }

    /**
     * Get contract address from backend
     */
    async getContractAddress() {
        try {
            // This should be configured in your Django settings or fetched from API
            // For now, return a placeholder - you'll need to set this up
            return process.env.VOTING_CONTRACT_ADDRESS || '0x...'; // Replace with actual contract address
        } catch (error) {
            console.error('Error getting contract address:', error);
            return null;
        }
    }

    /**
     * Generate voter hash (should match backend implementation)
     */
    generateVoterHash(voterData) {
        const dataString = `${voterData.id}${voterData.email}${voterData.aadhaar_number}`;
        return this.web3.utils.keccak256(dataString);
    }

    /**
     * Check if voter has already voted
     */
    async hasVoted(voterHash) {
        try {
            if (!this.contract) {
                throw new Error('Contract not initialized');
            }

            const voted = await this.contract.methods.hasVoted(voterHash).call();
            return voted;
        } catch (error) {
            console.error('Error checking vote status:', error);
            return false;
        }
    }

    /**
     * Check if voting is currently active
     */
    async isVotingActive() {
        try {
            if (!this.contract) {
                throw new Error('Contract not initialized');
            }

            const active = await this.contract.methods.isVotingActive().call();
            return active;
        } catch (error) {
            console.error('Error checking voting status:', error);
            return false;
        }
    }

    /**
     * Cast vote on blockchain with transaction tracking
     */
    async castVote(voterData, partyId) {
        try {
            if (!this.isConnected) {
                throw new Error('Wallet not connected');
            }

            if (!this.contract) {
                throw new Error('Contract not initialized');
            }

            // Generate voter hash
            const voterHash = this.generateVoterHash(voterData);

            // Check if already voted
            const alreadyVoted = await this.hasVoted(voterHash);
            if (alreadyVoted) {
                throw new Error('You have already voted');
            }

            // Check if voting is active
            const votingActive = await this.isVotingActive();
            if (!votingActive) {
                throw new Error('Voting is not currently active');
            }

            // Update UI to show transaction pending
            this.updateTransactionStatus('pending', 'Preparing transaction...');

            // Estimate gas
            const gasEstimate = await this.contract.methods
                .castVote(voterHash, partyId)
                .estimateGas({ from: this.account });

            this.updateTransactionStatus('pending', 'Sending transaction to blockchain...');

            // Send transaction
            const transaction = await this.contract.methods
                .castVote(voterHash, partyId)
                .send({
                    from: this.account,
                    gas: Math.floor(gasEstimate * 1.2), // Add 20% buffer
                });

            this.updateTransactionStatus('confirming', `Transaction sent. Hash: ${transaction.transactionHash}`);

            // Wait for confirmation
            const receipt = await this.waitForTransactionConfirmation(transaction.transactionHash);

            this.updateTransactionStatus('confirmed', `Vote confirmed! Block: ${receipt.blockNumber}`);

            return {
                success: true,
                transactionHash: transaction.transactionHash,
                blockNumber: receipt.blockNumber,
                gasUsed: receipt.gasUsed
            };

        } catch (error) {
            console.error('Error casting vote:', error);
            this.updateTransactionStatus('error', `Transaction failed: ${error.message}`);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get vote count for a party
     */
    async getVoteCount(partyId) {
        try {
            if (!this.contract) {
                throw new Error('Contract not initialized');
            }

            const count = await this.contract.methods.getVoteCount(partyId).call();
            return parseInt(count);
        } catch (error) {
            console.error('Error getting vote count:', error);
            return 0;
        }
    }

    /**
     * Get total votes
     */
    async getTotalVotes() {
        try {
            if (!this.contract) {
                throw new Error('Contract not initialized');
            }

            const total = await this.contract.methods.getTotalVotes().call();
            return parseInt(total);
        } catch (error) {
            console.error('Error getting total votes:', error);
            return 0;
        }
    }

    /**
     * Handle account changes
     */
    handleAccountsChanged(accounts) {
        if (accounts.length === 0) {
            this.handleDisconnect();
        } else {
            this.account = accounts[0];
            this.updateUI();
        }
    }

    /**
     * Handle chain changes
     */
    handleChainChanged(chainId) {
        this.networkId = parseInt(chainId, 16);
        this.updateUI();
        // Reload page to reset state
        window.location.reload();
    }

    /**
     * Handle disconnect
     */
    handleDisconnect() {
        this.account = null;
        this.isConnected = false;
        this.contract = null;
        this.updateUI();
    }

    /**
     * Wait for transaction confirmation
     */
    async waitForTransactionConfirmation(txHash, confirmations = 1) {
        return new Promise((resolve, reject) => {
            const checkConfirmation = async () => {
                try {
                    const receipt = await this.web3.eth.getTransactionReceipt(txHash);
                    if (receipt && receipt.blockNumber) {
                        const currentBlock = await this.web3.eth.getBlockNumber();
                        const confirmationCount = currentBlock - receipt.blockNumber + 1;
                        
                        if (confirmationCount >= confirmations) {
                            resolve(receipt);
                        } else {
                            this.updateTransactionStatus('confirming', 
                                `Waiting for confirmations: ${confirmationCount}/${confirmations}`);
                            setTimeout(checkConfirmation, 3000);
                        }
                    } else {
                        setTimeout(checkConfirmation, 3000);
                    }
                } catch (error) {
                    reject(error);
                }
            };
            checkConfirmation();
        });
    }

    /**
     * Update transaction status in UI
     */
    updateTransactionStatus(status, message) {
        const statusElement = document.getElementById('transactionStatus');
        const messageElement = document.getElementById('transactionMessage');
        const spinnerElement = document.getElementById('transactionSpinner');
        
        if (statusElement) {
            statusElement.className = `transaction-status ${status}`;
            statusElement.style.display = 'block';
        }
        
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        // Show/hide spinner based on status
        if (spinnerElement) {
            if (status === 'pending' || status === 'confirming') {
                spinnerElement.style.display = 'flex';
            } else {
                spinnerElement.style.display = 'none';
            }
        }
        
        console.log(`Transaction ${status}: ${message}`);
        
        // Auto-hide success/error messages after 10 seconds
        if (status === 'confirmed' || status === 'error') {
            setTimeout(() => {
                if (statusElement) {
                    statusElement.style.display = 'none';
                }
            }, 10000);
        }
    }

    /**
     * Update UI based on connection status
     */
    updateUI() {
        // Update wallet connection status
        const connectBtn = document.getElementById('connectWalletBtn');
        const walletStatus = document.getElementById('walletStatus');
        const accountInfo = document.getElementById('accountInfo');

        if (this.isConnected && this.account) {
            if (connectBtn) {
                connectBtn.textContent = 'Wallet Connected';
                connectBtn.disabled = true;
                connectBtn.classList.remove('btn-primary');
                connectBtn.classList.add('btn-success');
            }

            if (walletStatus) {
                walletStatus.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        Wallet Connected: ${this.account.substring(0, 6)}...${this.account.substring(38)}
                    </div>
                `;
            }

            if (accountInfo) {
                accountInfo.innerHTML = `
                    <div class="wallet-info">
                        <strong>Account:</strong> ${this.account.substring(0, 6)}...${this.account.substring(38)}<br>
                        <strong>Network:</strong> ${this.getNetworkName(this.networkId)}
                    </div>
                `;
            }
        } else {
            if (connectBtn) {
                connectBtn.textContent = 'Connect MetaMask';
                connectBtn.disabled = false;
                connectBtn.classList.remove('btn-success');
                connectBtn.classList.add('btn-primary');
            }

            if (walletStatus) {
                walletStatus.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Please connect your MetaMask wallet to vote on blockchain
                    </div>
                `;
            }

            if (accountInfo) {
                accountInfo.innerHTML = '';
            }
        }
    }

    /**
     * Get network name from ID
     */
    getNetworkName(networkId) {
        const networks = {
            1: 'Ethereum Mainnet',
            3: 'Ropsten Testnet',
            4: 'Rinkeby Testnet',
            5: 'Goerli Testnet',
            42: 'Kovan Testnet',
            1337: 'Local Development',
            31337: 'Hardhat Network'
        };
        return networks[networkId] || `Network ${networkId}`;
    }

    /**
     * Disconnect wallet
     */
    disconnect() {
        this.handleDisconnect();
    }
}

// Initialize MetaMask integration when DOM is loaded
let metaMaskVoting;

document.addEventListener('DOMContentLoaded', function() {
    metaMaskVoting = new MetaMaskVoting();
    
    // Bind connect wallet button
    const connectBtn = document.getElementById('connectWalletBtn');
    if (connectBtn) {
        connectBtn.addEventListener('click', async () => {
            const result = await metaMaskVoting.connectWallet();
            if (!result.success) {
                alert('Failed to connect wallet: ' + result.error);
            }
        });
    }
});

// Export for global access
window.MetaMaskVoting = MetaMaskVoting;
window.metaMaskVoting = metaMaskVoting;
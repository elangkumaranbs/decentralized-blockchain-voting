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
        try {
            if (typeof window.ethereum !== 'undefined') {
                this.web3 = new Web3(window.ethereum);
                await this.setupEventListeners();
                await this.checkConnection();
                console.log('MetaMask integration initialized successfully');
            } else {
                console.warn('MetaMask not detected. Blockchain features will be disabled.');
                this.showMetaMaskInstallPrompt();
            }
        } catch (error) {
            console.error('Failed to initialize MetaMask:', error);
            this.showMetaMaskError(error.message);
        }
    }

    /**
     * Show MetaMask installation prompt
     */
    showMetaMaskInstallPrompt() {
        if (typeof window !== 'undefined' && document.getElementById('metamask-install-prompt')) {
            const promptEl = document.getElementById('metamask-install-prompt');
            promptEl.style.display = 'block';
        }
    }

    /**
     * Show MetaMask error message
     */
    showMetaMaskError(message) {
        console.error('MetaMask Error:', message);
        if (typeof window !== 'undefined') {
            // Create or update error message element
            let errorEl = document.getElementById('metamask-error');
            if (!errorEl) {
                errorEl = document.createElement('div');
                errorEl.id = 'metamask-error';
                errorEl.className = 'alert alert-warning metamask-error';
                errorEl.style.cssText = 'margin: 1rem 0; padding: 1rem; border-radius: 8px; background: #fff3cd; border: 1px solid #ffeaa7; color: #856404;';
                
                // Find a good place to insert the error message
                const container = document.querySelector('.voting-container') || document.querySelector('.container') || document.body;
                container.insertBefore(errorEl, container.firstChild);
            }
            errorEl.innerHTML = `
                <div style="display: flex; align-items: center;">
                    <i class="fas fa-exclamation-triangle" style="margin-right: 0.5rem;"></i>
                    <div>
                        <strong>MetaMask Not Available:</strong> ${message}
                        <br><small>Don't worry! You can still vote using the traditional method.</small>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Check if MetaMask is available and ready
     */
    isMetaMaskAvailable() {
        return typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask;
    }

    /**
     * Get MetaMask status information
     */
    getStatus() {
        return {
            isAvailable: this.isMetaMaskAvailable(),
            isConnected: this.isConnected,
            account: this.account,
            networkId: this.networkId,
            hasContract: !!this.contract
        };
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
            // Check if MetaMask is installed
            if (typeof window.ethereum === 'undefined') {
                const error = 'MetaMask extension not found. Please install MetaMask from https://metamask.io/';
                this.showMetaMaskError(error);
                throw new Error(error);
            }

            // Check if MetaMask is accessible
            if (!window.ethereum.isMetaMask) {
                const error = 'MetaMask not detected. Please make sure MetaMask is installed and enabled.';
                this.showMetaMaskError(error);
                throw new Error(error);
            }

            // Request account access
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            }).catch((err) => {
                if (err.code === 4001) {
                    throw new Error('User rejected the request to connect to MetaMask.');
                } else if (err.code === -32002) {
                    throw new Error('MetaMask is already processing a connection request. Please check MetaMask.');
                } else {
                    throw new Error('Failed to connect to MetaMask: ' + err.message);
                }
            });

            if (accounts.length === 0) {
                throw new Error('No accounts found. Please unlock MetaMask and try again.');
            }

            this.account = accounts[0];
            this.isConnected = true;
            this.networkId = await this.web3.eth.net.getId();

            // Initialize contract
            await this.initContract();

            // Update UI
            this.updateUI();

            // Hide any error messages
            const errorEl = document.getElementById('metamask-error');
            if (errorEl) {
                errorEl.style.display = 'none';
            }

            console.log('MetaMask connected successfully:', this.account);

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
            if (contractAddress && contractAddress !== '0x...' && contractAddress !== 'undefined') {
                this.contractAddress = contractAddress;
                this.contract = new this.web3.eth.Contract(this.contractABI, contractAddress);
                console.log('Smart contract initialized:', contractAddress);
            } else {
                console.warn('Contract address not configured - blockchain voting disabled');
                this.contract = null;
                // Don't show error to user, just log it
                console.info('Smart contract not configured. Traditional voting will be used.');
            }
        } catch (error) {
            console.error('Error initializing contract:', error);
            this.contract = null;
            // Don't show error UI, just disable blockchain features
            console.info('Failed to initialize smart contract. Traditional voting will be used.');
        }
    }

    /**
     * Get contract address from backend
     */
    async getContractAddress() {
        try {
            // Check for contract address in various places
            
            // 1. Environment variable (if available)
            if (typeof process !== 'undefined' && process.env && process.env.VOTING_CONTRACT_ADDRESS) {
                return process.env.VOTING_CONTRACT_ADDRESS;
            }
            
            // 2. Meta tag in HTML
            const metaTag = document.querySelector('meta[name="voting-contract-address"]');
            if (metaTag && metaTag.getAttribute('content')) {
                return metaTag.getAttribute('content');
            }
            
            // 3. Global variable
            if (typeof window.VOTING_CONTRACT_ADDRESS !== 'undefined') {
                return window.VOTING_CONTRACT_ADDRESS;
            }
            
            // 4. Try to fetch from backend API (if available)
            try {
                const response = await fetch('/api/blockchain/contract-address/');
                if (response.ok) {
                    const data = await response.json();
                    return data.address;
                }
            } catch (fetchError) {
                console.log('Could not fetch contract address from API:', fetchError.message);
            }
            
            // 5. Return null if not found anywhere
            console.warn('Voting contract address not configured in any location');
            return null;
            
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
                console.warn('Contract not available for vote checking - assuming not voted');
                return false; // Assume not voted if contract unavailable
            }

            const voted = await this.contract.methods.hasVoted(voterHash).call();
            return voted;
        } catch (error) {
            console.error('Error checking vote status:', error);
            return false; // Default to allowing vote if check fails
        }
    }

    /**
     * Check if voting is currently active
     */
    async isVotingActive() {
        try {
            if (!this.contract) {
                console.warn('Contract not available for voting status check - assuming active');
                return true; // Assume voting is active if contract unavailable
            }

            const active = await this.contract.methods.isVotingActive().call();
            return active;
        } catch (error) {
            console.error('Error checking voting status:', error);
            return true; // Default to allowing vote if check fails
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
// Initialize MetaMask integration immediately or create safe fallback
let metaMaskVoting;

// Create a safe wrapper that handles initialization and errors gracefully
function createMetaMaskWrapper() {
    return {
        isConnected: false,
        isMetaMaskAvailable: () => typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask,
        connectWallet: async () => {
            if (!window.metaMaskVoting.isMetaMaskAvailable()) {
                throw new Error('MetaMask extension not found. Please install MetaMask from https://metamask.io/');
            }
            if (metaMaskVoting && typeof metaMaskVoting.connectWallet === 'function') {
                return await metaMaskVoting.connectWallet();
            }
            throw new Error('MetaMask integration not fully initialized yet. Please wait for page to load.');
        },
        getStatus: () => {
            if (metaMaskVoting && typeof metaMaskVoting.getStatus === 'function') {
                return metaMaskVoting.getStatus();
            }
            return {
                isAvailable: typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask,
                isConnected: false,
                account: null,
                networkId: null,
                hasContract: false
            };
        }
    };
}

// Make it available immediately
window.metaMaskVoting = createMetaMaskWrapper();

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing MetaMask integration...');
    
    try {
        metaMaskVoting = new MetaMaskVoting();
        
        // Update the global reference once initialized
        window.metaMaskVoting = metaMaskVoting;
        
        console.log('MetaMask integration fully initialized');
        
    } catch (error) {
        console.error('Failed to initialize MetaMask integration:', error);
        // Keep the safe wrapper in place
    }
    
    // Bind connect wallet button
    const connectBtn = document.getElementById('connectWalletBtn');
    if (connectBtn) {
        connectBtn.addEventListener('click', async () => {
            try {
                const result = await window.metaMaskVoting.connectWallet();
                if (!result.success) {
                    alert('Failed to connect wallet: ' + result.error);
                }
            } catch (error) {
                console.error('Connect wallet error:', error);
                alert('Error connecting to MetaMask: ' + error.message);
            }
        });
    }
});

// Export for global access
window.MetaMaskVoting = MetaMaskVoting;
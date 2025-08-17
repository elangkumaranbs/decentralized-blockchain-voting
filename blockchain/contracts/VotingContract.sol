// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title VotingContract
 * @dev Smart contract for secure and transparent voting system
 * @author Blockchain Voting System
 */
contract VotingContract {
    // Events
    event VoteCast(bytes32 indexed voterHash, string partyId, uint256 timestamp);
    event VotingSessionStarted(uint256 sessionId, uint256 startTime, uint256 endTime);
    event VotingSessionEnded(uint256 sessionId, uint256 endTime);
    event PartyRegistered(string partyId, string partyName);
    event AdminAdded(address indexed admin);
    event AdminRemoved(address indexed admin);
    
    // Structs
    struct Vote {
        bytes32 voterHash;
        string partyId;
        uint256 timestamp;
        bool exists;
    }
    
    struct Party {
        string partyId;
        string partyName;
        string description;
        uint256 voteCount;
        bool isActive;
    }
    
    struct VotingSession {
        uint256 sessionId;
        string sessionName;
        uint256 startTime;
        uint256 endTime;
        bool isActive;
        uint256 totalVotes;
    }
    
    // State variables
    address public owner;
    mapping(address => bool) public admins;
    mapping(bytes32 => bool) public hasVoted;
    mapping(string => Party) public parties;
    mapping(bytes32 => Vote) public votes;
    mapping(uint256 => VotingSession) public votingSessions;
    
    string[] public partyIds;
    bytes32[] public voteHashes;
    uint256 public currentSessionId;
    uint256 public totalVotes;
    
    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }
    
    modifier onlyAdmin() {
        require(admins[msg.sender] || msg.sender == owner, "Only admin can perform this action");
        _;
    }
    
    modifier votingActive() {
        require(currentSessionId > 0, "No active voting session");
        VotingSession storage session = votingSessions[currentSessionId];
        require(session.isActive, "Voting session is not active");
        require(block.timestamp >= session.startTime, "Voting has not started yet");
        require(block.timestamp <= session.endTime, "Voting has ended");
        _;
    }
    
    modifier validParty(string memory _partyId) {
        require(parties[_partyId].isActive, "Party is not active or does not exist");
        _;
    }
    
    // Constructor
    constructor() {
        owner = msg.sender;
        admins[msg.sender] = true;
        currentSessionId = 0;
        totalVotes = 0;
    }
    
    // Admin management functions
    function addAdmin(address _admin) external onlyOwner {
        require(_admin != address(0), "Invalid admin address");
        require(!admins[_admin], "Address is already an admin");
        
        admins[_admin] = true;
        emit AdminAdded(_admin);
    }
    
    function removeAdmin(address _admin) external onlyOwner {
        require(_admin != owner, "Cannot remove owner as admin");
        require(admins[_admin], "Address is not an admin");
        
        admins[_admin] = false;
        emit AdminRemoved(_admin);
    }
    
    // Party management functions
    function registerParty(
        string memory _partyId,
        string memory _partyName,
        string memory _description
    ) external onlyAdmin {
        require(bytes(_partyId).length > 0, "Party ID cannot be empty");
        require(bytes(_partyName).length > 0, "Party name cannot be empty");
        require(!parties[_partyId].isActive, "Party already exists");
        
        parties[_partyId] = Party({
            partyId: _partyId,
            partyName: _partyName,
            description: _description,
            voteCount: 0,
            isActive: true
        });
        
        partyIds.push(_partyId);
        emit PartyRegistered(_partyId, _partyName);
    }
    
    function deactivateParty(string memory _partyId) external onlyAdmin {
        require(parties[_partyId].isActive, "Party does not exist or is already inactive");
        parties[_partyId].isActive = false;
    }
    
    function activateParty(string memory _partyId) external onlyAdmin {
        require(bytes(parties[_partyId].partyId).length > 0, "Party does not exist");
        parties[_partyId].isActive = true;
    }
    
    // Voting session management
    function startVotingSession(
        string memory _sessionName,
        uint256 _duration
    ) external onlyAdmin {
        require(_duration > 0, "Duration must be greater than 0");
        require(currentSessionId == 0 || !votingSessions[currentSessionId].isActive, "Another session is already active");
        
        currentSessionId++;
        uint256 startTime = block.timestamp;
        uint256 endTime = startTime + _duration;
        
        votingSessions[currentSessionId] = VotingSession({
            sessionId: currentSessionId,
            sessionName: _sessionName,
            startTime: startTime,
            endTime: endTime,
            isActive: true,
            totalVotes: 0
        });
        
        emit VotingSessionStarted(currentSessionId, startTime, endTime);
    }
    
    function endVotingSession() external onlyAdmin {
        require(currentSessionId > 0, "No voting session to end");
        require(votingSessions[currentSessionId].isActive, "Voting session is already ended");
        
        votingSessions[currentSessionId].isActive = false;
        votingSessions[currentSessionId].totalVotes = totalVotes;
        
        emit VotingSessionEnded(currentSessionId, block.timestamp);
    }
    
    // Core voting function
    function castVote(bytes32 _voterHash, string memory _partyId) 
        external 
        votingActive 
        validParty(_partyId) 
    {
        require(!hasVoted[_voterHash], "Voter has already voted");
        require(_voterHash != bytes32(0), "Invalid voter hash");
        
        // Record the vote
        hasVoted[_voterHash] = true;
        votes[_voterHash] = Vote({
            voterHash: _voterHash,
            partyId: _partyId,
            timestamp: block.timestamp,
            exists: true
        });
        
        // Update vote counts
        parties[_partyId].voteCount++;
        totalVotes++;
        voteHashes.push(_voterHash);
        
        emit VoteCast(_voterHash, _partyId, block.timestamp);
    }
    
    // View functions
    function getVoteCount(string memory _partyId) external view returns (uint256) {
        return parties[_partyId].voteCount;
    }
    
    function getTotalVotes() external view returns (uint256) {
        return totalVotes;
    }
    
    function getPartyInfo(string memory _partyId) external view returns (
        string memory partyName,
        string memory description,
        uint256 voteCount,
        bool isActive
    ) {
        Party storage party = parties[_partyId];
        return (party.partyName, party.description, party.voteCount, party.isActive);
    }
    
    function getAllParties() external view returns (string[] memory) {
        return partyIds;
    }
    
    function getVotingSessionInfo(uint256 _sessionId) external view returns (
        string memory sessionName,
        uint256 startTime,
        uint256 endTime,
        bool isActive,
        uint256 sessionTotalVotes
    ) {
        VotingSession storage session = votingSessions[_sessionId];
        return (
            session.sessionName,
            session.startTime,
            session.endTime,
            session.isActive,
            session.totalVotes
        );
    }
    
    function getCurrentSession() external view returns (
        uint256 sessionId,
        string memory sessionName,
        uint256 startTime,
        uint256 endTime,
        bool isActive
    ) {
        if (currentSessionId == 0) {
            return (0, "", 0, 0, false);
        }
        
        VotingSession storage session = votingSessions[currentSessionId];
        return (
            session.sessionId,
            session.sessionName,
            session.startTime,
            session.endTime,
            session.isActive
        );
    }
    
    function getVoteDetails(bytes32 _voterHash) external view returns (
        string memory partyId,
        uint256 timestamp,
        bool exists
    ) {
        Vote storage vote = votes[_voterHash];
        return (vote.partyId, vote.timestamp, vote.exists);
    }
    
    function isVotingActive() external view returns (bool) {
        if (currentSessionId == 0) return false;
        
        VotingSession storage session = votingSessions[currentSessionId];
        return session.isActive && 
               block.timestamp >= session.startTime && 
               block.timestamp <= session.endTime;
    }
    
    function getTimeRemaining() external view returns (uint256) {
        if (currentSessionId == 0) return 0;
        
        VotingSession storage session = votingSessions[currentSessionId];
        if (!session.isActive || block.timestamp > session.endTime) {
            return 0;
        }
        
        return session.endTime - block.timestamp;
    }
    
    // Results and analytics
    function getResults() external view returns (
        string[] memory partyIdList,
        uint256[] memory voteCounts
    ) {
        uint256[] memory counts = new uint256[](partyIds.length);
        
        for (uint256 i = 0; i < partyIds.length; i++) {
            counts[i] = parties[partyIds[i]].voteCount;
        }
        
        return (partyIds, counts);
    }
    
    function getWinner() external view returns (
        string memory winnerPartyId,
        string memory winnerPartyName,
        uint256 winnerVoteCount
    ) {
        require(partyIds.length > 0, "No parties registered");
        
        string memory winner = partyIds[0];
        uint256 maxVotes = parties[winner].voteCount;
        
        for (uint256 i = 1; i < partyIds.length; i++) {
            if (parties[partyIds[i]].voteCount > maxVotes) {
                maxVotes = parties[partyIds[i]].voteCount;
                winner = partyIds[i];
            }
        }
        
        return (winner, parties[winner].partyName, maxVotes);
    }
    
    // Emergency functions
    function emergencyStop() external onlyOwner {
        if (currentSessionId > 0) {
            votingSessions[currentSessionId].isActive = false;
        }
    }
    
    function transferOwnership(address _newOwner) external onlyOwner {
        require(_newOwner != address(0), "Invalid new owner address");
        require(_newOwner != owner, "New owner is the same as current owner");
        
        admins[owner] = false;
        owner = _newOwner;
        admins[_newOwner] = true;
    }
    
    // Utility functions
    function getContractInfo() external view returns (
        address contractOwner,
        uint256 totalPartiesRegistered,
        uint256 totalVotesCast,
        uint256 currentSession,
        bool votingIsActive
    ) {
        return (
            owner,
            partyIds.length,
            totalVotes,
            currentSessionId,
            this.isVotingActive()
        );
    }
}
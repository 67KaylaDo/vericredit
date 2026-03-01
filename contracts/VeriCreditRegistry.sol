// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VeriCreditRegistry {
    struct Verification {
        bytes32 identityHash;
        uint256 aiRiskScore;        // 0..100
        uint256 ahpScore;           // 0..100 (scaled)
        bool humanConsensusUsed;    // true if AHP finalized
        bytes32 evidenceHash;       // oracle evidence hash
        uint256 timestamp;
        address reporter;
    }

    mapping(bytes32 => Verification) public records;

    event VerificationRecorded(
        bytes32 indexed identityHash,
        uint256 aiRiskScore,
        uint256 ahpScore,
        bool humanConsensusUsed,
        bytes32 evidenceHash,
        address reporter,
        uint256 timestamp
    );

    function recordVerification(
        bytes32 identityHash,
        uint256 aiRiskScore,
        uint256 ahpScore,
        bool humanConsensusUsed,
        bytes32 evidenceHash
    ) external {
        require(aiRiskScore <= 100, "aiRiskScore 0..100");
        require(ahpScore <= 100, "ahpScore 0..100");

        records[identityHash] = Verification({
            identityHash: identityHash,
            aiRiskScore: aiRiskScore,
            ahpScore: ahpScore,
            humanConsensusUsed: humanConsensusUsed,
            evidenceHash: evidenceHash,
            timestamp: block.timestamp,
            reporter: msg.sender
        });

        emit VerificationRecorded(
            identityHash,
            aiRiskScore,
            ahpScore,
            humanConsensusUsed,
            evidenceHash,
            msg.sender,
            block.timestamp
        );
    }
}
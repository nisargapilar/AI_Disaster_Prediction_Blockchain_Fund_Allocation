// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title DisasterRelief
/// @notice Minimal version: single-shot fund release per event (no milestone
///         tranches yet) plus on-chain beneficiary hash verification.
///         Only the triggerAuthority (the backend's wallet) may release
///         funds or verify beneficiaries. The owner may change the
///         triggerAuthority if needed (e.g. key rotation).
contract DisasterRelief {
    address public owner;
    address public triggerAuthority;

    // beneficiaryHash => verified
    mapping(bytes32 => bool) public verifiedBeneficiaries;

    event FundsReleased(address indexed to, uint256 amount, string eventId);
    event BeneficiaryVerified(bytes32 indexed beneficiaryHash, string distributionRecordId);
    event TriggerAuthorityChanged(address indexed oldAuthority, address indexed newAuthority);
    event Funded(address indexed from, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyTriggerAuthority() {
        require(msg.sender == triggerAuthority, "Not trigger authority");
        _;
    }

    constructor(address _triggerAuthority) {
        owner = msg.sender;
        triggerAuthority = _triggerAuthority;
    }

    /// @notice Anyone can top up the contract's balance (e.g. the owner,
    ///         funding it before disasters occur).
    receive() external payable {
        emit Funded(msg.sender, msg.value);
    }

    /// @notice Release funds to an NGO/local-govt wallet for a confirmed
    ///         disaster event. Only callable by the backend's trigger
    ///         authority wallet. eventId ties this release back to a row
    ///         in the off-chain `events` table for auditability.
    function releaseFunds(address payable ngoWallet, uint256 amount, string calldata eventId)
        external
        onlyTriggerAuthority
    {
        require(ngoWallet != address(0), "Invalid wallet");
        require(address(this).balance >= amount, "Insufficient contract balance");

        (bool sent, ) = ngoWallet.call{value: amount}("");
        require(sent, "Transfer failed");

        emit FundsReleased(ngoWallet, amount, eventId);
    }

    /// @notice Marks a beneficiary as verified on-chain. Only the hash of
    ///         the mock-Aadhaar-style ID is ever stored here — never the
    ///         raw ID. distributionRecordId ties this back to the
    ///         off-chain `distribution_records` row for auditability.
    function verifyBeneficiary(bytes32 beneficiaryHash, string calldata distributionRecordId)
        external
        onlyTriggerAuthority
    {
        require(!verifiedBeneficiaries[beneficiaryHash], "Already verified");
        verifiedBeneficiaries[beneficiaryHash] = true;
        emit BeneficiaryVerified(beneficiaryHash, distributionRecordId);
    }

    /// @notice Public read — anyone can check if a given beneficiary hash
    ///         has been verified, no login required. This is the core
    ///         transparency mechanism: proof a distinct real person was
    ///         confirmed, without exposing their identity.
    function isBeneficiaryVerified(bytes32 beneficiaryHash) external view returns (bool) {
        return verifiedBeneficiaries[beneficiaryHash];
    }

    /// @notice Lets the owner rotate the backend's authorized wallet
    ///         (e.g. if the private key needs to be replaced).
    function setTriggerAuthority(address newAuthority) external onlyOwner {
        require(newAuthority != address(0), "Invalid address");
        address old = triggerAuthority;
        triggerAuthority = newAuthority;
        emit TriggerAuthorityChanged(old, newAuthority);
    }

    function contractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
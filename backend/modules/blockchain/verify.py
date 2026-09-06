from web3 import Web3
from modules.blockchain.client import contract, send_transaction


def verify_beneficiary(mock_id: str, distribution_record_id: str) -> dict:
    beneficiary_hash = Web3.keccak(text=mock_id)

    already = contract.functions.isBeneficiaryVerified(beneficiary_hash).call()
    if already:
        return {"status": "already_verified"}

    fn = contract.functions.verifyBeneficiary(beneficiary_hash, str(distribution_record_id))

    try:
        tx_hash, receipt = send_transaction(fn)
        return {
            "status": "verified",
            "tx_hash": tx_hash,
            "beneficiary_hash": beneficiary_hash.hex(),
            "block": receipt.blockNumber,
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}
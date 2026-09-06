from web3 import Web3
from modules.blockchain.client import contract, w3, send_transaction
from modules.blockchain.config import NGO_WALLET_ADDRESS, FIXED_RELEASE_AMOUNT_POL


def trigger_fund_release(event_id: str, disaster_type: str, region: str) -> dict:
    amount_wei = w3.to_wei(FIXED_RELEASE_AMOUNT_POL, "ether")

    fn = contract.functions.releaseFunds(
        Web3.to_checksum_address(NGO_WALLET_ADDRESS),
        amount_wei,
        str(event_id),
    )

    try:
        tx_hash, receipt = send_transaction(fn)
        print(f"[blockchain] Released {FIXED_RELEASE_AMOUNT_POL} POL for {disaster_type} in {region} -> tx {tx_hash}")
        return {"status": "released", "tx_hash": tx_hash, "block": receipt.blockNumber}
    except Exception as e:
        print(f"[blockchain] Release FAILED for event {event_id}: {e}")
        return {"status": "failed", "error": str(e)}
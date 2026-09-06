import json
import os
from web3 import Web3
from modules.blockchain.config import AMOY_RPC_URL, PRIVATE_KEY, CONTRACT_ADDRESS

_abi_path = os.path.join(os.path.dirname(__file__), "abi.json")
with open(_abi_path) as f:
    CONTRACT_ABI = json.load(f)

w3 = Web3(Web3.HTTPProvider(AMOY_RPC_URL))

account = w3.eth.account.from_key(PRIVATE_KEY)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=CONTRACT_ABI,
)


def send_transaction(function_call):
    """Builds, signs, sends a contract function call. Returns tx hash + receipt."""
    tx = function_call.build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex(), receipt
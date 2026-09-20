from web3 import Web3
from modules.blockchain.client import contract, send_transaction
from db import async_session
from models import DistributionRecordModel


async def verify_beneficiary(event_id: str, mock_id: str) -> dict:
    beneficiary_hash = Web3.keccak(text=mock_id)
    beneficiary_hash_hex = beneficiary_hash.hex()

    async with async_session() as session:
        record = DistributionRecordModel(
            event_id=event_id,
            beneficiary_hash=beneficiary_hash_hex,
            mock_id_last4=mock_id[-4:] if len(mock_id) >= 4 else mock_id,
            status="pending",
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

        already = contract.functions.isBeneficiaryVerified(beneficiary_hash).call()
        if already:
            record.status = "already_verified"
            await session.commit()
            return {"status": "already_verified", "record_id": str(record.record_id)}

        fn = contract.functions.verifyBeneficiary(beneficiary_hash, str(record.record_id))
        try:
            tx_hash, receipt = send_transaction(fn)
            record.status = "verified"
            record.tx_hash = tx_hash
            await session.commit()
            return {
                "status": "verified",
                "record_id": str(record.record_id),
                "tx_hash": tx_hash,
                "beneficiary_hash": beneficiary_hash_hex,
                "block": receipt.blockNumber,
            }
        except Exception as e:
            record.status = "failed"
            await session.commit()
            return {"status": "failed", "error": str(e), "record_id": str(record.record_id)}
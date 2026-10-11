import asyncio
import sys

from db import async_session
from models import OperatorModel
from modules.blockchain.auth import hash_password


async def main(username: str, password: str):
    async with async_session() as session:
        session.add(
            OperatorModel(username=username, password_hash=hash_password(password))
        )
        await session.commit()
    print(f"Operator '{username}' created.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_operator.py <username> <password>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
import base64
from datetime import datetime
import json
import os
import pytz
from django.utils import timezone
import asyncio
from asgiref.sync import sync_to_async
from files.models import File
from users.models import User

# Conditional Solana imports
try:
    from solana.transaction import Transaction
    from solders.instruction import Instruction
    from solders.pubkey import Pubkey
    from solders.keypair import Keypair
    from solders.signature import Signature
    from solana.rpc.async_api import AsyncClient
    from solana.rpc.commitment import Confirmed
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False

#Initialize Solana client
MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
SOLANA_RPC_URL = "https://api.devnet.solana.com"


async def log_access(user: User, action: str, file: File):
    if not SOLANA_AVAILABLE:
        print(f"Solana not available - would log: {user.email} {action} {file.uploaded_file}")
        return
    
    # Servers solana keypair
    service_keypair = load_service_keypair()

    # Prepare the access log message
    access_log_message = f"{user.email} {action} {file.uploaded_file}"

    # Create a transaction with a memo instruction
    memo_instruction = Instruction(
        program_id=Pubkey.from_string(MEMO_PROGRAM_ID),
        data=access_log_message.encode('utf-8'),
        accounts=[]
    )

    async with AsyncClient(SOLANA_RPC_URL) as client:

        txn = Transaction().add(memo_instruction)
        txn.fee_payer = service_keypair.pubkey()

        response = await client.send_transaction(txn, service_keypair)
        await client.confirm_transaction(response.value, commitment=Confirmed)
        transaction_id = response.value

        print(f"Transaction ID: {transaction_id}")
        print(f"Response: {response.value}")
    
    transaction_id_str = str(transaction_id)

    file.transaction_ids.append(transaction_id_str)
    await sync_to_async(file.save)()


import json

async def retrieve_access_logs(file):
    if not SOLANA_AVAILABLE:
        print(f"Solana not available - would retrieve logs for: {file.uploaded_file}")
        return []
    
    pacific_tz = pytz.timezone('America/Los_Angeles')
    access_logs = []
    async with AsyncClient(SOLANA_RPC_URL) as client:
        for tx_id in file.transaction_ids:
            signature = Signature.from_string(tx_id)

            response = await client.get_transaction(
                signature,               # Use the converted signature
                encoding='jsonParsed',
                commitment='confirmed'
            )
            tx_detail = response.value

            try:
                # Convert tx_detail to JSON
                tx_json = json.loads(tx_detail.to_json())

                # Extract block time
                block_time = tx_json['blockTime']
                timestamp = datetime.fromtimestamp(block_time) if block_time else datetime.now()
                timestamp = timezone.make_aware(timestamp).astimezone(pacific_tz)

                # Extract instructions
                instructions = tx_json['transaction']['message']['instructions']

                for instruction in instructions:
                    # Check if this is a memo program instruction
                    if instruction['programId'] == MEMO_PROGRAM_ID:
                        # Extract memo from parsed data
                        memo = instruction['parsed']
                        memo_parts = memo.split()
                        user = memo_parts[0]
                        action = memo_parts[1]
                        access_logs.append({
                            'timestamp': timestamp,
                            'user':user,
                            'action': action
                        })
                        break
            except Exception as e:
                print(f"Error processing transaction for tx_id {tx_id}: {e}")
    
    access_logs.sort(key=lambda x: x['timestamp'], reverse=True)
    return access_logs
    


def load_service_keypair():
    """
    Loads the service's Solana keypair from the SERVICE_KEYPAIR environment variable.
    The keypair is a list of 64 integers.
    """
    if not SOLANA_AVAILABLE:
        raise ValueError("Solana packages not available")
        
    keypair_json = os.environ.get("SERVICE_KEYPAIR")
    if not keypair_json:
        raise ValueError("SERVICE_KEYPAIR environment variable not set.")
    try:
        keypair_list = json.loads(keypair_json)
        if not isinstance(keypair_list, list) or len(keypair_list) != 64:
            raise ValueError("SERVICE_KEYPAIR must be a JSON array of 64 integers.")
        keypair_bytes = bytes(keypair_list)
        return Keypair.from_bytes(keypair_bytes)
    except json.JSONDecodeError:
        raise ValueError("SERVICE_KEYPAIR environment variable is not valid JSON.")
    except Exception as e:
        raise ValueError(f"Failed to load service keypair: {e}")
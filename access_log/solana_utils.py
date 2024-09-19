from solana.rpc.api import Client
from solana.transaction import Transaction, Instruction, AccountMeta
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey

# Initialize Solana client for localhost
client = Client("http://localhost:8899")

# Load your keypair (replace with your actual keypair)
secret_key = bytes([190, 77, 189, 28, 164, 18, 117, 21, 106, 147, 218, 95, 177, 183, 52, 41, 101, 178, 161, 163, 240, 49, 12, 22, 188, 25, 178, 164, 137, 144, 95, 188, 241, 17, 163, 234, 95, 117, 185, 232, 11, 65, 127, 126, 157, 27, 153, 117, 24, 201, 15, 204, 233, 201, 65, 66, 32, 73, 81, 246, 112, 75, 74, 28])
keypair = Keypair.from_bytes(secret_key)

# Replace with your deployed program ID
PROGRAM_ID = Pubkey.from_string("3AX2HzDgj5J1pyUHENrRBDcUAJKyCp4TDtkCCqf6JrmD")

def log_access(user_id, file_id, action):
    # Create a transaction
    transaction = Transaction()

    # Serialize the instruction data properly
    instruction_data = f"{user_id},{file_id},{action}".encode('utf-8')

    # Create the instruction
    instruction = Instruction(
        program_id=PROGRAM_ID,
        accounts=[
            AccountMeta(pubkey=keypair.pubkey(), is_signer=True, is_writable=True)
        ],
        data=instruction_data
    )

    # Add the instruction to the transaction
    transaction.add(instruction)

    # Sign and send the transaction
    response = client.send_transaction(
        transaction,
        keypair,
        opts=TxOpts(skip_preflight=True, preflight_commitment="confirmed")
    )
    return response
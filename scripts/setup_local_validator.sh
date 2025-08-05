#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status messages
print_status() {
    echo -e "${GREEN}[✓] $1${NC}"
}

print_error() {
    echo -e "${RED}[✗] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# Check if solana CLI is installed
if ! command_exists solana; then
    print_error "Solana CLI is not installed. Please install it first:"
    echo "sh -c \"\$(curl -sSfL https://release.solana.com/v1.18.18/install)\""
    exit 1
fi

# Check if solana-test-validator is installed
if ! command_exists solana-test-validator; then
    print_error "solana-test-validator is not installed. Please install it first:"
    echo "cargo install solana-test-validator"
    exit 1
fi

# Create necessary directories
mkdir -p test-ledger
mkdir -p logs

# Function to start the validator
start_validator() {
    print_status "Starting local Solana validator..."
    
    # Create a fresh directory in the user's home directory
    VALIDATOR_DIR="$HOME/solana-test-validator"
    rm -rf "$VALIDATOR_DIR"
    mkdir -p "$VALIDATOR_DIR"
    
    # Disable macOS extended attributes for this directory
    xattr -cr "$VALIDATOR_DIR"
    
    # Create a temporary directory for genesis files
    TEMP_DIR=$(mktemp -d)
    
    # Start the validator with verbose logging
    print_status "Starting validator in $VALIDATOR_DIR..."
    cd "$TEMP_DIR" && solana-test-validator \
        --reset \
        --ledger "$VALIDATOR_DIR" \
        --rpc-port 8899 \
        --faucet-port 9900 \
        --log &
    
    # Store the PID
    echo $! > .validator.pid
    
    # Wait for validator to start and check if it's running
    sleep 5
    if ! ps -p $(cat .validator.pid) > /dev/null; then
        print_error "Validator failed to start. Check the logs for details."
        rm .validator.pid
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Configure CLI to use local validator
    solana config set --url http://localhost:8899
    
    # Verify the validator is responding
    if ! solana cluster-version > /dev/null 2>&1; then
        print_error "Validator is not responding. Please check the logs."
        stop_validator
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Clean up temporary directory
    rm -rf "$TEMP_DIR"
    
    print_status "Local validator started successfully!"
    print_status "RPC URL: http://localhost:8899"
    print_status "Faucet URL: http://localhost:9900"
    print_status "Validator directory: $VALIDATOR_DIR"
}

# Function to stop the validator
stop_validator() {
    if [ -f .validator.pid ]; then
        print_status "Stopping local validator..."
        kill $(cat .validator.pid)
        rm .validator.pid
        print_status "Local validator stopped."
    else
        print_warning "No validator process found."
    fi
}

# Function to check validator status
check_status() {
    if [ -f .validator.pid ]; then
        if ps -p $(cat .validator.pid) > /dev/null; then
            print_status "Validator is running (PID: $(cat .validator.pid))"
        else
            print_warning "Validator process file exists but process is not running"
            rm .validator.pid
        fi
    else
        print_warning "Validator is not running"
    fi
}

# Function to create a test account
create_test_account() {
    print_status "Creating test account..."
    solana-keygen new --no-bip39-passphrase --outfile test-ledger/test-keypair.json
    solana airdrop 100 $(solana-keygen pubkey test-ledger/test-keypair.json)
    print_status "Test account created and funded with 100 SOL"
}

# Handle command line arguments
case "$1" in
    start)
        start_validator
        ;;
    stop)
        stop_validator
        ;;
    restart)
        stop_validator
        sleep 2
        start_validator
        ;;
    status)
        check_status
        ;;
    create-account)
        create_test_account
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|create-account}"
        exit 1
        ;;
esac

exit 0 
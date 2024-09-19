from solana_utils import log_access

# Test data
user_id = "user123"
file_id = "file456"
action = "read"

# Call the log_access function
response = log_access(user_id, file_id, action)

# Print the response
print(response)
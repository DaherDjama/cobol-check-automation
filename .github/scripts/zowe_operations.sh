#!/bin/bash
# zowe_operations.sh - Using SSH/SCP to upload files

set -e

# Convert username to lowercase for USS paths
LOWERCASE_USERNAME=$(echo "$ZOWE_USERNAME" | tr '[:upper:]' '[:lower:]')

# Create temporary file for SSH key
echo "$SSH_PRIVATE_KEY" > /tmp/github_actions_key
chmod 600 /tmp/github_actions_key

echo "Uploading files to mainframe via SSH..."

# 1. Create the target directory on the mainframe
ssh -i /tmp/github_actions_key -o StrictHostKeyChecking=no \
    "${LOWERCASE_USERNAME}@204.90.115.200" \
    "mkdir -p /z/${LOWERCASE_USERNAME}/cobolcheck"

# 2. Upload the cobol-check tool
scp -i /tmp/github_actions_key -o StrictHostKeyChecking=no -r \
    ./cobol-check \
    "${LOWERCASE_USERNAME}@204.90.115.200:/z/${LOWERCASE_USERNAME}/cobolcheck/"

# 3. Upload source and test files
scp -i /tmp/github_actions_key -o StrictHostKeyChecking=no -r \
    ./src \
    "${LOWERCASE_USERNAME}@204.90.115.200:/z/${LOWERCASE_USERNAME}/cobolcheck/"

# 4. Upload JCL files
scp -i /tmp/github_actions_key -o StrictHostKeyChecking=no \
    ./*.JCL \
    "${LOWERCASE_USERNAME}@204.90.115.200:/z/${LOWERCASE_USERNAME}/cobolcheck/"

# Clean up
rm -f /tmp/github_actions_key

echo "Upload complete!"

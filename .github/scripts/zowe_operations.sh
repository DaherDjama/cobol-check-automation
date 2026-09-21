#!/bin/bash
# zowe_operations.sh - Using SSH/SCP with Password to upload files

set -e

# Convert username to lowercase for USS paths
LOWERCASE_USERNAME=$(echo "$ZOWE_USERNAME" | tr '[:upper:]' '[:lower:]')

echo "Uploading files to mainframe via SSH (Password Auth)..."

# 1. Create the target directory on the mainframe
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no \
    "${LOWERCASE_USERNAME}@204.90.115.200" \
    "mkdir -p /z/${LOWERCASE_USERNAME}/cobolcheck"

# 2. Upload the cobol-check tool
sshpass -p "$SSH_PASSWORD" scp -o StrictHostKeyChecking=no -r \
    ./cobol-check \
    "${LOWERCASE_USERNAME}@204.90.115.200:/z/${LOWERCASE_USERNAME}/cobolcheck/"

# 3. Upload source and test files
sshpass -p "$SSH_PASSWORD" scp -o StrictHostKeyChecking=no -r \
    ./src \
    "${LOWERCASE_USERNAME}@204.90.115.200:/z/${LOWERCASE_USERNAME}/cobolcheck/"

# 4. Upload JCL files
sshpass -p "$SSH_PASSWORD" scp -o StrictHostKeyChecking=no \
    ./*.JCL \
    "${LOWERCASE_USERNAME}@204.90.115.200:/z/${LOWERCASE_USERNAME}/cobolcheck/"

echo "Upload complete!"

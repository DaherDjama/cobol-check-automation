#!/bin/bash

# Convert username to lowercase
LOWERCASE_USERNAME=$(echo "$ZOWE_USERNAME" | tr '[:upper:]' '[:lower:]')

# Create directory path
DIR_PATH=/z/$LOWERCASE_USERNAME/cobolcheck

# Check if directory exists
echo "Checking if directory exists: $DIR_PATH"
zowe zos-files list uss-files "$DIR_PATH" --zosmf-profile zosmf
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "Directory does not exist. Creating it..."
    zowe zos-files create uss-directory "$DIR_PATH" --zosmf-profile zosmf
else
    echo "Directory already exists."
fi

# Upload files
echo "Uploading COBOL Check files..."
zowe zos-files upload dir-to-uss ./cobol-check "$DIR_PATH" --recursive --binary-files cobol-check-0.2.19.jar --zosmf-profile zosmf

# Verify upload
echo "Verifying upload:"
zowe zos-files list uss-files "$DIR_PATH" --zosmf-profile zosmf

echo "Upload complete!"

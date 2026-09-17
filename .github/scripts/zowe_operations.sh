
#!/bin/bash

# Convert username to lowercase
LOWERCASE_USERNAME=$(echo "$ZOWE_USERNAME" | tr '[:upper:]' '[:lower:]')

# Create directory path
DIR_PATH=/z/$LOWERCASE_USERNAME/cobolcheck

# Check if directory exists
echo "Checking if directory exists: $DIR_PATH"
zowe zos-files list uss-files "$DIR_PATH" \
  --host 204.90.115.200 \
  --port 443 \
  --user "$ZOWE_USERNAME" \
  --password "$ZOWE_PASSWORD" \
  --reject-unauthorized false
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "Directory does not exist. Creating it..."
    zowe zos-files create uss-directory "$DIR_PATH" \
      --host 204.90.115.200 \
      --port 443 \
      --user "$ZOWE_USERNAME" \
      --password "$ZOWE_PASSWORD" \
      --reject-unauthorized false
else
    echo "Directory already exists."
fi

# Upload files
echo "Uploading COBOL Check files..."
zowe zos-files upload dir-to-uss ./cobol-check "$DIR_PATH" \
  --recursive \
  --binary-files cobol-check-0.2.19.jar \
  --host 204.90.115.200 \
  --port 443 \
  --user "$ZOWE_USERNAME" \
  --password "$ZOWE_PASSWORD" \
  --reject-unauthorized false

# Verify upload
echo "Verifying upload:"
zowe zos-files list uss-files "$DIR_PATH" \
  --host 204.90.115.200 \
  --port 443 \
  --user "$ZOWE_USERNAME" \
  --password "$ZOWE_PASSWORD" \
  --reject-unauthorized false

echo "Upload complete!"

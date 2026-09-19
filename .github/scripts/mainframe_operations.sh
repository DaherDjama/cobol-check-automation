#!/bin/bash
# mainframe_operations.sh - Run tests on mainframe via SSH

set -e

# Convert username to lowercase
LOWERCASE_USERNAME=$(echo "$ZOWE_USERNAME" | tr '[:upper:]' '[:lower:]')

# Create temporary file for SSH key
echo "$SSH_PRIVATE_KEY" > /tmp/github_actions_key
chmod 600 /tmp/github_actions_key

echo "Running COBOL Check on mainframe via SSH..."

# Execute commands directly on the mainframe
ssh -i /tmp/github_actions_key -o StrictHostKeyChecking=no "${LOWERCASE_USERNAME}@204.90.115.200" << EOF
    cd /z/${LOWERCASE_USERNAME}/cobolcheck/cobol-check
    
    # Make tools executable
    chmod +x bin/cobolcheck
    chmod +x scripts/linux_gnucobol_run_tests
    cp config.properties .
    
    # Loop through programs
    for program in NUMBERS EMPPAY DEPTPAY; do
        echo "----------------------------------------"
        echo "Processing: \$program"
        echo "----------------------------------------"
        
        # Run the test
        ./bin/cobolcheck -p \$program
        
        # Copy results to MVS datasets
        if [ -f "CC##99.CBL" ]; then
            cp CC##99.CBL "'//${ZOWE_USERNAME}.CBL(\$program)'"
            echo "Copied CC##99.CBL to ${ZOWE_USERNAME}.CBL(\$program)"
        fi
        
        if [ -f "../\${program}.JCL" ]; then
            cp ../\${program}.JCL "'//${ZOWE_USERNAME}.JCL(\$program)'"
            echo "Copied \${program}.JCL to ${ZOWE_USERNAME}.JCL(\$program)"
        fi
    done
EOF

# Clean up
rm -f /tmp/github_actions_key

echo "Mainframe operations completed!"


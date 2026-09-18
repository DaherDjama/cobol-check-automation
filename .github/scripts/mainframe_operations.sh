
#!/bin/bash
# mainframe_operations.sh

export PATH=$PATH:/usr/lpp/java/J8.0_64/bin
export JAVA_HOME=/usr/lpp/java/J8.0_64
java -version

if [ -z "$ZOWE_USERNAME" ]; then
    ZOWE_USERNAME="Z89674"
fi

echo "Current directory: $(pwd)"

# 1. Copy config and SCRIPTS to the root directory
cp cobol-check/config.properties .
cp -r cobol-check/scripts .   # <--- THIS FIXES THE "No such file" ERROR
chmod -R +x scripts/          # Make sure the script is executable

# Make cobolcheck binary executable
chmod +x cobol-check/bin/cobolcheck

for program in NUMBERS EMPPAY DEPTPAY; do
    echo "----------------------------------------"
    echo "Processing: $program"
    echo "----------------------------------------"
    
    # Run COBOL Check from root
    ./cobol-check/bin/cobolcheck -p $program
    
    # Upload results
    if [ -f "CC##99.CBL" ]; then
        zowe zos-files upload file-to-data-set "CC##99.CBL" "${ZOWE_USERNAME}.CBL(${program})" \
            --host 204.90.115.200 --port 443 \
            --user "$ZOWE_USERNAME" --password "$ZOWE_PASSWORD" \
            --reject-unauthorized false
    fi
    
    if [ -f "${program}.JCL" ]; then
        zowe zos-files upload file-to-data-set "${program}.JCL" "${ZOWE_USERNAME}.JCL(${program})" \
            --host 204.90.115.200 --port 443 \
            --user "$ZOWE_USERNAME" --password "$ZOWE_PASSWORD" \
            --reject-unauthorized false
    fi
done

echo "Mainframe operations completed"


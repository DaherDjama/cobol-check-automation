#!/bin/bash
# mainframe_operations.sh

export PATH=$PATH:/usr/lpp/java/J8.0_64/bin
export JAVA_HOME=/usr/lpp/java/J8.0_64
java -version

if [ -z "$ZOWE_USERNAME" ]; then
    ZOWE_USERNAME="Z89674"
fi

echo "Current directory: $(pwd)"
ls -al

# Copy config to root
cp cobol-check/config.properties .

# Make executable
chmod +x cobol-check/bin/cobolcheck

for program in NUMBERS EMPPAY DEPTPAY; do
    echo "Running for $program"
    ./cobol-check/bin/cobolcheck -p $program
    
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



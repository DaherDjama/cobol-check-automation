#!/bin/bash
# mainframe_operations.sh

# Set up environment
export PATH=$PATH:/usr/lpp/java/J8.0_64/bin
export JAVA_HOME=/usr/lpp/java/J8.0_64

# Check Java availability
java -version

# Set ZOWE_USERNAME 
ZOWE_USERNAME="Z89674"

# Change to the cobol-check directory
cd cobol-check
echo "Changed to $(pwd)"
ls -al

# Make cobolcheck executable
chmod +x bin/cobolcheck
echo "Made cobolcheck executable"

# Make script in scripts directory executable
chmod +x scripts/linux_gnucobol_run_tests
echo "Made linux_gnucobol_run_tests executable"

# Function to run cobolcheck and copy files
run_cobolcheck(){
    program=$1
    echo "Running cobolcheck for $program"
    
    # Run cobolcheck
    ./bin/cobolcheck -p $program
    echo "Cobolcheck execution completed for $program"
    
    # Check if CC##99.CBL was created
    if [ -f "CC##99.CBL" ]; then
        # Copy to the MVS dataset
        cp CC##99.CBL "//'${ZOWE_USERNAME}.CBL($program)'"
        echo "Copied CC##99.CBL to ${ZOWE_USERNAME}.CBL($program)"
    else
        echo "CC##99.CBL not found for $program"
    fi
    
    # Copy the JCL file if it exists (it's in the parent directory)
    if [ -f "../${program}.JCL" ]; then
        cp ../${program}.JCL "//'${ZOWE_USERNAME}.JCL($program)'"
        echo "Copied ${program}.JCL to ${ZOWE_USERNAME}.JCL($program)"
    else
        echo "${program}.JCL not found"
    fi
}

# Run for each program
for program in NUMBERS EMPPAY DEPTPAY; do
    run_cobolcheck $program
done

echo "Mainframe operations completed"

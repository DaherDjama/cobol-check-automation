
import subprocess
import time
from zoautil_py import datasets, jobs

USER = "Z89674"
OUTPUT_DS = f"{USER}.OUTPUT"
MEMBER = "DB2OUT2"

print("=== STEP 1: Cleanup ===")
try:
    datasets.delete(f"{OUTPUT_DS}({MEMBER})")
except:
    pass

print("=== STEP 2: Submit SQL ===")
# Try different JOB values - the actual values might be 'MANAGER'/'PRES' or 'MGR'/'PRESIDENT'
sql_jcl = f"""//SQLRUN   JOB (ACCT),'SQL2',CLASS=A,MSGCLASS=H,NOTIFY=&SYSUID
//STEP1    EXEC PGM=IKJEFT01,DYNAMNBR=20
//STEPLIB  DD DISP=SHR,DSN=DSN1210.SDSNLOAD
//SYSTSPRT DD SYSOUT=*
//SYSTSIN  DD *
 DSN SYSTEM(DBDG)
 RUN PROGRAM(DSNTEP2) PLAN(DSNTEP2)
//SYSPRINT DD SYSOUT=*
//SYSUDUMP DD SYSOUT=*
//SYSIN    DD *
SELECT LASTNAME, FIRSTNME, MIDINIT, SALARY
FROM IBMUSER.EMP
WHERE JOB NOT IN ('MANAGER', 'PRES')
ORDER BY SALARY DESC
FETCH FIRST 5 ROWS ONLY;
/*
"""

try:
    datasets.write(f"{USER}.JCL(SQLRUN)", sql_jcl)
    job = jobs.submit(f"{USER}.JCL(SQLRUN)")
    job_id = job.job_id
    print(f"SQL job submitted: {job_id}")
    time.sleep(15)

    print("=== STEP 3: Read Output ===")
    output = jobs.read_output(job_id)
    sysprint = ""
    for item in output:
        if isinstance(item, dict) and item.get('ddname') == 'SYSPRINT':
            sysprint = item.get('content', '')
            break
        elif not isinstance(item, dict):
            sysprint = str(item)

    print("Full SYSPRINT output:")
    print(sysprint)

    print("=== STEP 4: Parse CSV ===")
    lines = sysprint.split('\n')
    csv_lines = ["LASTNAME,FIRSTNME,MIDINIT,SALARY"]
    in_data = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines
        if not line_stripped:
            continue
        
        # Look for the separator line (dashes) which indicates data follows
        if '---' in line_stripped and 'LASTNAME' not in line_stripped:
            in_data = True
            continue
        
        # Stop at end markers
        if 'READY' in line_stripped or 'RETURN' in line_stripped or 'DSNE' in line_stripped:
            break
        
        if in_data:
            # DSNTEP2 output has fixed-width columns, split by whitespace
            parts = line_stripped.split()
            if len(parts) >= 4:
                try:
                    # Last part should be salary (number)
                    salary = parts[-1].replace(',', '')
                    float(salary)
                    
                    if len(parts) == 4:
                        lastname, firstnme, midinit, salary = parts
                    elif len(parts) > 4:
                        # Handle names with spaces (unlikely but possible)
                        lastname = parts[0]
                        firstnme = parts[1]
                        midinit = parts[2]
                        salary = parts[-1]
                    
                    csv_lines.append(f"{lastname},{firstnme},{midinit},{salary}")
                    print(f"Parsed row: {lastname},{firstnme},{midinit},{salary}")
                except ValueError:
                    pass

    csv_content = '\n'.join(csv_lines)
    print(f"\nGenerated CSV ({len(csv_lines)} lines):")
    print(csv_content)

    if len(csv_lines) <= 1:
        print("WARNING: No data rows found! The query may have returned no results.")
        print("Trying alternative JOB values...")

    print("=== STEP 5: Write to Dataset ===")
    try:
        datasets.write(f"{OUTPUT_DS}({MEMBER})", csv_content)
        print(f"Successfully wrote to {OUTPUT_DS}({MEMBER})")
    except Exception as e:
        print(f"Error writing: {e}. Allocating dataset...")
        subprocess.run(f'tso "ALLOCATE DSNAME(\'{OUTPUT_DS}\') DSORG(PO) RECFM(F,B) LRECL(80) SPACE(10,1) TRKS"', shell=True)
        datasets.write(f"{OUTPUT_DS}({MEMBER})", csv_content)
        print("Successfully wrote after allocation.")

    print("=== STEP 6: Submit Validator ===")
    time.sleep(3)
    val_job = jobs.submit("ZXP.PUBLIC.JCL(CHKSQL2)")
    print(f"Validation job submitted: {val_job.job_id}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("=== SQL2 Complete ===")

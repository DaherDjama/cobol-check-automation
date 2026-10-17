import subprocess
import time
from zoautil_py import datasets, jobs

USER = "Z89674"
OUTPUT_DS = f"{USER}.OUTPUT"
MEMBER = "DB2OUT2"
TEMP_DS = f"{USER}.SQLTMP"

print("=== STEP 1: Cleanup ===")
try:
    datasets.delete(f"{OUTPUT_DS}({MEMBER})")
except:
    pass
try:
    datasets.delete(TEMP_DS)
except:
    pass

print("=== STEP 2: Submit SQL via JCL (output to dataset) ===")
# Write DSNTEP2 output to a temporary dataset instead of SYSOUT
sql_jcl = f"""//SQLRUN   JOB (ACCT),'SQL2',CLASS=A,MSGCLASS=H,NOTIFY=&SYSUID
//STEP1    EXEC PGM=IKJEFT01,DYNAMNBR=20
//STEPLIB  DD DISP=SHR,DSN=DSN1210.SDSNLOAD
//SYSTSPRT DD SYSOUT=*
//SYSTSIN  DD *
 DSN SYSTEM(DBDG)
 RUN PROGRAM(DSNTEP2) PLAN(DSNTEP2)
//SYSPRINT DD DSN={TEMP_DS},DISP=(NEW,CATLG,DELETE),
//            UNIT=SYSDA,SPACE=(TRK,(5,1)),
//            RECFM=FB,LRECL=133
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
    
    print("Waiting for job to complete...")
    time.sleep(20)
    
    print("=== STEP 3: Read Output Dataset ===")
    # Read the temporary dataset directly
    try:
        output = datasets.read(TEMP_DS)
        print(f"Output type: {type(output)}")
        print(f"Output length: {len(output)}")
        print("First 2000 chars:")
        print(output[:2000])
    except Exception as e:
        print(f"Error reading dataset: {e}")
        output = ""

    print("\n=== STEP 4: Parse Output ===")
    csv_lines = ["LASTNAME,FIRSTNME,MIDINIT,SALARY"]
    
    if output:
        lines = output.split('\n')
        in_data = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            # Look for DSNTEP2 header: LASTNAME, FIRSTNME, MIDINIT, SALARY (no SELECT, no commas)
            if ('LASTNAME' in line_stripped and 'FIRSTNME' in line_stripped and 
                'MIDINIT' in line_stripped and 'SALARY' in line_stripped and
                'SELECT' not in line_stripped and ',' not in line_stripped):
                print(f"Found header at line {i}: {line_stripped}")
                continue
            
            # Look for separator line (dashes)
            if not in_data and '---' in line_stripped:
                in_data = True
                print(f"Found separator at line {i}: {line_stripped}")
                continue
            
            # Parse data rows
            if in_data:
                # Stop at end markers
                if 'READY' in line_stripped or 'RETURN' in line_stripped or 'DSNE' in line_stripped:
                    break
                
                # Skip empty lines and pure dash lines
                if not line_stripped or all(c in '-= ' for c in line_stripped):
                    continue
                
                # Parse the data row
                parts = line_stripped.split()
                if len(parts) >= 4:
                    try:
                        salary = parts[-1].replace(',', '')
                        float(salary)
                        
                        if len(parts) == 4:
                            lastname, firstnme, midinit, salary = parts
                        else:
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
        print("\nWARNING: No data rows found!")
        print("Trying alternative JOB values...")
        
        # Try with different JOB values
        alt_sql = f"""//SQLRUN2  JOB (ACCT),'SQL2B',CLASS=A,MSGCLASS=H,NOTIFY=&SYSUID
//STEP1    EXEC PGM=IKJEFT01,DYNAMNBR=20
//STEPLIB  DD DISP=SHR,DSN=DSN1210.SDSNLOAD
//SYSTSPRT DD SYSOUT=*
//SYSTSIN  DD *
 DSN SYSTEM(DBDG)
 RUN PROGRAM(DSNTEP2) PLAN(DSNTEP2)
//SYSPRINT DD DSN={TEMP_DS},DISP=(NEW,CATLG,DELETE),
//            UNIT=SYSDA,SPACE=(TRK,(5,1)),
//            RECFM=FB,LRECL=133
//SYSUDUMP DD SYSOUT=*
//SYSIN    DD *
SELECT LASTNAME, FIRSTNME, MIDINIT, SALARY
FROM IBMUSER.EMP
WHERE JOB NOT IN ('MGR', 'PRES')
ORDER BY SALARY DESC
FETCH FIRST 5 ROWS ONLY;
/*
"""
        try:
            datasets.write(f"{USER}.JCL(SQLRUN2)", alt_sql)
            job2 = jobs.submit(f"{USER}.JCL(SQLRUN2)")
            print(f"Alternative job submitted: {job2.job_id}")
            time.sleep(20)
            
            try:
                output2 = datasets.read(TEMP_DS)
                print(f"Alt output length: {len(output2)}")
                
                lines2 = output2.split('\n')
                in_data2 = False
                
                for i, line in enumerate(lines2):
                    line_stripped = line.strip()
                    
                    if not line_stripped:
                        continue
                    
                    if ('LASTNAME' in line_stripped and 'FIRSTNME' in line_stripped and 
                        'MIDINIT' in line_stripped and 'SALARY' in line_stripped and
                        'SELECT' not in line_stripped and ',' not in line_stripped):
                        print(f"Found header at line {i}: {line_stripped}")
                        continue
                    
                    if not in_data2 and '---' in line_stripped:
                        in_data2 = True
                        print(f"Found separator at line {i}: {line_stripped}")
                        continue
                    
                    if in_data2:
                        if 'READY' in line_stripped or 'RETURN' in line_stripped or 'DSNE' in line_stripped:
                            break
                        
                        if not line_stripped or all(c in '-= ' for c in line_stripped):
                            continue
                        
                        parts = line_stripped.split()
                        if len(parts) >= 4:
                            try:
                                salary = parts[-1].replace(',', '')
                                float(salary)
                                
                                if len(parts) == 4:
                                    lastname, firstnme, midinit, salary = parts
                                else:
                                    lastname = parts[0]
                                    firstnme = parts[1]
                                    midinit = parts[2]
                                    salary = parts[-1]
                                
                                csv_lines.append(f"{lastname},{firstnme},{midinit},{salary}")
                                print(f"Parsed row (alt): {lastname},{firstnme},{midinit},{salary}")
                            except ValueError:
                                pass
                
                csv_content = '\n'.join(csv_lines)
                print(f"\nUpdated CSV ({len(csv_lines)} lines):")
                print(csv_content)
                
            except Exception as e:
                print(f"Error reading alt output: {e}")
            
        except Exception as e:
            print(f"Alternative query error: {e}")

    print("\n=== STEP 5: Write to Dataset ===")
    try:
        datasets.write(f"{OUTPUT_DS}({MEMBER})", csv_content)
        print(f"Successfully wrote to {OUTPUT_DS}({MEMBER})")
    except Exception as e:
        print(f"Error writing: {e}")
        subprocess.run(f'tso "ALLOCATE DSNAME(\'{OUTPUT_DS}\') DSORG(PO) RECFM(F,B) LRECL(80) SPACE(10,1) TRKS"', shell=True)
        datasets.write(f"{OUTPUT_DS}({MEMBER})", csv_content)

    print("\n=== STEP 6: Submit Validator ===")
    time.sleep(3)
    val_job = jobs.submit("ZXP.PUBLIC.JCL(CHKSQL2)")
    print(f"Validation job submitted: {val_job.job_id}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== SQL2 Complete ===")

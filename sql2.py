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

# Try only the 3 most likely STEPLIB options
steplib_options = ['DSN1110.SDSNLOAD', 'DSN1210.SDSNLOAD', None]

success = False

for steplib in steplib_options:
    if success:
        break
    
    steplib_display = steplib if steplib else "NONE"
    print(f"\nTrying STEPLIB: {steplib_display}")
    
    if steplib:
        steplib_dd = f"//STEPLIB  DD DISP=SHR,DSN={steplib}\n"
    else:
        steplib_dd = ""
    
    sql_jcl = f"""//SQLRUN   JOB (ACCT),'SQL2',CLASS=A,MSGCLASS=H,NOTIFY=&SYSUID
//STEP1    EXEC PGM=IKJEFT01,DYNAMNBR=20
{steplib_dd}//SYSTSPRT DD SYSOUT=*
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
        print(f"Job submitted: {job_id}")
        
        # Reduced wait time
        time.sleep(15)
        
        output = jobs.read_output(job_id)
        full_output = '\n'.join([str(item) for item in output]) if isinstance(output, list) else str(output)
        
        if 'NOT FOUND' in full_output or 'JCL ERROR' in full_output:
            print(f"Failed with {steplib_display}")
            continue
        
        print(f"Success with {steplib_display}!")
        
        # Parse output
        csv_lines = ["LASTNAME,FIRSTNME,MIDINIT,SALARY"]
        lines = full_output.split('\n')
        in_data = False
        header_found = False
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            if ('LASTNAME' in line_stripped and 'FIRSTNME' in line_stripped and 
                'MIDINIT' in line_stripped and 'SALARY' in line_stripped and
                'SELECT' not in line_stripped and ',' not in line_stripped):
                header_found = True
                continue
            
            if header_found and not in_data and line_stripped.count('-') > 10:
                in_data = True
                continue
            
            if in_data:
                if 'READY' in line_stripped or 'RETURN' in line_stripped:
                    break
                if not line_stripped or line_stripped.count('-') > 10:
                    continue
                if 'IEF' in line_stripped or 'ICH' in line_stripped:
                    continue
                
                parts = line_stripped.split()
                if len(parts) >= 4:
                    try:
                        salary = parts[-1].replace(',', '')
                        float(salary)
                        if len(parts) == 4:
                            lastname, firstnme, midinit, salary = parts
                        else:
                            lastname, firstnme, midinit, salary = parts[0], parts[1], parts[2], parts[-1]
                        csv_lines.append(f"{lastname},{firstnme},{midinit},{salary}")
                        print(f"Parsed: {lastname},{firstnme},{midinit},{salary}")
                    except:
                        pass
        
        csv_content = '\n'.join(csv_lines)
        print(f"CSV ({len(csv_lines)} lines): {csv_content}")
        
        if len(csv_lines) > 1:
            success = True
            datasets.write(f"{OUTPUT_DS}({MEMBER})", csv_content)
            print(f"Wrote to {OUTPUT_DS}({MEMBER})")
            
            time.sleep(2)
            val_job = jobs.submit("ZXP.PUBLIC.JCL(CHKSQL2)")
            print(f"Validator submitted: {val_job.job_id}")
    
    except Exception as e:
        print(f"Error: {e}")
        continue

if not success:
    print("All attempts failed!")

print("=== Done ===")

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

print("=== STEP 2: Run SQL Query via TSO ===")
# Use TSO DSNTEP2 directly instead of JCL
sql_query = """SELECT LASTNAME, FIRSTNME, MIDINIT, SALARY
FROM IBMUSER.EMP
WHERE JOB NOT IN ('MANAGER', 'PRES')
ORDER BY SALARY DESC
FETCH FIRST 5 ROWS ONLY;"""

# Create a temporary dataset with the SQL query
sql_ds = f"{USER}.SQLTMP"
try:
    datasets.delete(sql_ds)
except:
    pass

datasets.write(sql_ds, sql_query)
print(f"SQL query written to {sql_ds}")

# Run DSNTEP2 via TSO
cmd = f'tso "DSN SYSTEM(DBDG) RUN PROGRAM(DSNTEP2) PLAN(DSNTEP2) LIBRARY(\'DSN1210.RUNLIB.LOAD\')" < /z/{USER.lower()}/sqltmp'
print(f"Running command: {cmd}")

result = subprocess.run(cmd, shell=True, capture_output=True, encoding='latin-1', errors='replace')
output = result.stdout + result.stderr

print("=== STEP 3: Parse Output ===")
print("Raw output:")
print(output[:2000])

lines = output.split('\n')
csv_lines = ["LASTNAME,FIRSTNME,MIDINIT,SALARY"]
in_data = False

for line in lines:
    line_stripped = line.strip()
    
    if not line_stripped:
        continue
    
    if '---' in line_stripped and 'LASTNAME' not in line_stripped:
        in_data = True
        continue
    
    if 'READY' in line_stripped or 'RETURN' in line_stripped or 'DSNE' in line_stripped:
        break
    
    if in_data:
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
                print(f"Parsed: {lastname},{firstnme},{midinit},{salary}")
            except ValueError:
                pass

csv_content = '\n'.join(csv_lines)
print(f"\nGenerated CSV ({len(csv_lines)} lines):")
print(csv_content)

print("=== STEP 4: Write to Dataset ===")
try:
    datasets.write(f"{OUTPUT_DS}({MEMBER})", csv_content)
    print(f"Successfully wrote to {OUTPUT_DS}({MEMBER})")
except Exception as e:
    print(f"Error: {e}")
    subprocess.run(f'tso "ALLOCATE DSNAME(\'{OUTPUT_DS}\') DSORG(PO) RECFM(F,B) LRECL(80) SPACE(10,1) TRKS"', shell=True)
    datasets.write(f"{OUTPUT_DS}({MEMBER})", csv_content)

print("=== STEP 5: Submit Validator ===")
time.sleep(3)
val_job = jobs.submit("ZXP.PUBLIC.JCL(CHKSQL2)")
print(f"Validation job submitted: {val_job.job_id}")

print("=== SQL2 Complete ===")

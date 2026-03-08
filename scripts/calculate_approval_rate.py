#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path

def calculate_approval_rate(input_csv, output_jsonl, output_report):
    """
    Reads a completed review CSV, calculates approval rate.
    If >=80%, generates a JSONL for SFT training.
    Also produces a markdown report.
    """
    input_path = Path(input_csv)
    out_jsonl_path = Path(output_jsonl)
    out_report_path = Path(output_report)
    
    if not input_path.exists():
        print(f"Error: Review sheet {input_csv} does not exist.")
        sys.exit(1)
        
    total = 0
    approved = 0
    rejected = 0
    revised = 0
    missing = 0
    
    valid_records = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            decision = str(row.get("lawyer_decision", "")).strip().upper()
            
            if decision == "APPROVE":
                approved += 1
                valid_records.append({
                    "instruction": "Aşağıdaki kaynaklara dayanarak soruyu yanıtla.",
                    "input": f"KAYNAKLAR:\n{row['context']}\n\nSORU: {row['question']}",
                    "output": row["generated_answer"]
                })
            elif decision == "REVISE":
                revised += 1
                valid_records.append({
                    "instruction": "Aşağıdaki kaynaklara dayanarak soruyu yanıtla.",
                    "input": f"KAYNAKLAR:\n{row['context']}\n\nSORU: {row['question']}",
                    "output": row["corrected_answer"] if row["corrected_answer"].strip() else row["generated_answer"]
                })
            elif decision == "REJECT":
                rejected += 1
            else:
                missing += 1
                
    if total == 0:
        print("Error: No records found in the CSV.")
        sys.exit(1)
        
    approval_count = approved + revised
    approval_rate = (approval_count / total) * 100
    
    report_md = f"""# Quality Gate Review Report

**Review File:** `{input_path.name}`
**Total Records:** {total}
**Approved:** {approved}
**Revised (Accepted):** {revised}
**Rejected:** {rejected}
**Missing/Unreviewed:** {missing}

### Approval Rate: **{approval_rate:.2f}%**

"""

    is_passed = approval_rate >= 80.0
    
    if is_passed:
        report_md += "## Result: 🟢 PASSED\n\nThe quality gate of 80% has been met. The valid records have been exported to the SFT format.\n"
        # Export to JSONL
        with open(out_jsonl_path, 'w', encoding='utf-8') as f:
            for rec in valid_records:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        report_md += f"**Exported File:** `{out_jsonl_path.name}` ({len(valid_records)} records)\n"
    else:
        report_md += "## Result: 🔴 FAILED\n\nThe quality gate of 80% has NOT been met. The data needs to be improved, re-generated, and reviewed again.\n"
        
    # Write report
    with open(out_report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)
        
    print(report_md)
    print(f"Report saved to {out_report_path}")
    
    if is_passed:
        print(f"SFT data saved to {out_jsonl_path}")
        sys.exit(0)
    else:
        sys.exit(1) # Exit code 1 for CI/CD or automation failures

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scripts/calculate_approval_rate.py <input_reviewed.csv> <output.jsonl> <output_report.md>")
        sys.exit(1)
        
    calculate_approval_rate(sys.argv[1], sys.argv[2], sys.argv[3])

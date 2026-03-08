#!/usr/bin/env python3
import json
import csv
import sys
import uuid
from pathlib import Path

def prepare_review_sheet(input_jsonl, output_csv):
    """
    Reads a candidate JSONL file (typically extracted from RAG logs or generated synthetically)
    and outputs a CSV template for lawyer review.
    
    Expected JSONL input format:
    {"instruction": "...", "input": "context...", "output": "..."}
    """
    input_path = Path(input_jsonl)
    output_path = Path(output_csv)
    
    if not input_path.exists():
        print(f"Error: Input file {input_jsonl} does not exist.")
        sys.exit(1)
        
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                # Parse input field to separate context and question if possible
                # Expected format: KAYNAKLAR:\n<context>\n\nSORU: <question>
                raw_input = data.get("input", "")
                context = ""
                question = ""
                
                if "SORU:" in raw_input:
                    parts = raw_input.split("SORU:")
                    context = parts[0].replace("KAYNAKLAR:\n", "").strip()
                    question = parts[1].strip()
                else:
                    context = raw_input
                    question = data.get("instruction", "")
                
                record = {
                    "id": str(uuid.uuid4())[:8],
                    "question": question,
                    "context": context,
                    "generated_answer": data.get("output", ""),
                    "lawyer_decision": "", # APPROVE, REVISE, REJECT
                    "lawyer_comment": "",
                    "corrected_answer": "",
                    "reviewer_name": ""
                }
                records.append(record)
            except json.JSONDecodeError:
                print("Warning: Skipped invalid JSON line.")
                
    headers = ["id", "question", "context", "generated_answer", 
               "lawyer_decision", "lawyer_comment", "corrected_answer", "reviewer_name"]
               
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow(r)
            
    print(f"Successfully generated review sheet with {len(records)} items at {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/prepare_review_sheets.py <input.jsonl> <output.csv>")
        sys.exit(1)
        
    prepare_review_sheet(sys.argv[1], sys.argv[2])

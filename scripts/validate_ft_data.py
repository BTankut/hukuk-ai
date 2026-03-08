"""
Validation script for Fine-Tuning SFT and DPO JSONL datasets.
Ensures schema compliance before training.
"""
import json
import argparse
import sys

def validate_sft_file(file_path: str) -> bool:
    """Validates SFT JSONL format: must contain instruction, input, output."""
    is_valid = True
    line_number = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line_number += 1
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if not all(k in data for k in ("instruction", "input", "output")):
                    print(f"Error in line {line_number}: Missing required keys (instruction, input, output).")
                    is_valid = False
            except json.JSONDecodeError:
                print(f"Error in line {line_number}: Invalid JSON.")
                is_valid = False
    return is_valid

def validate_dpo_file(file_path: str) -> bool:
    """Validates DPO JSONL format: must contain prompt, chosen, rejected."""
    is_valid = True
    line_number = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line_number += 1
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if not all(k in data for k in ("prompt", "chosen", "rejected")):
                    print(f"Error in line {line_number}: Missing required keys (prompt, chosen, rejected).")
                    is_valid = False
            except json.JSONDecodeError:
                print(f"Error in line {line_number}: Invalid JSON.")
                is_valid = False
    return is_valid

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate JSONL dataset schemas.")
    parser.add_argument("--file", required=True, help="Path to the JSONL file to validate.")
    parser.add_argument("--type", choices=['sft', 'dpo'], required=True, help="Type of dataset (sft or dpo).")
    args = parser.parse_args()

    print(f"Validating {args.file} as {args.type.upper()} format...")
    if args.type == 'sft':
        success = validate_sft_file(args.file)
    else:
        success = validate_dpo_file(args.file)

    if success:
        print("Validation PASSED.")
        sys.exit(0)
    else:
        print("Validation FAILED.")
        sys.exit(1)

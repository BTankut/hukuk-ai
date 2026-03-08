"""
This is a scaffolding template for extracting QA data from Phase 1 logs.
DO NOT use this directly for training without lawyer review.
"""
import json
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_qa(log_file_path: str, output_file_path: str):
    """
    Extracts candidate QA pairs from Phase 1 logs.
    Expected log format: {"query": "...", "context": ["..."], "response": "..."}
    Output format: {"instruction": "...", "input": "...", "output": "..."}
    """
    log_path = Path(log_file_path)
    out_path = Path(output_file_path)
    
    if not log_path.exists():
        logger.error(f"Log file not found: {log_file_path}")
        return

    extracted_count = 0
    with open(log_path, 'r', encoding='utf-8') as infile, \
         open(out_path, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            if not line.strip():
                continue
            try:
                log_entry = json.loads(line)
                
                # Basic mapping (adjust based on actual log schema)
                question = log_entry.get("query", "")
                context = "\n".join(log_entry.get("context", []))
                response = log_entry.get("response", "")
                
                if question and response:
                    ft_entry = {
                        "instruction": "Aşağıdaki kaynaklara dayanarak soruyu yanıtla.",
                        "input": f"KAYNAKLAR:\n{context}\n\nSORU: {question}",
                        "output": response
                    }
                    outfile.write(json.dumps(ft_entry, ensure_ascii=False) + "\n")
                    extracted_count += 1
            except json.JSONDecodeError:
                logger.warning("Skipping invalid JSON line.")
                
    logger.info(f"Extracted {extracted_count} candidate pairs to {output_file_path}")
    logger.info("REMINDER: These pairs MUST go through the Lawyer Review Quality Gate before fine-tuning.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract candidate QA pairs from Phase 1 logs.")
    parser.add_argument("--input", required=True, help="Path to Phase 1 log file (JSONL).")
    parser.add_argument("--output", required=True, help="Path to output SFT candidate file (JSONL).")
    args = parser.parse_args()
    
    extract_qa(args.input, args.output)

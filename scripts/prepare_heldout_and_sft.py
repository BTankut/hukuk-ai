import json
import random
import os
from collections import defaultdict

def main():
    seed = 42
    random.seed(seed)
    
    input_file = "data/review_sheets/phase2_first_batch_20260308/reconciled_20260308/batch1_first100_reconciled_master.jsonl"
    heldout_file = "data/finetune/eval/held_out_test.jsonl"
    sft_train_file = "data/finetune/sft/sft_training_batch1.jsonl"
    
    # Read reconciled data
    records = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    # Filter only those included in training
    valid_records = [r for r in records if r.get('include_in_training') == '1' or r.get('include_in_training') == 1]
    
    # Stratify by category and difficulty
    stratified = defaultdict(list)
    for r in valid_records:
        key = f"{r.get('category', 'unknown')}_{r.get('difficulty', 'unknown')}"
        stratified[key].append(r)
        
    held_out = []
    sft_train = []
    
    heldout_ratio = 0.2  # 20%
    
    for key, items in stratified.items():
        random.shuffle(items)
        n_heldout = max(1, int(len(items) * heldout_ratio)) if len(items) >= 5 else (1 if len(items) > 1 and random.random() < heldout_ratio * len(items) else 0)
        
        # Ensure we don't put everything in held-out if len is small, unless we absolutely have to
        # Let's just do simple exact calculation and round, but guarantee at least some train data
        if n_heldout >= len(items):
            n_heldout = len(items) - 1
            
        held_out.extend(items[:n_heldout])
        sft_train.extend(items[n_heldout:])
        
    # If we got too few or too many, we could adjust, but this is fine.
    print(f"Total valid records: {len(valid_records)}")
    print(f"Held-out set size: {len(held_out)}")
    print(f"SFT train set size: {len(sft_train)}")
    
    # Write held_out_test.jsonl
    with open(heldout_file, 'w', encoding='utf-8') as f:
        for r in held_out:
            out_record = {
                "instruction": "Aşağıdaki kaynaklara dayanarak soruyu yanıtla.",
                "input": f"KAYNAKLAR:\n{r['context']}\n\nSORU: {r['question']}",
                "output": r['final_answer']
            }
            f.write(json.dumps(out_record, ensure_ascii=False) + '\n')
            
    # Write sft_training.jsonl
    with open(sft_train_file, 'w', encoding='utf-8') as f:
        for r in sft_train:
            out_record = {
                "instruction": "Aşağıdaki kaynaklara dayanarak soruyu yanıtla.",
                "input": f"KAYNAKLAR:\n{r['context']}\n\nSORU: {r['question']}",
                "output": r['final_answer']
            }
            f.write(json.dumps(out_record, ensure_ascii=False) + '\n')

    print("Successfully created real held-out and SFT training files.")

if __name__ == "__main__":
    main()

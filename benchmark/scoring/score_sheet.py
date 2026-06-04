import json
import csv
import sys
import os

def generate_score_sheet(raw_response_file):
    with open(raw_response_file, "r") as f:
        results = json.load(f)

    # Build output path
    filename = os.path.basename(raw_response_file).replace(".json", "_scores.csv")
    scores_dir = os.path.join(os.path.dirname(raw_response_file), "..", "scores")
    os.makedirs(scores_dir, exist_ok=True)
    output_path = os.path.join(scores_dir, filename)

    fieldnames = [
        "id", "domain", "difficulty", "reasoning_type",
        "question", "reference_answer", "model_response",
        "factual_accuracy",        # 0=wrong, 1=partially correct, 2=correct, 3=exceptionally precise
        "reasoning_consistency",   # 0=incoherent, 1=minor gaps, 2=sound, 3=rigorous
        "confidence_calibration",  # 0=overconfident+wrong, 1=overconfident, 2=appropriate, 3=well-calibrated
        "domain_depth",            # 0=superficial, 1=textbook, 2=specialist, 3=expert-level niche
        "notes"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "id": r.get("id", ""),
                "domain": r.get("domain", ""),
                "difficulty": r.get("difficulty", ""),
                "reasoning_type": r.get("reasoning_type", ""),
                "question": r.get("question", ""),
                "reference_answer": r.get("reference_answer", ""),
                "model_response": r.get("model_response", ""),
                "factual_accuracy": "",
                "reasoning_consistency": "",
                "confidence_calibration": "",
                "domain_depth": "",
                "notes": ""
            })

    print(f"✓ Score sheet saved to:\n  {output_path}")
    print(f"\nNext step:")
    print(f"  Open the CSV in Excel or Google Sheets")
    print(f"  Fill in the four score columns (0–3) for each row")
    print(f"  Then run: python scoring/aggregate_scores.py results/scores/{filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python score_sheet.py results/raw_responses/<filename>.json")
        sys.exit(1)
    generate_score_sheet(sys.argv[1])

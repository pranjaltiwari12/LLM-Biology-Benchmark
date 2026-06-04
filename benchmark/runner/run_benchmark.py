import json
import os
import time
from datetime import datetime
import google.generativeai as genai

# --- CONFIG ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-1.5-pro"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "raw_responses")

DOMAIN_FILES = {
    "molecular_biology": "molecular_biology.json",
    "bioinformatics": "bioinformatics.json",
    "pathway_analysis": "pathway_analysis.json"
}

SYSTEM_PROMPT = """You are an expert biologist and bioinformatician.
Answer the following question as precisely and thoroughly as possible.
If you are uncertain about any part of your answer, explicitly state your uncertainty.
Do not hallucinate facts. If a question is outside your confident knowledge, say so."""

# --- SETUP ---
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)


def load_all_questions():
    all_questions = []
    for domain, filename in DOMAIN_FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found, skipping.")
            continue
        with open(filepath, "r") as f:
            questions = json.load(f)
        for q in questions:
            q["domain"] = domain  # ensure domain tag is set
        all_questions.extend(questions)
        print(f"Loaded {len(questions)} questions from {filename}")
    return all_questions


def query_gemini(question_text):
    prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {question_text}"
    response = model.generate_content(prompt)
    return response.text


def run_benchmark():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    questions = load_all_questions()
    if not questions:
        print("No questions loaded. Check your data/ folder.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"{MODEL_NAME}_{timestamp}.json")

    results = []
    total = len(questions)

    for i, q in enumerate(questions):
        print(f"[{i+1}/{total}] {q.get('id', '?')} — {q['domain']}")
        try:
            response_text = query_gemini(q["question"])
        except Exception as e:
            response_text = f"ERROR: {str(e)}"

        results.append({
            "id": q.get("id", f"Q{i+1}"),
            "domain": q["domain"],
            "difficulty": q.get("difficulty", ""),
            "reasoning_type": q.get("reasoning_type", ""),
            "question": q["question"],
            "reference_answer": q.get("reference_answer", ""),
            "model": MODEL_NAME,
            "model_response": response_text,
            "timestamp": timestamp
        })

        time.sleep(1.5)  # stay within Gemini rate limits

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Done. {total} responses saved to:\n  {output_file}")


if __name__ == "__main__":
    run_benchmark()

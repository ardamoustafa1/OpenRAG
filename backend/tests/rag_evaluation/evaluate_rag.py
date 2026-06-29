import asyncio
import os
import json
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)

async def run_evaluation():
    print("Starting Real Ragas Evaluation...")
    
    # Load dataset if exists, else use defaults
    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    if os.path.exists(dataset_path):
        with open(dataset_path, "r") as f:
            data = json.load(f)
    else:
        # Fallback sample dataset
        data = {
            "question": ["What is the enterprise pricing for the AI platform?"],
            "answer": ["The enterprise pricing starts at $999/month."],
            "contexts": [["Our basic plan is $49, and enterprise pricing starts at $999/month."]],
            "ground_truth": ["Enterprise pricing starts at $999/month."]
        }
    
    dataset = Dataset.from_dict(data)
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Ragas uses LLM-as-a-judge for evaluation. This may fail if no LiteLLM fallback is configured.")
        
    try:
        score = evaluate(
            dataset,
            metrics=[
                context_precision,
                context_recall,
                faithfulness,
                answer_relevancy,
            ]
        )
        print("\n--- RAG Evaluation Results ---")
        print(score)
        
        df = score.to_pandas()
        df.to_csv("rag_eval_results.csv", index=False)
        print("Results saved to rag_eval_results.csv")
    except Exception as e:
        print(f"Evaluation failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())

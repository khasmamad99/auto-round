import argparse
import json
import os

import pandas as pd

from eval_042.evaluation import simple_evaluate as lm_eval_evaluate
from eval.evaluation import EXT_TASKS, eval_model as gptq_evaluate





def clean_lm_eval_results(lm_eval_results, tasks: list[str]):
    """Clean up the results from lm-eval."""
    cleaned_results = {}
    
    accuracies = []
    for k, dic in lm_eval_results["results"].items():
        if "alias" in dic:
            k = dic.pop("alias")
            
        if k not in tasks:
            continue
            
        for (mf), v in dic.items():
            m, _, f = mf.partition(",")
            if m.endswith("_stderr"):
                continue
            
            v = float(v)
            if m == "acc":
                if k == "openbookqa":  # OpenBookQA is flaky and sometimes reports 1000% accuracy
                    if v > 100:
                        v = v / 10
                else:
                    v = v * 100
                accuracies.append(v)
                cleaned_results[k] = round(v, 2)
            elif m == "word_perplexity":
                cleaned_results[k] = round(v, 2)
    
    avg_accuracy = round(sum(accuracies) / len(accuracies), 2)
    cleaned_results["avg_accuracy"] = avg_accuracy
    return cleaned_results


def evaluate(
    model_path: str,
    batch_size: int = 4,
    tasks: str = (
        "lambada_openai,hellaswag,winogrande,piqa,mmlu,wikitext,truthfulqa_mc1"
        ",truthfulqa_mc2,openbookqa,boolq,rte,arc_easy,arc_challenge,wikitext2"
    ),
    seed: int = 0,
):
    """
    Evaluate a model on a set of tasks.

    Args:
        model_path: The path to the model to evaluate.
        batch_size: The batch size to use during evaluation.
        tasks: A comma-separated list of tasks to evaluate on.
    """
    tasks = tasks.split(",")
    lm_eval_evaluate_tasks = [task for task in tasks if task not in EXT_TASKS]
    gptq_evaluate_tasks = [task for task in tasks if task in EXT_TASKS]
    if not os.path.exists(model_path):
        output_dir = os.path.join("tmp_autoround", "fp_results", model_path)
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = model_path
        
    results = {}
    model_args = f"pretrained={model_path},trust_remote_code=True"
    if len(lm_eval_evaluate_tasks) > 0:
        lm_eval_results = lm_eval_evaluate(
            model="hf",
            model_args=model_args,
            tasks=lm_eval_evaluate_tasks,
            batch_size=batch_size,
            random_seed=seed,
        )
        lm_eval_results_write_path = os.path.join(output_dir, "lm_eval_raw_results.json")
        with open(lm_eval_results_write_path, "w") as f:
            json.dump(lm_eval_results, f)
        
        cleaned_lm_eval_results = clean_lm_eval_results(lm_eval_results, tasks=lm_eval_evaluate_tasks)
        results.update(cleaned_lm_eval_results)
        print(cleaned_lm_eval_results)
        
        
    if len(gptq_evaluate_tasks) > 0:
        gptq_results = gptq_evaluate(
            model_path=model_path,
            tasks=gptq_evaluate_tasks,
            eval_bs=batch_size,
            seed=seed,
        )
        
        gptq_results_write_path = os.path.join(output_dir, "gptq_raw_results.json")
        with open(gptq_results_write_path, "w") as f:
            json.dump(gptq_results, f)
        
        results.update(gptq_results)
        print(gptq_results)
    
    results_df = pd.DataFrame([results])
    print(results_df)
    results_df.to_csv(os.path.join(output_dir, "results.csv"), index=False)
    return results_df
        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument(
        "--tasks", 
        type=str, 
        default=(
            "wikitext2,ptb,c4,wikitext"
            ",mmlu,lambada_openai,hellaswag,winogrande,piqa,truthfulqa_mc1"
            ",openbookqa,boolq,rte,arc_easy,arc_challenge"
        )
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    
    evaluate(
        model_path=args.model_path,
        batch_size=args.batch_size,
        tasks=args.tasks,
        seed=args.seed,
    )
    
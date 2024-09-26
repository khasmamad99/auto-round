import argparse

import pandas as pd

from eval_042.evaluation import simple_evaluate as lm_eval_evaluate
from eval.evaluation import EXT_TASKS, eval_model as gptq_evaluate


def make_pandas_dataframe_from_lm_eval_results(
    result_dict, 
    column: str = "results"
) -> pd.DataFrame:
    """Generate dataframe of results."""

    if column == "results":
        column_name = "Tasks"
    elif column == "groups":
        column_name = "Groups"

    all_headers = [
        column_name,
        "Version",
        "Filter",
        "n-shot",
        "Metric",
        "Value",
        "Stderr",
    ]
    
    values = []

    for k, dic in result_dict["results"].items():
        version = result_dict["versions"].get(k, None)
        n = int(result_dict["n-shot"][k])

        if "alias" in dic:
            k = dic.pop("alias")

        for (mf), v in dic.items():
            m, _, f = mf.partition(",")
            if m.endswith("_stderr"):
                continue
            
            v = float(v)
            if m + "_stderr" + "," + f in dic:
                se = dic[m + "_stderr" + "," + f]
                if se == "N/A":
                    se = None
                else:
                    se = float(se)
                values.append([k, version, f, n, m, v, se])
            else:
                values.append([k, version, f, n, m, v, None])
    
    df = pd.DataFrame(values, columns=all_headers)
    return df


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
        results.update(lm_eval_results)
        lm_eval_results_df = make_pandas_dataframe_from_lm_eval_results(lm_eval_results)
        print(lm_eval_results_df)
        
        
    if len(gptq_evaluate_tasks) > 0:
        gptq_results = gptq_evaluate(
            model_path=model_path,
            tasks=gptq_evaluate_tasks,
            eval_bs=batch_size,
            seed=seed,
        )
        results.update(gptq_results)
        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--tasks", type=str, default="lambada_openai,hellaswag,winogrande,piqa,mmlu,wikitext,truthfulqa_mc1,,openbookqa,boolq,rte,arc_easy,arc_challenge,wikitext2,ptb,c4")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    
    evaluate(
        model_path=args.model_path,
        batch_size=args.batch_size,
        tasks=args.tasks,
        seed=args.seed,
    )
    
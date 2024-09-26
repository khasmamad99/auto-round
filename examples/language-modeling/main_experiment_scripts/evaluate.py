from lm_eval.utils import make_table

from eval_042.evaluation import simple_evaluate as lm_eval_evaluate
from eval.evaluation import EXT_TASKS, eval_model as gptq_evaluate
from auto_round.learning_curve_stats_utils import make_pandas_dataframe_from_lm_eval_results


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
            seed=seed,
        )
        results.update(lm_eval_results)
        print(make_table(lm_eval_results))
        
    if len(gptq_evaluate_tasks) > 0:
        gptq_results = gptq_evaluate(
            model_path=model_path,
            tasks=gptq_evaluate_tasks,
            batch_size=batch_size,
            seed=seed,
        )
        results.update(gptq_results)
        print(gptq_results)
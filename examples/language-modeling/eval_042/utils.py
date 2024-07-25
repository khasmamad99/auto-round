import pandas as pd


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

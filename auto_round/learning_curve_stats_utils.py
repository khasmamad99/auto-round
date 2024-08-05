import numpy as np
import scipy.stats
import plotly.graph_objects as go
import pandas as pd


def calculate_convergence_iter(loss_values, std_fraction=0.1, window=5, consecutive_iters=5):
    """
    Calculate the convergence iter for a given list of loss values with a dynamic threshold.

    Parameters:
        loss_values (list or np.array): Array of loss values over iters.
        std_fraction (float): The fraction of the standard deviation to use as the threshold.
        window (int): The size of the moving average window.
        consecutive_iters (int): The number of consecutive iters for checking stabilization.

    Returns:
        int: The convergence iter, or -1 if convergence is not detected.
    """
    # Compute the moving average of the loss values
    moving_avg = np.convolve(loss_values, np.ones(window)/window, mode='valid')
    
    # Calculate the standard deviation of the moving average
    std_dev = np.std(moving_avg)
    
    # Define the dynamic threshold
    threshold = std_fraction * std_dev
    
    # Iterate through the moving average values to find the convergence iter
    for i in range(len(moving_avg) - consecutive_iters + 1):
        if all(np.abs(np.diff(moving_avg[i:i + consecutive_iters])) < threshold):
            return i + window // 2  # Adjust for the window offset
    
    return -1  # Return -1 if no convergence is detected


def calculate_average_absolute_change(loss_values, window=5):
    """
    Calculate the average absolute change in loss values over a moving window.

    Parameters:
        loss_values (list or np.array): Array of loss values over epochs.
        window (int): The size of the moving average window.

    Returns:
        np.array: Array of average absolute changes in loss values.
    """
    # Compute the moving average of the loss values
    moving_avg = np.convolve(loss_values, np.ones(window)/window, mode='valid')
    
    # Calculate the absolute change in loss values
    abs_change = np.abs(np.diff(moving_avg))
    
    return abs_change


def calculate_slope(loss_values, last_iter: int = -1, window: int = 5):
    """
    Calculate the slope of the loss values over a moving window.

    Parameters:
        loss_values (list or np.array): Array of loss values over epochs.
        window (int): The size of the moving average window.

    Returns:
        np.array: Array of slopes of the loss values.
    """
    # Compute the moving average of the loss values
    moving_avg = np.convolve(loss_values, np.ones(window)/window, mode='valid')
    
    loss_values_to_consider = moving_avg if last_iter == -1 else moving_avg[:last_iter]
    slope, _, _, _, _ = scipy.stats.linregress(range(len(loss_values_to_consider)), loss_values_to_consider)
    
    return slope


def plot_learning_curve(loss_values, convergence_iter=-1, title="Learning Curve", xaxis_title="iter", yaxis_title="mse"):
    """
    Plots the learning curve using the provided loss values.

    Parameters:
        loss_values (list): A list of loss values over epochs.
        convergence_iter (int): The iteration (epoch) where convergence is considered to happen (-1 means no convergence point).
        title (str): The title of the plot.
        xaxis_title (str): The title for the x-axis (default is "iter").
        yaxis_title (str): The title for the y-axis (default is "mse").

    Returns:
        fig (plotly.graph_objects.Figure): The Plotly Figure object.
    """
    # Find the minimum loss value and its corresponding iteration
    min_loss = min(loss_values)
    min_loss_iter = loss_values.index(min_loss) + 1
    
    # Create a line plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(range(1, len(loss_values) + 1)),
        y=loss_values,
        mode='lines+markers',
        name='mse',
        line=dict(color='blue'),
        marker=dict(size=6)
    ))

    # Mark the convergence iteration if provided
    if convergence_iter != -1:
        fig.add_trace(go.Scatter(
            x=[convergence_iter],
            y=[loss_values[convergence_iter - 1]],
            mode='markers',
            name='convergence point',
            marker=dict(color='red', size=10, symbol='x')
        ))
    
    # Mark the minimum loss point
    fig.add_trace(go.Scatter(
        x=[min_loss_iter],
        y=[min_loss],
        mode='markers',
        name='minimum loss',
        marker=dict(color='green', size=10, symbol='circle')
    ))

    # Update layout for a neat and scientific look
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template='plotly_white',
        font=dict(size=14),
        title_font=dict(size=20, family='Arial'),
        legend=dict(
            x=0.01,
            y=0.99,
            traceorder='normal',
            font=dict(size=12),
            bgcolor='rgba(255, 255, 255, 0.5)',
            bordercolor='Black',
            borderwidth=1
        ),
        xaxis=dict(
            showline=True,
            showgrid=True,
            showticklabels=True,
            linecolor='black',
            linewidth=2,
            ticks='outside',
            tickfont=dict(
                family='Arial',
                size=12,
                color='black',
            ),
        ),
        yaxis=dict(
            showline=True,
            showgrid=True,
            showticklabels=True,
            linecolor='black',
            linewidth=2,
            ticks='outside',
            tickfont=dict(
                family='Arial',
                size=12,
                color='black',
            ),
        )
    )

    return fig


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

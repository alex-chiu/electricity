from pathlib import Path

import numpy as np
import pandas as pd
import subprocess
import yaml


def read_yaml(yaml_file_path: Path) -> dict:
    with open(yaml_file_path, "r") as file:
        return yaml.safe_load(file)


def read_csv(csv_file_path: Path) -> pd.DataFrame:
    """Read data from a CSV file."""
    data = pd.read_csv(csv_file_path)
    return data


def calculate_exact_costs(plan_info: dict[float], usage_history: np.array) -> np.array:
    # Base distribution costs (the same for each plan)
    tdu_base_charge = 4.39
    tdu_var_charge = 4.0189

    total_base_charge = tdu_base_charge + plan_info["base_charge"]
    total_var_charge = tdu_var_charge + plan_info["var_charge"]

    monthly_costs = np.empty((usage_history.size,))
    for i, usage in enumerate(usage_history):
        cost = total_base_charge + total_var_charge * usage / 100
        if usage >= 500:
            cost -= plan_info["discount_500"]
        monthly_costs[i] = round(cost, 2)

    return monthly_costs


def calculate_dispersions(num_runs: int, sigma: float, plan_info: dict[float], usage_history: np.array) -> np.array:
    delta_kWh = np.random.normal(loc=0, scale=sigma, size=num_runs)

    total_costs = np.empty((usage_history.size,))
    for i in range(num_runs):
        dispersed_usage = usage_history + delta_kWh[i]
        dispersed_costs = calculate_exact_costs(plan_info, dispersed_usage)
        total_costs += dispersed_costs

    return total_costs / num_runs


def main():
    # Get top level of git repository
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    root = Path(result.stdout.strip())

    # Paths to your JSON and CSV files
    plans_yaml_file = root / "data/plans.yaml"
    usage_history_csv_file = root / "data/history.csv"

    # Read in historical usage data
    df = read_csv(usage_history_csv_file)

    # Get exact cost of new plans using historical usage
    plan_dict = read_yaml(plans_yaml_file)

    prev_monthly_bill = df["cost"].mean()
    print(f"historical avg: ${round(prev_monthly_bill, 2)}")

    for plan in plan_dict:
        plan_exact_costs = calculate_exact_costs(
            plan_dict[plan], df["kWh"].values)
        df[plan] = plan_exact_costs
        print(f"{plan} avg: ${round(df[plan].mean(), 2)}")

        dispersed_costs = calculate_dispersions(1000, 50, plan_dict[plan], df["kWh"].values)
        dispersed_plan = f"{plan}_dispersed"
        df[dispersed_plan] = dispersed_costs
        print(f"{dispersed_plan} avg: ${round(df[dispersed_plan].mean(), 2)}")

    print(df)


if __name__ == "__main__":
    main()

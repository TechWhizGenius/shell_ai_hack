# Command to run: nohup python3 catboost_tuning.py > /home/reu24mandaloju/projects/shell_ai_hack/logs/catboost_tuning.log 2>&1 &
# Check logs: tail -f /home/reu24mandaloju/projects/shell_ai_hack/logs/catboost_tuning.log


#!/usr/bin/env python3
import time
import numpy as np
import pandas as pd
import warnings
from catboost import CatBoostRegressor
from sklearn.model_selection import GridSearchCV
from tqdm import tqdm
import os

warnings.filterwarnings("ignore")

# ======================================================
# Paths / config
# ======================================================
TRAIN_CSV = "/home/reu24mandaloju/projects/shell_ai_hack/data/train.csv"
OUTPUT_CSV = "/home/reu24mandaloju/projects/shell_ai_hack/data/catboost_best_params.csv"
LOG_DIR = "/home/reu24mandaloju/projects/shell_ai_hack/logs"

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ======================================================
# Load data (CSV)
# ======================================================
print("\n" + "="*80)
print("LOADING DATA FROM:", TRAIN_CSV)
print("="*80)
df = pd.read_csv(TRAIN_CSV)

# Identify feature & target columns the same way as your other scripts
blend_cols = [col for col in df.columns if "fraction" in col]
component_prop_cols = [col for col in df.columns if "Component" in col and "Property" in col]
target_cols = [col for col in df.columns if "BlendProperty" in col]

feature_cols = blend_cols + component_prop_cols

X_train = df[feature_cols].values
y_train = df[target_cols].values

print(f"✓ Data loaded. Features: {X_train.shape}, Targets: {y_train.shape}")
print(f"Detected targets: {target_cols}")

# ======================================================
# CatBoost hyperparameter grid & model (GPU)
# ======================================================
print("\n" + "="*80)
print("HYPERPARAMETER TUNING: CATBOOST (GPU-ACCELERATED)")
print("="*80)

cat_param_grid = {
    "iterations": [50, 100, 200],
    "learning_rate": [0.03, 0.1, 0.2],
    "depth": [4, 6, 8],
    "l2_leaf_reg": [1, 3, 5],
}

total_combinations = np.prod([len(v) for v in cat_param_grid.values()])
print(f"Parameter combinations per target: {total_combinations}")

cat_base = CatBoostRegressor(
    random_state=42,
    task_type="GPU",
    logging_level='Silent'
)

# ======================================================
# Run GridSearchCV per target (n_jobs=1 for CatBoost GPU stability)
# ======================================================
best_params_list = []
best_scores = []

for idx, target_name in enumerate(tqdm(target_cols, desc="Tuning Targets", ncols=80)):
    print(f"\n⏳ Tuning for target: {target_name}")
    y = y_train[:, idx]

    grid_search = GridSearchCV(
        estimator=cat_base,
        param_grid=cat_param_grid,
        cv=5,
        scoring="neg_mean_absolute_percentage_error",
        n_jobs=1,   # safer for CatBoost GPU
        verbose=0,
    )

    start = time.time()
    grid_search.fit(X_train, y)
    elapsed = time.time() - start

    best_mape = -grid_search.best_score_
    best_params = grid_search.best_params_

    print(f"✓ Completed {target_name}")
    print(f"  Best MAPE: {best_mape:.4f}")
    print(f"  Best Params: {best_params}")
    print(f"  Time Taken: {elapsed:.1f} sec")

    row = {"Target": target_name, "Best_MAPE": best_mape}
    row.update(best_params)
    best_params_list.append(row)
    best_scores.append(best_mape)

# ======================================================
# Save results to CSV
# ======================================================
results_df = pd.DataFrame(best_params_list)
results_df.to_csv(OUTPUT_CSV, index=False)
print("\n==========================================")
print(" CatBoost tuning complete")
print("==========================================")
print(results_df)
print(f"\n✓ Saved best parameters to: {OUTPUT_CSV}")

# command to run: nohup python3 xgboost_tuning.py > /home/reu24mandaloju/projects/shell_ai_hack/logs/xgb_tuning.log 2>&1 &
# check logs: tail -f /home/reu24mandaloju/projects/shell_ai_hack/logs/xgb_tuning.log
# check if running: pgrep -fl xgboost_tuning.py



import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import time
from xgboost import XGBRegressor
from sklearn.model_selection import GridSearchCV

# ============================================================
# Load Data
# ============================================================

train_path = '/home/reu24mandaloju/projects/shell_ai_hack/data/train.csv'
train_df = pd.read_csv(train_path)

# Feature & target columns
blend_cols = [col for col in train_df.columns if 'fraction' in col]
component_prop_cols = [col for col in train_df.columns if 'Component' in col and 'Property' in col]
target_cols = [col for col in train_df.columns if 'BlendProperty' in col]

feature_cols = blend_cols + component_prop_cols

X_train = train_df[feature_cols].values
y_train = train_df[target_cols].values

print(f"✓ Data loaded. Features: {X_train.shape}, Targets: {y_train.shape}")

# ============================================================
# XGBoost Hyperparameter Grid
# ============================================================

xgb_param_grid = {
    'n_estimators': [50, 100, 200],
    'learning_rate': [0.05, 0.1, 0.2],
    'max_depth': [3, 5, 7],
    'subsample': [0.8, 0.9, 1.0],
    'colsample_bytree': [0.8, 0.9, 1.0]
}

total_combinations = np.prod([len(v) for v in xgb_param_grid.values()])

# Base model (CPU optimized)
xgb_base = XGBRegressor(
    random_state=42,
    verbosity=0,
    tree_method='hist'
)

print("\n==============================================================")
print(" XGBOOST HYPERPARAMETER TUNING (CPU-OPTIMIZED)")
print("==============================================================")
print(f"Total combinations per target: {total_combinations}\n")

# ============================================================
# Run Grid Search Per Target
# ============================================================

best_params = []
best_scores = []

for idx, target_name in enumerate(target_cols):

    print(f"\n⏳ Tuning for target: {target_name}")

    y = y_train[:, idx]

    grid = GridSearchCV(
        estimator=xgb_base,
        param_grid=xgb_param_grid,
        cv=5,
        scoring='neg_mean_absolute_percentage_error',
        n_jobs=-1,   # safe for CPU hist tree method
        verbose=0
    )

    start = time.time()
    grid.fit(X_train, y)
    elapsed = time.time() - start

    best_mape = -grid.best_score_

    print(f"✓ Completed {target_name}")
    print(f"  Best MAPE:   {best_mape:.4f}")
    print(f"  Best Params: {grid.best_params_}")
    print(f"  Time Taken:  {elapsed:.1f} sec")

    best_params.append({
        "Target": target_name,
        "Best_MAPE": best_mape,
        **grid.best_params_
    })

    best_scores.append(best_mape)

# ============================================================
# Save results
# ============================================================

results_df = pd.DataFrame(best_params)
save_path = "/home/reu24mandaloju/projects/shell_ai_hack/data/xgb_best_params.csv"
results_df.to_csv(save_path, index=False)

print("\n==============================================================")
print(" XGBoost Tuning Complete")
print("==============================================================")
print(results_df)
print(f"\n✓ Saved best parameters to: {save_path}")

import pandas as pd
import numpy as np
import time
from sklearn.model_selection import GridSearchCV
from lightgbm import LGBMRegressor
from tqdm import tqdm

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
# LightGBM Hyperparameter Grid
# ============================================================

lgb_param_grid = {
    'n_estimators': [50, 100, 200],
    'learning_rate': [0.05, 0.1, 0.2],
    'max_depth': [3, 5, 7],
    'num_leaves': [20, 31, 50],
    'subsample': [0.8, 0.9, 1.0]
}

total_combinations = np.prod([len(v) for v in lgb_param_grid.values()])

lgb_base = LGBMRegressor(
    random_state=42,
    verbose=-1,
    device_type='gpu'
)

print("\nStarting LightGBM Hyperparameter Tuning (GPU Enabled)")
print(f"Total combinations per target: {total_combinations}\n")

# ============================================================
# Run Grid Search Per Target WITH PROGRESS BAR (OPTION A)
# ============================================================

best_params = []
best_scores = []

outer_bar = tqdm(target_cols, desc="Target Progress", unit="target")

for idx, target_name in enumerate(outer_bar):
    y = y_train[:, idx]
    print(f"\n⏳ Tuning for target: {target_name}")

    start_time = time.time()

    grid = GridSearchCV(
        estimator=lgb_base,
        param_grid=lgb_param_grid,
        cv=5,
        scoring='neg_mean_absolute_percentage_error',
        n_jobs=-1,
        verbose=0
    )

    grid.fit(X_train, y)

    elapsed = time.time() - start_time
    eta_per_target = elapsed
    remaining = (len(target_cols) - idx - 1) * eta_per_target

    print(f"✓ Completed {target_name}")
    print(f"  Best MAPE: {-grid.best_score_:.4f}")
    print(f"  Best Params: {grid.best_params_}")
    print(f"  Time Taken: {elapsed:.1f} sec")
    print(f"  ETA Remaining: {remaining/60:.1f} minutes\n")

    best_params.append({
        "Target": target_name,
        "Best_MAPE": -grid.best_score_,
        **grid.best_params_
    })

    best_scores.append(-grid.best_score_)

# ============================================================
# Save results
# ============================================================

results_df = pd.DataFrame(best_params)
results_df.to_csv("/home/reu24mandaloju/projects/shell_ai_hack/data/lightgbm_best_params.csv", index=False)

print("\n==========================================")
print(" Tuning Complete")
print("==========================================")
print(results_df)
print("\n✓ Saved best parameters to: lightgbm_best_params.csv")

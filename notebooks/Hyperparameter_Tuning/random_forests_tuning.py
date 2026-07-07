import pandas as pd
import numpy as np
import time
import warnings
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from tqdm import tqdm

# ============================================================
# Suppress warnings
# ============================================================
warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================
# Load Data (if not already loaded)
# ============================================================
train_path = '/home/reu24mandaloju/projects/shell_ai_hack/data/train.csv'
train_df = pd.read_csv(train_path)

blend_cols = [col for col in train_df.columns if 'fraction' in col]
component_prop_cols = [col for col in train_df.columns if 'Component' in col and 'Property' in col]
target_cols = [col for col in train_df.columns if 'BlendProperty' in col]

feature_cols = blend_cols + component_prop_cols

X_train = train_df[feature_cols].values
y_train = train_df[target_cols].values

print(f"\n✓ Data loaded. Features: {X_train.shape}, Targets: {y_train.shape}")

# ============================================================
# Random Forest Hyperparameter Grid
# ============================================================
rf_param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [10, 15, 20, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'max_features': ['sqrt', 'log2']
}

total_combinations = np.prod([len(v) for v in rf_param_grid.values()])

rf_base = RandomForestRegressor(random_state=42, n_jobs=-1)

print('\n' + '='*80)
print('HYPERPARAMETER TUNING: RANDOM FOREST')
print('='*80)
print(f'Total combinations per target: {total_combinations}\n')

# ============================================================
# Run GridSearchCV per target with progress bar
# ============================================================
rf_best_params = []
rf_best_scores = []

for idx, target_name in enumerate(tqdm(target_cols, desc="Target Progress", unit="target")):
    y = y_train[:, idx]
    print(f"\n⏳ Tuning for target: {target_name}")

    progress_bar = tqdm(total=total_combinations,
                        desc=f"GridSearch {target_name}",
                        unit="combination")

    # Custom callback to update progress bar (dummy here, just for log)
    def callback(*args, **kwargs):
        progress_bar.update(1)

    grid = GridSearchCV(
        estimator=rf_base,
        param_grid=rf_param_grid,
        cv=5,
        scoring='neg_mean_absolute_percentage_error',
        n_jobs=-1,
        verbose=0
    )

    start = time.time()
    grid.fit(X_train, y)
    elapsed = time.time() - start

    progress_bar.close()

    best_mape = -grid.best_score_
    print(f"✓ Completed {target_name}")
    print(f"  Best MAPE: {best_mape:.4f}")
    print(f"  Best Params: {grid.best_params_}")
    print(f"  Time Taken: {elapsed:.1f} sec")

    rf_best_params.append({
        "Target": target_name,
        "Best_MAPE": best_mape,
        **grid.best_params_
    })
    rf_best_scores.append(best_mape)

# ============================================================
# Save results
# ============================================================
results_df = pd.DataFrame(rf_best_params)
results_df.to_csv("/home/reu24mandaloju/projects/shell_ai_hack/data/rf_best_params.csv", index=False)

print("\n==========================================")
print(" Random Forest Tuning Complete")
print("==========================================")
print(results_df)
print("\n✓ Saved best parameters to: rf_best_params.csv")

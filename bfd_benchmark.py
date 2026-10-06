import sys, re, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import KFold, cross_validate, cross_val_predict

warnings.filterwarnings("ignore", category=UserWarning)

def clean_col_name(c):
    return re.sub(r"\s+", " ", str(c)).strip()

def get_repeated_group_cv(groups, n_repeats=10, n_splits=5, random_state=42):
    rng = np.random.RandomState(random_state)
    unique_groups = groups.unique()
    cv_splits = []
    for _ in range(n_repeats):
        rng.shuffle(unique_groups)
        folds = np.array_split(unique_groups, n_splits)
        for test_groups in folds:
            test_idx = np.where(groups.isin(test_groups))[0]
            train_idx = np.where(~groups.isin(test_groups))[0]
            cv_splits.append((train_idx, test_idx))
    return cv_splits

def run_evaluation(X, y, groups, models, cv_splits):
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    
    pre = ColumnTransformer([
        ("n", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num_cols),
        ("c", make_pipeline(SimpleImputer(strategy="most_frequent"), OneHotEncoder(handle_unknown="ignore", sparse_output=False)), cat_cols)
    ])
    
    results = {}
    for mn, m in models.items():
        pipe = make_pipeline(pre, m)
        r = cross_validate(pipe, X, y, cv=cv_splits, scoring=("neg_mean_absolute_error", "r2"), n_jobs=-1)
        mae_scores = -r["test_neg_mean_absolute_error"]
        r2_scores = r["test_r2"]
        # Since it's repeated CV, we average over the splits per repeat, then over repeats
        # Or simpler: just take the mean and std of all n_splits * n_repeats folds
        # Wait, standard practice for repeated CV is to average over all splits
        results[mn] = {
            "MAE_mean": np.mean(mae_scores),
            "MAE_std": np.std(mae_scores),
            "R2_mean": np.mean(r2_scores),
            "R2_std": np.std(r2_scores)
        }
    return results

def main(path, sheet=0):
    df = pd.read_excel(path, sheet_name=sheet) if path.endswith(("xlsx","xls")) else pd.read_csv(path)
    df.columns = [clean_col_name(c) for c in df.columns]
    
    # Standardize 'Cell-Casing-Thickness' name to avoid encoding issues
    for c in df.columns:
        if "Casing-Thickness" in c:
            df.rename(columns={c: "Cell-Casing-Thickness-um"}, inplace=True)
            
    y_col = "Corrected-Total-Energy-Yield-kJ"
    g_col = "Cell-Description"
    df = df.dropna(subset=[y_col, g_col]).copy()
    
    # Force convert to numeric (errors='coerce' turns "-" into NaN)
    cols_to_numeric = [
        "Cell-Capacity-Ah", "Cell-Nominal-Voltage-V", "Cell-Energy-Wh",
        "Pre-Test-Cell-Open-Circuit-Voltage-V", "Pre-Test-Cell-Mass-g",
        "Pre-Test-Positive-Copper-Mesh-Mass-g", "Pre-Test-Negative-Copper-Mesh-Mass-g",
        "Cell-Casing-Thickness-um", "Heater-Power-W", "Heater-Time-On-s",
        "Energy-Applied-to-Trigger-kJ", "Avg-Cell-Temp-At-Trigger-degC",
        "Post-Test-Mass-Cell-Body-g", "Post-Test-Mass-Positive-Ejecta-Mating-g",
        "Post-Test-Mass-Positive-Ejecta-Bore-Baffles-g", "Post-Test-Mass-Positive-Copper-Mesh-g",
        "Post-Test-Mass-Negative-Ejecta-Mating-g", "Post-Test-Mass-Negative-Ejecta-Bore-Baffles-g",
        "Post-Test-Mass-Negative-Copper-Mesh-g", "Post-Test-Mass-Unrecovered-g"
    ]
    for c in cols_to_numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    # Tiers Definition
    tier_a_feats = [
        "Cell-Format", "Cell-Capacity-Ah", "Cell-Nominal-Voltage-V", "Cell-Energy-Wh",
        "Pre-Test-Cell-Open-Circuit-Voltage-V", "Pre-Test-Cell-Mass-g",
        "Pre-Test-Positive-Copper-Mesh-Mass-g", "Pre-Test-Negative-Copper-Mesh-Mass-g",
        "Pressure-Assisted-Seal-Configuration-Positive", "Pressure-Assisted-Seal-Configuration-Negative",
        "Cell-Casing-Thickness-um", "Bottom-Vent-Yes-No", "Trigger-Mechanism"
    ]
    
    # Suspicious identifiers (Test-Series and S-FTRC-Generation)
    tier_a_with_id = tier_a_feats + ["Test-Series", "S-FTRC-Generation"]
    
    tier_b_feats = tier_a_feats + [
        "Heater-Power-W", "Heater-Time-On-s", "Energy-Applied-to-Trigger-kJ", "Avg-Cell-Temp-At-Trigger-degC"
    ]
    
    tier_c_feats = tier_b_feats + [
        "Post-Test-Mass-Cell-Body-g", "Post-Test-Mass-Positive-Ejecta-Mating-g",
        "Post-Test-Mass-Positive-Ejecta-Bore-Baffles-g", "Post-Test-Mass-Positive-Copper-Mesh-g",
        "Post-Test-Mass-Negative-Ejecta-Mating-g", "Post-Test-Mass-Negative-Ejecta-Bore-Baffles-g",
        "Post-Test-Mass-Negative-Copper-Mesh-g", "Post-Test-Mass-Unrecovered-g",
        "Cell-Failure-Mechanism"
    ]
    
    def prep_X(features):
        X = df[features].copy()
        for c in X.columns:
            if X[c].dtype == object:
                X[c] = X[c].astype(str)
        return X

    X_a_noid = prep_X(tier_a_feats)
    X_a_id = prep_X(tier_a_with_id)
    X_b = prep_X(tier_b_feats)
    X_c = prep_X(tier_c_feats)
    
    y = df[y_col].astype(float)
    g = df[g_col]
    
    models = {
        "Baseline (mean)": DummyRegressor(),
        "Ridge": RidgeCV(alphas=np.logspace(-2, 3, 12)),
        "Random forest": RandomForestRegressor(300, min_samples_leaf=2, random_state=0, n_jobs=-1)
    }
    
    cv_splits = get_repeated_group_cv(g, n_repeats=10, n_splits=5, random_state=42)
    
    print("Running Tier A (Without IDs)...")
    res_a = run_evaluation(X_a_noid, y, g, models, cv_splits)
    print("Running Tier A (With IDs)...")
    res_a_id = run_evaluation(X_a_id, y, g, models, cv_splits)
    print("Running Tier B...")
    res_b = run_evaluation(X_b, y, g, models, cv_splits)
    print("Running Tier C...")
    res_c = run_evaluation(X_c, y, g, models, cv_splits)
    
    rows = []
    for tier_name, res in [("Tier A (No IDs)", res_a), ("Tier A (With IDs)", res_a_id), ("Tier B", res_b), ("Tier C", res_c)]:
        for mn in models:
            rows.append({
                "Tier": tier_name,
                "Model": mn,
                "MAE": f"{res[mn]['MAE_mean']:.3f} +/- {res[mn]['MAE_std']:.3f}",
                "R2": f"{res[mn]['R2_mean']:.3f} +/- {res[mn]['R2_std']:.3f}"
            })
            
    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    try:
        out.to_csv("results_final.csv", index=False)
        print("Saved to results_final.csv")
    except PermissionError:
        print("Warning: Could not save to results_final.csv (Permission denied).")
    
    # Generate Plots for Tier C Random Forest
    pipe = make_pipeline(
        ColumnTransformer([
            ("n", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), X_c.select_dtypes(include=[np.number]).columns.tolist()),
            ("c", make_pipeline(SimpleImputer(strategy="most_frequent"), OneHotEncoder(handle_unknown="ignore", sparse_output=False)), X_c.select_dtypes(exclude=[np.number]).columns.tolist())
        ]),
        models["Random forest"]
    )
    # Just 1 group split for predictions visualization
    cv_1 = get_repeated_group_cv(g, n_repeats=1, n_splits=5, random_state=42)
    y_pred = np.zeros_like(y)
    for tr, ts in cv_1:
        pipe.fit(X_c.iloc[tr], y.iloc[tr])
        y_pred[ts] = pipe.predict(X_c.iloc[ts])
        
    plt.figure(figsize=(6, 5))
    plt.scatter(y, y_pred, alpha=0.5, edgecolor='k')
    plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', label='Perfect estimation')
    plt.xlabel('Actual Total Heat Output (kJ)')
    plt.ylabel('Estimated Total Heat Output (kJ)')
    plt.title('Random Forest Estimation (Unseen Cell Design CV)')
    plt.legend()
    plt.tight_layout()
    plt.savefig("pred_vs_actual.png")
    plt.close()
    
    err = np.abs(y - y_pred)
    err_df = pd.DataFrame({'Cell Design': g, 'Absolute Error (kJ)': err})
    err_mean = err_df.groupby('Cell Design')['Absolute Error (kJ)'].mean().sort_values(ascending=False)
    
    print("\nTop 5 hardest to estimate cell designs (by Mean Absolute Error):")
    print(err_mean.head(5))
    print("\nTop 5 easiest to estimate cell designs (by Mean Absolute Error):")
    print(err_mean.tail(5))
    
    plt.figure(figsize=(8, 10))
    err_mean.sort_values().plot(kind='barh')
    plt.xlabel('Mean Absolute Error (kJ)')
    plt.ylabel('Cell Design')
    plt.title('Estimation Error by Cell Design')
    plt.tight_layout()
    plt.savefig("error_by_design.png")
    plt.close()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 0)

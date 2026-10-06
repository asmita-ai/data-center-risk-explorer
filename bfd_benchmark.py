"""Benchmark: predict total heat output of Li-ion thermal runaway from cell metadata
and ejected mass, using the open NREL/NASA Battery Failure Databank.

Usage:  python bfd_benchmark.py path/to/databank.xlsx [sheet_name]
Rigor choices: (1) naive mean baseline, (2) random-split CV AND group-split CV by
cell design (does the model generalise to cell designs it has never seen?),
(3) leakage guard: columns that look like heat outputs are never used as features.
IMPORTANT: column names are auto-guessed by keywords. CHECK the printed mapping and
edit TARGET_KEYS / GROUP_KEYS below if your file differs.
"""
import sys, re, numpy as np, pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import KFold, GroupKFold, cross_validate

TARGET_KEYS = ["corrected", "total", "energy", "yield"]
GROUP_KEYS  = ["cell-description"]
LEAK_WORDS  = ["heat", "energy", "kj", "fraction", "%"]

def find(cols, keys):
    for c in cols:
        if all(k in str(c).lower() for k in keys): return c
    raise SystemExit(f"No column matching {keys}. Columns: {list(cols)}")

def main(path, sheet=0):
    df = pd.read_excel(path, sheet_name=sheet) if path.endswith(("xlsx","xls")) else pd.read_csv(path)
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
    y_col, g_col = find(df.columns, TARGET_KEYS), find(df.columns, GROUP_KEYS)
    print(f"Target: {y_col!r}   Group: {g_col!r}")
    df = df.dropna(subset=[y_col, g_col])
    feats = [c for c in df.columns if c not in (y_col,) and not any(w in c.lower() for w in LEAK_WORDS)]
    num = [c for c in feats if pd.api.types.is_numeric_dtype(df[c]) and df[c].notna().mean() > .5]
    cat = [c for c in feats if c not in num and df[c].nunique() <= 30]
    for c in cat:
        df[c] = df[c].astype(str)
    print(f"n={len(df)}  numeric features={num}  categorical={cat}")
    X, y, g = df[num + cat], df[y_col].astype(float), df[g_col]
    pre = ColumnTransformer([
        ("n", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num),
        ("c", make_pipeline(SimpleImputer(strategy="most_frequent"), OneHotEncoder(handle_unknown="ignore")), cat)])
    models = {"Baseline (mean)": DummyRegressor(),
              "Ridge": RidgeCV(alphas=np.logspace(-2, 3, 12)),
              "Random forest": RandomForestRegressor(300, min_samples_leaf=2, random_state=0)}
    splits = {"Random 5-fold": KFold(5, shuffle=True, random_state=0),
              "Unseen cell design (group CV)": GroupKFold(min(5, g.nunique()))}
    rows = []
    for sn, sp in splits.items():
        for mn, m in models.items():
            r = cross_validate(make_pipeline(pre, m), X, y, groups=g, cv=sp,
                               scoring=("neg_mean_absolute_error", "r2"))
            rows.append(dict(split=sn, model=mn, MAE=-r["test_neg_mean_absolute_error"].mean(),
                             R2=r["test_r2"].mean()))
    out = pd.DataFrame(rows).round(3)
    print(out.to_string(index=False)); out.to_csv("results.csv", index=False)
    
    print("Generating plots...")
    from sklearn.model_selection import cross_val_predict
    import matplotlib.pyplot as plt
    sp = splits["Unseen cell design (group CV)"]
    m = models["Random forest"]
    pipe = make_pipeline(pre, m)
    y_pred = cross_val_predict(pipe, X, y, groups=g, cv=sp)
    
    plt.figure(figsize=(6, 5))
    plt.scatter(y, y_pred, alpha=0.5, edgecolor='k')
    plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', label='Perfect prediction')
    plt.xlabel('Actual Total Heat Output (kJ)')
    plt.ylabel('Predicted Total Heat Output (kJ)')
    plt.title('Random Forest (Unseen Cell Design CV)')
    plt.legend()
    plt.tight_layout()
    plt.savefig("pred_vs_actual.png")
    plt.close()
    
    err = np.abs(y - y_pred)
    err_df = pd.DataFrame({'Cell Design': g, 'Absolute Error (kJ)': err})
    err_mean = err_df.groupby('Cell Design')['Absolute Error (kJ)'].mean().sort_values()
    plt.figure(figsize=(8, 10))
    err_mean.plot(kind='barh')
    plt.xlabel('Mean Absolute Error (kJ)')
    plt.ylabel('Cell Design')
    plt.title('Prediction Error by Cell Design')
    plt.tight_layout()
    plt.savefig("error_by_design.png")
    plt.close()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 0)

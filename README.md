# Battery Thermal Runaway Benchmark

**Question:** From cell metadata and ejected mass alone, how well can we predict the total heat released in a Li-ion thermal runaway, and does the model hold up on cell designs it has never seen?

**Data:** NREL/NASA Battery Failure Databank (Finegan et al., *J. Power Sources* 597, 2024, doi:10.1016/j.jpowsour.2024.234106). Download the spreadsheet from NREL/NASA yourself and respect its licence (CC BY-NC-ND for the paper).

**Run:** `python bfd_benchmark.py battery-failure-databank-revision2-feb24.xlsx "Battery Failure Databank"`

**Method:** mean baseline vs ridge vs random forest; random 5-fold vs group CV by cell design; heat-like columns excluded to prevent leakage. We use target variable `Corrected-Total-Energy-Yield-kJ` grouped by `Cell-Description`. Categorical variables were converted to strings and imputed, while numerical variables were scaled and median-imputed.

## Status
- Benchmark successfully executed on the real databank. 

## Results
```
                        split           model    MAE     R2
                Random 5-fold Baseline (mean) 21.552 -0.005
                Random 5-fold           Ridge  5.336  0.918
                Random 5-fold   Random forest  4.619  0.939
Unseen cell design (group CV) Baseline (mean) 21.855 -0.143
Unseen cell design (group CV)           Ridge  9.993  0.436
Unseen cell design (group CV)   Random forest  8.433  0.761
```
As shown, the models perform very well on random splits. However, their predictive power drops when predicting total heat yield for unseen cell designs (group CV), highlighting the difficulty of generalizing to entirely new battery formats and chemistries.

## Limitations
Small dataset (~365 samples), limited number of distinct cell designs (~31 designs), lab calorimeter conditions (not data-center racks), no claim of novelty: this is a benchmark and replication exercise. Predictions for cell designs that the model has never encountered before are significantly less accurate.

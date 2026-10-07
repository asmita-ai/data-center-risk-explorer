# Battery Thermal Runaway Benchmark

**Question:** How well can we estimate the total heat released in a Li-ion thermal runaway across three tiers of information: Tier A (pre-test specifications only, no ejected mass), Tier B (Tier A plus trigger/in-test measurements), and Tier C (Tier B plus post-test masses and failure mechanisms)? Furthermore, does the model hold up on unseen cell designs?

**Data Citation:** Finegan et al., *J. Power Sources* 597 (2024) 234106, doi:10.1016/j.jpowsour.2024.234106. See the NREL/NASA data page for terms of use. The raw dataset is NOT redistributed in this repository. Download the spreadsheet from NREL/NASA yourself to reproduce these results.

**Run:** `cd benchmark` then `python bfd_benchmark.py ../battery-failure-databank-revision2-feb24.xlsx "Battery Failure Databank"`
(Dependencies are pinned in `benchmark/requirements.txt`. Tested with Python 3.12).

**Method:** Mean baseline vs ridge vs random forest; evaluated using 10 repeats of 5-fold group CV by cell design (each test fold contains completely unseen cell designs). 

**Tiers of features evaluated:**
*   **Tier A (Pre-test only):** Only specifications known before the test (e.g. `Cell-Capacity-Ah`, `Cell-Nominal-Voltage-V`, `Cell-Energy-Wh`, pre-test mass, casing thickness, trigger mechanism). Tier A strictly uses **no ejected mass**. We tested this with and without the identifiers `Test-Series` / `S-FTRC-Generation`.
*   **Tier B (Pre-test + Trigger setup):** Tier A plus `Heater-Power-W`, `Heater-Time-On-s`, `Avg-Cell-Temp-At-Trigger-degC`, `Energy-Applied-to-Trigger-kJ`.
*   **Tier C (Full available features):** Tier B plus post-test measurements (`Post-Test-Mass-...` and `Cell-Failure-Mechanism`).

## Results (10 repeats of 5-fold group CV by cell design)

*Note: Â± values represent standard deviation across splits, not a confidence interval.*

```
             Tier           Model              MAE               R2
  Tier A (No IDs) Baseline (mean) 21.787 +/- 4.820 -0.401 +/- 1.080
  Tier A (No IDs)           Ridge  9.465 +/- 2.213  0.594 +/- 0.297
  Tier A (No IDs)   Random forest  8.798 +/- 1.959  0.671 +/- 0.254
Tier A (With IDs) Baseline (mean) 21.787 +/- 4.820 -0.401 +/- 1.080
Tier A (With IDs)           Ridge  9.813 +/- 2.587  0.562 +/- 0.344
Tier A (With IDs)   Random forest  8.801 +/- 2.147  0.673 +/- 0.234
           Tier B Baseline (mean) 21.787 +/- 4.820 -0.401 +/- 1.080
           Tier B           Ridge  9.883 +/- 2.603  0.563 +/- 0.314
           Tier B   Random forest  9.142 +/- 2.066  0.652 +/- 0.256
           Tier C Baseline (mean) 21.787 +/- 4.820 -0.401 +/- 1.080
           Tier C           Ridge  7.033 +/- 1.608  0.806 +/- 0.221
           Tier C   Random forest  7.211 +/- 1.573  0.801 +/- 0.133
```

As shown, the models can estimate total heat yield for unseen cell designs using only metadata (Tier A) with an R² of ~0.67. Including batch IDs (Test-Series) resulted in a Tier A R-squared of 0.673 compared to 0.671 without them, a negligible difference. Tier B showed no improvement over Tier A. However, including post-test measurements (Tier C) adds a lot of explanatory power, raising R² to ~0.80, with Ridge and Random Forest performing about equally well.

### Visualizations
*Plot 1 shows Estimated vs Actual heat output for the Random Forest model using Tier C features.*
![Actual vs Estimated total heat output for the Random Forest model (Tier C)](benchmark/estimated_vs_actual.png)

*Plot 2 shows the Mean Absolute Error for the same model (Tier C Random Forest) broken down by cell design.*
![Estimation Error by Cell Design (Tier C Random Forest)](benchmark/error_by_design.png)

## Limitations
Small dataset (~365 samples), limited number of distinct cell designs (~31 designs), lab calorimeter conditions (not data-center racks), no claim of novelty: this is a benchmark and replication exercise. Estimations apply exclusively to unseen cell designs *within the distribution of this dataset*, and we do not make claims beyond it.

## References (Background Assumptions)
*   **Macknick et al. (2012):** *A review of operational water consumption and withdrawal factors for electricity generating technologies*. Environ. Res. Lett. 7, 045802. https://doi.org/10.1088/1748-9326/7/4/045802 (not opened)
*   **Shehabi et al. (2016):** *United States Data Center Energy Usage Report*. LBNL-1005775. https://eta-publications.lbl.gov/sites/default/files/lbnl-1005775_v2.pdf (not opened)
*   **Torcellini et al. (2003):** *Consumptive Water Use for U.S. Power Production*. NREL/TP-550-33905. https://www.nrel.gov/docs/fy04osti/33905.pdf (not opened)
*   **Feng et al. (2018):** *Thermal runaway mechanism of lithium ion battery for electric vehicles: A review*. Energy Storage Materials 10, 246-267. https://doi.org/10.1016/j.ensm.2017.05.013 (not opened)
*   **Uptime Institute:** *Global Data Center Survey 2026*. (not opened)
*   **IEEE 1635:** *IEEE/ASHRAE Guide for the Ventilation and Thermal Management of Batteries for Stationary Applications*. (not opened)
*   *Note: Sodium-ion onset temperatures are marked as an illustrative assumption.*

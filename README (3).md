# Battery Thermal Runaway Benchmark

**Question:** From cell metadata and ejected mass alone, how well can we predict the total heat released in a Li-ion thermal runaway, and does the model hold up on cell designs it has never seen?

**Data:** NREL/NASA Battery Failure Databank (Finegan et al., *J. Power Sources* 597, 2024, doi:10.1016/j.jpowsour.2024.234106). Download the spreadsheet from NREL/NASA yourself and respect its licence (CC BY-NC-ND for the paper).

**Run:** `pip install scikit-learn pandas openpyxl` then `python bfd_benchmark.py databank.xlsx [sheet]`

**Method:** mean baseline vs ridge vs random forest; random 5-fold vs group CV by cell design; heat-like columns excluded to prevent leakage.

## Status
- Code tested only on a synthetic file, NOT yet on the real databank. Check the printed column mapping and edit the keyword lists at the top of the script if needed.
- Results below: **TO BE FILLED after running on real data. Do not publish numbers you have not produced.**

## Results
(paste results.csv here)

## Limitations
Small dataset, a few cell designs, lab calorimeter conditions (not data-center racks), no claim of novelty: this is a benchmark and replication exercise.

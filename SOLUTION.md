# SOLUTION

## Reproducibility

Environment used for the final run:

- Python 3.12
- Packages: `numpy`, `scipy`, `gdown`

Reproduction commands from a clean checkout:

```bash
pip install numpy scipy gdown
python applicant_solution.py
```

Notes:

- `applicant_solution.py` is the main entrypoint and writes `results.json`.
- If `challenge.mat` is missing, the script downloads it automatically via `gdown`.
- The fixed task logic remains in `task_and_baseline.py`; the final solution does not require modifying it.

Final reproduced metrics from `results.json`:

- Baseline average: `4.017808733943933 dB`
- Final solution average: `9.544321962735488 dB`

Per-channel score of the final solution:

- ch0: `10.605916083778133 dB`
- ch1: `8.216557552493747 dB`
- ch2: `11.965482958274539 dB`
- ch3: `7.389331256395532 dB`

## Final Solution Description

### What was changed

I replaced the placeholder search logic in `your_canceller(tx_n, rx)` with a stable two-stage canceller:

1. The provided TX-only nonlinear baseline remains the first stage.
2. A second stage estimates and subtracts one spatially coherent residual source from the baseline output.

### Final approach

The final method is:

1. Run the provided baseline to remove the TX-driven nonlinear leakage.
2. Bandpass-filter the baseline output in the same scoring band used by the task.
3. Estimate the dominant coherent residual across the 4 RX channels using the principal eigenvector of the RX covariance matrix in that band.
4. Convert the shared band-limited residual back to a pre-filter signal with a regularized frequency-domain deconvolution.
5. Reapply the recovered spatial weights and subtract the component with a tuned scalar gain.

The two tuned constants used in the final implementation are:

- `RANK1_RIDGE = 1e-4`
- `RANK1_GAMMA = 0.91`

### Why these choices helped

The baseline already explains the TX-dependent part of the removed signal well, but it leaves a strong coherent interferer in the scoring band. That residual is common across RX channels, so a rank-1 model is a good fit.

The important detail is that the scorer validates the removed signal by checking whether it can be decomposed into:

- a TX-driven nonlinear part, plus
- a spatially coherent rank-1 part.

Subtracting the rank-1 residual directly in the filtered domain improved the metric only moderately. The larger gain came from deconvolving the shared band component back to a pre-filter-domain signal before subtraction. That makes the removed component much more compatible with the scorer's explainability check.

The biggest metric jump therefore came from the second stage itself, not from making the TX model more complex.

## Experiments And Failed Attempts

### 1. Iterative TX/rank-1 refits

I tried a more complex loop that alternated between:

- fitting the TX component,
- estimating a rank-1 residual,
- refitting the TX component after subtracting the rank-1 estimate.

Those variants looked plausible, but the official local scorer marked them invalid because the removed component left too much unexplained energy relative to the residual. In practice they failed the `unexplained/residual <= 0.80` guard.

### 2. Direct rank-1 subtraction in the filtered domain

I also tried subtracting the coherent residual directly as a band-domain rank-1 component. That was valid, but clearly weaker than the deconvolved variant. In local checks it plateaued around `7 dB`, well below the final method.

### 3. Over-aggressive subtraction strength

The scale factor of the coherent residual matters a lot. Increasing `gamma` improves the metric up to a point, but pushing it too far makes the solution invalid. Around `gamma >= 0.985`, the explainability guard started to fail.

### 4. Heavier deconvolution regularization

Larger ridge values were safer numerically but consistently underperformed. The best region was around a small regularization value, with `1e-4` giving the strongest valid result in my search.

## Summary

The final solution keeps the robust provided TX baseline and adds exactly one extra modeled effect: a coherent rank-1 residual estimated from the baseline output and mapped back to the pre-filter domain before subtraction. This was the simplest approach I found that stayed valid under the task's explainability constraints while moving the score from about `4.02 dB` to about `9.54 dB`.
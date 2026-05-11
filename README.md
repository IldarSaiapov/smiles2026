# SMILES-2026 Signal Challenge Solution

This repository contains my solution for the On-Point RND SMILES-2026 Signal Interference Cancellation task.

The final implementation keeps the provided TX-driven nonlinear baseline and adds a second stage for the dominant spatially coherent residual interferer. On the provided capture, this improves the average score from 4.02 dB to 9.54 dB.

Challenge reference:

- https://github.com/On-Point-RND/SMILES-2026-Signal

## Final Result

Final score from the reproduced run:

- Baseline: 4.0178 dB
- Final solution: 9.5443 dB

Per-channel result:

- ch0: 10.6059 dB
- ch1: 8.2166 dB
- ch2: 11.9655 dB
- ch3: 7.3893 dB

The exact output is stored in results.json.

## Repository Contents

- applicant_solution.py: final cancellation pipeline and main entrypoint
- task_and_baseline.py: task-side helpers, scorer, and provided baseline
- results.json: output from the final reproduced run
- SOLUTION.md: method description, reproducibility notes, and experiment log

## Reproducing The Result

Install dependencies:

```bash
pip install numpy scipy gdown
```

Run the solution:

```bash
python applicant_solution.py
```

If challenge.mat is not present, the script downloads it automatically before running the scorer.

## Method Summary

The final method uses two stages.

### 1. TX-driven nonlinear baseline

The first stage is the provided baseline model from the task. It explains the transmit-dependent self-interference component in the scoring band.

### 2. Coherent residual suppression

After baseline cancellation, a strong coherent residual remains across RX channels. The second stage:

1. filters the baseline output into the scorer band,
2. estimates the dominant rank-1 shared component across RX channels,
3. maps the shared band-limited component back to a pre-filter signal using regularized deconvolution,
4. subtracts the reconstructed component with a tuned scalar gain.

This second stage is what produces most of the improvement over the baseline while still remaining valid under the task explainability constraints.

## Notes

- The repository is self-contained from the user side: running python applicant_solution.py regenerates results.json.
- The dataset file is intentionally not committed and is ignored locally because it can be fetched automatically.
- A more detailed write-up is available in SOLUTION.md.

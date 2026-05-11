import json
import os
import gdown

import numpy as np
from scipy.io import loadmat

from task_and_baseline import baseline, build_task_helpers, make_bandpass, CENTER, BW


def download_dataset(file_id, output_path):
    if os.path.exists(output_path):
        return

    try:
        gdown.download(id=file_id, output=output_path, quiet=False)
        return
    except TypeError:
        pass

    direct_url = f"https://drive.google.com/uc?id={file_id}"
    gdown.download(url=direct_url, output=output_path, quiet=False)


download_dataset("1BBHVSI4KB-B8OX46eN1Nm4ARCeq6Rui4", "challenge.mat")

data = loadmat("challenge.mat", simplify_cells=True)
tx = data["tx"].astype(np.complex128)
rx = data["rx"].astype(np.complex128)
Fs = float(data["Fs"])
N, _ = tx.shape

tx_n = tx / (np.sqrt(np.mean(np.abs(tx) ** 2, axis=0, keepdims=True)) + 1e-30)
helpers = build_task_helpers(tx_n, Fs, N)
score_kernel = make_bandpass(CENTER, BW, Fs)

RANK1_RIDGE = 1e-4
RANK1_GAMMA = 0.91


def bandpass_matrix(score_filter, matrix):
    return np.column_stack([score_filter(matrix[:, ch]) for ch in range(matrix.shape[1])])


def estimate_rank1_component(band_matrix):
    cov = band_matrix.conj().T @ band_matrix / band_matrix.shape[0]
    _, vecs = np.linalg.eigh(cov)
    steering = vecs[:, -1]
    shared_source = band_matrix @ steering
    denom = np.vdot(shared_source, shared_source) + 1e-30
    weights = np.array(
        [np.vdot(shared_source, band_matrix[:, ch]) / denom for ch in range(band_matrix.shape[1])],
        dtype=np.complex128,
    )
    return shared_source, weights


def deconvolve_same(target, kernel, ridge):
    n = len(target)
    m = len(kernel)
    n_fft = 1 << (n + m - 2).bit_length()
    kernel_padded = np.pad(kernel, (0, n_fft - m))
    kernel_padded = np.roll(kernel_padded, -(m // 2))
    kernel_fft = np.fft.fft(kernel_padded)
    target_fft = np.fft.fft(target, n_fft)
    reg = ridge * np.max(np.abs(kernel_fft) ** 2)
    estimate_fft = target_fft * np.conj(kernel_fft) / (np.abs(kernel_fft) ** 2 + reg)
    return np.fft.ifft(estimate_fft)[:n]


def your_canceller(tx_n, rx):
    fit_tx_prediction = helpers["fit_tx_prediction"]
    score_filter = helpers["score_filter"]

    rx_hat = baseline(tx_n, rx, fit_tx_prediction)
    shared_band, weights = estimate_rank1_component(bandpass_matrix(score_filter, rx_hat))
    shared_pre = deconvolve_same(shared_band, score_kernel, ridge=RANK1_RIDGE)
    rank1_component = shared_pre[:, None] * weights[None, :]
    return rx_hat - RANK1_GAMMA * rank1_component


print("\n=== Baseline ===")
baseline_reds, baseline_avg = helpers["score"](
    rx, baseline(tx_n, rx, helpers["fit_tx_prediction"]), label="baseline"
)

print("=== Your Solution ===")
yours_reds, yours_avg = helpers["score"](rx, your_canceller(tx_n, rx), label="yours")

results = {
    "baseline": {
        "per_channel_db": baseline_reds,
        "average_db": baseline_avg,
    },
    "yours": {
        "per_channel_db": yours_reds,
        "average_db": yours_avg,
    },
}

with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

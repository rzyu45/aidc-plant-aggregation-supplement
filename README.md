# Supplementary material

Companion to **Task-Oriented Modeling of AI Data Center Plants for Resonance Analysis**.

The manuscript is maintained in a separate private repository. This repository contains the supplement source and PDF, the complete 21-state supply-block equations, the electrical and workload parameters, the construction of the single-block equivalent, the definitions of the comparison quantities, the complete saved comparison tables of the full model and the single-block equivalent, and a figure of the internal variables of the two scenarios that the paper does not show.

## Build

Compile locally with TeX Live and `latexmk`.

```sh
latexmk
```

The result is `supplement.pdf`. Intermediate files stay in `build/`.

Regenerate the tables and the figure from the included saved results with Python, NumPy and Matplotlib.

```sh
MPLCONFIGDIR=/tmp/aidc-supplement-mpl python scripts/make_assets.py
latexmk
```

These commands read saved results. They do not build an electrical model or run a simulation. `scripts/make_assets.py` writes Table S3, the tables of Section S4 and Fig. S1, and it checks that every number quoted in the prose of `sections/*.tex` equals the value formatted from the bundled data. It stops when a quoted value and its source disagree.

## Evidence

- `data/design.json` contains full-precision parameters and PI gains for all 12 halls.
- `data/grid_parameters.json` contains the external grid branches, power-base conversion and generator/converter parameter dictionaries.
- `data/scenarios.json` records node counts, task allocation, seeds, phase parameters and source records of both realizations of every scenario.
- `data/operating_points.json`, `data/inference_map.json` and `data/checks.json` record the operating points, the fit of inference power against request rate and the checks of the constructed inputs.
- `data/p5_summary.json` contains every result of the comparison of the full model with the single-block equivalent. `data/p5_registration.json` records the comparison rules, which were fixed before the first result of the equivalent existed.
- `data/full_model_checks.json` contains the model checks, the modal summary and the screening of the task-driven runs of the full model.
- `data/S1_internal.npz` and `data/S3_internal.npz` contain the variables of Fig. S1 at all 24401 saved output instants and the window registered for each scenario.
- `data/source_manifest.json` records the original path and SHA-256 hash of every source and of every data file. `asset_sources.json` records the packaged inputs to the table and figure generator.

In the data files, the suffix `_phase_build` identifies the realization used in the paper and the suffix `_phase_test` the second realization. The model identifier `K01_1f243e` denotes the single-block equivalent and `F` the full model.

The figure arrays retain the saved trajectories without time shifts, smoothing or resampling. The original source papers and raw NLR archives are not included. Dataset DOI is [10.7799/3025227](https://doi.org/10.7799/3025227). This package supports document and figure reproduction. It is not a standalone distribution of the Solverz/SolPSDyn simulation environment.

Section S3.3 explains the local 12-state supply-block subsystem and the remaining AFE/DC-link/grid coupling. The saved comparisons do not isolate inter-block network coupling as the cause of the dominant resonances or of the differences between the two models.

## Note for publication

The git history of this repository still contains the earlier clustering and aggregation material of the supplement, including its group-count comparisons and data files. If those results are to stay private, publish the current tree from a fresh history, for example as a new repository with a single initial commit, and do not push this history. The repository name and the URL that the paper cites also refer to aggregation.

## TeX source convention

Write one prose sentence per source line, including captions and contribution items. Preserve blank lines between paragraphs. Keep equations, table rows and drawing commands in their logical LaTeX structure. Markdown paragraphs remain on one source line.

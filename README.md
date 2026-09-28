# Supplementary material

Companion to **Task-Oriented Modeling and Aggregation of AI Data Center Plants for Resonance Analysis**.

The manuscript is maintained in the separate private repository [aidc-plant-aggregation-paper](https://github.com/rzyu45/aidc-plant-aggregation-paper). This repository contains the supplement source and PDF, the complete 21-state supply-chain equations, electrical and workload parameters, aggregation and error definitions, complete saved comparison tables, and figures that show limitations of the equivalents.

## Build

Compile locally with TeX Live and `latexmk`.

```sh
latexmk
```

The result is `supplement.pdf`. Intermediate files stay in `build/`.

Regenerate the tables and additional figures from the included saved results with Python, NumPy and Matplotlib.

```sh
MPLCONFIGDIR=/tmp/aidc-supplement-mpl python scripts/make_assets.py
latexmk
```

These commands read saved results. They do not build an electrical model or run a simulation.

## Evidence

- `data/design.json` contains full-precision parameters and PI gains for all 12 halls.
- `data/grid_parameters.json` contains the external grid branches, power-base conversion and generator/converter parameter dictionaries.
- `data/scenarios.json` records node counts, task allocation, seeds, phase parameters and source records.
- `data/groups.json` records the fixed memberships and feature scales.
- `data/p2_summary.json` and `data/p3_summary.json` contain the frequency-domain and time-domain results.
- `scripts/make_assets.py` writes every table under `tables/` from these files, including the eigenvalue distances of the modal comparison (`tables/mode_distance.tex`) and the DC-link voltage errors of the representative chains (`tables/internal_errors.tex`).
- `data/S1_K4_selected.npz` and `data/S2_K8_selected.npz` contain selected columns at every saved output instant for the supplemental figures.
- `data/source_manifest.json` records the original paths and SHA-256 hashes. `asset_sources.json` records the packaged inputs to the table and figure generator.

The selected arrays retain the saved trajectories without time shifts, smoothing or resampling. The original source papers and raw NLR archives are not included. Dataset DOI is [10.7799/3025227](https://doi.org/10.7799/3025227). This package supports document and figure reproduction; it is not a standalone distribution of the Solverz/SolPSDyn simulation environment.

Section S3.4 explains the local 12-state supply-chain subsystem and the remaining AFE/DC-link/grid coupling.

## TeX source convention

Write one prose sentence per source line, including captions and contribution items. Preserve blank lines between paragraphs. Keep equations, table rows and drawing commands in their logical LaTeX structure. Markdown paragraphs remain on one source line.

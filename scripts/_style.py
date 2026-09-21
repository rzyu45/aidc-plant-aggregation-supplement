"""Shared matplotlib style for every figure of the replication.

One font family and size set, a colour-blind-safe palette, and helpers so
that every linear axis begins and ends on a tick and every log axis spans
whole decades. Import at the top of each plot script:

    from _style import apply_style, snap_axis, snap_log_axis, save, COL_W, FULL_W
"""
from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

COL_W = 3.45          # IEEEtran column width in inches
FULL_W = 7.16         # IEEEtran text width in inches

# Okabe-Ito palette; fixed roles across the figure set.
C_BLACK = '#1a1a1a'
C_BLUE = '#0072B2'
C_ORANGE = '#D55E00'
C_GREEN = '#009E73'
C_PURPLE = '#CC79A7'
C_YELLOW = '#E69F00'
C_SKY = '#56B4E9'
PALETTE = [C_BLUE, C_ORANGE, C_GREEN, C_PURPLE, C_YELLOW, C_SKY, C_BLACK]

_RC = {
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans'],
    'axes.unicode_minus': False,
    'font.size': 8,
    'axes.labelsize': 8,
    'axes.titlesize': 8,
    'xtick.labelsize': 7,
    'ytick.labelsize': 7,
    'legend.fontsize': 7,
    'axes.linewidth': 0.7,
    'lines.linewidth': 1.1,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.major.width': 0.7,
    'ytick.major.width': 0.7,
    'xtick.major.size': 2.6,
    'ytick.major.size': 2.6,
    'legend.frameon': False,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.01,
    'pdf.fonttype': 42,
}


def apply_style():
    plt.rcParams.update(_RC)


def snap_axis(ax, lo, hi, axis='y', nbins=5):
    """Set ticks so the axis BEGINS and ENDS exactly on a tick while containing [lo, hi]."""
    if hi - lo < 1e-12:
        hi = lo + 1e-12
    ticks = MaxNLocator(nbins=nbins, steps=[1, 2, 2.5, 5, 10]).tick_values(lo, hi)
    if axis == 'y':
        ax.set_yticks(ticks)
        ax.set_ylim(ticks[0], ticks[-1])
    else:
        ax.set_xticks(ticks)
        ax.set_xlim(ticks[0], ticks[-1])


def snap_log_axis(ax, lo, hi, axis='x'):
    """Log axis spanning whole decades that contain [lo, hi]."""
    d0 = int(np.floor(np.log10(lo)))
    d1 = int(np.ceil(np.log10(hi)))
    ticks = [10.0 ** d for d in range(d0, d1 + 1)]
    if axis == 'x':
        ax.set_xscale('log')
        ax.set_xticks(ticks)
        ax.set_xlim(ticks[0], ticks[-1])
    else:
        ax.set_yscale('log')
        ax.set_yticks(ticks)
        ax.set_ylim(ticks[0], ticks[-1])


def padded_limits(series, frac=0.08, clamp_zero=False):
    """Data limits with symmetric padding; optionally no dead space below zero."""
    lo = min(float(np.min(s)) for s in series)
    hi = max(float(np.max(s)) for s in series)
    pad = frac * (hi - lo) if hi > lo else 0.1
    lo_p, hi_p = lo - pad, hi + pad
    if clamp_zero and lo >= 0.0 > lo_p:
        lo_p = 0.0
    return lo_p, hi_p


def save(fig, stem):
    """Write <stem>.pdf and <stem>.png at 300 dpi and close the figure."""
    for ext in ('pdf', 'png'):
        fig.savefig(f'{stem}.{ext}', dpi=300)
    plt.close(fig)
    print(f'  -> {stem}.pdf / .png')

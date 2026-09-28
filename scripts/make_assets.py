"""Generate the tables and the figure of the supplement from the saved evidence bundled with this repository.

Nothing is simulated and no model is built. Every number of a generated table is read from ``data/``. Every number
that the prose of ``sections/*.tex`` quotes is formatted from the same files by ``claims`` and must appear verbatim
in the named section file, so the script stops when a quoted value and its source disagree.

    MPLCONFIGDIR=/tmp/aidc-supplement-mpl python scripts/make_assets.py
"""
from pathlib import Path
import hashlib
import json
import math

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

from _style import C_BLACK, C_PURPLE, apply_style, plt, save, snap_axis

R = Path(__file__).resolve().parent.parent
D, T, F, S = R / 'data', R / 'tables', R / 'figures', R / 'sections'
TEXT_W = 166 / 25.4                      # text width of supplement.tex, A4 with 22 mm margins, in inches
SCEN = ('S1', 'S2', 'S3')
REAL = (('build', 'paper'), ('test', 'second'))          # data suffix, label of the realization in the tables
OUT = ('P_MW', 'Q_Mvar', 'V_pu', 'f_Hz')
BLOCK_VARS = ('v_dc', 'v_ac', 'v_psu', 'v_eq', 'i_afe')  # block variables with a ratio of equivalent to largest hall
INTERNAL_ROWS = (('p_it_mw', 'Server power', r'$P_{{\rm IT},h}$', 'MW'), ('p_ac_mw', 'AC input power', r'$P_{{\rm AC},h}$', 'MW'),
                 ('v_dc', 'DC-link voltage', r'$v_d$', 'p.u.'), ('v_ac', 'VSI output voltage', r'$|\bm v_v|$', 'p.u.'),
                 ('v_psu', 'PSU output voltage', r'$v_p$', 'p.u.'), ('v_eq', 'Server voltage', r'$v_e$', 'p.u.'),
                 ('i_afe', 'AFE current', r'$|\bm i_a|$', 'p.u.'))
FIGURE = ('S1', 'S3')                    # the paper shows S2 in its Fig. 4
PANELS = (('p_it_mw', r'$P_{\mathrm{IT},h}$ / MW'), ('p_ac_mw', r'$P_{\mathrm{AC},h}$ / MW'), ('dP', r'$\Delta P_\mathrm{PCC}$ / MW'),
          ('v_dc', r'$v_d$ / p.u.'), ('v_psu', r'$v_p$ / p.u.'), ('v_eq', r'$v_e$ / p.u.'))
HALL_GREY = '0.72'


def js(name):
    return json.loads((D / name).read_text())


def num(x, d):
    """Fixed-point number with a typeset minus sign."""
    s = f'{x:.{d}f}'
    return '$-$' + s[1:] if s.startswith('-') else s


def pct(x, d=2):
    return num(100 * x, d)


def sci(x, d=1):
    """``a\\cdot10^{b}`` with ``d`` decimals of the mantissa, rounded to nearest."""
    m, e = f'{x:.{d}e}'.split('e')
    return rf'{m}\cdot10^{{{int(e)}}}'


def up(x, d):
    """Round up to ``d`` decimals, for a stated upper bound."""
    return f'{math.ceil(x * 10 ** d - 1e-9) / 10 ** d:.{d}f}'


def down(x, d):
    """Round down to ``d`` decimals, for a stated lower bound."""
    return f'{math.floor(x * 10 ** d + 1e-9) / 10 ** d:.{d}f}'


def task_label(t):
    return dict(train='training', tune='fine-tuning', infer='inference').get(t, t.replace('job', 'job '))


def inputs(scenarios=SCEN):
    return [(sc, sp, lab, f'{sc}_phase_{sp}') for sc in scenarios for sp, lab in REAL]


def write(name, body):
    (T / name).write_text(body)


# ----------------------------------------------------------------------
# tables
# ----------------------------------------------------------------------
def tables(p5):
    design = js('design.json'); rows = []
    for h in design['halls']:
        v = h['values']
        rows.append(' & '.join([str(h['hall'] + 1)] + [f'{v[k]:.2f}' for k in ('fbw_pll', 'fbw_dc', 'fbw_v_vsi', 'fbw_v_psu', 'feeder_km', 'tx_z_pct')]) + r' \\')
    write('hall_design.tex', r'''\begin{table}[H]
\centering\small
\caption{Hall Design Summary.
Frequencies in Hz, Feeder Length in km, Transformer Impedance in Percent.}
\label{tab:hall-design}
\begin{tabular}{rrrrrrr}\toprule
Hall & PLL & AFE voltage & VSI voltage & PSU voltage & Feeder & Transformer\\\midrule
''' + '\n'.join(rows) + r'''
\bottomrule\end{tabular}\end{table}
''')

    rows = []
    for sc in SCEN:
        for t in p5['paper']['rows'][f'{sc}_phase_build']['tasks']:
            for i, (_, sp, lab, n) in enumerate(inputs((sc,))):
                r = p5['paper']['rows'][n]['tasks'][t]
                cells = [sc if i == 0 else '', task_label(t) if i == 0 else '', lab, pct(r['band_P_low']), pct(r['band_P_high']),
                         num(r['peak_gain_F'], 3), num(r['f_peak_F'], 2), num(r['peak_gain_E'], 3), num(r['f_peak_E'], 2),
                         num(r['phase_diff_deg'], 1)]
                rows.append(' & '.join(cells) + (r' \\*' if i == 0 else r' \\'))
        rows.append(r'\midrule')
    head = r'''\toprule
 & & & \multicolumn{2}{c}{Band error, \%} & \multicolumn{2}{c}{Full model peak} & \multicolumn{2}{c}{Equivalent peak} & Phase\\
Scenario & Task & Realization & 0.1--3 Hz & 3--20 Hz & Gain & Hz & Gain & Hz & deg\\\midrule'''
    write('band_tasks.tex', r'''{\small\setlength{\tabcolsep}{4.5pt}\setlength{\LTcapwidth}{\textwidth}
\begin{longtable}{lllrrrrrrr}
\caption{Task-to-PCC Active-Power Comparison for Every Task and Both Realizations.
Paper Denotes the Realization Used in the Paper.
The Six Jobs of S2 Are Training Jobs.}\label{tab:task-band}\\
''' + head + r'''
\endfirsthead
''' + head + r'''
\endhead
''' + '\n'.join(rows[:-1]) + r'''
\bottomrule\end{longtable}}
''')

    rows = []
    for sc, sp, lab, n in inputs():
        po = p5['ss'][n]['per_output']
        rows.append(' & '.join([sc, lab] + [pct(po[z][b]) for z in OUT for b in ('low', 'high')]) + r' \\')
    write('band_outputs.tex', r'''\begin{table}[H]
\centering\small\setlength{\tabcolsep}{4.5pt}
\caption{Largest Band Error over the Jobs of Each Realization for the Four Outputs, in Percent.
Bands in Hz.}
\label{tab:output-band}
\begin{tabular}{llrrrrrrrr}\toprule
 & & \multicolumn{2}{c}{Active power} & \multicolumn{2}{c}{Reactive power} & \multicolumn{2}{c}{PCC voltage} & \multicolumn{2}{c}{Machine frequency}\\
Scenario & Realization & 0.1--3 & 3--20 & 0.1--3 & 3--20 & 0.1--3 & 3--20 & 0.1--3 & 3--20\\\midrule
''' + '\n'.join(rows) + r'''
\bottomrule\end{tabular}\end{table}
''')

    cols = inputs()
    rows = [' & '.join([str(h + 1)] + [pct(p5['ss'][n]['direction']['single_hall_high'][h]) for *_, n in cols]) + r' \\' for h in range(12)]
    rows.append(r'\midrule')
    rows.append(' & '.join(['uniform'] + [pct(p5['ss'][n]['direction']['uniform_high']) for *_, n in cols]) + r' \\')
    write('band_halls.tex', r'''\begin{table}[H]
\centering\small
\caption{PCC Active-Power Band Error over 3--20 Hz, in Percent, for a Unit Input in One Hall and for the Same Input Spread Evenly over All Halls}
\label{tab:hall-band}
\begin{tabular}{lrrrrrr}\toprule
 & \multicolumn{2}{c}{S1} & \multicolumn{2}{c}{S2} & \multicolumn{2}{c}{S3}\\
Input & Paper & Second & Paper & Second & Paper & Second\\\midrule
''' + '\n'.join(rows) + r'''
\bottomrule\end{tabular}\end{table}
''')

    rows = []
    for sc, sp, lab, n in inputs():
        m = p5['paper']['rows'][n]['modes']; e = sorted(m['E'], key=lambda r: r['f_hz'])
        rows.append(' & '.join([sc, lab, str(m['n_F']), f"{num(m['F_f_range'][0], 2)}--{num(m['F_f_range'][1], 2)}",
                                f"{num(m['F_zeta_range'][0], 3)}--{num(m['F_zeta_range'][1], 3)}", str(m['n_E']),
                                ', '.join(num(r['f_hz'], 2) for r in e), ', '.join(num(r['zeta'], 3) for r in e)]) + r' \\')
    write('modes.tex', r'''\begin{table}[H]
\centering\small\setlength{\tabcolsep}{4.5pt}
\caption{Modes between 3 and 20 Hz That Reach 10\% of the Largest Contribution of the Full Model}
\label{tab:modes}
\begin{tabular}{llrllrll}\toprule
 & & \multicolumn{3}{c}{Full model} & \multicolumn{3}{c}{Single-block equivalent}\\
Scenario & Realization & Modes & Frequency, Hz & Damping ratio & Modes & Frequency, Hz & Damping ratio\\\midrule
''' + '\n'.join(rows) + r'''
\bottomrule\end{tabular}\end{table}
''')

    rows = []
    for sc, sp, lab, n in inputs():
        t = p5['td'][n]; sh = t['error_spectrum_P']['shares']
        rows.append(' & '.join([sc, lab] + [pct(t[z]['rms_rel']) for z in OUT] +
                               [num(1e3 * t['P_MW']['b0'], 2), num(1e3 * t['Q_Mvar']['b0'], 2), num(1e6 * t['V_pu']['b0'], 2),
                                pct(sh['f3_to_6'] + sh['f6_to_9'], 1)]) + r' \\')
    write('dynamic.tex', r'''\begin{table}[H]
\centering\small\setlength{\tabcolsep}{4.5pt}
\caption{Dynamic Errors of the Four Outputs, Initial Offsets and Share of the Active-Power Error Variance between 3 and 9 Hz}
\label{tab:dynamic}
\begin{tabular}{llrrrrrrrr}\toprule
 & & \multicolumn{4}{c}{Dynamic error, \%} & \multicolumn{3}{c}{Initial offset $b_0$} & Share\\
Scenario & Realization & $P$ & $Q$ & $V$ & $f$ & $P$, kW & $Q$, kvar & $V$, $10^{-6}$ p.u. & 3--9 Hz, \%\\\midrule
''' + '\n'.join(rows) + r'''
\bottomrule\end{tabular}\end{table}
''')

    rows = []
    for sc in SCEN:
        q = p5['internal'][f'{sc}_phase_build']
        for i, (v, name, sym, unit) in enumerate(INTERNAL_ROWS):
            f_, e_ = q['F'][v], q['E'][v]; d = 3 if unit == 'MW' else 4
            ratio = q['equivalent_over_largest_hall'].get(v)
            cells = [sc if i == 0 else '', f'{name} {sym}', unit, str(f_['hall_of_largest'] + 1), num(f_['largest_peak_dev'], d),
                     f"{num(min(f_['peak_dev']), d)}--{num(max(f_['peak_dev']), d)}",
                     '---' if ratio is None else num(e_['largest_peak_dev'], d), '---' if ratio is None else num(ratio, 3)]
            rows.append(' & '.join(cells) + r' \\')
        rows.append(r'\midrule')
    write('internal.tex', r'''\begin{table}[tbp]
\centering\small\setlength{\tabcolsep}{4.5pt}
\caption{Peak Deviations of Internal Variables in the Realization Used in the Paper.
Per-Unit Values on the Block Base.}
\label{tab:internal}
\begin{tabular}{lllrrlrr}\toprule
 & & & \multicolumn{3}{c}{Full model} & & \\
Scenario & Quantity & Unit & Hall & Largest & Range over halls & Equivalent & Ratio\\\midrule
''' + '\n'.join(rows[:-1]) + r'''
\bottomrule\end{tabular}\end{table}
''')


# ----------------------------------------------------------------------
# figure
# ----------------------------------------------------------------------
def window_axis(w):
    """The registered window, widened to the nearest ticks as in Fig. 4 of the paper."""
    ticks = MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5, 10]).tick_values(*w)
    return float(ticks[0]), float(ticks[-1])


def figure_data(sc):
    z = np.load(D / f'{sc}_internal.npz')
    a, b = window_axis(z['window_input_s'])
    t = z['t'] - float(z['t_on_s']); k = (t >= a) & (t <= b)
    dv = np.abs(z['F_v_dc'][k] - z['F_v_dc'][0][None, :]).max(axis=0)
    return z, t, k, (a, b), int(np.argmax(dv))


def plots():
    fig, axes = plt.subplots(len(PANELS), len(FIGURE), figsize=(TEXT_W, 5.3), sharex='col',
                             gridspec_kw=dict(hspace=0.3, wspace=0.2))
    fig.subplots_adjust(left=0.085, right=0.99, top=0.9, bottom=0.075)
    for col, sc in enumerate(FIGURE):
        z, t, k, (a, b), hot = figure_data(sc)
        for row, (var, lab) in enumerate(PANELS):
            ax = axes[row, col]
            if var == 'dP':
                x, e = z['F_P_MW'] - z['F_P_MW'][0], z['E_P_MW'] - z['E_P_MW'][0]
                ax.plot(t[k], x[k], color=C_BLACK, lw=1.0)
                ax.plot(t[k], e[k], color=C_PURPLE, ls='--', lw=1.0)
                lo, hi = min(x[k].min(), e[k].min()), max(x[k].max(), e[k].max())
            else:
                x = z['F_' + var]
                for h in range(x.shape[1]):
                    if h != hot:
                        ax.plot(t[k], x[k, h], color=HALL_GREY, lw=0.6)
                ax.plot(t[k], x[k, hot], color=C_BLACK, lw=1.0)
                lo, hi = x[k].min(), x[k].max()
                if 'E_' + var in z.files:                    # the equivalent has the plant total, not a hall power
                    e = z['E_' + var]
                    ax.plot(t[k], e[k], color=C_PURPLE, ls='--', lw=1.0)
                    lo, hi = min(lo, e[k].min()), max(hi, e[k].max())
            snap_axis(ax, lo, hi, axis='y', nbins=3)
            if col == 0:
                ax.set_ylabel(lab)
            ax.text(1.0, 1.03, f'({chr(97 + row)})', transform=ax.transAxes, va='bottom', ha='right', fontsize=7)
        snap_axis(axes[-1, col], a, b, axis='x', nbins=5)
        axes[-1, col].set_xlabel('time in the task window / s')
        axes[0, col].set_title(sc)
    fig.align_ylabels(axes[:, 0])
    handles = [Line2D([], [], color=C_BLACK, lw=1.0, label='full model'), Line2D([], [], color=HALL_GREY, lw=0.8, label='other halls'),
               Line2D([], [], color=C_PURPLE, ls='--', lw=1.0, label='single-block equivalent')]
    fig.legend(handles=handles, loc='upper center', ncol=3, bbox_to_anchor=(0.5, 1.0), columnspacing=1.6, handlelength=2.2)
    save(fig, str(F / 'internal_variables'))


# ----------------------------------------------------------------------
# prose numbers
# ----------------------------------------------------------------------
def claims(p5, fm):
    """(section file, text that must appear in it), every value formatted from the bundled data."""
    ss, td, q, g = p5['ss'], p5['td'], p5['internal'], p5['gates']
    ALL = [n for *_, n in inputs()]
    BUILD = [f'{sc}_phase_build' for sc in SCEN]
    c = []
    # electrical and methods
    c += [('electrical', rf"$N=48$ blocks and {p5['paper']['n_states']['F']} states"),
          ('electrical', rf"$N=1$ and {p5['paper']['n_states']['E']} states")]
    assert 37 + 21 * 48 == p5['paper']['n_states']['F'] and 37 + 21 == p5['paper']['n_states']['E']
    rating = {round(1.0 / g[n]['hall_matrix']['min'], 9) for n in ALL}
    assert len(rating) == 1 and all(g[n]['hall_matrix']['every_hall_to_the_block'] for n in ALL)
    c.append(('methods', f'which is {rating.pop():.0f}~MVA for the 48 blocks'))
    gains = [k for k in js('design.json')['halls'][0]['params'] if k.startswith(('kp_', 'ki_'))]
    c.append(('methods', f'and the {len(gains)} PI gains'))
    ctl = p5['control']
    assert ctl['passed'] and abs(ctl['F']['terminal_target_mw'] / 12 - 6.0) < 1e-12
    c += [('methods', f"a server power of {ctl['F']['terminal_target_mw'] / 12:.0f}~MW"),
          ('methods', f"Over {ctl['frequencies']} frequencies"),
          ('methods', rf"is at most ${sci(ctl['normalized_difference'])}$")]
    assert ctl['normalized_difference'] <= float(sci(ctl['normalized_difference']).replace(r'\cdot10^{', 'e').rstrip('}'))
    # task-to-PCC response
    infer = [ss[n]['tasks']['infer']['P_high'] for n in ALL]
    c.append(('validation', f'ranges from {pct(min(infer))}\\% to {pct(max(infer))}\\%'))
    c.append(('validation', 'is ' + ', '.join(f"{pct(ss[n]['all_high'])}\\%" for n in BUILD[:2]) + f" and {pct(ss[BUILD[2]]['all_high'])}\\% for S1, S2 and S3"))
    arg = {n: max(OUT, key=lambda z: ss[n]['per_output'][z]['high']) for n in BUILD}
    assert arg == {'S1_phase_build': 'Q_Mvar', 'S2_phase_build': 'V_pu', 'S3_phase_build': 'Q_Mvar'}, arg
    c.append(('validation', 'The reactive power gives this value in S1 and S3, and the PCC voltage in S2.'))
    gap = max(abs(ss[f'{sc}_phase_build']['tasks'][t]['band'][z][b] - ss[f'{sc}_phase_test']['tasks'][t]['band'][z][b])
              for sc in SCEN for t in ss[f'{sc}_phase_build']['tasks'] for z in OUT for b in ('low', 'high'))
    c.append(('validation', f'by at most {up(100 * gap, 2)} percentage points'))
    single = [x for n in ALL for x in ss[n]['direction']['single_hall_high']]
    uni = [ss[n]['direction']['uniform_high'] for n in ALL]
    c += [('validation', f'band errors from {pct(min(single))}\\% to {pct(max(single))}\\%'),
          ('validation', f'the uniform input gives {pct(min(uni))}\\% to {pct(max(uni))}\\%')]
    assert all(int(np.argmax(ss[n]['direction']['single_hall_high'])) == 0 and int(np.argmin(ss[n]['direction']['single_hall_high'])) == 11 for n in ALL)
    c.append(('validation', 'Hall~1 gives the largest and hall~12 the smallest single-hall error at every operating point.'))
    nF = [p5['paper']['rows'][n]['modes']['n_F'] for n in ALL]
    nE = {sc: {p5['paper']['rows'][f'{sc}_phase_{sp}']['modes']['n_E'] for sp, _ in REAL} for sc in SCEN}
    assert nE == {'S1': {3}, 'S2': {1}, 'S3': {3}}, nE
    c.append(('validation', f'The full model has {min(nF)} to {max(nF)} such modes, whereas the equivalent has one in S2 and three in S1 and S3.'))
    # time domain
    P = [td[n]['P_MW']['rms_rel'] for n in ALL]
    c.append(('validation', f'ranges from {pct(min(P))}\\% to {pct(max(P))}\\%'))
    for sp, _ in REAL:
        for z in OUT:
            assert max(SCEN, key=lambda sc: td[f'{sc}_phase_{sp}'][z]['rms_rel']) == 'S2'
    c.append(('validation', 'S2 gives the largest error of every output in both realizations'))
    b0 = [-1e3 * td[n]['P_MW']['b0'] for n in ALL]
    assert min(b0) > 0
    c.append(('validation', f'between {num(min(b0), 2)} and {num(max(b0), 2)}~kW below'))
    assert all(td[n]['f_Hz']['b0'] == 0.0 for n in ALL)
    c.append(('validation', 'The initial frequency offset is zero in every run.'))
    share = [td[n]['error_spectrum_P']['shares']['f3_to_6'] + td[n]['error_spectrum_P']['shares']['f6_to_9'] for n in ALL]
    c.append(('validation', f'Between {pct(min(share), 1)}\\% and {pct(max(share), 1)}\\% of the variance'))
    st = p5['strict']; assert st['input'] == 'S2_phase_build'
    c += [('validation', f"is then {pct(st['P_MW']['rms_rel_strict'], 4)}\\%, against {pct(st['P_MW']['rms_rel_production'], 4)}\\%"),
          ('validation', f"a difference of {pct(st['P_MW']['difference'], 4)} percentage points"),
          ('validation', f"the other three outputs is {pct(max(st[z]['difference'] for z in OUT[1:]), 4)} percentage points")]
    # internal variables
    ratio = {sc: [q[f'{sc}_phase_build']['equivalent_over_largest_hall'][v] for v in BLOCK_VARS] for sc in SCEN}
    c.append(('validation', f"from {num(min(ratio['S2']), 2)} to {num(max(ratio['S2']), 2)} in S2 and from "
                            f"{num(min(ratio['S1'] + ratio['S3']), 2)} to {num(max(ratio['S1'] + ratio['S3']), 2)} in S1 and S3"))
    assert all(r < 1 for rs in ratio.values() for r in rs)
    for sc in SCEN:
        for v in BLOCK_VARS:
            e, pk = q[f'{sc}_phase_build']['E'][v]['largest_peak_dev'], q[f'{sc}_phase_build']['F'][v]['peak_dev']
            assert (e < min(pk)) if sc == 'S2' else (min(pk) <= e <= max(pk)), (sc, v)
    fac = [q[n]['F']['p_ac_mw']['largest_peak_dev'] / q[n]['F']['p_it_mw']['largest_peak_dev'] for n in BUILD]
    c.append(('validation', f'by a factor of {min(fac):.1f} to {max(fac):.1f} in every scenario'))
    for sc in FIGURE:
        z = np.load(D / f'{sc}_internal.npz')
        c.append(('validation', f"${num(float(z['jump_mw']), 2).replace('$', '')}$~MW at {float(z['t_star_input_s']):.2f}~s in {sc}"))
        w, ts = z['window_input_s'], float(z['t_star_input_s'])
        assert abs(w[0] - (ts - 0.5)) < 1e-12 and abs(w[1] - (ts + 1.5)) < 1e-12
    c.append(('validation', 'The window begins 0.5~s before the phase transition with the largest step of the total server power and ends 1.5~s after it'))
    hot = {sc: figure_data(sc)[4] + 1 for sc in FIGURE}
    c.append(('validation', f"which is hall~{hot['S1']} in S1 and hall~{hot['S3']} in S3"))
    # numerical checks
    assert all(g[n]['passed'] for n in ALL) and all(fm['gates'][n]['passed'] for n in BUILD)
    assert {(g[n]['eqn_size'], g[n]['vsize']) for n in ALL} == {(179, 179)}
    assert {(fm['gates'][n]['eqn_size'], fm['gates'][n]['vsize']) for n in BUILD} == {(1873, 1873)} and {fm['F'][n]['vsize'] for n in ALL} == {1873}
    c.append(('validation', 'The equivalent has 179 equations and variables, and the full model has 1873.'))
    res_e, res_f = max(g[n]['residual'] for n in ALL), max(fm['F'][n]['residual'] for n in ALL)
    c.append(('validation', f'the largest initial residual is ${sci(res_e)}$ for the equivalent and ${sci(res_f)}$ for the full model.'))
    term = max(g[n]['terminal_error_mw'] for n in ALL)
    c.append(('validation', rf"within ${sci(term)}$~MW"))
    assert term <= float(f'{term:.1e}') and all(g[n]['static_loads_equal'] for n in ALL)
    assert {g[n]['flat_run']['t_end'] for n in ALL} == {fm['gates'][n]['flat_run']['t_end'] for n in BUILD} == {2.0}
    c.append(('validation', 'A two-second run without input checks that each operating point is an equilibrium.'))
    drift_e, drift_f = max(g[n]['flat_run']['max_drift'] for n in ALL), max(fm['gates'][n]['flat_run']['max_drift'] for n in BUILD)
    c += [('validation', f'The largest change of any variable of the equivalent is ${sci(drift_e)}$'),
          ('validation', f'and that of the full model is ${sci(drift_f)}$')]
    assert all(ss[n]['stable'] and ss[n]['stable_F'] and fm['F'][n]['stable'] and fm['F'][n]['zero_modes'] == 1 for n in ALL)
    mr = {num(fm['F'][n]['max_real'], 3) for n in ALL}; assert len(mr) == 1
    c.append(('validation', f"is ${mr.pop().replace('$', '')}$~s$^{{-1}}$"))
    c.append(('validation', f"The largest normalized distance is ${sci(ctl['eig_of_E_missing_in_F'])}$"))
    det = [q[n][k]['determinism'] for n in BUILD for k in ('gates_F', 'gates_K01_1f243e')]
    assert all(d['passed'] and d['same_grid'] and d['P_MW_max_abs'] == 0.0 and d['v_dc_max_abs'] == 0.0 for d in det)
    c.append(('validation', 'with zero difference in the PCC active power and in the DC-link voltage at every output instant'))
    spread = max(max(q[n]['gates_F']['hall_spread'].values()) for n in BUILD)
    assert spread <= float(f'{spread:.1e}')
    c.append(('validation', rf'within ${sci(spread)}$'))
    sf = fm['screen_F']
    c.append(('validation', f"current below {up(max(sf[n]['i_max'] for n in ALL), 3)}~p.u., every modulation index below "
                            f"{up(max(sf[n]['m_ratio_max'] for n in ALL), 3)} times its operating-point value and the DC-link voltage between "
                            f"{down(min(sf[n]['v_dc'][0] for n in ALL), 3)} and {up(max(sf[n]['v_dc'][1] for n in ALL), 3)}~p.u."))
    assert all(sf[n]['status'] == 'complete' and sf[n]['t_reached'] == 61.0 for n in ALL)
    return c


def check_prose(p5, fm):
    text = {p.stem: ' '.join(p.read_text().split()) for p in S.glob('*.tex')}
    bad = [(sec, s) for sec, s in claims(p5, fm) if ' '.join(s.split()) not in text[sec]]
    for sec, s in bad:
        print(f'  MISSING in sections/{sec}.tex: {s}')
    if bad:
        raise SystemExit(f'{len(bad)} quoted values do not match the bundled data')
    print(f'  {len(claims(p5, fm))} quoted values match the bundled data')


if __name__ == '__main__':
    T.mkdir(exist_ok=True); F.mkdir(exist_ok=True); apply_style()
    p5, fm = js('p5_summary.json'), js('full_model_checks.json')
    tables(p5); plots(); check_prose(p5, fm)
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(D.iterdir()) if p.is_file()}
    (R / 'asset_sources.json').write_text(json.dumps(manifest, indent=2) + '\n')

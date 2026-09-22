"""Generate tables and plots from the saved evidence bundled with this repository."""
from pathlib import Path
import json
import hashlib
import numpy as np
from _style import apply_style, plt, snap_axis, save, FULL_W, C_BLACK, C_BLUE, C_ORANGE
R=Path(__file__).resolve().parent.parent
D=R/'data'; T=R/'tables'; F=R/'figures'
def js(n):return json.loads((D/n).read_text())

def tables():
    design=js('design.json');rows=[]
    for h in design['halls']:
        v=h['values'];rows.append(' & '.join([str(h['hall']+1)]+[f'{v[k]:.2f}' for k in ('fbw_pll','fbw_dc','fbw_v_vsi','fbw_v_psu','feeder_km','tx_z_pct')])+r' \\')
    body=r'''\begin{table}[H]
\centering\small
\caption{Hall Design Summary.
Frequencies in Hz, Feeder Length in km, Transformer Impedance in Percent.}
\label{tab:hall-design}
\begin{tabular}{rrrrrrr}\toprule
Hall & PLL & AFE voltage & VSI voltage & PSU voltage & Feeder & Transformer\\\midrule
'''+ '\n'.join(rows)+r'''
\bottomrule\end{tabular}\end{table}
'''
    (T/'hall_design.tex').write_text(body)
    p2=js('p2_summary.json');rows=[]
    for sc in ('S1','S2','S3'):
        for K in (2,4,6,8,10,12):
            r=[sc,str(K)]
            for cfg in ('param_fixed','resp_fixed'):
                a=p2['table'][f'{cfg}|{sc}|{K}'];r += [f"{100*a[sp]['P_high']:.2f}" for sp in ('build','test')]
            rows.append(' & '.join(r)+r' \\')
        rows.append(r'\midrule')
    (T/'band_errors.tex').write_text(r'''\begin{longtable}{llrrrr}
\caption{Worst-Task PCC Active-Power Band Errors in Percent over 3--20 Hz}\label{tab:all-band}\\
\toprule
 & & \multicolumn{2}{c}{Parameter features} & \multicolumn{2}{c}{Response features}\\
Scenario & $K$ & Grouping & Test & Grouping & Test\\\midrule\endfirsthead
\toprule Scenario & $K$ & Parameter grouping & Parameter test & Response grouping & Response test\\\midrule\endhead
'''+ '\n'.join(rows[:-1])+r'''
\bottomrule\end{longtable}
''')
    p3=js('p3_summary.json');rows=[]
    for sc in ('S1','S2','S3'):
        for lab,v in p3['table2'][sc]['equivalents'].items():
            for sp in ('build','test'):
                q=p3['td'][f'{sc}_phase_{sp}'][lab]
                values=[sc,lab.replace('_',r'\_'),'grouping' if sp=='build' else 'test']
                values += [f"{q['P_MW']['b0']:.5f}",f"{q['P_MW']['rms_abs']:.5f}",f"{100*q['P_MW']['rms_rel']:.3f}",f"{100*q['Q_Mvar']['rms_rel']:.3f}"]
                rows.append(' & '.join(values)+r' \\')
    (T/'time_errors.tex').write_text(r'''\begin{longtable}{lllrrrr}
\caption{PCC Errors, Including Initial Active-Power Offset}\label{tab:all-time}\\
\toprule Scenario & Model & Input & $P_0$ offset & $P$ RMS error & $P$ relative & $Q$ relative\\
 & & & MW & MW & \% & \%\\\midrule\endfirsthead
\toprule Scenario & Model & Input & $P_0$ offset & $P$ RMS error & $P$ relative & $Q$ relative\\
 & & & MW & MW & \% & \%\\\midrule\endhead
'''+ '\n'.join(rows)+r'''
\bottomrule\end{longtable}
''')


def plots():
    styles={'F':dict(color=C_BLACK,ls='-',label='full plant'),'param':dict(color=C_ORANGE,ls='--',label='parameter features'),'resp':dict(color=C_BLUE,ls='-.',label='response features')}
    z=np.load(D/'S1_K4_selected.npz');t=z['t']-1
    fig,axes=plt.subplots(3,2,figsize=(FULL_W,4.25),gridspec_kw=dict(hspace=.22,wspace=.22))
    summ=js('p3_summary.json');zoom=summ['zoom']['S1_phase_build']['window_input_s']
    from matplotlib.ticker import MaxNLocator
    for col,window in enumerate([(0,20),zoom]):
        ticks=MaxNLocator(nbins=4,steps=[1,2,2.5,5,10]).tick_values(*window);a,b=ticks[0],ticks[-1];k=(t>=a)&(t<=b)
        for row,q in enumerate(['P_MW','v_dc','error']):
            vals=[]
            for role,st in styles.items():
                if q=='error':
                    if role=='F':continue
                    y=(z[role+'_P_MW']-z[role+'_P_MW'][0])-(z['F_P_MW']-z['F_P_MW'][0])
                else:y=z[role+'_'+q]
                vals.append(y[k]);axes[row,col].plot(t[k],y[k],**st,lw=.8 if col==0 else 1.1)
            snap_axis(axes[row,col],min(v.min() for v in vals),max(v.max() for v in vals),nbins=4)
            snap_axis(axes[row,col],a,b,axis='x',nbins=4)
            if col==0:axes[row,col].set_ylabel(['PCC power / MW','DC-link voltage / p.u.','dynamic P error / MW'][row])
            if row<2:plt.setp(axes[row,col].get_xticklabels(),visible=False)
        axes[2,col].set_xlabel('time in task window / s')
    axes[0,0].set_title('S1, K = 4, grouping input');axes[0,1].set_title('Common event window')
    h,l=axes[0,0].get_legend_handles_labels();fig.legend(h,l,loc='lower center',ncol=3,bbox_to_anchor=(.5,-.035))
    save(fig,str(F/'internal_voltage'))
    z=np.load(D/'S2_K8_selected.npz');t=z['t']-1;k=(t>=0)&(t<=20)
    fig,axes=plt.subplots(2,1,figsize=(FULL_W,2.7),sharex=True,gridspec_kw=dict(hspace=.14))
    vals=[]
    for role,st in styles.items():
        y=z[role+'_P_MW'];axes[0].plot(t[k],y[k],**st,lw=.8);vals.append(y[k])
        if role!='F':axes[1].plot(t[k],((y-y[0])-(z['F_P_MW']-z['F_P_MW'][0]))[k],**st,lw=.8)
    snap_axis(axes[0],min(v.min() for v in vals),max(v.max() for v in vals),nbins=4)
    e=[((z[r+'_P_MW']-z[r+'_P_MW'][0])-(z['F_P_MW']-z['F_P_MW'][0]))[k] for r in ('param','resp')]
    snap_axis(axes[1],min(v.min() for v in e),max(v.max() for v in e),nbins=4);snap_axis(axes[1],0,20,axis='x',nbins=5)
    axes[0].set_ylabel('PCC power / MW');axes[1].set_ylabel('dynamic P error / MW');axes[1].set_xlabel('time in task window / s')
    h,l=axes[0].get_legend_handles_labels();fig.legend(h,l,loc='lower center',ncol=3,bbox_to_anchor=(.5,-.13))
    save(fig,str(F/'similar_accuracy'))
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.iterdir() if p.is_file()}
    (R/'asset_sources.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':
    T.mkdir(exist_ok=True);F.mkdir(exist_ok=True);apply_style();tables();plots()

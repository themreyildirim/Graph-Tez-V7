"""Kabul edilmiş notebook'u yeni QA konumuna yönlendirip altı grafiği karşılaştırır."""
import base64,contextlib,io
from pathlib import Path
from unittest.mock import patch
import nbformat
import numpy as np
import pandas as pd
from PIL import Image
from wp11_close_audit import ROOT,C,G,csv,preserve
from wp11_linear_shap import sha,write_json


def pixels(value):
    with Image.open(value) as picture:return np.asarray(picture.convert('RGBA')).copy()


def run():
    if (C/'image_data_checks.csv').exists():raise RuntimeError('Image verification already exists')
    preserve()
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    import IPython.display
    from wp11_graph_forward import torch
    nbpath=ROOT/'notebooks/WP11_A1P1_graph_explanations.ipynb';nb=nbformat.read(nbpath,as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code'];assert len(code)==9 and all(c.execution_count for c in code)
    allout=[o for c in code for o in c.outputs];assert not any(o.output_type=='error' for o in allout)
    embedded=[pixels(io.BytesIO(base64.b64decode(o['data']['image/png']))) for o in allout if 'image/png' in o.get('data',{})];assert len(embedded)==6
    oldroot=(ROOT/'reports/figures/WP11/graph_v1').resolve();dest=C/'figure_reconstruction';dest.mkdir(exist_ok=False)
    oldsave=Figure.savefig;oldmkdir=Path.mkdir;rows=[];embedded_new=[];displays=[]
    def save(fig,fname,*args,**kwargs):
        actual=Path(fname).resolve();assert actual.parent==oldroot and actual.suffix=='.png','Unexpected notebook write'
        out=dest/actual.name;oldsave(fig,out,*args,**kwargs)
        a,b=pixels(actual),pixels(out);assert a.shape==b.shape
        rows.append({'figure':actual.name,'original_sha256':sha(actual),'closure_render_sha256':sha(out),'RGBA_shape':str(a.shape),'differing_pixels':int(np.any(a!=b,axis=2).sum()),'max_channel_error':int(np.abs(a.astype(int)-b.astype(int)).max())})
    def mkdir(path,*args,**kwargs):
        if path.resolve()==oldroot:assert path.is_dir();return
        return oldmkdir(path,*args,**kwargs)
    def show(*args,**kwargs):
        for i in plt.get_fignums():
            stream=io.BytesIO();oldsave(plt.figure(i),stream,format='png',dpi=100,bbox_inches='tight');embedded_new.append(pixels(io.BytesIO(stream.getvalue())))
        plt.close('all')
    def display(value,*a,**k):
        if isinstance(value,pd.DataFrame):displays.append({'rows':len(value),'columns':','.join(map(str,value.columns))})
    def forbidden(*a,**k):raise AssertionError('Rendering cannot optimize or train')
    namespace={'__name__':'__closure_render__'};log=io.StringIO()
    with patch.object(Figure,'savefig',save),patch.object(Path,'mkdir',mkdir),patch.object(plt,'show',show),patch.object(IPython.display,'display',display),patch.object(torch.optim.Optimizer,'__init__',forbidden),patch.object(torch.Tensor,'backward',forbidden),contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        for i,cell in enumerate(code):exec(compile(cell.source,f'accepted-notebook-cell-{i+1}','exec'),namespace)
    (C/'accepted_notebook_readonly_render.txt').write_text(log.getvalue(),encoding='utf-8')
    assert len(rows)==len(embedded_new)==6
    for row,original,new in zip(rows,embedded,embedded_new):
        assert original.shape==new.shape
        row['embedded_differing_pixels']=int(np.any(original!=new,axis=2).sum())
        assert row['differing_pixels']==row['embedded_differing_pixels']==0,row
    csv('image_data_checks.csv',rows);csv('notebook_table_outputs_checked.csv',displays)
    # B1 notebook is inspected without rewriting/reexecuting its producer.
    b1=nbformat.read(ROOT/'notebooks/WP11_B1_SHAP.ipynb',as_version=4);nbformat.validate(b1)
    b1code=[c for c in b1.cells if c.cell_type=='code'];assert len(b1code)==8 and all(c.execution_count for c in b1code)
    assert not any(o.output_type=='error' for c in b1code for o in c.outputs)
    write_json(C/'notebook_checks.json',{'graph_executed_cells':9,'graph_PNG':6,'graph_embedded_images_pixel_equal':True,'all_six_PNG_renders_pixel_equal':True,'B1_executed_cells':8,'accepted_notebooks_written':False,'old_figures_written':False,'WP12':False})
    preserve();print(pd.DataFrame(rows).to_string(index=False))


if __name__=='__main__':run()

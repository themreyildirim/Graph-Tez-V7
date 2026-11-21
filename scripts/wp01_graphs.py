"""WP01 öğretici graf yardımcıları. Kaynakları değiştirmez; model kurmaz."""
from pathlib import Path
import json
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'reports/figures/WP01'

def toy_graph():
    g=nx.Graph()
    g.add_edges_from([('A','B'),('A','C'),('B','C'),('C','D')])
    g.add_node('E')
    return g

def real_graph(snapshot):
    g=nx.DiGraph()
    for r in snapshot['relations']:
        d='drug:'+r['DrugBank_ID']; p='protein:'+r['UniProt_ID']
        g.add_node(d,kind='drug',label=r['Drug_Name'],identifier=r['DrugBank_ID'])
        g.add_node(p,kind='protein',label=r['Gene_Name'] or r['UniProt_ID'],identifier=r['UniProt_ID'],organism=r['Organizma'])
        if g.has_edge(d,p):
            raise ValueError('Duplicate drug-protein pair')
        g.add_edge(d,p,relation='targets_legacy',source_row=r['source_row'])
    return g

def metrics(g):
    """Merkezilikler yönsüz, ağırlıksız izdüşümde; genel n-1 normalizasyonu."""
    u=g.to_undirected()
    dc=nx.degree_centrality(u); bc=nx.betweenness_centrality(u,normalized=True,weight=None)
    cc=nx.closeness_centrality(u,wf_improved=True)
    return pd.DataFrame([dict(node=n,label=g.nodes[n].get('label',n),kind=g.nodes[n].get('kind','toy'),
                              degree=u.degree(n),degree_centrality=dc[n],betweenness=bc[n],closeness_WF=cc[n])
                         for n in sorted(g)]).sort_values(['degree','node'],ascending=[False,True]).reset_index(drop=True)

def summary(g):
    u=g.to_undirected(); components=list(nx.connected_components(u))
    return pd.DataFrame([{'nodes':len(g),'edges':g.number_of_edges(),'components_undirected':len(components),
                          'isolates':len(list(nx.isolates(g))),'density_directed_or_undirected':nx.density(g),
                          'average_degree_undirected':sum(dict(u.degree()).values())/len(u),
                          'clustering_undirected':nx.average_clustering(u)}])

def draw(g,name,title,pos=None,labels=None,highlight=(),edge_labels=None):
    FIG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    fig,ax=plt.subplots(figsize=(11,6.5),layout='constrained')
    pos=pos if pos is not None else nx.spring_layout(g,seed=17)
    labels=labels or {n:g.nodes[n].get('label',n) for n in g}
    colors=['#e9b949' if n in highlight else '#237b8d' if g.nodes[n].get('kind')=='drug' else '#83bd99' for n in g]
    nx.draw_networkx_nodes(g,pos,node_color=colors,node_size=2100,edgecolors='white',ax=ax)
    nx.draw_networkx_edges(g,pos,arrows=g.is_directed(),node_size=2100,arrowstyle='-|>',arrowsize=19,
                           edge_color='#74818d',width=1.4,ax=ax)
    nx.draw_networkx_labels(g,pos,labels,font_size=9,ax=ax)
    if edge_labels:
        nx.draw_networkx_edge_labels(g,pos,edge_labels=edge_labels,font_size=9,ax=ax)
    ax.set_title(title,loc='left',fontweight='bold',pad=15);ax.margins(.2);ax.axis('off')
    fig.savefig(FIG/(name+'.png'),dpi=160)
    plt.show()
    return pos

def real_positions(g):
    d=sorted(n for n in g if g.nodes[n]['kind']=='drug')
    p=sorted(n for n in g if g.nodes[n]['kind']=='protein')
    return {n:(x,1-i/(max(len(ns)-1,1))) for x,ns in [(0,d),(1,p)] for i,n in enumerate(ns)}

def interactive(g,pos,path):
    import plotly.graph_objects as go
    import html
    ex=[];ey=[]
    for a,b in g.edges:
        ex.extend([pos[a][0],pos[b][0],None]);ey.extend([pos[a][1],pos[b][1],None])
    edges=go.Scatter(x=ex,y=ey,mode='lines',line=dict(color='#9aa8b5',width=1.5),hoverinfo='skip')
    nodes=list(g)
    tips=['<br>'.join(html.escape(str(v)) for v in [g.nodes[n]['label'],g.nodes[n]['identifier'],g.nodes[n].get('organism','İlaç'),f'Alt graf derecesi: {g.to_undirected().degree(n)}']) for n in nodes]
    trace=go.Scatter(x=[pos[n][0] for n in nodes],y=[pos[n][1] for n in nodes],mode='markers+text',
                     text=[g.nodes[n]['label'] for n in nodes],textposition='top center',hovertext=tips,hoverinfo='text',
                     marker=dict(size=22,color=['#237b8d' if g.nodes[n]['kind']=='drug' else '#83bd99' for n in nodes]))
    fig=go.Figure([edges,trace])
    fig.update_layout(title='WP01 · İlaç (sol) → protein (sağ) ilişkileri · fare ile inceleyin',
                      showlegend=False,plot_bgcolor='white',height=700,margin=dict(l=100,r=100,t=100,b=90),
                      xaxis=dict(visible=False,range=[-.3,1.3]),yaxis=dict(visible=False,range=[-.2,1.2]),
                      annotations=[dict(text='Yön soldan sağa; çizgiler PPI değildir. Seçilmiş legacy kayıtları; merkezilik biyolojik önem kanıtı değildir.',
                                        x=.5,y=-.13,xref='paper',yref='paper',showarrow=False)])
    fig.write_html(path,include_plotlyjs=True,full_html=True,config={'displaylogo':False})

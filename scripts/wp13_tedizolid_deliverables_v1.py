"""Preparation tables/figures only. No new-drug scoring or reference document access."""
import json
from pathlib import Path
import pandas as pd
from wp12_api_security import public_sha
from wp09_close_wp10_notebooks import execute,INIT
ROOT=Path(__file__).resolve().parents[1];Q=ROOT/'reports/qa/WP13/tedizolid_preparation_v1';F=ROOT/'reports/figures/WP13/tedizolid_preparation_v1'
def dump(p,data):
 with p.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
def main():
 execute('WP13_Tedizolid_external_preparation_v1.ipynb',[
 ('md','''# WP13 — Tedizolid / fosfat dış tahmin hazırlığı

Bu defter yeni ilaç tahmini veya eğitim yapmaz. SIVEXTRO PDF/SIDER tedizolid etiketi yok. **Arama parçacıklarında beklenmedik güvenlilik bilgisi maruziyeti oldu; tam araştırmacı bilgi körlüğü iddiası yok.** Kimyasal girdiler yalnız DrugBank yapı kaydı ve frozen RDKit tanımlarıyla hazırlanmıştır. Gerçek dış deney kullanıcı kararını bekler.'''),
 ('code',INIT+r'''
Q=ROOT/'reports/qa/WP13/tedizolid_preparation_v1';F=ROOT/'reports/figures/WP13/tedizolid_preparation_v1'
display(pd.read_json(Q/'identity_vs_frozen62.json'))
chem=pd.read_csv(Q/'chemical_QC_features.csv');display(chem[['id','name','MW','LogP','HBD','HBA','TPSA','XML_InChIKey','rdkit_inchikey','components','chiral_assigned','chiral_unassigned']])
from IPython.display import Image
for name in ['DB14569_structure.png','DB09042_structure.png']:display(Image(filename=str(F/name),width=850))
'''),
 ('md','''**Yorum:** Etkin tedizolid ve fosfat ön ilacı iki farklı InChIKey/bağlantısallık yapısıdır. İkisi de frozen62/fit envanterinin dışında; fosfat bir karşı iyon silme işlemiyle temizlenmez. Stereokimya belirtilmiş, yeni stereo üretilmedi. RDKit HBA/LogP tanımları kaynak ChemAxon sayılarıyla karıştırılmaz. Birincil temsil önerisi DB14569; kullanıcı onayı olmadan yeni skor yok.'''),
 ('code',r'''
sim=pd.read_csv(Q/'structure_similarity_to62.csv');display(sim.groupby('query').head(5))
fig,ax=plt.subplots(figsize=(8,4));nearest=sim.groupby('query').similarity.max();nearest.plot.bar(ax=ax,rot=0,color='#3e8495');ax.set(ylabel='Morgan2 / 2048bit Tanimoto',title='Mevcut62 yapıya en yakın benzerlik; başarı ölçümü değil',ylim=(0,1));plt.tight_layout();plt.savefig(F/'03_identity_similarity_diagnostic.png',dpi=160);plt.show()
display(pd.read_csv(Q/'human_protein_QA.csv'));display(pd.read_csv(Q/'fold_PPI_scope.csv'))
'''),
 ('md','''**Yorum:** En yakın yapı Linezolid, tam kimlik/bağlantısallık eşliği yok. İnsan enzyme rolleri MAOA/MAOB; bakteriyel23S RNA ayrı. PPI her fold için aynı değil:3.foldta iki protein train evreninde yok. Bu, hesaplanmış sıfır katkı değil, ilgili train yolunun yokluğudur. A1P1 dış adapter parity'si henüz yapılmadı.'''),
 ('code',r'''
r=pd.read_csv(Q/'B1_heldout_replay.csv');display(r.groupby('status').agg(queries=('drug_id','size'),PT_scores=('PT','sum')));display(r[['transform_error','score_error']].max().to_frame('max_error'))
fig,ax=plt.subplots(figsize=(8,4));r.status.value_counts().plot.bar(ax=ax,rot=0,color=['#398297','#b6a16c']);ax.set(title='Yalnız mevcut heldout ilaç replay durumları',ylabel='Durum sayısı');plt.tight_layout();plt.savefig(F/'04_existing_heldout_replay.png',dpi=160);plt.show()
display(pd.read_json(Q/'model_policy_options.json',typ='series').to_frame('öneri_ve_kapı'))
'''),
 ('md','''**Yorum:**108eski heldout query/27854skor parity PASS,16abstention. Yeni tedizolid skoru yok. Dönüşümfarkı0, skorhatası yaklaşık1,11×10⁻¹⁶. Beşprimary B1 ayrı önerilir;201ortakPT ortalaması ancak önceden onaylı ek politika olabilir. Feature/temsil/model/prospektüs sonucu kilitlenmeden referans karşılaştırması başlamaz.'''),
 ('code',r'''
display(pd.read_json(Q/'blindness_audit.json',typ='series').to_frame('dürüstlük_ve_kapsam'))
display(pd.read_json(Q/'xml_read_audit.json',typ='series').to_frame('ham_kaynak_okuma'))
'''),
 ('md','''**Yorum:** Körlük maruziyeti saklanmaz; kaynak girdisinin outcome-free olması araştırmacının tamamen kör olduğu anlamına gelmez. Dış inference/SHAP/PDF karşılaştırması NOT_RUN. İnsan/temsil/yöntem kararları kullanıcıyı bekler. Kimyasal yapı ve model replay teknik doğruluğu klinik başarı değildir.''')])
 prior=json.loads((Q/'prior_pins.json').read_text())
 for name,h in prior.items():assert public_sha(ROOT/name)==h,name
 assert 'Ran 14 tests' in (Q/'tests_final.log').read_text(encoding='utf-8-sig')
 assert (Q/'tests_final.log').read_text(encoding='utf-8-sig').rstrip().endswith('OK')
 replay=pd.read_csv(Q/'B1_heldout_replay.csv');before=(Q/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==before
 prefix='''# WP13 Tedizolid dış hazırlık v1 ·09.11.2026

DB14569 tedizolid veDB09042fosfat: frozen62/20B1-A1P1fit kimliğinde yok; tamkey/bağlantısallık/alias eşleşmesi yok. YerelDrugBank SMILES veWP04RDKit5özellik hazır; birincilDB14569öneri, fosfat ayrıönilaç. B1eskiheldout124durum:108parity/27854skor,16abstention; dönüşümhatası0, skor1.11e-16. Yeniilaç skoru0. İnsanMAOA/MAOBenzyme56özellik mevcut;primary1/2/4/5PPI4'erkenar,fold3trainyolu yok. A1P1frozen62/QCguarddeğişmedi; dışadapter doğrulanmadı.14testPASS. Kimlik araması istenmeyen güvenlilik/prospektüs parçacıkları döndürdü: tamaraştırmacı körlüğü COMPROMISED; özelliklerde/seçimde kullanılmadı, PDFaçılmadı/SIDERtedizolidetiketiokunmadı. Bu sınır raporlandı; bağımsızuygulayıcı gereği kullanıcıkararı. Rapor reports/WP13_TEDIZOLID_PREPARATION_v1.md; notebook notebooks/WP13_Tedizolid_external_preparation_v1.ipynb; QA/figures WP13/tedizolid_preparation_v1. Temsil/beşB1ayrı/201PTopsiyonelortalama kararları onaybekliyor. Yeni inference/eğitim/attribution/PDFkarşılaştırması yok; tümgeçmiş korunur.

---
Önceki durum (tam baytları korunmuş):

'''
 (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+before)
 dump(Q/'final_verification.json',{'previous_hashes_verified':len(prior),'tests_PASS':14,'external_scores':0,'new_training':0,'new_attribution':0,'SIVEXTRO_PDF_opened':False,'SIDER_tedizolid_labels_read':False,'strict_analyst_blindness':'COMPROMISED_BY_INCIDENTAL_SEARCH_SNIPPETS','heldout_replay_cases':len(replay),'existing_score_replay_count':int(replay.PT.sum()),'max_transform_error':float(replay.transform_error.max()),'max_score_error':float(replay.score_error.max()),'prior_history_exact_suffix':(ROOT/'run_status.md').read_bytes().endswith(before)})
 explicit=['reports/WP13_TEDIZOLID_PREPARATION_v1.md','notebooks/WP13_Tedizolid_external_preparation_v1.ipynb','scripts/wp13_tedizolid_extract_v1.py','scripts/wp13_tedizolid_prepare_v1.py','scripts/wp13_b1_external_parity_v1.py','scripts/wp13_tedizolid_deliverables_v1.py','tests/test_wp13_tedizolid_preparation_v1.py','run_status.md']
 explicit.extend(p.relative_to(ROOT).as_posix() for folder in [Q,F] for p in folder.iterdir() if p.is_file())
 dump(Q/'evidence_manifest.json',{p:public_sha(ROOT/p) for p in sorted(set(explicit))})
 print('Previous public files verified:',len(prior))
if __name__=='__main__':main()

"""Real existing-value plots, notebook and preservation evidence; no new attribution."""
import json,math
import numpy as np,pandas as pd
import wp13_explain_v2 as m
from wp12_api_security import public_sha
from wp09_close_wp10_notebooks import execute,INIT
ROOT=m.ROOT;Q=m.Q;F=ROOT/'reports/figures/WP13/final_demo_v2'
def dump(p,obj):
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def main():
 coverage=[]
 for method,file in [('B1_SHAP','reports/qa/WP11/B1_SHAP_v1/local_pair_outputs.csv'),('A1P1','reports/qa/WP11/graph_v1/original_outputs.csv')]:
  df=pd.read_csv(ROOT/file)
  for (context,protocol,drug),g in df.groupby(['context','protocol','drug_id']):coverage.append({'model':method,'context':context,'protocol':protocol,'drug_id':drug,'PT_count':g.class_id.nunique()})
 pd.DataFrame(coverage).to_csv(Q/'full_native_PT_coverage.csv',index=False)
 comments=[];checks=[]
 for parent,fold in [('DB00199',3),('DB00254',1)]:
  bundle=m.old.recorded(parent)
  for pt in ['C0000731','C0000737']:
   a=m.get(parent,pt,fold)
   for kind,key,fn in [('B1_SHAP','shap',m.shap_sentence),('A1P1','graph',m.delta_sentence)]:
    for r in a[key]:comments.append({'drug_id':parent,'PT':pt,'fold':fold,'model':kind,'raw_value':r.get('SHAP_logit',r.get('delta_z')),'mode':r.get('mode','SHAP'),'comment_tr':fn(r)})
   g=pd.DataFrame(a['graph']);s=pd.DataFrame(a['shap'])
   out=next(r for r in bundle['shap_outputs'] if r['class_id']==pt)
   checks.append({'drug_id':parent,'PT':pt,'fold':fold,'SHAP_additivity_error':abs(out['base']+s.SHAP_logit.sum()-out['logit']),
    'delta_identity_max_error':(g.original_logit-g.intervened_logit-g.delta_z).abs().max(),
    'B1_sigmoid_proxy_error':abs(1/(1+math.exp(-out['logit']))-out['proxy_score'])})
 pd.DataFrame(comments).to_csv(Q/'Turkish_numeric_commentary.csv',index=False,encoding='utf-8-sig');pd.DataFrame(checks).to_csv(Q/'C0000731_C0000737_checks.csv',index=False)
 stats=pd.read_csv(Q/'full_WP11_coverage_by_drug_fold.csv').groupby('method')['rows'].sum().to_dict();dump(Q/'complete_scan_summary.json',stats)
 execute('WP13_FINAL_DEMO_v2_explanations.ipynb',[
 ('md','# WP13 FINAL DEMO v2 — Gerçek katkılardan deterministik Türkçe açıklama\n\nYeni attribution, forward, API veya eğitim yok. SHAP B1; tekil mesaj maskesi A1P1; biyolojik mekanizma NOT_ESTABLISHED.'),
 ('code',INIT+"\nQ=ROOT/'reports/qa/WP13/final_demo_v2';F=ROOT/'reports/figures/WP13/final_demo_v2'\ndisplay(pd.read_csv(Q/'full_native_PT_coverage.csv'));display(pd.read_json(Q/'complete_scan_summary.json',typ='series'));display(pd.read_csv(Q/'C0000731_C0000737_checks.csv'))"),
 ('md','**Yorum:** Tam mevcut tablolar tarandı; 2.608.100 katkı satırı yeni hesap değildir. Fold hedefleri birleştirilip doldurulmaz. Dört örnekte SHAP toplamı/logit ve Δz işareti kontrol edildi.'),
 ('code',"import wp13_explain_v2 as explain\na=explain.get('DB00199','C0000731',3)\ns=pd.DataFrame(a['shap']);g=pd.DataFrame(a['graph']);fixed=g[g['mode'].eq('fixed')].copy()\nfig,ax=plt.subplots(figsize=(9,4));ax.barh(s.feature,s.SHAP_logit,color=['#267b89' if v>=0 else '#b55a67' for v in s.SHAP_logit]);ax.set_xlabel('B1 SHAP logit katkısı; klinik risk değil');plt.tight_layout();plt.savefig(F/'03_real_B1_SHAP_signed.png',dpi=170);plt.show()\ndisplay(pd.DataFrame([{'feature':r['feature'],'SHAP':r['SHAP_logit'],'Türkçe yorum':explain.shap_sentence(r)} for r in a['shap']]))"),
 ('md','**Yorum:** Pozitif B1 logitini artırıcı, negatif azaltıcı katkıdır; maske kimyasal özellik değildir. Bu A1P1 açıklaması değildir. Tam değerler CSV’de korunur; klinik yüzdeye dönüşüm yapılmaz.'),
 ('code',"plot=fixed.assign(abs_effect=fixed.delta_z.abs()).sort_values('abs_effect',ascending=False).head(8).reset_index(drop=True)\nfig,ax=plt.subplots(figsize=(9,4));ax.barh(plot.index.astype(str),plot.delta_z,color='#498396');ax.set(xlabel='A1P1 sabit paydalı maske Δz',ylabel='Aşağıdaki gerçek bağlantı sıra indeksi');plt.tight_layout();plt.savefig(F/'04_real_A1P1_signed_delta.png',dpi=170);plt.show()\ndisplay(plot[['kind','role','protein_id','protein_a','protein_b','delta_z']]);display(pd.DataFrame({'yorum':[explain.delta_sentence(r) for r in plot.to_dict('records')]}))"),
 ('md','**Yorum:** Görsel en büyük mutlak8 müdahaleyi gösterir; seçim modeli/deneyi değiştirmez. Δz pozitifse müdahale logiti azaltmış, negatifse artırmıştır. Deletion/renormalization ayrı yöntemdir. Tekil etkiler toplamsal biyolojik nedenler değildir.'),
 ('code',"from IPython.display import Image\nfor f in ['02_final_A1P1_verbal.jpg','05_final_B1_verbal.jpg']:display(Image(filename=str(F/f),width=1000))"),
 ('md','**Yorum:** Gerçek localhost8510 ekranlarıdır. Tahmin/PDF kolları ayrı; uzman PT eşlemesi yoksa UNMAPPED/PENDING. Dış adapter yalnız sözleşme/plan; gerçek dış ilaç tahmini NOT_RUN.')])
 report='''# WP13 FINAL DEMO v2 — Deterministik sözlü açıklama

AGENTS/aktif ROADMAP, WP11 fixed-degree açıklama sözleşmesi ve uygulanmış policy_v1, WP13 FINAL v1 ve kör fizibilite v1 esas alındı. Yeni kod ayrı v2; geçmiş dosya/model/QA ve insan PENDING değişmez.

## Gerçek kapsam denetimi

Tam local_shap.csv ve role/ppi_contributions.csv.gz akışla50.000satırlık parçalarla tarandı, her dosya WP11 artifact manifestiyle hash doğrulandı. Toplam2.608.100 satır: B1 SHAP167124, rol557574, PPI1883402. Primary/stress ve model/context/ilaç bazında satır kapsamı full_WP11_coverage_by_drug_fold.csv; native PT sayıları full_native_PT_coverage.csv. Bunlar mevcut10outer model/family kapsamıdır, fold hedef union'u doldurulmadı. İki demo ilacının tam önceden hesaplanmış kayıtları yeni salt okunur indekslere alındı; yeni attribution yapılmadı.

DB00199 primary outer3: A1P1 müdahalesi318PT, B1 SHAP267PT. DB00254 primary outer1: A1P1 müdahalesi240PT, B1 SHAP220PT. B1 ve GNN head/kapsamı farklıdır; biri diğerinin açıklaması değildir. Önceki v1 yalnız iki seçilmiş örneği gösteriyordu; bu bir hesaplama eksikliği değil, sunum kapsamı kısıtıydı. C0000731/C0000737 her iki ilaçta kaynak hash ve model/fold/PT hizasıyla test edildi. B1 toplam/base/logit ve sigmoid/proxy ayrımı; A1P1 Δz=orijinal−müdahale değerleri korunur. Yanlış PT/fold/model/ilaç açık ValueError ile reddedilir.

## Anlaşılır açıklama ve sınırlar

Üç düzey ayrı:1girdi şeması,2seçili ilaç/PT için gerçek katkı,3biyolojik mekanizma NOT_ESTABLISHED. Seçili A1P1 ilişki skoru/sırası üstte. Açıklanabilir örnekler seçicisi mevcut kayıtlı hedeflere bağlı. İki örnek PT'nin Türkçe editoryal gösterimi orijinal adla birlikte ve onaysız terminoloji uyarısıyla sunulur; bu PDF→PT eşlemesi değildir. Diğer adlar frozen sözlükteki haliyle kalır.

SHAP>0 logiti artırıcı,SHAP<0 azaltıcı,0sıfır katkı; raw sayı repr ile korunur. Kimya5 ve modalite maskesi ayrı adlandırılır. B1 açıklaması A1P1 skoruna gerekçe yapılmaz. Δz>0 maskelenince logit azalır;Δz<0 artar. Fixed-degree ana görsel, physical-delete/renormalization ayrı kapalı alan. Kaynakta olmayan yol NA, gerçek sıfır0; absent_paths_NA kaydı ayrı gösterilir. Grafik altındaki yorum gerçek gösterilen satır/katsayı işaretlerinden deterministik üretilir; klinik oran, sıklık, kalibrasyon veya nedensellik iddiası yoktur. En büyük|Δz|8bağlantı görselde, ilk3ü sözlü; tüm bağlantılar kapalı ayrıntıdadır. İlk tarayıcı görüntüsündeki boş protein alanlarının nan etiketi son sürümde yalnız gösterim için boş bırakıldı; ham veriler değişmedi, erken ekran kanıtı tutuldu.

Bu açıklamalar modelin seçili girdilere yerel sayısal duyarlılığını anlatır; bütün sıralamanın nedenini eksiksiz açıklama, protein biyolojisi veya klinik mekanizma kanıtı değildir. Atom/kimya attribution'u A1P1 için burada yok; genel girdi listesi yerine özel gerekçe uydurulmaz. Prospektüs karşılaştırması v1'deki gibi ayrı, UNMAPPED/PENDING. PDF yüklemek yeni GNN tahmini değildir.

## Dış inference ve yeni attribution kapısı

Ayrı reports/WP13_EXTERNAL_INFERENCE_FEASIBILITY_v2.md ve docs/plan/WP13_EXTERNAL_INFERENCE_ADAPTER_CONTRACT_v1.md. B1 vektör çekirdeği var, doğrulanmış dış kimlik/QC/scaler adapter'ı yok. A1P1 frozen62 guard'ı değiştirilmedi. Yeni ana etkin madde bağımsızlığı, alias/DBSALT/kimyasal bağlantısallık, tüm62train birleşimi,5özellik/birim/sıra/maskeler, immutable scalers/head, atom/protein/PPI query-cache izolasyonu ve önceden model/ensemble kararı zorunlu. Öneri beşB1 modeli ayrı; ensemble/tekmodel henüz kullanıcı karar kapısı. Dış adapter testleri plan olarak yazıldı; uygulanmış veya geçmiş gibi gösterilmedi. Yeni dış tahmin/prospektüs karşılaştırması NOT_RUN.

Mevcut başlıklarda çoğu attribution zaten arşivde; yeni hesaplamaya gerek olmayabilir. Gerçek yeni hedef/model/atom attribution için ayrı yöntem ve onay gerekir. Maliyet karmaşıklığı ve gerekli dosyalar ayrı fizibilitede; yeni süre/RAM benchmark'ı yapılmadı. Eski OOF/PDF incelemesi retrospektif/keşifseldir; genel dış klinik doğruluk değildir.

## Test ve kanıtlar

15yeni test PASS: SHAP işaret/büyüklük, maske ayrımı, Δz iki işaret, fixed/delete ayrımı, NA/sıfır, yanlışmodel/fold/PT/ilaç, dört gerçekörnekte SHAPtoplam/logit/sigmoid ve Δz, eksik açıklama uydurmama/kapsam. Önceki FINALv1'in16regresyon testi ayrıca PASS; eski log değiştirilmedi. Test kanıtları yeni final_demo_v2 dizininde. Gerçek browser'da seçili C0000731 Türkçe adı, skor187.sıra/0.145759180188179, rol müdahalesi ve B1 sözlü SHAP görüldü. Bu örnekteki skor yalnız Erythromycin/A1P1 ownfold3 içindir. Görseller gerçeklocalhost8510; notebook çalıştırılmıştır.

Yeni API/eğitim/forward/attribution/dış inference0. Eski hash kontrol kapsamı final_verification.json'dadır; tüm disk taraması yapılmadı. Gizli .env/anahtar okunmadı veya hashlenmedi. Eski run_status baytları yeni giriş altında aynen saklandı. Kullanıcı değerlendirmesi bekleniyor.

## Çalıştırma

`& "C:\\Users\\emrey\\Downloads\\Graph-Tez-V7_SADELESTIRILMIS_CODEX\\Graph-Tez-V7\\scripts\\WP13_Start_FINAL_DEMO_v2.ps1" -Port 8511`

Hazır QA: http://127.0.0.1:8510. Eski sunucular kapatılmadı; yalnız bu turdaki v2 QA sunucusu etiket/NA sunumu düzeltmesi için yeniden başlatıldı. Model açıklanabilirliği sekmesini açın; üstteki Açıklanabilir örnekler seçicisi hedefi değiştirir. Teknik tablolar kapalıdır. Yeni dış deney için ayrı onay gerekir.
'''
 (ROOT/'reports/WP13_FINAL_DEMO_v2.md').write_text(report,encoding='utf-8')
 prior=json.loads((Q/'prior_pins.json').read_text())
 for p,h in prior.items():assert public_sha(ROOT/p)==h,p
 for p,h in json.loads((Q/'WP11_source_pins.json').read_text()).items():assert public_sha(ROOT/p)==h
 before=(Q/'run_status_before.md').read_bytes();assert (ROOT/'run_status.md').read_bytes()==before
 prefix='''# WP13 FINAL DEMO v2 ·09.11.2026

Deterministik Türkçe B1 SHAP/A1P1 müdahale açıklamaları; işaret/logit/proxy ayrımı, skor/sıra üstte, üçdüzey ve NOT_ESTABLISHED mekanizma. Tam mevcutWP11 katkıları2.608.100satır akışla okundu; yeni attribution0. Ery318/267 veDoxy240/220 A1P1/B1 PT kapsamı.15yeni+16regresyon testPASS. Dış inference adapter yalnız sözleşme/fizibilite; yeniilaç denemesiNOT_RUN, PDF/PT UNMAPPED/PENDING aynı. YeniAPI/eğitim/forward0. QA localhost8510; launcher scripts/WP13_Start_FINAL_DEMO_v2.ps1. Rapor reports/WP13_FINAL_DEMO_v2.md; dışfizibilite reports/WP13_EXTERNAL_INFERENCE_FEASIBILITY_v2.md; notebook notebooks/WP13_FINAL_DEMO_v2_explanations.ipynb. Eski dosyalar ve durum tarihçesi korunur. Kullanıcı onayı bekleniyor.

---
Önceki durum (tam baytları korunmuş):

'''
 (ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+before)
 dump(Q/'final_verification.json',{'previous_hashes_verified':len(prior),'new_tests_PASS':15,'regression_tests_PASS':16,'existing_contribution_rows_scanned':sum(stats.values()),'new_API':0,'new_training':0,'new_attribution':0,'new_external_inference':0,'human_QA':'PENDING_UNCHANGED','history_exact_suffix':(ROOT/'run_status.md').read_bytes().endswith(before)})
 files=['scripts/wp13_explain_v2.py','scripts/wp13_explain_audit_v2.py','scripts/wp13_explain_deliverables_v2.py','scripts/WP13_Start_FINAL_DEMO_v2.ps1','apps/drug_safety_explorer_FINAL_v2.py','tests/test_wp13_explain_v2.py','docs/plan/WP13_EXTERNAL_INFERENCE_ADAPTER_CONTRACT_v1.md','reports/WP13_EXTERNAL_INFERENCE_FEASIBILITY_v2.md','reports/WP13_FINAL_DEMO_v2.md','notebooks/WP13_FINAL_DEMO_v2_explanations.ipynb','run_status.md']
 files.extend(p.relative_to(ROOT).as_posix() for folder in [Q,F] for p in folder.iterdir() if p.is_file())
 dump(Q/'evidence_manifest.json',{p:public_sha(ROOT/p) for p in sorted(set(files))});print('Prior verified',len(prior))
if __name__=='__main__':main()

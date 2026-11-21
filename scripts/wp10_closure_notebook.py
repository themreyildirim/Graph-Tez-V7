"""Yalnız kapanış kanıtlarını gösterir;WP11 hesabı veya fit çalıştırmaz."""
from wp09_close_wp10_notebooks import execute


def main():
    parts=[('md','''# WP10 — Nihai kapanış denetimi

WP10 sonuçları kullanıcı tarafından araştırma kapsamında kabul edildi. Bu notebook yalnız kapanış QA'sını ve korunmuş sonuçları gösterir. **Yeni eğitim/optimizer/SHAP/graf attribution yoktur.** WP11 için yalnız aktif ROADMAP'ten bir hazırlık notu vardır;uygulaması başlamadı.'''),('code',r'''from pathlib import Path
import json
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists():
    if ROOT.parent==ROOT:raise RuntimeError('Proje kökü bulunamadı')
    ROOT=ROOT.parent
Q=ROOT/'reports/qa/WP10/final_closure_v1';T=ROOT/'reports/qa/WP10/training_v1'
F=ROOT/'reports/figures/WP10/final_closure_v1';F.mkdir(parents=True,exist_ok=True)
pd.set_option('display.max_rows',160);pd.set_option('display.max_columns',22)
result=json.loads((Q/'closure_checks.json').read_text(encoding='utf-8'))
display(pd.DataFrame([result]).T.rename(columns={0:'doğrulanmış_kapanış'}))
display(pd.read_csv(Q/'manifest_checks.csv'))
display(pd.read_csv(Q/'model_hash_checks_all152.csv'))'''),('md','''**Yorum:**152 ağırlık/metadata çifti ve3013 önceki artefakt doğrulandı. Kontroller eski dosyaları yazmaz. Tarihsel manifestin run_status kaydı kapanış öncesi tam arşivle doğrulanır;yalnız güncel durum kaydı ayrıca güncellenebilir. Büyük ham kaynaklar yeniden taranmadı.

## 1. OOF ve test kanıtı'''),('code',r'''display(pd.read_csv(Q/'OOF_reconstruction_all40_outer.csv'))
display(pd.read_csv(Q/'comparison_key_checks.csv'))
display(pd.read_csv(Q/'test_selection.csv'))
print((Q/'readonly_tests_rerun.txt').read_text(encoding='utf-8')[-400:])'''),('md','''**Yorum:**40 outer modelde143896 kayıtlı skor yeniden üretildi;max fark1,11×10⁻¹⁶. Bu yeni test tahmini kaydetmek veya sonuç seçmek değildir.13 salt okunur test yeniden geçti;önceki19/19 test kaydı hash ile korundu. Diğer6 test trainer/backward yoluna girdiğinden bu turda çalıştırılmadı;yeniden fit yasağı guard ile korundu. Yeni optimizer/fit sayısı0.

## 2. Aynen korunan sonuç'''),('code',r'''m=pd.read_csv(T/'metrics_with_group_CI.csv')
a=m[m.protocol.eq('primary')&m.scope.eq('paired54')&m.metric.eq('drug_macro_AP')&m.model.isin(['A0P0','A0P1','A1P0','A1P1'])]
display(a[['model','estimate','CI95_low','CI95_high']])
fig,ax=plt.subplots(figsize=(8,4.2));xx=np.arange(4)
ax.errorbar(xx,a.estimate,yerr=np.vstack([a.estimate-a.CI95_low,a.CI95_high-a.estimate]),fmt='o',capsize=4,color='#66899b')
ax.set_xticks(xx,a.model);ax.set(ylabel='Drug-macro observed-record AP',ylim=(0,1),xlim=(-.5,3.5),title='Kabul edilmiş primary paired54 sonuçları')
for i,r in enumerate(a.itertuples()):ax.text(i,r.estimate+.065,f'{r.estimate:.6f}',ha='center')
plt.tight_layout();plt.savefig(F/'01_preserved_primary_AP.png',dpi=160);plt.show()
effects=pd.read_csv(T/'factorial_contrasts_group_CI.csv')
display(effects[effects.scope.eq('paired54')&effects.metric.eq('drug_macro_AP')][['protocol','contrast','estimate','CI95_low','CI95_high']])'''),('md','''**Yorum:**Atom dalında küçük koşullu ana katkı korunur;stresin koşullu atom CI'ları sıfırı içerir. PPI veetkileşim katkısı gösterilemedi. B0/B1'e belirgin üstünlük sağlanamadı. CI sabitOOF'ye koşullu ve keşifseldir;dış doğrulama veya nedensellik değildir. Bu grafik yeni performans hesabı değil,korunmuş CSV'nin gösterimidir.

## 3. Kapsam ve durma noktası'''),('code',r'''coverage=pd.read_csv(T/'evaluation_coverage.csv');display(coverage[coverage.model.eq('A1P1')])
fig,axs=plt.subplots(1,2,figsize=(10,4.2))
axs[0].bar(['Skorlanan pozitif','Sözlük/fit dışında'],[3820,1685],color=['#85a58a','#bd9a80']);axs[0].set(title='Paired54 • 5505 kaynak pozitif',ylabel='Kaynak pozitif çift')
axs[1].bar(['Kaynak pozitif','Unknown'],[3820,10144],color=['#85a58a','#7093a6']);axs[1].set(title='Paired54 • 13964 skorlanan çift',ylabel='İlaç–PT çifti')
for ax in axs:ax.tick_params(axis='x',labelsize=8)
plt.tight_layout();plt.savefig(F/'02_preserved_source_coverage.png',dpi=160);plt.show()
scope=json.loads((Q/'WP11_roadmap_scope.json').read_text(encoding='utf-8'));display(pd.DataFrame([scope]).T)
'''),('md','''**Yorum:**1685 kapsam dışı pozitif bütün62 ilacın yanlış-negatif sayısı değildir. Unknown çiftler doğrulanmış biyolojik negatif değildir.62 ilaç/1061 kaynakPT/6416 pozitif,Methenamine abstention,QC veNA kararları korunur. Klinik risk,hasta güvenliği veya nedensellik iddiası yoktur.

WP11'in yol haritasındaki konusu kimya baseline local/global SHAP vekoşullu protein/kenar açıklamalarıdır. Bu notebook hiçbir açıklama değeri üretmez;yalnız kapsam satırını gösterir. [Hazırlık notu](../reports/WP11_PREPARATION_DECISION.md) onay bekleyen seçimleri açıklar. **WP10 kapanır;WP11 uygulaması,yeni model veya yeni eğitim başlamadan durulur.**''')]
    execute('WP10_final_closure.ipynb',parts)


if __name__=='__main__':main()

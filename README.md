# Graph-Tez V7 — Sadeleştirilmiş ve Kanıta Dayalı Codex Paketi

**Bu arşiv, önceki V7 planlama paketlerinin yerine geçer.** Gereksiz veri kaynakları aktif kapsamdan çıkarıldı. ZIP içindeki `legacy/` yalnız orijinal kullanıcı raporlarının ve eski kodun değişmemiş kopyalarıdır; eski raporlarda planlanan fakat uygulanmamış veri setleri aktif talimat değildir.

## Ne yapacağız?
1. Eski V6'nın gerçek girişlerini ve hatalarını öğrenerek ilk veri envanterini yapacağız (WP00).
2. DrugBank XML + SIDER + `drug links.csv` + PubChem API ile kimlik ve etiket eşlemesini düzelteceğiz; yan etki etiketli ilaç sayısını **ulaşabildiğimiz ölçüde artıracağız**.
3. Protein özelliklerini temiz dizilerden, `kalite_skoru` olmadan yeniden çıkaracağız.
4. Önce kimyasal baseline, sonra ilaç–protein özet modeli, ancak veri/ekonomik fayda uygunsa mevcut STRING PPI'lı gerçek GiG karşılaştırması yapacağız.
5. Kaynaklı PDF→Ollama açıklaması ve SHAP/GNN XAI ayrı aşamalar; önce veri sızıntısı önlenecek.

## Kullanacağımız kaynaklar
- Ham: `full database.xml`, `meddra_all_se.tsv`, `drug links.csv` ve PubChem API.
- Yalnız gerekli olursa PPI deneyi için: `ppi_insan_v3.csv`, `ppi_bakteri_v3.csv` veya bunların **insan/E. coli** kaynak dosyaları.
- Kontrol için eski çıktılar: beş V5/V6 CSV'si (`ilac_feature_v5_atc`, `ilac_yan_etki_v5`, `ilac_protein_eslesmesi_v6`, `protein_dizileri_v6`, `protein_feature_v6`) ve model grafı (`heterogen_ag_v6.pt`).
- **Bağımsız UniProt ham verisi zorunlu değil**: Eski Python, dizileri ve UniProtKB kimliklerini DrugBank XML'den alıyor.

## Kapsam dışı (okunmayacak)
MIMIC-IV, CARD, DisGeNET, FAERS, OnSIDES, ChEMBL, DailyMed/openFDA, başka bakteri türlerine ait STRING; `all.csv`, eski master-network/nihai-ağ denemeleri gibi ara tarihsel dosyalar. Kaynak adları `legacy/` belgelerinde bulunabilir fakat aktif kapsama geri alınamaz.

## Nasıl başlanır?
1. ZIP'i çıkar, Codex'te proje kökü `Graph-Tez-V7/` klasörünü aç.
2. `AGENTS.md` otomatik okunmalı; Codex'e ayrıca `docs/prompts/PROMPT_01_CODEX.md` içeriğini ver.
3. Windows yerel ham veri yolu: `C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset`. Bu klasörde **yalnız allowlist kaynaklarına** bakılacak. Ham veriler ZIP'in içinde değildir.
4. Yalnız WP00; kullanıcı onayı gelene kadar model eğitimi veya ek veri indirme yok.
5. WP00 sonrasında `reports/WP00.md`, `reports/qa/source_inventory.csv` ve görselleri incele, sonra WP01.

## Dokümanlar
- `docs/plan/SOURCE_USAGE_AUDIT.md`: Orijinal PDF/DOCX/Python kodundan **fiili kullanım** denetimi, tarihsel/öngörü ayrımı.
- `docs/plan/ROADMAP_V7.md`: öğretici ve modüler iş paketi sırası (WP00–WP13).
- `docs/plan/DATA_CONTRACTS.md`: aktif dosya şemaları, yasak özellikler, leaky split, kimlik kontratları.
- `docs/plan/COHORT_EXPANSION.md`: ilaç sayısını mevcut kaynaklardan artırma stratejisi ve gerçekçi kazanım metriği.
- `docs/prompts/PROMPT_01_CODEX.md`: Codex'e gönderilecek tek ilk görev.
- `legacy/`: eski sistemin tarihsel belgeleri, orijinal (değiştirilmedi).

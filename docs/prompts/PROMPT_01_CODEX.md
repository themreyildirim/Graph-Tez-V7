# Codex başlangıç talimatı — YALNIZ WP00

Graph-Tez V7 projesine başlıyoruz. Önce `AGENTS.md`, `README.md`, `docs/plan/SOURCE_USAGE_AUDIT.md`, `docs/plan/ROADMAP_V7.md`, `docs/plan/DATA_CONTRACTS.md`, `docs/plan/COHORT_EXPANSION.md` dosyalarını oku. `legacy/` yalnız kaynak; eski kodu çalıştırma.

**Ham verilerin Windows yerel yolu:**
`C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset`

Önce bu yolun gerçekten mevcut ve erişilebilir olduğunu test et. Windows dışı bulut Codex isen erişim varmış gibi davranma; yalnız **yerel dosya yolu erişilemiyor** raporu ver, kullanıcıdan erişim yöntemi iste ve dur.

### Kesin WP00 kapsamı
1. Proje dosyalarının ağaç yapısını doğrula.
2. Windows veri klasörünün yalnız **üst düzey dosya/klasör adlarını** listele. `AGENTS.md` dışlama listesiyle eşleştir. **MIMIC-IV, CARD, FAERS, DisGeNET, OnSIDES, ChEMBL, DailyMed/openFDA, ek organizma STRING ve eski master-network gibi dışlananların klasörlerine girme, içeriklerini okuma, hash alma veya kopyalama**.
3. Sadece şu dosyaları adlarından bularak, salt okunur biçimde işle: `full database.xml`, `meddra_all_se.tsv`, `drug links.csv`; varsa `ilac_feature_v5_atc.csv`, `ilac_yan_etki_v5.csv`, `ilac_protein_eslesmesi_v6.csv`, `protein_dizileri_v6.csv`, `protein_feature_v6.csv`. STRING `ppi_insan_v3.csv` / `ppi_bakteri_v3.csv` dosyalarının yalnız varlık/boyut bilgisini WP00'da al; içeriğini sonraki iş paketinde incele.
4. Veri kaynaklarının her biri için: boyut, kaynak/sürüm (biliniyorsa), başlık ve 3 temsilî örnek, ilk 1000 satırdaki eksiklikler, son işlenmiş veriyle şema uyumu. **Büyük XML için 1–3 drug bloğu stream**, büyük TSV için küçük başlık örneği; tam okuma/row count/GB hash zorunlu değil.
5. `reports/qa/source_inventory.csv` (allowlist kaynağı, durumu, yol, boyut, kapsam tipi, incelendi mi, gerekçe); `reports/WP00.md`; `reports/figures/source_sizes.png` ve `data_dictionary_draft.md` üret.
6. Gerçek erişebildiğin dosyalarla Drive denetiminde bildirilen sayıları karşılaştır: eski V6 56 ilaç kimyası, 53 ADR ilaç, 41 hedef-proteinli ilaç, 38 kesişim; `kalite_skoru`, ATC sıfırları ve protein dizi header sorunlarını **sadece işaretle**, henüz değiştirme.
7. WP00 testleri yaz, kullanılan dosya ve `status=exists/unreadable/missing/excluded` bilgisini kaydet. Eski/ara rapordaki kaynağı `used` diye varsayma: kaynak denetim belgesi kararını izlemelisin.

### Yasaklar
- Model kurma/eğitme, normalize etme, protein feature yeniden üretme, tüm XML/STRING dosyasını RAM'e yükleme.
- Dış veri indirme / API kullanımı / Google Drive bağlantısına bağımlı iş.
- Yeni veri kaynağı ekleme, tarihsel dosyaları modele dahil etme.
- Kullanıcıya ait ham dosyaları silme/yeniden adlandırma/üzerine yazma.
- WP01'e geçme.

### Çıkış
Türkçe anlaşılır eğitim notu + keşfedilen üç örnek kayıt + temel veri görselleri + otomatik test listesi + `reports/WP00.md`; sonra **bekle**. Veriye erişemediysen tüm başarılı işler uydurma; erişim sorunu raporu bırak ve dur.

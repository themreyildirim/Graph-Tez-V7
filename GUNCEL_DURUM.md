# Graph-Tez V7 (EMT2) — Guncel Durum ve Calistirma Rehberi

> Bu dosya 14.11.2026'da eklendi. `README.md` ve `AGENTS.md` butunluk
> manifestlerinde hash ile kilitli oldugu icin **degistirilmedi**; guncel
> isleyis burada toplanir. Celiski durumunda gecerli olan bu dosyadir.

## 1. Projede hangi dosya guncel?

Depoda her asamanin tarihsel surumu korunur. Su an gecerli olanlar:

| Konu | Guncel dosya | Durum |
|---|---|---|
| Web arayuzu | `apps/arayuz_v5.py` + `apps/tedizolid_v5.py` | **Guncel (v5)** |
| Arayuz baslatici | `scripts/WP13_Start_v5.ps1` (port 8530) | **Guncel** |
| Onceki arayuz | `EMT2_Teslim_v1/demo/uygulama.py` ("Sunum v4", port 8527) | Calisir, korunur |
| Arayuz kaynagi | `apps/drug_safety_explorer_FINAL_v3.py` (port 8501) | v4'un turetildigi surum |
| Teslim paketi | `EMT2_Teslim_v1/` | Tam paket (rapor, slayt, juri, ekranlar, QA) |
| Rapor metni | `EMT2_Akademik_v3/EMT2_FINAL_REPORT.docx` (34 sayfa) | **Guncel** |
| Onceki rapor | `EMT2_Akademik_v2/` (33 sayfa) | Korunur |
| Durum gunlugu | `run_status.md` | Ters kronolojik: **en yeni kayit en ustte** |
| Aktif plan | `docs/plan/ROADMAP_V7.md` | WP00-WP13 |

`apps/` altindaki diger alti dosya ve `scripts/WP13_Start*.ps1` ailesinin
geri kalani **tarihseldir**; calisir durumda tutulur ama gelistirilmez.

## 2. Is paketlerinin gercek durumu

| Paket | Durum |
|---|---|
| WP00-WP07 | COMPLETED, kullanici onayli |
| WP08 | Faz 1 kapandi (B0/B1/B2). ATC, RandomForest, kimya MLP, protein-mean MLP **yapilmadi** |
| WP09 | Kullanici tarafindan kabul edildi (PPI encoder + ablation) |
| WP10 | Kullanici tarafindan kabul edildi (atom x PPI faktoriyel) |
| WP11 | Nihai kapanis PASS (B1 SHAP + A1P1 mesaj maskeleme) |
| WP12 | **Resmi kapanis yok** — insan degerlendirmesi bekliyor |
| WP13 | **Resmi kapanis yok** — uzman terim eslemesi PENDING |

## 3. Kurulum ve calistirma

Calisan ortam `.venv_wp13/` icindedir (Python 3.11.3). Surumler
`requirements.txt` dosyasinda kayitlidir.

Arayuzu baslat (v5):

```bash
powershell -ExecutionPolicy Bypass -File scripts/WP13_Start_v5.ps1
```

Onceki v4 arayuzu hala calisir:

```bash
powershell -ExecutionPolicy Bypass -File EMT2_Teslim_v1/DEMO_BASLAT.ps1
```

Testlerin tamamini tek komutla calistir:

```bash
.venv_wp13/Scripts/python.exe -m pytest -q
```

Tek bir is paketinin testi:

```bash
.venv_wp13/Scripts/python.exe -m pytest tests/test_wp10_training.py -q
```

Etkin ham veri yolunu gor:

```bash
.venv_wp13/Scripts/python.exe -I scripts/paths.py
```

## 4. Ham veri yolu

Ham veriler depoda degildir. Yol su sirayla cozumlenir
(`scripts/paths.py`):

1. `GRAPH_TEZ_DATA_ROOT` ortam degiskeni
2. `configs/data_paths.yaml` icindeki `dataset_root`
3. `scripts/wp0*.py` icindeki tarihsel varsayilan

**Onemli sinir:** WP00-WP06 scriptleri ham veri yolunu modul duzeyinde
sabit kodlanmis tasir ve bu dosyalarin SHA-256 degerleri 29 ayri butunluk
manifestinde kayitlidir. Icerikleri degistirmek kabul edilmis sonuc
zincirini gecersiz kilacagi icin **degistirilmemistir**. Baska bir
makinede veri hattini bastan calistirmak gerekirse ilgili scriptin bir
**kopyasi** uzerinde varsayilan yol `paths.data_root()` ile degistirilmeli,
orijinal dosyaya dokunulmamalidir.

## 5. Butunluk zinciri — neye dokunulmamali

Proje hash-kilitlidir. `preserve()` fonksiyonlari (`scripts/wp09_train.py`,
`wp09_null_gate.py`, `wp10_train.py`) bir **manifest** okur ve listelenen
her dosyanin hash'ini dogrular.

- **Dosya eklemek guvenlidir** — manifestte yer almayan dosya kontrol
  edilmez. Sayimlar (1567 / 1711 / 2487) manifest uzunlugudur, canli
  dizin sayimi degildir.
- **Listelenen bir dosyayi degistirmek testleri kirar** ve bilimsel
  kayitlari gecersiz kilar. `scripts/`, `tests/`, `configs/`, `docs/`,
  `models/`, `reports/`, `notebooks/` altindaki mevcut dosyalar ile
  `README.md`, `AGENTS.md`, `run_status.md` bu kapsamdadir.

14.11.2026'da eklenen dosyalar (hicbiri manifestte degil):
`requirements.txt`, `pyproject.toml`, `pytest.ini`, `tests/conftest.py`,
`scripts/paths.py`, `configs/data_paths.yaml`, `apps/arayuz_v5.py`,
`apps/tedizolid_v5.py`, `scripts/WP13_Start_v5.ps1`,
`tests/test_arayuz_v5.py`, `scripts/wp13_capture_v5.py`,
`EMT2_Akademik_v3/` (rapor ve uretim betigi), `EMT1_EMT2_KARSILASTIRMA.md`,
bu dosya.

Ayrica `.venv_wp13` icine **python-docx 1.2.0** kuruldu (kullanici onayi ile);
raporu uretmek icin gereklidir ve `requirements.txt` icinde kayitlidir.

## 5b. Arayuz v5 — ne degisti?

v5 YENI dosyalardir; v4 ve FINAL_v3 degistirilmedi ve calismaya devam
eder. Veri, kilit ve dogrulama katmani ayni modullerden okunur
(`wp13_final_data_v1`, `wp13_explain_v2`, `wp13_tr_sources_v1`,
`wp13_external_reference_v1`). Yeni model, egitim, forward, SHAP hesabi,
API veya OCR yoktur.

| Sorun (v4) | Cozum (v5) |
|---|---|
| `st.bar_chart` kategorileri **alfabetik** siraliyordu; ilk 10 grafigi tablodan farkli bir sira gosteriyordu | Altair, `sort='-x'` ile skora bagli siralama. `tests/test_arayuz_v5.py::test_07` bunun regresyon testidir |
| Tablolarda gorsel hiyerarsi yoktu | `column_config` + `ProgressColumn` ile skor cubugu, 3 ondalik |
| Uyari metinleri govde metniyle ayni agirliktaydi | Her sekmede tek "Sinirlar ve okuma uyarilari" acilir bolumu; **hicbir uyari silinmedi** |
| Tedizolid tablosu yatay tasip son sutunu kesiyordu | Bes sutuna indirildi; siklik/kapsam/sayfa/insan incelemesi acilir bolumde |
| `A1P1`, `PT`, `OOF`, `proxy` gibi terimler aciklamasizdi | Metrik kartlarinda ve secicilerde `help=` aciklamalari |
| SHAP/Δz grafiklerinde isaret ayrimi yoktu | Pozitif/negatif ayri renk; eksen etiketleri tam gosterilir |
| `mask__chemistry` ham alan adiyla gorunuyordu | "Kimya eksiklik maskesi" olarak adlandirildi |
| Streamlit `Deploy`/`Stop` dugmeleri sunumda gorunuyordu | Baslaticida `--client.toolbarMode=minimal` |
| Ust bilgi/kimlik yoktu | Baslik seridi + "Arastirma prototipi" rozeti |

Dogrulama: `tests/test_arayuz_v5.py` 13 Streamlit AppTest kontrolu
(tarayici/model/API yok). `test_11`, yeniden tasarimin bilimsel kisitlari
(`NOT_CALCULABLE`, `STRICT_ANALYST_BLINDNESS_COMPROMISED`, `PENDING`)
silmedigini dogrular.

## 6. Sonuclarin ozeti

Ana karsilastirma — paired54, ilac-makro gozlenen-kayit AP
(`reports/WP10_FINAL_CLOSURE.md`, `reports/WP08_FINAL_CONCLUSIONS.md`):

| Model | AP |
|---|---:|
| B1 (5 kimya + maske, L2-LR) | 0.6556 |
| B0_like_B2 (siklik referansi) | 0.6466 |
| A1P1 (atom + PPI GNN) | 0.6462 |
| G_realPPI | 0.6429 |
| B2 | 0.6262 |

GNN varyantlari basit referanslari **gecemedi**; PPI'nin ek katkisi
gosterilemedi. Skorlar SIDER kayit siralama vekilidir; klinik yan etki
olasiligi, kalibre edilmis risk veya nedensellik degildir. Unknown ciftler
dogrulanmis biyolojik negatif degildir.

## 7. Test paketinin bilinen durumu (14.11.2026)

`.venv_wp13/Scripts/python.exe -m pytest -q` sonucu:

**1191 gecti · 3 basarisiz · 5 atlandi · 158 saniye**

Uc basarisizlik da **onceden mevcuttur** ve 14.11.2026'da eklenen
dosyalarla ilgisi yoktur. Ucu de ayni desene sahiptir: *erken bir asamanin
kapisi, sonraki asamanin gercek calistirmasi tarafindan gecersiz kilinmis.*
Hicbiri bilimsel bir sonucu, modeli veya skoru etkilemez.

| Test | Beklenen | Gercek durum | Yorum |
|---|---|---|---|
| `test_wp12_conditional_gemma_v2.py::test_25_claim_not_consumed_by_preparation` | `stage_A_generation_claim.json` **olmamali** | Dosya var (08.11.2026) | Gercek Gemma calistirmasi uretim slotunu tuketti. Test, calistirma oncesi hazirlik asamasi icin yazilmisti. |
| `test_wp12_openai_pilot.py::test_27_no_real_API_ledger_slots` | API defteri **bos olmali** | `http_01..03`, `inference_reservation_01`, `S01_attempt_01` var | Gercek OpenAI pilotu bu testten sonra calisti ve defteri doldurdu. |
| `test_wp13_external_reference_v1.py::test_32_executed_notebook_no_errors` | Notebook'ta **5** kod hucresi | **6** kod hucresi, 1-6 arasi calistirilmis, **hata yok** | Notebook saglam; testin beklentisi eskimis. `run_status.md`'deki "alti hucreli" ifadesi dogru, kapanis belgesindeki "bes hucreli" yanlistir. |

Bu testler **duzeltilmedi.** `tests/` altindaki dosyalar 23-27 ayri
butunluk manifestinde hash ile kayitlidir; iceriklerini degistirmek kabul
edilmis sonuc zincirini gecersiz kilardi. Dogru davranis, durumu burada
belgelemektir.

Buna karsilik butunluk zincirinin kendisi **saglamdir**: eklenen yedi yeni
dosyaya ragmen `test_wp10_training.py::test_01_prior_artifacts_and_model_hashes_unchanged`,
`test_wp09_*::preserve()` ve `test_wp11_*` butunluk testlerinin tamami
gecmistir. Bu, dosya eklemenin manifestleri bozmadigini dogrular.

Bes atlanan test `VOCAB_ONLY_UTILITY_RAM_GUARD` gerekcesiyle atlanir:
Gemma sozluk sayaci yardimci araci, bellek esigi asilmadigi icin kendini
devre disi birakir. Bu kasitli bir korumadir, hata degildir.

Teslim paketinin ayri regresyonu da gecer:

```bash
.venv_wp13/Scripts/python.exe -I -m unittest discover -s EMT2_Teslim_v1/demo -p "test_teslim_v4.py"
```

## 8. EMT2 nihai raporu (v3)

`EMT2_Akademik_v3/` 14.11.2026'da uretildi. Kaynak `EMT2_Akademik_v2` taslagidir
ve o klasor **degistirilmedi**. Uretici: `EMT2_Akademik_v3/calisma/uret_v3.py`.

v2'ye gore yapilan degisiklikler yalnizca sunlardir:

| # | Degisiklik | Yer | Gerekce |
|---|---|---|---|
| 1 | EMT1 cercevesi: onceki donemde **raporlanmis bir egitilmis model basarimi bulunmadigi** ve bu rapordaki degerlerin bir gerileme olarak okunamayacagi | §1.2, iki yeni paragraf | EMT1 final raporu §2.3, §5, §6.2; ara rapor OZET |
| 2 | Tekrarlanabilirlik duzenlemeleri (bagimlilik kaydi, tek test komutu, merkezi yol yapilandirmasi) | §4.11 | Asama A |
| 3 | Sunum katmaninin yeniden duzenlenmesi ve grafik siralama duzeltmesi | §5.12 | Asama B |
| 4 | Sekil 11, 13 ve 14'un v5 ekranlariyla degistirilmesi; aciklamalarda v4 → v5 | Sekil listesi ve govde | Kullanici karari |

**Hicbir sayisal sonuc, tablo, model ciktisi veya bilimsel kisit
degistirilmedi.** Yeni egitim, forward, SHAP veya API cagrisi yoktur.

Ekran goruntuleri `scripts/wp13_capture_v5.py` ile uretildi. Orijinal
`EMT2_Teslim_v1/build/capture.cjs` Node + Playwright ister; bu makinede Node
kurulu olmadigindan ayni is kurulu Chrome ve Chrome DevTools Protocol
uzerinden yapildi. Cikti `reports/figures/WP13/arayuz_v5/` altinda yedi PNG,
1640x1060, mevcut rapor sekilleriyle ayni cozunurluk.

PDF'e cevirme Word COM ile yapilir:

```bash
powershell -ExecutionPolicy Bypass -File EMT2_Akademik_v2/calisma/pdf.ps1 -Name EMT2_FINAL_REPORT
```

---

## 9. WP15 — Agac tabanli karsilastirma modelleri (15.11.2026)

Kullanici onayiyla yurutulen sinirli ek deney. B1 ile **birebir ayni**
girdiler, bolmeler, uygunluk ve hedef sozlugu; degisen tek sey kestirici.

| Kol | Model | Secilen ayar (20 katin cogunda) |
|---|---|---|
| T1 | RandomForest, 300 agac | `max_depth=3, min_samples_leaf=3` |
| T2 | HistGradientBoosting, 100 yineleme | `max_depth=2` |

Egitimden **once** kapatilan iki kapi (`run_config.json` icinde kayitli):
- HGB `early_stopping=True` seyrek hedeflerde cokuyordu -> `False`, `max_iter=100`
- RF `n_jobs=-1` ayni tohumla birebir ayni olasiligi vermedi -> `n_jobs=1`

**Sonuc (birincil protokol, paired54, ilac-makro AP):**

| Karsilastirma | Fark | %95 GA | Ayirt edilebilir? |
|---|---:|---|---|
| T1 - B1 | +0,001697 | [-0,013428; +0,018248] | Hayir |
| T2 - B1 | -0,023159 | [-0,039580; -0,009189] | Evet (daha kotu) |
| T1 - B2 | +0,031100 | [+0,010025; +0,052217] | Evet |

**Kabul olcutu karsilanmadi; T1 ana model DEGILDIR.**

Onceden kayitli stres protokolunde T1 - B1 = +0,024713
[+0,002413; +0,048397] (aralik tumuyle sifirin ustunde). B1 0,6556 ->
0,6319 duserken T1 0,6573 -> 0,6566. Keşifsel bulgu; coklu karsilastirma
duzeltmesi yok.

Rapor: `reports/WP15_AGAC_MODELLERI_SONUCLARI.md`
Sekiller: `reports/figures/WP15/01-03`
Kayitlar: `reports/qa/WP15/tree_v1/`

## 10. Teknik dogrulama arsivi

`EMT2_Teknik_Dogrulama_Arsivi/` — ana rapordan cikarilan teknik icerigin
(kanit dizinleri, hash listeleri, dosya yollari, test sayilari, is paketi
kodlari) depodaki gercek konumlarini gosteren dizin belgesi. Hicbir dosya
tasinmadi veya silinmedi.

```bash
.venv_wp13/Scripts/python.exe -I scripts/wp16_teknik_arsiv.py
```

## 11. EMT2 nihai raporu (v6 — GUNCEL)

**`EMT2_Akademik_v6/EMT2_FINAL_REPORT.docx` / `.pdf`** resmi EMT sablonu
uzerine sifirdan kurulmus surumdur; 53 sayfa, 8 bolum, 18 sekil, 11
cizelge. v3/v4/v5 klasorleri tarihsel olarak durur.

Uretim ve denetim:

```bash
.venv_wp13/Scripts/python.exe -I EMT2_Akademik_v6/calisma/uret_v6.py
```

```bash
powershell -ExecutionPolicy Bypass -File EMT2_Akademik_v6/calisma/disa_aktar.ps1
```

```bash
.venv_wp13/Scripts/python.exe -I EMT2_Akademik_v6/calisma/denetle.py
```

`disa_aktar.ps1` Word ile alan kodlarini gunceller: icindekiler, sekil ve
cizelge listelerinin sayfa numaralari bu adimda dolar. `denetle.py` yedi
denetim yapar; rapordaki her sayisal degerin kayitli QA ciktisinda
bulundugunu dogrular.

Ayrinti ve bilinen eksikler: `EMT2_Akademik_v6/SURUM_NOTU.md`

# WP11 nihai kapanış kanıtları — 08.11.2026

Kabul edilmiş B1 SHAP/graf açıklaması sonuçları yeniden üretilip değiştirilmedi. Bu dizin ayrı kapanış denetimidir;WP12 uygulanmadı.

- `prior_artifacts_sha256.json`:3139 kabul edilmiş dosyanın başlangıç hash'leri. `run_status_before.md` önceki ilerleme kaydının tam bayt arşividir.
- `manifest_checks.csv`, `model_integrity_all742.csv`:8 önceki manifest ve742 ağırlık–metadata çiftinin kimlik/hash/numeric-state kontrolü.
- `contribution_stream_checks.csv`, `all_intervention_key_checks.csv`:tam2.440.976 katkı satırı ve8358 müdahale anahtarının source kimliği,yerel PT tekilliği,orijinal çıktı/Δz veözet eşitliği.
- `NA_source_consistency.csv`:kaynak bundle'dan yeniden türetilen eksik yolların eski NA tablolarıyla eşitliği. Gerçek sıfır katkı ayrı kalır.
- `replay_keys_frozen.csv`, `replay_commit.json`:katkı değerlerine göre seçilmemiş mevcut kayıtlar. `existing_attribution_replay.csv` bunların iki yöntemde100 müdahale/29560 PT satırlık kontrolüdür. Tam attribution üretimi değildir.
- `original_model_output_replay.csv`:10 kayıtlı A1P1 modelinin35974 orijinal logit kaydıyla eşitliği.
- `*_closure_rerun.txt`, `tests_rerun_summary.csv`:26 graf ve18 B1 testi için eski logları ezmeyen yeni kanıt.
- `network_data_consistency.csv`:gerçek ağ JSON'larının tam/örnek CSV ve source graph ile uyumu. `image_data_checks.csv` ve `figure_reconstruction/`:kabul edilmiş notebook'tan farklı konuma çizilen altı PNG;orijinal ve gömülü görüntülerle piksel eşitliği.
- `accepted_performance_unchanged.csv`:yeni AP/CI hesabı değildir;WP09/WP10'dan okunan sabit referanslar ve kaynak hash'leri.
- `closure_checks.json`, `evidence_manifest.json`, `evidence_manifest.sha256`:nihai kapanış sonucu ve yeni kanıtları bağlayan manifest. Hash kontrolü dış noter/zaman damgası iddiası değildir.

Oldukça büyük ham XML/STRING tekrar taranmadı. Modelde kullanılan işlenmiş kaynaklar kontrol edildi. Bütün müdahale forward'ları değil,önceden kimlikle seçilen100 mevcut müdahale tekrarlandı;tamCSV'deki bütün kayıtlar ise cebir/kimlik/sözlük/özet kontrollerinden geçti. Yöntemler veya kaynaklar değiştirilmedi.

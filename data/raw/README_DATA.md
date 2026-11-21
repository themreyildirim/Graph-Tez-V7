# Ham veri burada depolanmak zorunda değil

Ham veri **depo dışında**, yapılandırılabilir bir kökten **salt okunur** kullanılır.
Kök şu sırayla çözümlenir (`scripts/paths.py`):

1. `GRAPH_TEZ_DATA_ROOT` ortam değişkeni
2. `configs/data_paths.yaml` içindeki `dataset_root`
3. ilgili script'teki tarihsel varsayılan

Hangi veri setinin kullanıldığı yalnız **isim, sürüm ve lisans** olarak
[`DATA_INVENTORY.md`](../../DATA_INVENTORY.md) içinde belgelenmiştir.

Kurallar:

- Gereksiz dosyaları (toplam ~4.4 GB) proje içine kopyalamayın.
- Bu depo hiçbir ham veri setini veya hasta kaydını içermez.
- Görünmeyen kaynakları varsaymayın; yalnız allowlist kaynaklarını okuyun.

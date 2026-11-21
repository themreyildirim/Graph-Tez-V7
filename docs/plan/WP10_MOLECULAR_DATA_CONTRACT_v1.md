# WP10 moleküler veri sözleşmesi v1

Durum: teknik encoder uygulandı; gerçek PT eğitimi için yetki yoktur. Eski WP09 sözleşmesi korunur.

- Kaynak WP04 structure_sources/structure_validation:62 primary ID ve aynı CID/InChIKey;54 atom maskesi açık,8 inceleme kapalıdır.
- Data yalnız x float32[N,44], edge_index int64[2,2B], edge_attr float32[2B,14] ve explicit num_nodes taşır. y/ID/ek alan reddedilir. Kaynak ve QC bilgisi ayrı registry'dedir.
- Sabit kategoriler feature_schema.json içindedir. H sayısı/yük/aromatiklik/stereo ayrıdır. Atom indeksi özellik değildir. Belirtilmemiş potansiyel atom stereo ayrı token; belirtilmemiş potansiyel çift bağ ANY olarak kodlanır. Ham kaynak stereo ve direction metadata korunur; R/S/E/Z tamamlanmaz.
- Her kovalent bağ iki yönlüdür; invariant edge_attr iki yönde aynı ve hizalıdır. Self-loop, duplicate ve moleküller arası kenar yasaktır. İzole atomlar num_nodes ile korunur.
- Sayısal NPZ allow_pickle=False ile Data'ya yeniden kurulur. Dosya ve kanonik tensor hash'leri kontrol edilir. Bütün62 için kaynak cache'i tutmak bütün62'yi eğitim grafına eklemek değildir.
- load_context/validate_context_bundles frozen train/query üyeliklerini doğrular. Generic encoder fold seçmez; context kontrolü giriş katmanında zorunludur. Ordered MolecularInput.ids yalnız join içindir.
- QC maskesi WP04 sabit54 listesiyle kontrol edilir. A0 etkin atom maskesi0; A1 bu54 maskeyi kullanır. Frozen61 uygunluğu ve Methenamine eligible=False değişmez.
- Encoder44→16, tek bond-aware residual mean, global mean→8;1592 parametre. WP09 base141+masked8+mask1=150; başlıksız toplam5512. Gerçek veride head=None.
- A0P0/A0P1/A1P0/A1P1 aynı mimari ve context başlangıcını kullanır. P0 boş protein komşuluğu; P1 strict insan700. Context80 ve koşullu E.coli PPI eklenmez.
- ProteinCache train protein temsili, graph/model digest ve variant taşır. Query cache'e geri mesaj vermez; yeni query proteini eski self-only yolundadır. PT etiketi bu ABI'ya giremez.
- Seed20261106/context formülü, CPU1 thread; float64 permutation toleransı1e-12. İleride gerçek trainer için ayrıca kullanıcı onayı ve train-only PT/heldout/selection testleri gerekir.

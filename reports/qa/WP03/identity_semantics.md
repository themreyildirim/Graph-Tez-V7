# Kimlik dönüşümü kanıtı

05.11.2026. Yalnız mevcut veri kaynaklarının format açıklamaları okundu; ek STITCH/SIDER veri dosyası indirilmedi.

- [Resmi STITCH README](https://stitch-db.org/download/README): CID0/CIDs stereo kimliğin suffix'i PubChem CID'dir. CID1/CIDm flat kimlik, stereo biçimlerin birleştirilmiş temsilidir; baştaki tür işareti sayıdan ayrılmalıdır. STITCH ayrıca tuz biçimlerini birleştirdiğini belirtir. Kimlik eşitliği, ayrı ürün/formülasyon için klinik eşdeğerlik kanıtı değildir.
- [Resmi SIDER README](https://sideeffects.embl.de/media/download/README): ilk iki alan flat/stereo STITCH, üçüncü etiket CUI, dördüncü LLT/PT türü, beşinci MedDRA teriminin UMLS CUI'si, altıncı ad. LLT→PT bağlantısı UMLS'den türetilmiştir. CUI'ler MedDRA'nın sayısal kodu değildir.
- [PubChem kimyasal kimlik açıklaması](https://pubchem.ncbi.nlm.nih.gov/docs/structure-search): bağlantı yapısı ile stereokimya eşitliği farklı kimlik ölçütleridir. Flat eşleşme bu nedenle kesin stereo eşleşme yerine geçirilmez.

SIDER web sayfası otomatik erişim koruması, eski STITCH alan adı da sertifika hatası verdi. README'ler güncel resmi alan adlarından sistem curl ile başarıyla okundu; sertifika denetimi kapatılmadı. Genel web sonuçlarındaki üçüncü taraf dönüşüm kodları kullanılmadı.

Yerel örnek: CID100000085 → tür=flat, suffix CID=85; CID000010917 → tür=stereo, suffix CID=10917. İlk değerin CID yazısını kaldırıp 100000085 diye PubChem'e bağlanması hatalıdır. Flat=85 ile stereo=10917 aynı CID değildir.

Kesin eşleme politikası: XML Compound CID ile DrugBank köprü CID uyumu → türü doğrulanmış stereo CID eşitliği → SIDER satırının PT ve geçerli UMLS CUI kontrolü. `SID` bu yola girmez. Flat-only adayların stereo biçimleri raporlanır ama etiketleri kesin pozitiflere eklenmez. Çözülemeyen tuz/formülasyon kimyası isimle veya SID sayısıyla doldurulmaz. Kaynak kimliği düzeyindeki bu doğrulama klinik nedensellik veya bireysel risk doğrulaması değildir.

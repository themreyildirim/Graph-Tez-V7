# 📊 GIG Heterojen GNN Tez Veri Seti Dokümantasyonu (v6)

Bu doküman Drive klasörünüzdeki güncel v6 dosyalarından otomatik üretilmiştir.

---

## 📄 Dosya: `ilac_feature_v5_atc.csv`
- **Satır Sayısı:** 56
- **Sütun Sayısı:** 33

### 🛠️ Sütun Yapısı ve İlk 3 Örnek

|     MW |   LogP |   HBD |   HBA |   TPSA | DrugBank_ID   | Drug_Name    |   pubchem_clean |   MW_norm |   LogP_norm |   HBD_norm |   HBA_norm |   TPSA_norm |   ATC_A01A |   ATC_A02B |   ATC_A07A |   ATC_D01A |   ATC_D06B |   ATC_D10A |   ATC_G01A |   ATC_J01C |   ATC_J01D |   ATC_J01E |   ATC_J01M |   ATC_J01R |   ATC_J01X |   ATC_J02A |   ATC_J04A |   ATC_J04B |   ATC_P01A |   ATC_S01A |   ATC_S02A |   ATC_S03A |
|-------:|-------:|------:|------:|-------:|:--------------|:-------------|----------------:|----------:|------------:|-----------:|-----------:|------------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|
| 306.27 |    0.4 |     1 |     7 |   81.7 | DB00196       | Fluconazole  |            3365 |  0.128904 |    0.55303  |  0.0526316 |       0.24 |    0.124756 |          0 |          0 |          0 |          1 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          1 |          0 |          1 |          0 |          0 |          0 |          0 |          0 |          0 |
| 733.9  |    2.7 |     5 |    14 |  194   | DB00199       | Erythromycin |           12560 |  0.454827 |    0.727273 |  0.263158  |       0.52 |    0.344006 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |
| 749    |    4   |     5 |    14 |  180   | DB00207       | Azithromycin |          447043 |  0.466335 |    0.825758 |  0.263158  |       0.52 |    0.316673 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |          0 |

---

## 📄 Dosya: `protein_feature_v6.csv`
- **Satır Sayısı:** 70
- **Sütun Sayısı:** 54

### 🛠️ Sütun Yapısı ve İlk 3 Örnek

| UniProt_ID   | Gene_Name   | Organizma                        |   kalite_skoru |   AAC_A |   AAC_C |   AAC_D |   AAC_E |   AAC_F |   AAC_G |   AAC_H |   AAC_I |   AAC_K |   AAC_L |   AAC_M |   AAC_N |   AAC_P |   AAC_Q |   AAC_R |   AAC_S |   AAC_T |   AAC_V |   AAC_W |   AAC_Y |   DC_Asidik_Asidik |   DC_Asidik_Bazik |   DC_Asidik_Polar |   DC_Asidik_Hidrofobik |   DC_Asidik_Aromatik |   DC_Bazik_Asidik |   DC_Bazik_Bazik |   DC_Bazik_Polar |   DC_Bazik_Hidrofobik |   DC_Bazik_Aromatik |   DC_Polar_Asidik |   DC_Polar_Bazik |   DC_Polar_Polar |   DC_Polar_Hidrofobik |   DC_Polar_Aromatik |   DC_Hidrofobik_Asidik |   DC_Hidrofobik_Bazik |   DC_Hidrofobik_Polar |   DC_Hidrofobik_Hidrofobik |   DC_Hidrofobik_Aromatik |   DC_Aromatik_Asidik |   DC_Aromatik_Bazik |   DC_Aromatik_Polar |   DC_Aromatik_Hidrofobik |   DC_Aromatik_Aromatik |   YZ_Asidik |   YZ_Bazik |   YZ_Polar |   YZ_Hidrofobik |   YZ_Aromatik |
|:-------------|:------------|:---------------------------------|---------------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|-------------------:|------------------:|------------------:|-----------------------:|---------------------:|------------------:|-----------------:|-----------------:|----------------------:|--------------------:|------------------:|-----------------:|-----------------:|----------------------:|--------------------:|-----------------------:|----------------------:|----------------------:|---------------------------:|-------------------------:|---------------------:|--------------------:|--------------------:|-------------------------:|-----------------------:|------------:|-----------:|-----------:|----------------:|--------------:|
| P10613       | ERG11       | Yeast                            |              1 |  0.052  |  0.009  |  0.0591 |  0.0627 |  0.0591 |  0.0573 |  0.0269 |  0.0573 |  0.0627 |  0.095  |  0.0251 |  0.0358 |  0.0538 |  0.0323 |  0.0466 |  0.0717 |  0.0609 |  0.0645 |  0.0143 |  0.0538 |             0.0164 |            0.0205 |            0.0308 |                 0.0595 |               0.0041 |            0.0246 |           0.0246 |           0.0205 |                0.0513 |              0.0164 |            0.0308 |           0.0267 |           0.0493 |                0.1027 |              0.0164 |                 0.0452 |                0.0616 |                0.1047 |                     0.1889 |                   0.0329 |               0.0103 |              0.0082 |              0.0164 |                   0.0329 |                 0.0041 |      0.1218 |     0.1362 |     0.2007 |          0.4068 |        0.1272 |
| P0C0X2       | folP2       | Mycobacterium leprae (strain TN) |              1 |  0.138  |  0.0153 |  0.0675 |  0.0583 |  0.0245 |  0.0859 |  0.0276 |  0.0368 |  0.0123 |  0.0859 |  0.0215 |  0.0184 |  0.0368 |  0.0184 |  0.0859 |  0.046  |  0.0859 |  0.1074 |  0.0123 |  0.0153 |             0.0152 |            0.0228 |            0.0304 |                 0.076  |               0.0038 |            0.019  |           0.0114 |           0.0342 |                0.0722 |              0.0038 |            0.0342 |           0.0418 |           0.0228 |                0.0798 |              0.0152 |                 0.076  |                0.0684 |                0.0875 |                     0.251  |                   0.0076 |               0.0076 |              0.0038 |              0.0076 |                   0.0076 |                 0      |      0.1258 |     0.1258 |     0.1687 |          0.4509 |        0.0521 |
| P0C0X1       | folP1       | Mycobacterium leprae (strain TN) |              1 |  0.1543 |  0.0064 |  0.074  |  0.0482 |  0.0096 |  0.0965 |  0.0257 |  0.0386 |  0.0161 |  0.0932 |  0.0161 |  0.0225 |  0.0547 |  0.0257 |  0.074  |  0.0514 |  0.0418 |  0.119  |  0.0161 |  0.0161 |             0.004  |            0.016  |            0.028  |                 0.084  |               0      |            0.016  |           0.008  |           0.012  |                0.084  |              0.012  |            0.036  |           0.028  |           0.02   |                0.06   |              0.012  |                 0.08   |                0.068  |                0.104  |                     0.276  |                   0.016  |               0.008  |              0.008  |              0.004  |                   0.016  |                 0      |      0.1222 |     0.1158 |     0.1414 |          0.4855 |        0.0418 |

---

## 📄 Dosya: `ilac_protein_eslesmesi_v6.csv`
- **Satır Sayısı:** 153
- **Sütun Sayısı:** 5

### 🛠️ Sütun Yapısı ve İlk 3 Örnek

| DrugBank_ID   | Drug_Name   | UniProt_ID   | Gene_Name   | Organizma                        |
|:--------------|:------------|:-------------|:------------|:---------------------------------|
| DB00196       | Fluconazole | P10613       | ERG11       | Yeast                            |
| DB00250       | Dapsone     | P0C0X2       | folP2       | Mycobacterium leprae (strain TN) |
| DB00250       | Dapsone     | P0C0X1       | folP1       | Mycobacterium leprae (strain TN) |

---

## 📄 Dosya: `protein_dizileri_v6.csv`
- **Satır Sayısı:** 70
- **Sütun Sayısı:** 4

### 🛠️ Sütun Yapısı ve İlk 3 Örnek

| UniProt_ID   | Gene_Name   | Sequence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Organizma                        |
|:-------------|:------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------|
| P10613       | ERG11       | >lcl|BSEQ0010022|Lanosterol 14-alpha demethylaseMAIVETVIDGINYFLSLSVTQQISILLGVPFVYNLVWQYLYSLRKDRAPLVFYWIPWFGSAASYGQQPYEFFESCRQKYGDVFSFMLLGKIMTVYLGPKGHEFVFNAKLSDVSAEDAYKHLTTPVFGKGVIYDCPNSRLMEQKKFAKFALTTDSFKRYVPKIREEILNYFVTDESFKLKEKTHGVANVMKTQPEITIFTASRSLFGDEMRRIFDRSFAQLYSDLDKGFTPINFVFPNLPLPHYWRRDAAQKKISATYMKEIKSRRERGDIDPNRDLIDSLLIHSTYKDGVKMTDQEIANLLIGILMGGQHTSASTSAWFLLHLGEKPHLQDVIYQEVVELLKEKGGDLNDLTYEDLQKLPSVNNTIKETLRMHMPLHSIFRKVTNPLRIPETNYIVPKGHYVLVSPGYAHTSERYFDNPEDFDPTRWDTAAAKANSVSFNSSDEVDYGFGKVSKGVSSPYLPFGGGRHRCIGEQFAYVQLGTILTTFVYNLRWTIDGYKVPDPDYSSMVVLPTEPAEIIWEKRETCMF | Yeast                            |
| P0C0X2       | folP2       | >lcl|BSEQ0011514|Inactive dihydropteroate synthase 2MQSMLCGRPVAADRQLIMAIVNRTPDSFYDRGATFSDEAARAAAHRAVAEGADVIDVGGVKAGPGQGVDVDTEIARLVPFIEWLRSAYTDLLISVDTWRAEVARLACTAGADLINDSWGGADPAMHEVAAELGAGLVCSHTGGALPRTRPFRVSYGTTTRGVVDDVIRQVTAAAERAVAAGVTRDSVLVDPTHDFGKNTFHGLLLLRHVDELVKTGWPVLMSLSNKDFVGETLGVGLTERLEGTLAATALAAAAGVRMFRVHEVVATRRVLEMVASIQGTRPPTRTVRGLA                                                                                                                                                                                                                                          | Mycobacterium leprae (strain TN) |
| P0C0X1       | folP1       | >lcl|BSEQ0011512|Dihydropteroate synthaseMSLAPVQVIGVLNVTDNSFSDGGRYLDPDDAVQHGLAMVAEGAAIVDVGGESTRPGAIRTDPRVELSRIVPVVKELAAQGITVSIDTTRADVARAALQSGARIVNDVSGGRADPAMAPLVAEAGVAWVLMHWRLMSAERPYEAPNYRDVVAEVRADLLAGVDQAVAAGVDPGSLVIDPGLGFAKTGQHNWALLNALPELVATGVPILLGASRKRFLGRLLAGADGAVRPPDGRETATAVISALAALHGAWGVRVHDVRASVDALKVVGAWLHAGPQIEKVRCDG                                                                                                                                                                                                                                                            | Mycobacterium leprae (strain TN) |

---

## 📄 Dosya: `xai_top5_tahminler.csv`
- **Satır Sayısı:** 190
- **Sütun Sayısı:** 6

### 🛠️ Sütun Yapısı ve İlk 3 Örnek

| İlaç        | DrugBank_ID   |   Rank | Yan Etki       |   Skor | İsabet   |
|:------------|:--------------|-------:|:---------------|-------:|:---------|
| Fluconazole | DB00196       |      1 | Mide bulantısı | 0.9853 | ✓        |
| Fluconazole | DB00196       |      2 | Deri döküntüsü | 0.9828 | ✓        |
| Fluconazole | DB00196       |      3 | Kusma          | 0.9727 | ✓        |

---

## 📄 Dosya: `xai_protein_katkisi.csv`
- **Satır Sayısı:** 92
- **Sütun Sayısı:** 6

### 🛠️ Sütun Yapısı ve İlk 3 Örnek

| İlaç        | DrugBank_ID   |   Protein_Rank | UniProt_ID   | Gene   |   Etki_Skoru |
|:------------|:--------------|---------------:|:-------------|:-------|-------------:|
| Fluconazole | DB00196       |              1 | P10613       | ERG11  |      11.8016 |
| Dapsone     | DB00250       |              1 | P0C0X1       | folP1  |      11.692  |
| Dapsone     | DB00250       |              2 | P0C0X2       | folP2  |       8.9587 |

---

## 📄 Dosya: `xai_drug_feature_importance.csv`
- **Satır Sayısı:** 25
- **Sütun Sayısı:** 2

### 🛠️ Sütun Yapısı ve İlk 3 Örnek

| Feature   |    Önem |
|:----------|--------:|
| ATC_J01M  | 8.86643 |
| MW_norm   | 5.93612 |
| LogP_norm | 5.75962 |

---

## 📄 Dosya: `xai_protein_feature_importance.csv`
- **Satır Sayısı:** 51
- **Sütun Sayısı:** 2

### 🛠️ Sütun Yapısı ve İlk 3 Örnek

| Feature       |     Önem |
|:--------------|---------:|
| kalite_skoru  | 4.53388  |
| YZ_Hidrofobik | 0.616422 |
| YZ_Polar      | 0.604468 |

---


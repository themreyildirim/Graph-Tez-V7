# Drive CSV şemaları ve kalite profilleri

Yedi CSV doğrudan Google Drive bağlantısından bellekte okundu; ham CSV kopyası yerel diske yazılmadı. Yanıt UTF-8 bayt uzunluğu yedi dosyada da Drive boyutuyla eşleşti; okuma öncesi/sonrası size ve modified_time değişmedi. Bunlar kriptografik checksum kontrolü değildir. Sürüm alanı olmayan CSV için dosya adı ve değiştirilme tarihi provenans olarak tutuldu.

## ilac_feature_v5_atc.csv

Kaynak: [1bJXKgwoGrchdJtc6BBl6nzKEFijfGTV2](https://drive.google.com/file/d/1bJXKgwoGrchdJtc6BBl6nzKEFijfGTV2/view?usp=drivesdk); değiştirilme: 2026-05-15T02:44:25.295Z.
Tam CSV: **56 satır × 33 sütun**. Tam satır tekrar fazlası: 0.

| Alan | Gözlenen tip | Tüm CSV boş | Boş % | İlk en çok 1000 boş / n |
|---|---|---:|---:|---:|
| MW | numeric-like | 0 | 0.0000 | 0/56 |
| LogP | numeric-like | 0 | 0.0000 | 0/56 |
| HBD | integer-like | 0 | 0.0000 | 0/56 |
| HBA | integer-like | 0 | 0.0000 | 0/56 |
| TPSA | numeric-like | 0 | 0.0000 | 0/56 |
| DrugBank_ID | string | 0 | 0.0000 | 0/56 |
| Drug_Name | string | 0 | 0.0000 | 0/56 |
| pubchem_clean | integer-like | 0 | 0.0000 | 0/56 |
| MW_norm | numeric-like | 0 | 0.0000 | 0/56 |
| LogP_norm | numeric-like | 0 | 0.0000 | 0/56 |
| HBD_norm | numeric-like | 0 | 0.0000 | 0/56 |
| HBA_norm | numeric-like | 0 | 0.0000 | 0/56 |
| TPSA_norm | numeric-like | 0 | 0.0000 | 0/56 |
| ATC_A01A | integer-like | 0 | 0.0000 | 0/56 |
| ATC_A02B | integer-like | 0 | 0.0000 | 0/56 |
| ATC_A07A | integer-like | 0 | 0.0000 | 0/56 |
| ATC_D01A | integer-like | 0 | 0.0000 | 0/56 |
| ATC_D06B | integer-like | 0 | 0.0000 | 0/56 |
| ATC_D10A | integer-like | 0 | 0.0000 | 0/56 |
| ATC_G01A | integer-like | 0 | 0.0000 | 0/56 |
| ATC_J01C | integer-like | 0 | 0.0000 | 0/56 |
| ATC_J01D | integer-like | 0 | 0.0000 | 0/56 |
| ATC_J01E | integer-like | 0 | 0.0000 | 0/56 |
| ATC_J01M | integer-like | 0 | 0.0000 | 0/56 |
| ATC_J01R | integer-like | 0 | 0.0000 | 0/56 |
| ATC_J01X | integer-like | 0 | 0.0000 | 0/56 |
| ATC_J02A | integer-like | 0 | 0.0000 | 0/56 |
| ATC_J04A | integer-like | 0 | 0.0000 | 0/56 |
| ATC_J04B | integer-like | 0 | 0.0000 | 0/56 |
| ATC_P01A | integer-like | 0 | 0.0000 | 0/56 |
| ATC_S01A | integer-like | 0 | 0.0000 | 0/56 |
| ATC_S02A | integer-like | 0 | 0.0000 | 0/56 |
| ATC_S03A | integer-like | 0 | 0.0000 | 0/56 |

İlk üç kayıt (uzun diziler görünüm için kısaltılmıştır):

```json
[
  {
    "MW": "306.27",
    "LogP": "0.4",
    "HBD": "1",
    "HBA": "7",
    "TPSA": "81.7",
    "DrugBank_ID": "DB00196",
    "Drug_Name": "Fluconazole",
    "pubchem_clean": "3365",
    "MW_norm": "0.1289041659680197",
    "LogP_norm": "0.5530303030303031",
    "HBD_norm": "0.0526315789473684",
    "HBA_norm": "0.24",
    "TPSA_norm": "0.1247559547051932",
    "ATC_A01A": "0",
    "ATC_A02B": "0",
    "ATC_A07A": "0",
    "ATC_D01A": "1",
    "ATC_D06B": "0",
    "ATC_D10A": "0",
    "ATC_G01A": "0",
    "ATC_J01C": "0",
    "ATC_J01D": "0",
    "ATC_J01E": "0",
    "ATC_J01M": "0",
    "ATC_J01R": "1",
    "ATC_J01X": "0",
    "ATC_J02A": "1",
    "ATC_J04A": "0",
    "ATC_J04B": "0",
    "ATC_P01A": "0",
    "ATC_S01A": "0",
    "ATC_S02A": "0",
    "ATC_S03A": "0"
  },
  {
    "MW": "733.9",
    "LogP": "2.7",
    "HBD": "5",
    "HBA": "14",
    "TPSA": "194.0",
    "DrugBank_ID": "DB00199",
    "Drug_Name": "Erythromycin",
    "pubchem_clean": "12560",
    "MW_norm": "0.454826760971297",
    "LogP_norm": "0.7272727272727274",
    "HBD_norm": "0.2631578947368421",
    "HBA_norm": "0.52",
    "TPSA_norm": "0.344006247559547",
    "ATC_A01A": "0",
    "ATC_A02B": "0",
    "ATC_A07A": "0",
    "ATC_D01A": "0",
    "ATC_D06B": "0",
    "ATC_D10A": "0",
    "ATC_G01A": "0",
    "ATC_J01C": "0",
    "ATC_J01D": "0",
    "ATC_J01E": "0",
    "ATC_J01M": "0",
    "ATC_J01R": "0",
    "ATC_J01X": "0",
    "ATC_J02A": "0",
    "ATC_J04A": "0",
    "ATC_J04B": "0",
    "ATC_P01A": "0",
    "ATC_S01A": "0",
    "ATC_S02A": "0",
    "ATC_S03A": "0"
  },
  {
    "MW": "749.0",
    "LogP": "4.0",
    "HBD": "5",
    "HBA": "14",
    "TPSA": "180.0",
    "DrugBank_ID": "DB00207",
    "Drug_Name": "Azithromycin",
    "pubchem_clean": "447043",
    "MW_norm": "0.4663353810039175",
    "LogP_norm": "0.8257575757575758",
    "HBD_norm": "0.2631578947368421",
    "HBA_norm": "0.52",
    "TPSA_norm": "0.3166731745411948",
    "ATC_A01A": "0",
    "ATC_A02B": "0",
    "ATC_A07A": "0",
    "ATC_D01A": "0",
    "ATC_D06B": "0",
    "ATC_D10A": "0",
    "ATC_G01A": "0",
    "ATC_J01C": "0",
    "ATC_J01D": "0",
    "ATC_J01E": "0",
    "ATC_J01M": "0",
    "ATC_J01R": "0",
    "ATC_J01X": "0",
    "ATC_J02A": "0",
    "ATC_J04A": "0",
    "ATC_J04B": "0",
    "ATC_P01A": "0",
    "ATC_S01A": "0",
    "ATC_S02A": "0",
    "ATC_S03A": "0"
  }
]
```

## protein_feature_v6.csv

Kaynak: [17F4x5gn-Y95ozHZaBk31iDlXrnFvTwEm](https://drive.google.com/file/d/17F4x5gn-Y95ozHZaBk31iDlXrnFvTwEm/view?usp=drivesdk); değiştirilme: 2026-05-15T02:21:45.428Z.
Tam CSV: **70 satır × 54 sütun**. Tam satır tekrar fazlası: 0.

| Alan | Gözlenen tip | Tüm CSV boş | Boş % | İlk en çok 1000 boş / n |
|---|---|---:|---:|---:|
| UniProt_ID | string | 0 | 0.0000 | 0/70 |
| Gene_Name | string | 2 | 2.8571 | 2/70 |
| Organizma | string | 0 | 0.0000 | 0/70 |
| kalite_skoru | integer-like | 0 | 0.0000 | 0/70 |
| AAC_A | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_C | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_D | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_E | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_F | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_G | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_H | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_I | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_K | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_L | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_M | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_N | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_P | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_Q | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_R | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_S | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_T | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_V | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_W | numeric-like | 0 | 0.0000 | 0/70 |
| AAC_Y | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Asidik_Asidik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Asidik_Bazik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Asidik_Polar | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Asidik_Hidrofobik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Asidik_Aromatik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Bazik_Asidik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Bazik_Bazik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Bazik_Polar | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Bazik_Hidrofobik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Bazik_Aromatik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Polar_Asidik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Polar_Bazik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Polar_Polar | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Polar_Hidrofobik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Polar_Aromatik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Hidrofobik_Asidik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Hidrofobik_Bazik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Hidrofobik_Polar | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Hidrofobik_Hidrofobik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Hidrofobik_Aromatik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Aromatik_Asidik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Aromatik_Bazik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Aromatik_Polar | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Aromatik_Hidrofobik | numeric-like | 0 | 0.0000 | 0/70 |
| DC_Aromatik_Aromatik | numeric-like | 0 | 0.0000 | 0/70 |
| YZ_Asidik | numeric-like | 0 | 0.0000 | 0/70 |
| YZ_Bazik | numeric-like | 0 | 0.0000 | 0/70 |
| YZ_Polar | numeric-like | 0 | 0.0000 | 0/70 |
| YZ_Hidrofobik | numeric-like | 0 | 0.0000 | 0/70 |
| YZ_Aromatik | numeric-like | 0 | 0.0000 | 0/70 |

İlk üç kayıt (uzun diziler görünüm için kısaltılmıştır):

```json
[
  {
    "UniProt_ID": "P10613",
    "Gene_Name": "ERG11",
    "Organizma": "Yeast",
    "kalite_skoru": "1",
    "AAC_A": "0.052",
    "AAC_C": "0.009",
    "AAC_D": "0.0591",
    "AAC_E": "0.0627",
    "AAC_F": "0.0591",
    "AAC_G": "0.0573",
    "AAC_H": "0.0269",
    "AAC_I": "0.0573",
    "AAC_K": "0.0627",
    "AAC_L": "0.095",
    "AAC_M": "0.0251",
    "AAC_N": "0.0358",
    "AAC_P": "0.0538",
    "AAC_Q": "0.0323",
    "AAC_R": "0.0466",
    "AAC_S": "0.0717",
    "AAC_T": "0.0609",
    "AAC_V": "0.0645",
    "AAC_W": "0.0143",
    "AAC_Y": "0.0538",
    "DC_Asidik_Asidik": "0.0164",
    "DC_Asidik_Bazik": "0.0205",
    "DC_Asidik_Polar": "0.0308",
    "DC_Asidik_Hidrofobik": "0.0595",
    "DC_Asidik_Aromatik": "0.0041",
    "DC_Bazik_Asidik": "0.0246",
    "DC_Bazik_Bazik": "0.0246",
    "DC_Bazik_Polar": "0.0205",
    "DC_Bazik_Hidrofobik": "0.0513",
    "DC_Bazik_Aromatik": "0.0164",
    "DC_Polar_Asidik": "0.0308",
    "DC_Polar_Bazik": "0.0267",
    "DC_Polar_Polar": "0.0493",
    "DC_Polar_Hidrofobik": "0.1027",
    "DC_Polar_Aromatik": "0.0164",
    "DC_Hidrofobik_Asidik": "0.0452",
    "DC_Hidrofobik_Bazik": "0.0616",
    "DC_Hidrofobik_Polar": "0.1047",
    "DC_Hidrofobik_Hidrofobik": "0.1889",
    "DC_Hidrofobik_Aromatik": "0.0329",
    "DC_Aromatik_Asidik": "0.0103",
    "DC_Aromatik_Bazik": "0.0082",
    "DC_Aromatik_Polar": "0.0164",
    "DC_Aromatik_Hidrofobik": "0.0329",
    "DC_Aromatik_Aromatik": "0.0041",
    "YZ_Asidik": "0.1218",
    "YZ_Bazik": "0.1362",
    "YZ_Polar": "0.2007",
    "YZ_Hidrofobik": "0.4068",
    "YZ_Aromatik": "0.1272"
  },
  {
    "UniProt_ID": "P0C0X2",
    "Gene_Name": "folP2",
    "Organizma": "Mycobacterium leprae (strain TN)",
    "kalite_skoru": "1",
    "AAC_A": "0.138",
    "AAC_C": "0.0153",
    "AAC_D": "0.0675",
    "AAC_E": "0.0583",
    "AAC_F": "0.0245",
    "AAC_G": "0.0859",
    "AAC_H": "0.0276",
    "AAC_I": "0.0368",
    "AAC_K": "0.0123",
    "AAC_L": "0.0859",
    "AAC_M": "0.0215",
    "AAC_N": "0.0184",
    "AAC_P": "0.0368",
    "AAC_Q": "0.0184",
    "AAC_R": "0.0859",
    "AAC_S": "0.046",
    "AAC_T": "0.0859",
    "AAC_V": "0.1074",
    "AAC_W": "0.0123",
    "AAC_Y": "0.0153",
    "DC_Asidik_Asidik": "0.0152",
    "DC_Asidik_Bazik": "0.0228",
    "DC_Asidik_Polar": "0.0304",
    "DC_Asidik_Hidrofobik": "0.076",
    "DC_Asidik_Aromatik": "0.0038",
    "DC_Bazik_Asidik": "0.019",
    "DC_Bazik_Bazik": "0.0114",
    "DC_Bazik_Polar": "0.0342",
    "DC_Bazik_Hidrofobik": "0.0722",
    "DC_Bazik_Aromatik": "0.0038",
    "DC_Polar_Asidik": "0.0342",
    "DC_Polar_Bazik": "0.0418",
    "DC_Polar_Polar": "0.0228",
    "DC_Polar_Hidrofobik": "0.0798",
    "DC_Polar_Aromatik": "0.0152",
    "DC_Hidrofobik_Asidik": "0.076",
    "DC_Hidrofobik_Bazik": "0.0684",
    "DC_Hidrofobik_Polar": "0.0875",
    "DC_Hidrofobik_Hidrofobik": "0.251",
    "DC_Hidrofobik_Aromatik": "0.0076",
    "DC_Aromatik_Asidik": "0.0076",
    "DC_Aromatik_Bazik": "0.0038",
    "DC_Aromatik_Polar": "0.0076",
    "DC_Aromatik_Hidrofobik": "0.0076",
    "DC_Aromatik_Aromatik": "0.0",
    "YZ_Asidik": "0.1258",
    "YZ_Bazik": "0.1258",
    "YZ_Polar": "0.1687",
    "YZ_Hidrofobik": "0.4509",
    "YZ_Aromatik": "0.0521"
  },
  {
    "UniProt_ID": "P0C0X1",
    "Gene_Name": "folP1",
    "Organizma": "Mycobacterium leprae (strain TN)",
    "kalite_skoru": "1",
    "AAC_A": "0.1543",
    "AAC_C": "0.0064",
    "AAC_D": "0.074",
    "AAC_E": "0.0482",
    "AAC_F": "0.0096",
    "AAC_G": "0.0965",
    "AAC_H": "0.0257",
    "AAC_I": "0.0386",
    "AAC_K": "0.0161",
    "AAC_L": "0.0932",
    "AAC_M": "0.0161",
    "AAC_N": "0.0225",
    "AAC_P": "0.0547",
    "AAC_Q": "0.0257",
    "AAC_R": "0.074",
    "AAC_S": "0.0514",
    "AAC_T": "0.0418",
    "AAC_V": "0.119",
    "AAC_W": "0.0161",
    "AAC_Y": "0.0161",
    "DC_Asidik_Asidik": "0.004",
    "DC_Asidik_Bazik": "0.016",
    "DC_Asidik_Polar": "0.028",
    "DC_Asidik_Hidrofobik": "0.084",
    "DC_Asidik_Aromatik": "0.0",
    "DC_Bazik_Asidik": "0.016",
    "DC_Bazik_Bazik": "0.008",
    "DC_Bazik_Polar": "0.012",
    "DC_Bazik_Hidrofobik": "0.084",
    "DC_Bazik_Aromatik": "0.012",
    "DC_Polar_Asidik": "0.036",
    "DC_Polar_Bazik": "0.028",
    "DC_Polar_Polar": "0.02",
    "DC_Polar_Hidrofobik": "0.06",
    "DC_Polar_Aromatik": "0.012",
    "DC_Hidrofobik_Asidik": "0.08",
    "DC_Hidrofobik_Bazik": "0.068",
    "DC_Hidrofobik_Polar": "0.104",
    "DC_Hidrofobik_Hidrofobik": "0.276",
    "DC_Hidrofobik_Aromatik": "0.016",
    "DC_Aromatik_Asidik": "0.008",
    "DC_Aromatik_Bazik": "0.008",
    "DC_Aromatik_Polar": "0.004",
    "DC_Aromatik_Hidrofobik": "0.016",
    "DC_Aromatik_Aromatik": "0.0",
    "YZ_Asidik": "0.1222",
    "YZ_Bazik": "0.1158",
    "YZ_Polar": "0.1414",
    "YZ_Hidrofobik": "0.4855",
    "YZ_Aromatik": "0.0418"
  }
]
```

## protein_dizileri_v6.csv

Kaynak: [1jswowpDg7qSneoWN88hB0Lgtr1B79on_](https://drive.google.com/file/d/1jswowpDg7qSneoWN88hB0Lgtr1B79on_/view?usp=drivesdk); değiştirilme: 2026-05-14T05:37:22.747Z.
Tam CSV: **70 satır × 4 sütun**. Tam satır tekrar fazlası: 0.

| Alan | Gözlenen tip | Tüm CSV boş | Boş % | İlk en çok 1000 boş / n |
|---|---|---:|---:|---:|
| UniProt_ID | string | 0 | 0.0000 | 0/70 |
| Gene_Name | string | 2 | 2.8571 | 2/70 |
| Sequence | string | 0 | 0.0000 | 0/70 |
| Organizma | string | 0 | 0.0000 | 0/70 |

İlk üç kayıt (uzun diziler görünüm için kısaltılmıştır):

```json
[
  {
    "UniProt_ID": "P10613",
    "Gene_Name": "ERG11",
    "Sequence": ">lcl|BSEQ0010022|Lanosterol 14-alpha demethylaseMAIVETVIDGINYFLSLSVTQQISILLGVPFVYNLVWQYLYSLRKDRAPLVFYWIPWFGSAASYGQQPYEFFESCRQKYGDVFSFMLLGKIMTVYLGPKGHEFVFNAKLSDVSAEDAYKHLTTPVFGKGVIY [truncated for display]",
    "Organizma": "Yeast"
  },
  {
    "UniProt_ID": "P0C0X2",
    "Gene_Name": "folP2",
    "Sequence": ">lcl|BSEQ0011514|Inactive dihydropteroate synthase 2MQSMLCGRPVAADRQLIMAIVNRTPDSFYDRGATFSDEAARAAAHRAVAEGADVIDVGGVKAGPGQGVDVDTEIARLVPFIEWLRSAYTDLLISVDTWRAEVARLACTAGADLINDSWGGADPAMHEV [truncated for display]",
    "Organizma": "Mycobacterium leprae (strain TN)"
  },
  {
    "UniProt_ID": "P0C0X1",
    "Gene_Name": "folP1",
    "Sequence": ">lcl|BSEQ0011512|Dihydropteroate synthaseMSLAPVQVIGVLNVTDNSFSDGGRYLDPDDAVQHGLAMVAEGAAIVDVGGESTRPGAIRTDPRVELSRIVPVVKELAAQGITVSIDTTRADVARAALQSGARIVNDVSGGRADPAMAPLVAEAGVAWVLMHWRLMSAER [truncated for display]",
    "Organizma": "Mycobacterium leprae (strain TN)"
  }
]
```

## ilac_protein_eslesmesi_v6.csv

Kaynak: [1SkXYX0w4k76yxwHZbLydz6Q5Aj9gA7cz](https://drive.google.com/file/d/1SkXYX0w4k76yxwHZbLydz6Q5Aj9gA7cz/view?usp=drivesdk); değiştirilme: 2026-05-14T05:37:21.845Z.
Tam CSV: **153 satır × 5 sütun**. Tam satır tekrar fazlası: 0.

| Alan | Gözlenen tip | Tüm CSV boş | Boş % | İlk en çok 1000 boş / n |
|---|---|---:|---:|---:|
| DrugBank_ID | string | 0 | 0.0000 | 0/153 |
| Drug_Name | string | 0 | 0.0000 | 0/153 |
| UniProt_ID | string | 0 | 0.0000 | 0/153 |
| Gene_Name | string | 2 | 1.3072 | 2/153 |
| Organizma | string | 0 | 0.0000 | 0/153 |

İlk üç kayıt (uzun diziler görünüm için kısaltılmıştır):

```json
[
  {
    "DrugBank_ID": "DB00196",
    "Drug_Name": "Fluconazole",
    "UniProt_ID": "P10613",
    "Gene_Name": "ERG11",
    "Organizma": "Yeast"
  },
  {
    "DrugBank_ID": "DB00250",
    "Drug_Name": "Dapsone",
    "UniProt_ID": "P0C0X2",
    "Gene_Name": "folP2",
    "Organizma": "Mycobacterium leprae (strain TN)"
  },
  {
    "DrugBank_ID": "DB00250",
    "Drug_Name": "Dapsone",
    "UniProt_ID": "P0C0X1",
    "Gene_Name": "folP1",
    "Organizma": "Mycobacterium leprae (strain TN)"
  }
]
```

## ilac_yan_etki_v5.csv

Kaynak: [1CZC7zCBFnDW2bQMN_8vD0MKnkaXqVBez](https://drive.google.com/file/d/1CZC7zCBFnDW2bQMN_8vD0MKnkaXqVBez/view?usp=drivesdk); değiştirilme: 2026-05-14T04:55:22.205Z.
Tam CSV: **865 satır × 6 sütun**. Tam satır tekrar fazlası: 0.

| Alan | Gözlenen tip | Tüm CSV boş | Boş % | İlk en çok 1000 boş / n |
|---|---|---:|---:|---:|
| pubchem_id | integer-like | 0 | 0.0000 | 0/865 |
| side_effect_name | string | 0 | 0.0000 | 0/865 |
| umls_cui | string | 0 | 0.0000 | 0/865 |
| se_kategori | string | 0 | 0.0000 | 0/865 |
| DrugBank_ID | string | 0 | 0.0000 | 0/865 |
| Drug_Name | string | 0 | 0.0000 | 0/865 |

İlk üç kayıt (uzun diziler görünüm için kısaltılmıştır):

```json
[
  {
    "pubchem_id": "5959",
    "side_effect_name": "Abdominal distension",
    "umls_cui": "C0000731",
    "se_kategori": "Şişkinlik",
    "DrugBank_ID": "DB00446",
    "Drug_Name": "Chloramphenicol"
  },
  {
    "pubchem_id": "5959",
    "side_effect_name": "Diarrhoea",
    "umls_cui": "C0011991",
    "se_kategori": "İshal",
    "DrugBank_ID": "DB00446",
    "Drug_Name": "Chloramphenicol"
  },
  {
    "pubchem_id": "5959",
    "side_effect_name": "Rash",
    "umls_cui": "C0015230",
    "se_kategori": "Deri döküntüsü",
    "DrugBank_ID": "DB00446",
    "Drug_Name": "Chloramphenicol"
  }
]
```

## drug links.csv

Kaynak: [1argDJtVoYYXQfYAWbO79gXQ9r-bbTWh2](https://drive.google.com/file/d/1argDJtVoYYXQfYAWbO79gXQ9r-bbTWh2/view?usp=drivesdk); değiştirilme: 2026-04-17T22:39:26.571Z.
Tam CSV: **19842 satır × 23 sütun**. Tam satır tekrar fazlası: 0.

| Alan | Gözlenen tip | Tüm CSV boş | Boş % | İlk en çok 1000 boş / n |
|---|---|---:|---:|---:|
| DrugBank ID | string | 0 | 0.0000 | 0/1000 |
| Name | string | 0 | 0.0000 | 0/1000 |
| CAS Number | string | 6735 | 33.9432 | 4/1000 |
| Drug Type | string | 0 | 0.0000 | 0/1000 |
| KEGG Compound ID | string | 17357 | 87.4761 | 369/1000 |
| KEGG Drug ID | string | 17669 | 89.0485 | 218/1000 |
| PubChem Compound ID | integer-like | 11120 | 56.0427 | 107/1000 |
| PubChem Substance ID | integer-like | 9400 | 47.3743 | 1/1000 |
| ChEBI ID | integer-like | 13791 | 69.5041 | 120/1000 |
| PharmGKB ID | string | 17996 | 90.6965 | 2/1000 |
| HET ID | string | 13250 | 66.7775 | 601/1000 |
| UniProt ID | string | 19747 | 99.5212 | 930/1000 |
| UniProt Title | string | 19750 | 99.5363 | 930/1000 |
| GenBank ID | string | 19772 | 99.6472 | 931/1000 |
| DPD ID | string | 17281 | 87.0930 | 198/1000 |
| RxList Link | string | 18570 | 93.5894 | 264/1000 |
| Pdrhealth Link | string | 19512 | 98.3369 | 771/1000 |
| Wikipedia ID | string | 12861 | 64.8171 | 6/1000 |
| Drugs.com Link | string | 18356 | 92.5108 | 220/1000 |
| NDC ID | unknown | 19842 | 100.0000 | 1000/1000 |
| ChemSpider ID | integer-like | 7744 | 39.0283 | 102/1000 |
| BindingDB ID | integer-like | 13893 | 70.0181 | 248/1000 |
| TTD ID | string | 18419 | 92.8283 | 94/1000 |

İlk üç kayıt (uzun diziler görünüm için kısaltılmıştır):

```json
[
  {
    "DrugBank ID": "DB00001",
    "Name": "Lepirudin",
    "CAS Number": "138068-37-8",
    "Drug Type": "BiotechDrug",
    "KEGG Compound ID": "",
    "KEGG Drug ID": "D06880",
    "PubChem Compound ID": "",
    "PubChem Substance ID": "46507011",
    "ChEBI ID": "",
    "PharmGKB ID": "PA450195",
    "HET ID": "",
    "UniProt ID": "P01050",
    "UniProt Title": "ITH1_HIRME",
    "GenBank ID": "",
    "DPD ID": "11916",
    "RxList Link": "http://www.rxlist.com/cgi/generic/lepirudin.htm",
    "Pdrhealth Link": "",
    "Wikipedia ID": "Lepirudin",
    "Drugs.com Link": "http://www.drugs.com/cdi/lepirudin.html",
    "NDC ID": "",
    "ChemSpider ID": "",
    "BindingDB ID": "",
    "TTD ID": "DAP000541"
  },
  {
    "DrugBank ID": "DB00002",
    "Name": "Cetuximab",
    "CAS Number": "205923-56-4",
    "Drug Type": "BiotechDrug",
    "KEGG Compound ID": "",
    "KEGG Drug ID": "D03455",
    "PubChem Compound ID": "",
    "PubChem Substance ID": "46507042",
    "ChEBI ID": "",
    "PharmGKB ID": "PA10040",
    "HET ID": "",
    "UniProt ID": "",
    "UniProt Title": "",
    "GenBank ID": "J00228",
    "DPD ID": "13175",
    "RxList Link": "http://www.rxlist.com/cgi/generic3/erbitux.htm",
    "Pdrhealth Link": "",
    "Wikipedia ID": "Cetuximab",
    "Drugs.com Link": "http://www.drugs.com/cdi/cetuximab.html",
    "NDC ID": "",
    "ChemSpider ID": "",
    "BindingDB ID": "",
    "TTD ID": "DNC000788"
  },
  {
    "DrugBank ID": "DB00003",
    "Name": "Dornase alfa",
    "CAS Number": "143831-71-4",
    "Drug Type": "BiotechDrug",
    "KEGG Compound ID": "",
    "KEGG Drug ID": "",
    "PubChem Compound ID": "",
    "PubChem Substance ID": "46507792",
    "ChEBI ID": "",
    "PharmGKB ID": "PA10318",
    "HET ID": "",
    "UniProt ID": "P24855",
    "UniProt Title": "DNAS1_HUMAN",
    "GenBank ID": "M55983",
    "DPD ID": "650",
    "RxList Link": "http://www.rxlist.com/cgi/generic/pulmozyme.htm",
    "Pdrhealth Link": "",
    "Wikipedia ID": "Dornase_alfa",
    "Drugs.com Link": "http://www.drugs.com/cdi/dornase-alfa.html",
    "NDC ID": "",
    "ChemSpider ID": "",
    "BindingDB ID": "",
    "TTD ID": "DAP000981"
  }
]
```

## sadece_antibiyotikler.csv

Kaynak: [1GyREHimp3-v0N-yPkcUnvNbneBaIp7Z1](https://drive.google.com/file/d/1GyREHimp3-v0N-yPkcUnvNbneBaIp7Z1/view?usp=drivesdk); değiştirilme: 2026-04-17T21:12:37.678Z.
Tam CSV: **209 satır × 3 sütun**. Tam satır tekrar fazlası: 0.

| Alan | Gözlenen tip | Tüm CSV boş | Boş % | İlk en çok 1000 boş / n |
|---|---|---:|---:|---:|
| DrugBank_ID | string | 0 | 0.0000 | 0/209 |
| İlaç_Adı | string | 0 | 0.0000 | 0/209 |
| ATC_Kodu | string | 0 | 0.0000 | 0/209 |

İlk üç kayıt (uzun diziler görünüm için kısaltılmıştır):

```json
[
  {
    "DrugBank_ID": "DB00080",
    "İlaç_Adı": "Daptomycin",
    "ATC_Kodu": "J01XX09"
  },
  {
    "DrugBank_ID": "DB00196",
    "İlaç_Adı": "Fluconazole",
    "ATC_Kodu": "J01RA07"
  },
  {
    "DrugBank_ID": "DBSALT002560",
    "İlaç_Adı": "Moxifloxacin",
    "ATC_Kodu": "J01MA14"
  }
]
```

# WP00 gerçek dosya şemaları

Örnekleme: XML ilk 3 üst düzey ilaç; metin tabloları ilk 1000 kayıt. Bunlar rastgele örnekler değildir. Eksiklik yalnız boş/whitespace hücredir; biyolojik eksiklik veya geçersiz kimlik aynı şey değildir. İlk 1001 kayıt okunarak dosyanın bitip bitmediği kontrol edilir; istatistiklere yalnız ilk 1000 girer. Tam dosya satır sayısı ve genel eksiklik oranı çıkarılmadı.

## full database.xml

İnceleme kapsamı: `first_3_top_level_drugs`.

Kök etiket: `{http://www.drugbank.ca}drugbank`; metadata: `{'{http://www.w3.org/2001/XMLSchema-instance}schemaLocation': 'http://www.drugbank.ca http://www.drugbank.ca/docs/drugbank.xsd', 'version': '5.1', 'exported-on': '2026-01-04'}`.
Okunan bayt (parser tamponu dahil): 442368. Tüm XML geçerliliği sınanmadı.

İlk üç gerçek örnek (temsili dağılım iddiası yok):

```json
[
  {
    "ids": [
      {
        "value": "DB00001",
        "primary": "true"
      },
      {
        "value": "BTD00024",
        "primary": ""
      },
      {
        "value": "BIOD00024",
        "primary": ""
      }
    ],
    "name": "Lepirudin",
    "type": "biotech",
    "atc_codes": [
      "B01AE02"
    ],
    "external_identifiers": [
      {
        "resource": "Drugs Product Database (DPD)",
        "identifier": "11916"
      },
      {
        "resource": "PubChem Substance",
        "identifier": "46507011"
      },
      {
        "resource": "KEGG Drug",
        "identifier": "D06880"
      },
      {
        "resource": "PharmGKB",
        "identifier": "PA450195"
      },
      {
        "resource": "UniProtKB",
        "identifier": "P01050"
      },
      {
        "resource": "Therapeutic Targets Database",
        "identifier": "DAP000541"
      },
      {
        "resource": "Wikipedia",
        "identifier": "Lepirudin"
      },
      {
        "resource": "ChEMBL",
        "identifier": "CHEMBL1201666"
      },
      {
        "resource": "RxCUI",
        "identifier": "237057"
      }
    ],
    "target_polypeptides": [
      {
        "id": "P00734",
        "source": "Swiss-Prot",
        "organism": "Humans",
        "gene_name": "F2",
        "child_tags": [
          "name",
          "general-function",
          "specific-function",
          "gene-name",
          "locus",
          "cellular-location",
          "transmembrane-regions",
          "signal-regions",
          "theoretical-pi",
          "molecular-weight",
          "chromosome-location",
          "organism",
          "external-identifiers",
          "synonyms",
          "amino-acid-sequence",
          "gene-sequence",
          "pfams",
          "go-classifiers"
        ],
        "identifiers": [
          {
            "resource": "HUGO Gene Nomenclature Committee (HGNC)",
            "identifier": "HGNC:3535"
          },
          {
            "resource": "GenAtlas",
            "identifier": "F2"
          },
          {
            "resource": "GeneCards",
            "identifier": "F2"
          },
          {
            "resource": "GenBank Gene Database",
            "identifier": "M17262"
          },
          {
            "resource": "GenBank Protein Database",
            "identifier": "339641"
          },
          {
            "resource": "Guide to Pharmacology",
            "identifier": "2362"
          },
          {
            "resource": "UniProtKB",
            "identifier": "P00734"
          },
          {
            "resource": "UniProt Accession",
            "identifier": "THRB_HUMAN"
          }
        ],
        "sequences": [
          {
            "tag": "amino-acid-sequence",
            "format": "FASTA",
            "raw_prefix": ">lcl|BSEQ0016004|Prothrombin\nMAHVRGLQLPGCLALAALCSLVHSQHVFLAPQQARSLLQRVRRANTFLEEVRKGNLEREC\nVEETCSYEEAFEALESSTATDVFWAKYTACETARTPRDKLAACLEGNCAE",
            "raw_length": 661,
            "qc": "standard_20_AA",
            "sequence_length": 622
          }
        ]
      }
    ],
    "child_tags": [
      "drugbank-id",
      "drugbank-id",
      "drugbank-id",
      "name",
      "description",
      "cas-number",
      "unii",
      "state",
      "groups",
      "general-references",
      "synthesis-reference",
      "indication",
      "pharmacodynamics",
      "mechanism-of-action",
      "toxicity",
      "metabolism",
      "absorption",
      "half-life",
      "protein-binding",
      "route-of-elimination",
      "volume-of-distribution",
      "clearance",
      "classification",
      "salts",
      "synonyms",
      "products",
      "international-brands",
      "mixtures",
      "packagers",
      "manufacturers",
      "prices",
      "categories",
      "affected-organisms",
      "dosages",
      "atc-codes",
      "ahfs-codes",
      "pdb-entries",
      "patents",
      "food-interactions",
      "drug-interactions",
      "sequences",
      "experimental-properties",
      "external-identifiers",
      "external-links",
      "pathways",
      "reactions",
      "snp-effects",
      "snp-adverse-drug-reactions",
      "targets",
      "enzymes",
      "carriers",
      "transporters"
    ]
  },
  {
    "ids": [
      {
        "value": "DB00002",
        "primary": "true"
      },
      {
        "value": "BTD00071",
        "primary": ""
      },
      {
        "value": "BIOD00071",
        "primary": ""
      }
    ],
    "name": "Cetuximab",
    "type": "biotech",
    "atc_codes": [
      "L01FE01"
    ],
    "external_identifiers": [
      {
        "resource": "Drugs Product Database (DPD)",
        "identifier": "13175"
      },
      {
        "resource": "PubChem Substance",
        "identifier": "46507042"
      },
      {
        "resource": "KEGG Drug",
        "identifier": "D03455"
      },
      {
        "resource": "GenBank",
        "identifier": "J00228"
      },
      {
        "resource": "PharmGKB",
        "identifier": "PA10040"
      },
      {
        "resource": "Therapeutic Targets Database",
        "identifier": "DNC000788"
      },
      {
        "resource": "Wikipedia",
        "identifier": "Cetuximab"
      },
      {
        "resource": "ChEMBL",
        "identifier": "CHEMBL1201577"
      },
      {
        "resource": "RxCUI",
        "identifier": "318341"
      }
    ],
    "target_polypeptides": [
      {
        "id": "P00533",
        "source": "Swiss-Prot",
        "organism": "Humans",
        "gene_name": "EGFR",
        "child_tags": [
          "name",
          "general-function",
          "specific-function",
          "gene-name",
          "locus",
          "cellular-location",
          "transmembrane-regions",
          "signal-regions",
          "theoretical-pi",
          "molecular-weight",
          "chromosome-location",
          "organism",
          "external-identifiers",
          "synonyms",
          "amino-acid-sequence",
          "gene-sequence",
          "pfams",
          "go-classifiers"
        ],
        "identifiers": [
          {
            "resource": "HUGO Gene Nomenclature Committee (HGNC)",
            "identifier": "HGNC:3236"
          },
          {
            "resource": "GenAtlas",
            "identifier": "EGFR"
          },
          {
            "resource": "GeneCards",
            "identifier": "EGFR"
          },
          {
            "resource": "GenBank Gene Database",
            "identifier": "X00588"
          },
          {
            "resource": "GenBank Protein Database",
            "identifier": "757924"
          },
          {
            "resource": "Guide to Pharmacology",
            "identifier": "1797"
          },
          {
            "resource": "UniProtKB",
            "identifier": "P00533"
          },
          {
            "resource": "UniProt Accession",
            "identifier": "EGFR_HUMAN"
          }
        ],
        "sequences": [
          {
            "tag": "amino-acid-sequence",
            "format": "FASTA",
            "raw_prefix": ">lcl|BSEQ0001530|Epidermal growth factor receptor\nMRPSGTAGAALLALLAALCPASRALEEKKVCQGTSNKLTQLGTFEDHFLSLQRMFNNCEV\nVLGNLEITYVQRNYDLSFLKTIQEVAGYV",
            "raw_length": 1280,
            "qc": "standard_20_AA",
            "sequence_length": 1210
          }
        ]
      },
      {
        "id": "O75015",
        "source": "Swiss-Prot",
        "organism": "Humans",
        "gene_name": "FCGR3B",
        "child_tags": [
          "name",
          "general-function",
          "specific-function",
          "gene-name",
          "locus",
          "cellular-location",
          "transmembrane-regions",
          "signal-regions",
          "theoretical-pi",
          "molecular-weight",
          "chromosome-location",
          "organism",
          "external-identifiers",
          "synonyms",
          "amino-acid-sequence",
          "gene-sequence",
          "pfams",
          "go-classifiers"
        ],
        "identifiers": [
          {
            "resource": "HUGO Gene Nomenclature Committee (HGNC)",
            "identifier": "HGNC:3620"
          },
          {
            "resource": "GenAtlas",
            "identifier": "FCGR3B"
          },
          {
            "resource": "GeneCards",
            "identifier": "FCGR3B"
          },
          {
            "resource": "GenBank Gene Database",
            "identifier": "X16863"
          },
          {
            "resource": "GenBank Protein Database",
            "identifier": "31322"
          },
          {
            "resource": "UniProtKB",
            "identifier": "O75015"
          },
          {
            "resource": "UniProt Accession",
            "identifier": "FCG3B_HUMAN"
          }
        ],
        "sequences": [
          {
            "tag": "amino-acid-sequence",
            "format": "FASTA",
            "raw_prefix": ">lcl|BSEQ0055007|Low affinity immunoglobulin gamma Fc region receptor III-B\nMWQLLLPTALLLLVSAGMRTEDLPKAVVFLEPQWYSVLEKDSVTLKCQGAYSPEDNSTQW\nFHN",
            "raw_length": 312,
            "qc": "standard_20_AA",
            "sequence_length": 233
          }
        ]
      },
      {
        "id": "P02745",
        "source": "Swiss-Prot",
        "organism": "Humans",
        "gene_name": "C1QA",
        "child_tags": [
          "name",
          "general-function",
          "specific-function",
          "gene-name",
          "locus",
          "cellular-location",
          "transmembrane-regions",
          "signal-regions",
          "theoretical-pi",
          "molecular-weight",
          "chromosome-location",
          "organism",
          "external-identifiers",
          "synonyms",
          "amino-acid-sequence",
          "gene-sequence",
          "pfams",
          "go-classifiers"
        ],
        "identifiers": [
          {
            "resource": "HUGO Gene Nomenclature Committee (HGNC)",
            "identifier": "HGNC:1241"
          },
          {
            "resource": "GenAtlas",
            "identifier": "C1QA"
          },
          {
            "resource": "GeneCards",
            "identifier": "C1QA"
          },
          {
            "resource": "GenBank Gene Database",
            "identifier": "AF135157"
          },
          {
            "resource": "GenBank Protein Database",
            "identifier": "4894854"
          },
          {
            "resource": "UniProtKB",
            "identifier": "P02745"
          },
          {
            "resource": "UniProt Accession",
            "identifier": "C1QA_HUMAN"
          }
        ],
        "sequences": [
          {
            "tag": "amino-acid-sequence",
            "format": "FASTA",
            "raw_prefix": ">lcl|BSEQ0016678|Complement C1q subcomponent subunit A\nMEGPRGWLVLCVLAISLASMVTEDLCRAPDGKKGEAGRPGRRGRPGLKGEQGEPGAPGIR\nTGIQGLKGDQGEPGPSGNPGKVGY",
            "raw_length": 304,
            "qc": "standard_20_AA",
            "sequence_length": 245
          }
        ]
      },
      {
        "id": "P02746",
        "source": "Swiss-Prot",
        "organism": "Humans",
        "gene_name": "C1QB",
        "child_tags": [
          "name",
          "general-function",
          "specific-function",
          "gene-name",
          "locus",
          "cellular-location",
          "transmembrane-regions",
          "signal-regions",
          "theoretical-pi",
          "molecular-weight",
          "chromosome-location",
          "organism",
          "external-identifiers",
          "synonyms",
          "amino-acid-sequence",
          "gene-sequence",
          "pfams",
          "go-classifiers"
        ],
        "identifiers": [
          {
            "resource": "HUGO Gene Nomenclature Committee (HGNC)",
            "identifier": "HGNC:1242"
          },
          {
            "resource": "GenAtlas",
            "identifier": "C1QB"
          },
          {
            "resource": "GeneCards",
            "identifier": "C1QB"
          },
          {
            "resource": "GenBank Gene Database",
            "identifier": "X03084"
          },
          {
            "resource": "GenBank Protein Database",
            "identifier": "573114"
          },
          {
            "resource": "UniProtKB",
            "identifier": "P02746"
          },
          {
            "resource": "UniProt Accession",
            "identifier": "C1QB_HUMAN"
          }
        ],
        "sequences": [
          {
            "tag": "amino-acid-sequence",
            "format": "FASTA",
            "raw_prefix": ">lcl|BSEQ0016676|Complement C1q subcomponent subunit B\nMMMKIPWGSIPVLMLLLLLGLIDISQAQLSCTGPPAIPGIPGIPGTPGPDGQPGTPGIKG\nEKGLPGLAGDHGEFGEKGDPGIPG",
            "raw_length": 312,
            "qc": "standard_20_AA",
            "sequence_length": 253
          }
        ]
      },
      {
        "id": "P02747",
        "source": "Swiss-Prot",
        "organism": "Humans",
        "gene_name": "C1QC",
        "child_tags": [
          "name",
          "general-function",
          "specific-function",
          "gene-name",
          "locus",
          "cellular-location",
          "transmembrane-regions",
          "signal-regions",
          "theoretical-pi",
          "molecular-weight",
          "chromosome-location",
          "organism",
          "external-identifiers",
          "synonyms",
          "amino-acid-sequence",
          "gene-sequence",
          "pfams",
          "go-classifiers"
        ],
        "identifiers": [
          {
            "resource": "HUGO Gene Nomenclature Committee (HGNC)",
            "identifier": "HGNC:1245"
          },
          {
            "resource": "GenAtlas",
            "identifier": "C1QC"
          },
          {
            "resource": "GeneCards",
            "identifier": "C1QC"
          },
          {
            "resource": "GenBank Gene Database",
            "identifier": "AF087892"
          },
          {
            "resource": "GenBank Protein Database",
            "identifier": "33150626"
          },
          {
            "resource": "UniProtKB",
            "identifier": "P02747"
          },
          {
            "resource": "UniProt Accession",
            "identifier": "C1QC_HUMAN"
          }
        ],
        "sequences": [
          {
            "tag": "amino-acid-sequence",
            "format": "FASTA",
            "raw_prefix": ">lcl|BSEQ0011520|Complement C1q subcomponent subunit C\nMDVGPSSLPHLGLKLLLLLLLLPLRGQANTGCYGIPGMPGLPGAPGKDGYDGLPGPKGEP\nGIPAIPGIRGPKGQKGEPGLPGHP",
            "raw_length": 304,
            "qc": "standard_20_AA",
            "sequence_length": 245
          }
        ]
      },
      {
        "id": "P08637",
        "source": "Swiss-Prot",
        "organism": "Humans",
        "gene_name": "FCGR3A",
        "child_tags": [
          "name",
          "general-function",
          "specific-function",
          "gene-name",
          "locus",
          "cellular-location",
          "transmembrane-regions",
          "signal-regions",
          "theoretical-pi",
          "molecular-weight",
          "chromosome-location",
          "organism",
          "external-identifiers",
          "synonyms",
          "amino-acid-sequence",
          "gene-sequence",
          "pfams",
          "go-classifiers"
        ],
        "identifiers": [
          {
            "resource": "HUGO Gene Nomenclature Committee (HGNC)",
            "identifier": "HGNC:3619"
          },
          {
            "resource": "GenAtlas",
            "identifier": "FCGR3A"
          },
          {
            "resource": "GeneCards",
            "identifier": "FCGR3A"
          },
          {
            "resource": "GenBank Gene Database",
            "identifier": "X52645"
          },
          {
            "resource": "GenBank Protein Database",
            "identifier": "31324"
          },
          {
            "resource": "Guide to Pharmacology",
            "identifier": "3017"
          },
          {
            "resource": "UniProtKB",
            "identifier": "P08637"
          },
          {
            "resource": "UniProt Accession",
            "identifier": "FCG3A_HUMAN"
          }
        ],
        "sequences": [
          {
            "tag": "amino-acid-sequence",
            "format": "FASTA",
            "raw_prefix": ">lcl|BSEQ0004112|Low affinity immunoglobulin gamma Fc region receptor III-A\nMWQLLLPTALLLLVSAGMRTEDLPKAVVFLEPQWYRVLEKDSVTLKCQGAYSPEDNSTQW\nFHN",
            "raw_length": 334,
            "qc": "standard_20_AA",
            "sequence_length": 254
          }
        ]
      },
      {
        "id": "P12314",
        "source": "Swiss-Prot",
        "organism": "Humans",
        "gene_name": "FCGR1A",
        "child_tags": [
          "name",
          "general-function",
          "specific-function",
          "gene-name",
          "locus",
          "cellular-location",
          "transmembrane-regions",
          "signal-regions",
          "theoretical-pi",
          "molecular-weight",
          "chromosome-location",
          "organism",
          "external-identifiers",
          "synonyms",
          "amino-acid-sequence",
          "gene-sequence",
          "pfams",
          "go-classifiers"
        ],
        "identifiers": [
          {
            "resource": "HUGO Gene Nomenclature Committee (HGNC)",
            "identifier": "HGNC:3613"
          },
          {
            "resource": "GenAtlas",
            "identifier": "FCGR1A"
          },
          {
            "resource": "GeneCards",
            "identifier": "FCGR1A"
          },
          {
            "resource": "GenBank Gene Database",
            "identifier": "X14356"
          },
          {
            "resource": "GenBank Protein Database",
            "identifier": "31332"
          },
          {
            "resource": "UniProtKB",
            "identifier": "P12314"
          },
          {
            "resource": "UniProt Accession",
            "identifier": "FCGR1_HUMAN"
          }
        ],
        "sequences": [
          {
            "tag": "amino-acid-sequence",
            "format": "FASTA",
            "raw_prefix": ">lcl|BSEQ0001416|High affinity immunoglobulin gamma Fc receptor I\nMWFLTTLLLWVPVDGQVDTTKAVITLQPPWVSVFQEETVTLHCEVLHLPGSSSTQWFLNG\nTATQTSTPSYRIT",
            "raw_length": 446,
            "qc": "standard_20_AA",
            "sequence_length": 374
          }
        ]
      },
      {
        "id": "P12318",
        "source": "Swiss-Prot",
        "organism": "Humans",
        "gene_name": "FCGR2A",
        "child_tags": [
          "name",
          "general-function",
          "specific-function",
          "gene-name",
          "locus",
          "cellular-location",
          "transmembrane-regions",
          "signal-regions",
          "theoretical-pi",
          "molecular-weight",
          "chromosome-location",
          "organism",
          "external-identifiers",
          "synonyms",
          "amino-acid-sequence",
          "gene-sequence",
          "pfams",
          "go-classifiers"
        ],
        "identifiers": [
          {
            "resource": "HUGO Gene Nomenclature Committee (HGNC)",
            "identifier": "HGNC:3616"
          },
          {
            "resource": "GenAtlas",
            "identifier": "FCGR2A"
          },
          {
            "resource": "GeneCards",
            "identifier": "FCGR2A"
          },
          {
            "resource": "GenBank Gene Database",
            "identifier": "M31932"
          },
          {
            "resource": "GenBank Protein Database",
            "identifier": "182474"
          },
          {
            "resource": "UniProtKB",
            "identifier": "P12318"
          },
          {
            "resource": "UniProt Accession",
            "identifier": "FCG2A_HUMAN"
          }
        ],
        "sequences": [
          {
            "tag": "amino-acid-sequence",
            "format": "FASTA",
            "raw_prefix": ">lcl|BSEQ0037156|Low affinity immunoglobulin gamma Fc region receptor II-a\nMTMETQMSQNVCPRNLWLLQPLTVLLLLASADSQAAAPPKAVLKLEPPWINVLQEDSVTL\nTCQG",
            "raw_length": 397,
            "qc": "standard_20_AA",
            "sequence_length": 317
          }
        ]
      }
    ],
    "child_tags": [
      "drugbank-id",
      "drugbank-id",
      "drugbank-id",
      "name",
      "description",
      "cas-number",
      "unii",
      "state",
      "groups",
      "general-references",
      "synthesis-reference",
      "indication",
      "pharmacodynamics",
      "mechanism-of-action",
      "toxicity",
      "metabolism",
      "absorption",
      "half-life",
      "protein-binding",
      "route-of-elimination",
      "volume-of-distribution",
      "clearance",
      "classification",
      "salts",
      "synonyms",
      "products",
      "international-brands",
      "mixtures",
      "packagers",
      "manufacturers",
      "prices",
      "categories",
      "affected-organisms",
      "dosages",
      "atc-codes",
      "ahfs-codes",
      "pdb-entries",
      "fda-label",
      "msds",
      "patents",
      "food-interactions",
      "drug-interactions",
      "sequences",
      "experimental-properties",
      "external-identifiers",
      "external-links",
      "pathways",
      "reactions",
      "snp-effects",
      "snp-adverse-drug-reactions",
      "targets",
      "enzymes",
      "carriers",
      "transporters"
    ]
  },
  {
    "ids": [
      {
        "value": "DB00003",
        "primary": "true"
      },
      {
        "value": "BTD00001",
        "primary": ""
      },
      {
        "value": "BIOD00001",
        "primary": ""
      }
    ],
    "name": "Dornase alfa",
    "type": "biotech",
    "atc_codes": [
      "R05CB13"
    ],
    "external_identifiers": [
      {
        "resource": "Drugs Product Database (DPD)",
        "identifier": "650"
      },
      {
        "resource": "PubChem Substance",
        "identifier": "46507792"
      },
      {
        "resource": "GenBank",
        "identifier": "M55983"
      },
      {
        "resource": "PharmGKB",
        "identifier": "PA10318"
      },
      {
        "resource": "UniProtKB",
        "identifier": "P24855"
      },
      {
        "resource": "Therapeutic Targets Database",
        "identifier": "DAP000981"
      },
      {
        "resource": "Wikipedia",
        "identifier": "Dornase_alfa"
      },
      {
        "resource": "ChEMBL",
        "identifier": "CHEMBL1201431"
      },
      {
        "resource": "RxCUI",
        "identifier": "337623"
      }
    ],
    "target_polypeptides": [
      {
        "id": "P24855",
        "source": "Swiss-Prot",
        "organism": "Humans",
        "gene_name": "DNASE1",
        "child_tags": [
          "name",
          "general-function",
          "specific-function",
          "gene-name",
          "locus",
          "cellular-location",
          "transmembrane-regions",
          "signal-regions",
          "theoretical-pi",
          "molecular-weight",
          "chromosome-location",
          "organism",
          "external-identifiers",
          "synonyms",
          "amino-acid-sequence",
          "gene-sequence",
          "pfams",
          "go-classifiers"
        ],
        "identifiers": [
          {
            "resource": "HUGO Gene Nomenclature Committee (HGNC)",
            "identifier": "HGNC:2956"
          },
          {
            "resource": "GeneCards",
            "identifier": "DNASE1"
          },
          {
            "resource": "UniProtKB",
            "identifier": "P24855"
          },
          {
            "resource": "UniProt Accession",
            "identifier": "DNAS1_HUMAN"
          }
        ],
        "sequences": [
          {
            "tag": "amino-acid-sequence",
            "format": "FASTA",
            "raw_prefix": ">lcl|BSEQ0009377|Deoxyribonuclease-1\nMRGMKLLGALLALAALLQGAVSLKIAAFNIQTFGETKMSNATLVSYIVQILSRYDIALVQ\nEVRDSHLTAVGKLLDNLNQDAPDTYHYVVSEPLGRNSYKERY",
            "raw_length": 323,
            "qc": "standard_20_AA",
            "sequence_length": 282
          }
        ]
      }
    ],
    "child_tags": [
      "drugbank-id",
      "drugbank-id",
      "drugbank-id",
      "name",
      "description",
      "cas-number",
      "unii",
      "state",
      "groups",
      "general-references",
      "synthesis-reference",
      "indication",
      "pharmacodynamics",
      "mechanism-of-action",
      "toxicity",
      "metabolism",
      "absorption",
      "half-life",
      "protein-binding",
      "route-of-elimination",
      "volume-of-distribution",
      "clearance",
      "classification",
      "salts",
      "synonyms",
      "products",
      "international-brands",
      "mixtures",
      "packagers",
      "manufacturers",
      "prices",
      "categories",
      "affected-organisms",
      "dosages",
      "atc-codes",
      "ahfs-codes",
      "pdb-entries",
      "fda-label",
      "msds",
      "patents",
      "food-interactions",
      "drug-interactions",
      "sequences",
      "experimental-properties",
      "external-identifiers",
      "external-links",
      "pathways",
      "reactions",
      "snp-effects",
      "snp-adverse-drug-reactions",
      "targets",
      "enzymes",
      "carriers",
      "transporters"
    ]
  }
]
```

## meddra_all_se.tsv

İnceleme kapsamı: `first_1000_records`.

| Alan | Gözlenen tip | Boş hücre | Boş % | Örnekte farklı değer |
|---|---|---:|---:|---:|
| flat_id | string | 0 | 0.0 | 10 |
| stereo_id | string | 0 | 0.0 | 12 |
| umls_cui_from_label | string | 0 | 0.0 | 276 |
| meddra_type | string | 4 | 0.4 | 3 |
| umls_cui | string | 4 | 0.4 | 317 |
| side_effect_name | string | 0 | 0.0 | 317 |

Tam satır tekrar fazlası: 0; hatalı sütun sayılı satırlar: [].

Örnek kapsamındaki ek kontroller:

```json
{
  "meddra_type_counts": {
    "LLT": 469,
    "PT": 527,
    "": 4
  },
  "unique_stereo_ids": 12,
  "duplicate_stereo_umls_type_excess": 31,
  "stitch_pattern_invalid_rows": 0,
  "observed_prefixes": {
    "flat": {
      "CID1": 1000
    },
    "stereo": {
      "CID0": 1000
    }
  }
}
```

İlk üç gerçek örnek (temsili dağılım iddiası yok):

```json
[
  {
    "flat_id": "CID100000085",
    "stereo_id": "CID000010917",
    "umls_cui_from_label": "C0000729",
    "meddra_type": "LLT",
    "umls_cui": "C0000729",
    "side_effect_name": "Abdominal cramps"
  },
  {
    "flat_id": "CID100000085",
    "stereo_id": "CID000010917",
    "umls_cui_from_label": "C0000729",
    "meddra_type": "PT",
    "umls_cui": "C0000737",
    "side_effect_name": "Abdominal pain"
  },
  {
    "flat_id": "CID100000085",
    "stereo_id": "CID000010917",
    "umls_cui_from_label": "C0000737",
    "meddra_type": "LLT",
    "umls_cui": "C0000737",
    "side_effect_name": "Abdominal pain"
  }
]
```

## 9606.protein.links.v12.0.txt

İnceleme kapsamı: `first_1000_records`.

| Alan | Gözlenen tip | Boş hücre | Boş % | Örnekte farklı değer |
|---|---|---:|---:|---:|
| protein1 | string | 0 | 0.0 | 1 |
| protein2 | string | 0 | 0.0 | 1000 |
| combined_score | integer-like; identifier may need string | 0 | 0.0 | 267 |

Tam satır tekrar fazlası: 0; hatalı sütun sayılı satırlar: [].

Örnek kapsamındaki ek kontroller:

```json
{
  "taxon_prefix_invalid_rows": 0,
  "score_min": 150,
  "score_max": 952,
  "self_loops": 0,
  "duplicate_directed_pairs_excess": 0
}
```

İlk üç gerçek örnek (temsili dağılım iddiası yok):

```json
[
  {
    "protein1": "9606.ENSP00000000233",
    "protein2": "9606.ENSP00000356607",
    "combined_score": "173"
  },
  {
    "protein1": "9606.ENSP00000000233",
    "protein2": "9606.ENSP00000427567",
    "combined_score": "154"
  },
  {
    "protein1": "9606.ENSP00000000233",
    "protein2": "9606.ENSP00000253413",
    "combined_score": "151"
  }
]
```

## 9606.protein.aliases.v12.0.txt

İnceleme kapsamı: `first_1000_records`.

| Alan | Gözlenen tip | Boş hücre | Boş % | Örnekte farklı değer |
|---|---|---:|---:|---:|
| #string_protein_id | string | 0 | 0.0 | 7 |
| alias | string | 0 | 0.0 | 714 |
| source | string | 0 | 0.0 | 68 |

Tam satır tekrar fazlası: 0; hatalı sütun sayılı satırlar: [].

Örnek kapsamındaki ek kontroller:

```json
{
  "duplicate_protein_alias_excess": 277,
  "source_values_first_10": [
    "Ensembl_PDB",
    "UniProt_DR_PDB",
    "Ensembl_HGNC_entrez_id",
    "KEGG_GENEID",
    "KEGG_KEGGID_SHORT",
    "UniProt_DR_GeneID",
    "Ensembl_UniProt",
    "Ensembl_protein_id",
    "Ensembl_EMBL",
    "Ensembl_HGNC_name"
  ],
  "multiple_aliases_expected": true
}
```

İlk üç gerçek örnek (temsili dağılım iddiası yok):

```json
[
  {
    "#string_protein_id": "9606.ENSP00000000233",
    "alias": "2B6H",
    "source": "Ensembl_PDB"
  },
  {
    "#string_protein_id": "9606.ENSP00000000233",
    "alias": "2B6H",
    "source": "UniProt_DR_PDB"
  },
  {
    "#string_protein_id": "9606.ENSP00000000233",
    "alias": "381",
    "source": "Ensembl_HGNC_entrez_id"
  }
]
```

## 511145.protein.links.v12.0.txt

İnceleme kapsamı: `first_1000_records`.

| Alan | Gözlenen tip | Boş hücre | Boş % | Örnekte farklı değer |
|---|---|---:|---:|---:|
| protein1 | string | 0 | 0.0 | 3 |
| protein2 | string | 0 | 0.0 | 934 |
| combined_score | integer-like; identifier may need string | 0 | 0.0 | 384 |

Tam satır tekrar fazlası: 0; hatalı sütun sayılı satırlar: [].

Örnek kapsamındaki ek kontroller:

```json
{
  "taxon_prefix_invalid_rows": 0,
  "score_min": 150,
  "score_max": 999,
  "self_loops": 0,
  "duplicate_directed_pairs_excess": 0
}
```

İlk üç gerçek örnek (temsili dağılım iddiası yok):

```json
[
  {
    "protein1": "511145.b0001",
    "protein2": "511145.b1715",
    "combined_score": "520"
  },
  {
    "protein1": "511145.b0001",
    "protein2": "511145.b3783",
    "combined_score": "208"
  },
  {
    "protein1": "511145.b0001",
    "protein2": "511145.b2310",
    "combined_score": "275"
  }
]
```

## 511145.protein.aliases.v12.0.txt

İnceleme kapsamı: `first_1000_records`.

| Alan | Gözlenen tip | Boş hücre | Boş % | Örnekte farklı değer |
|---|---|---:|---:|---:|
| #string_protein_id | string | 0 | 0.0 | 22 |
| alias | string | 0 | 0.0 | 780 |
| source | string | 0 | 0.0 | 29 |

Tam satır tekrar fazlası: 0; hatalı sütun sayılı satırlar: [].

Örnek kapsamındaki ek kontroller:

```json
{
  "duplicate_protein_alias_excess": 180,
  "source_values_first_10": [
    "KEGG_GENEID",
    "UniProt_DR_GeneID",
    "RefSeq_short",
    "RefSeq",
    "RefSeq_xref_ASAP",
    "RefSeq_synonym",
    "RefSeq_xref_EcoGene",
    "UniProt_GN_OrderedLocusNames",
    "UniProt_ID",
    "UniProt_DR_RefSeq"
  ],
  "multiple_aliases_expected": true
}
```

İlk üç gerçek örnek (temsili dağılım iddiası yok):

```json
[
  {
    "#string_protein_id": "511145.b0001",
    "alias": "944742",
    "source": "KEGG_GENEID"
  },
  {
    "#string_protein_id": "511145.b0001",
    "alias": "944742",
    "source": "UniProt_DR_GeneID"
  },
  {
    "#string_protein_id": "511145.b0001",
    "alias": "AAC73112",
    "source": "RefSeq_short"
  }
]
```


## Drive incelemesi

Kimlik köprüsü ve yedi CSV incelemesi tamamlandı. Tam sütun listeleri, örnekler ve boşluk oranları [drive_schema_summary.md](drive_schema_summary.md) dosyasında; ölçümler `drive_profiles.json` içinde. Allowlist kaynaklarının tamamı yerelde veya Drive’da mevcut. Yerel eksiklik genel dosya yokluğu değildir.

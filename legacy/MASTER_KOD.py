"""
═══════════════════════════════════════════════════════════════════════════════
TEZ PROJESİ — MASTER KOD DOSYASI
Antibiyotik Yan Etki Tahmini için Heterojen Graf Sinir Ağı (GiG)
═══════════════════════════════════════════════════════════════════════════════

Bu dosya projenin TÜM ADIM ADIM AKIŞINI içerir.
Her bölüm bir aşamayı temsil eder ve sırayla çalıştırılır.

İÇERİK:
  BÖLÜM 1: Ortam Hazırlığı (kütüphane kurulumu)
  BÖLÜM 2: Veri Toplama — DrugBank XML'den Antibiyotikler
  BÖLÜM 3: SIDER'dan İlaç-Yan Etki Eşleştirmesi (35 SE filtresi)
  BÖLÜM 4: PubChem API'den İlaç Fizikokimyasal Feature'ları
  BÖLÜM 5: ATC Kodlarının XML'den Çekilmesi
  BÖLÜM 6: DrugBank XML'den İlaç-Protein Hedefleri
  BÖLÜM 7: UniProt API'den Protein Dizileri
  BÖLÜM 8: Protein Feature Hesaplama (AAC + Grup DC)
  BÖLÜM 9: Heterojen Graf Kurulumu (PyTorch Geometric)
  BÖLÜM 10: GiG Modeli Eğitimi
  BÖLÜM 11: Açıklanabilirlik Analizi (XAI)
  BÖLÜM 12: Graph Görselleştirmeleri

ÇALIŞTIRMA NOTU:
  - Her bölüm Colab'da ayrı bir hücreye yapıştırılarak çalıştırılır.
  - PyTorch ve PyG kurulumu sonrası RUNTIME RESTART gerekir.
  - Tüm çıktılar /content/drive/MyDrive/Tez_Veri/ klasörüne kaydedilir.

═══════════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════════════════
# BÖLÜM 1: ORTAM HAZIRLIĞI
# ═══════════════════════════════════════════════════════════════════════════
# AMAÇ: Gerekli kütüphaneleri yükle, Drive'ı bağla.
# NOT: PyTorch 2.10 ile PyG uyumsuzdu, 2.2 sürümüne indirildi.

"""
# Bu komutları Colab'da çalıştır:
!pip uninstall torch torchvision torchaudio -y
!pip install torch==2.2.0+cu121 torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121
!pip install torch-geometric torch-scatter torch-sparse \
    -f https://data.pyg.org/whl/torch-2.2.0+cu121.html -q
# Runtime'ı restart et!
"""

import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import requests
import time
import re
import gc
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score, roc_curve
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import networkx as nx

from google.colab import drive
drive.mount('/content/drive')

DRIVE  = '/content/drive/MyDrive/Tez_Veri/'
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# ═══════════════════════════════════════════════════════════════════════════
# BÖLÜM 2: DRUGBANK XML'DEN ANTİBİYOTİK LİSTESİ
# ═══════════════════════════════════════════════════════════════════════════
# AMAÇ: 1.9 GB DrugBank XML dosyasından ATC kodu J01 (antibiyotik) olan
#       ilaçları çek. Sonuç: 209 antibiyotik.
# YÖNTEM: iterparse ile parça parça okuma (RAM dostu).

def antibiyotikleri_filtrele(xml_dosya_yolu):
    """ATC=J01 olan ilaçları XML'den çeker."""
    antibiyotik_listesi = []
    context = ET.iterparse(xml_dosya_yolu, events=("start", "end"))
    ns = '{http://www.drugbank.ca}'
    current_drug = {}

    for event, elem in context:
        if event == "start" and elem.tag == f"{ns}drug":
            current_drug = {'id': None, 'name': None,
                            'is_antibiotic': False, 'atc_kodu': None}

        elif event == "end":
            if elem.tag == f"{ns}drugbank-id" and elem.get('primary') == 'true':
                current_drug['id'] = elem.text

            elif elem.tag == f"{ns}name" and current_drug['name'] is None:
                current_drug['name'] = elem.text

            elif elem.tag == f"{ns}atc-code":
                code = elem.get('code')
                # J01 ile başlayan ATC kodları = antibiyotik
                if code and code.startswith('J01'):
                    current_drug['is_antibiotic'] = True
                    current_drug['atc_kodu'] = code

            elif elem.tag == f"{ns}drug":
                if current_drug['is_antibiotic'] and current_drug['id']:
                    antibiyotik_listesi.append({
                        'DrugBank_ID': current_drug['id'],
                        'İlaç_Adı'   : current_drug['name'],
                        'ATC_Kodu'   : current_drug['atc_kodu']
                    })
                elem.clear()  # RAM'i boşalt

    return pd.DataFrame(antibiyotik_listesi)

# Çalıştır
df_antibiyotikler = antibiyotikleri_filtrele(DRIVE + 'full database.xml')
df_antibiyotikler.to_csv(DRIVE + 'sadece_antibiyotikler.csv',
                         index=False, encoding='utf-8-sig')
print(f"Toplam antibiyotik: {len(df_antibiyotikler)}")


# ═══════════════════════════════════════════════════════════════════════════
# BÖLÜM 3: SIDER'DAN İLAÇ-YAN ETKİ EŞLEŞTİRMESİ (35 SE FİLTRESİ)
# ═══════════════════════════════════════════════════════════════════════════
# AMAÇ: SIDER 4.1 veritabanından hocanın belirttiği 35 yan etki ile
#       eşleşen ilaçları bul.
# KRİTİK KARAR: V4'te 9 ilaç kaldı, V5'te yön ters çevrildi
#               (antibiyotikten başlamak yerine SIDER'dan başlamak).

# Hocanın 35 hedef yan etki listesi (SIDER PT karşılıkları ile)
HEDEF_35_SE = {
    'Nausea': 'Mide bulantısı',
    'Vomiting': 'Kusma',
    'Diarrhoea': 'İshal',
    'Diarrhea': 'İshal',
    'Abdominal pain': 'Karın ağrısı',
    'Dyspepsia': 'Hazımsızlık',
    'Stomach discomfort': 'Hazımsızlık',
    'Abdominal distension': 'Şişkinlik',
    'Constipation': 'Kabızlık',
    'Decreased appetite': 'İştahsızlık',
    'Headache': 'Baş ağrısı',
    'Rash': 'Deri döküntüsü',
    'Pruritus': 'Kaşıntı',
    'Dizziness': 'Baş dönmesi',
    'Pyrexia': 'Ateş',
    'Vulvovaginal candidiasis': 'Vajinal mantar enfeksiyonu',
    'Oral candidiasis': 'Ağızda mantar enfeksiyonu',
    'Dysgeusia': 'Tat değişikliği',
    'Hypersensitivity': 'Alerjik reaksiyon',
    'Dyspnoea': 'Nefes almada zorluk',
    'Wheezing': 'Hırıltı',
    'Tachycardia': 'Kalp atışında hızlanma',
    'Hypotension': 'Tansiyon düşüklüğü',
    'Anaphylactic reaction': 'Anafilaksi',
    'Anaphylaxis': 'Anafilaksi',
    'Hepatotoxicity': 'Karaciğer toksisitesi',
    'Nephrotoxicity': 'Nefrotoksisite',
    'Renal impairment': 'Nefrotoksisite',
    'Peripheral neuropathy': 'Nöropati',
    'Seizure': 'Nöbet',
    'Convulsion': 'Nöbet',
    'Tremor': 'Titreme',
    'Clostridium difficile colitis': 'C. diff ilişkili ishal',
    'Colitis': 'Antibiyotikle ilişkili kolit',
    'Thrombocytopenia': 'Trombositopeni',
    'Neutropenia': 'Nötropeni',
    'Anaemia': 'Anemi',
    'Anemia': 'Anemi',
    'Loss of consciousness': 'Bilinç kaybı',
    'Syncope': 'Bilinç kaybı',
}

# V5 yaklaşımı: SIDER'da olan ilaçlardan antibiyotikleri filtrele
ANTIBIYOTIK_KEYWORDS = [
    'cillin', 'mycin', 'floxacin', 'cycline', 'azole', 'oxacin',
    'sulfa', 'penem', 'bactam', 'thromycin', 'zolid', 'sporin',
    'azithro', 'clarithro', 'erythro', 'nitro', 'trimethoprim',
    'vancomycin', 'clindamycin', 'metronidazol', 'tinidazol',
    'chloramphenicol', 'rifampin', 'isoniazid', 'colistin'
]

# SIDER dosyasını oku
sider = pd.read_csv(DRIVE + 'meddra_all_se.tsv', sep='\t', header=None,
                    names=['flat_id', 'stereo_id', 'umls_cui_from_label',
                           'meddra_type', 'umls_cui', 'side_effect_name'])
sider['pubchem_id'] = sider['stereo_id'].str[4:].astype(int)
sider_pt = sider[sider['meddra_type'] == 'PT'][
    ['pubchem_id', 'side_effect_name']].drop_duplicates()

# drug_links.csv ile PubChem-DrugBank eşleştirmesi
drug_links = pd.read_csv(DRIVE + 'drug links.csv')
drug_links['pubchem_clean'] = pd.to_numeric(
    drug_links['PubChem Compound ID'], errors='coerce').astype('Int64')
drug_links = drug_links.dropna(subset=['pubchem_clean'])
drug_links['pubchem_clean'] = drug_links['pubchem_clean'].astype(int)

# SIDER'da olan ilaçlardan antibiyotik filtresi
sider_ids = set(sider_pt['pubchem_id'])
drug_links_sider = drug_links[drug_links['pubchem_clean'].isin(sider_ids)].copy()
kw_mask = drug_links_sider['Name'].str.lower().str.contains(
    '|'.join(ANTIBIYOTIK_KEYWORDS), na=False)
ab_sider = drug_links_sider[kw_mask].rename(
    columns={'DrugBank ID': 'DrugBank_ID'})

# 35 SE filtresi uygula
ab_pubchem_ids = set(ab_sider['pubchem_clean'])
se_match = sider_pt[
    sider_pt['pubchem_id'].isin(ab_pubchem_ids) &
    sider_pt['side_effect_name'].isin(HEDEF_35_SE.keys())
].copy()
se_match['se_kategori'] = se_match['side_effect_name'].map(HEDEF_35_SE)

# DrugBank ID köprüsü
pubchem_to_db = ab_sider.set_index('pubchem_clean')['DrugBank_ID'].to_dict()
se_match['DrugBank_ID'] = se_match['pubchem_id'].map(pubchem_to_db)
se_match = se_match.dropna(subset=['DrugBank_ID'])
se_match.to_csv(DRIVE + 'ilac_yan_etki_v5.csv', index=False)


# ═══════════════════════════════════════════════════════════════════════════
# BÖLÜM 4: PubChem API'DEN İLAÇ FİZİKOKİMYASAL FEATURE
# ═══════════════════════════════════════════════════════════════════════════
# AMAÇ: Her antibiyotik için MW, LogP, HBD, HBA, TPSA değerlerini PubChem'den
#       çek. XML'den çekmek başarısız olduğu için API kullanıldı.

def pubchem_ozellik_cek(cid, deneme=3):
    """PubChem REST API'den fizikokimyasal özellikler."""
    if pd.isna(cid):
        return {}
    url = (f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{int(cid)}'
           f'/property/MolecularWeight,XLogP,HBondDonorCount,'
           f'HBondAcceptorCount,TPSA/JSON')
    for _ in range(deneme):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                props = r.json()['PropertyTable']['Properties'][0]
                return {
                    'MW'  : props.get('MolecularWeight'),
                    'LogP': props.get('XLogP'),
                    'HBD' : props.get('HBondDonorCount'),
                    'HBA' : props.get('HBondAcceptorCount'),
                    'TPSA': props.get('TPSA'),
                }
            elif r.status_code == 429:
                time.sleep(5)
        except Exception:
            time.sleep(2)
    return {}

# Tüm ilaçlar için API'den çek
pubchem_data = []
for i, row in ab_sider.iterrows():
    props = pubchem_ozellik_cek(row['pubchem_clean'])
    props['DrugBank_ID'] = row['DrugBank_ID']
    props['Drug_Name']   = row['Name']
    props['pubchem_clean'] = row['pubchem_clean']
    pubchem_data.append(props)
    time.sleep(0.2)  # Rate limit

ilac_feat = pd.DataFrame(pubchem_data)

# Normalize et (0-1 aralığı)
for col in ['MW', 'LogP', 'HBD', 'HBA', 'TPSA']:
    ilac_feat[col] = pd.to_numeric(ilac_feat[col], errors='coerce')
    mn, mx = ilac_feat[col].min(), ilac_feat[col].max()
    ilac_feat[f'{col}_norm'] = ((ilac_feat[col] - mn) / (mx - mn)
                                if mx > mn else 0.0)

ilac_feat.to_csv(DRIVE + 'ilac_feature_v5.csv', index=False)


# ═══════════════════════════════════════════════════════════════════════════
# BÖLÜM 5: ATC KODLARININ XML'DEN BINARY ENCODING
# ═══════════════════════════════════════════════════════════════════════════
# AMAÇ: Her ilacın ATC kodlarını XML'den çek, 3. seviye için binary vektör.
# ÖRNEK: Ciprofloxacin → J01MA → ATC_J01M = 1

def get_atc_kodlari(xml_path, hedef_ids):
    """XML'den her ilacın ATC kodlarını çıkar."""
    NS = 'http://www.drugbank.ca'
    def tag(name): return f'{{{NS}}}{name}'
    
    atc_map = {}
    drug_buffer = []
    drug_iceride = False
    
    with open(xml_path, 'r', encoding='utf-8', errors='replace') as f:
        for satir in f:
            stripped = satir.strip()
            if stripped.startswith('<drug ') or stripped == '<drug>':
                drug_buffer = [satir]
                drug_iceride = True
                continue
            if drug_iceride:
                drug_buffer.append(satir)
                if '</drug>' in satir:
                    drug_iceride = False
                    drug_xml = ''.join(drug_buffer)
                    ilk_tag_sonu = drug_xml.index('>')
                    drug_xml = (
                        f'<drug xmlns="{NS}">'
                        + drug_xml[ilk_tag_sonu+1:]
                    )
                    try:
                        elem = ET.fromstring(drug_xml)
                    except:
                        continue
                    
                    db_id = None
                    for child in elem:
                        if (child.tag == tag('drugbank-id')
                                and child.get('primary') == 'true'):
                            db_id = child.text
                            break
                    
                    if db_id not in hedef_ids:
                        continue
                    
                    atc_codes = []
                    atc_elem = elem.find(tag('atc-codes'))
                    if atc_elem is not None:
                        for atc in atc_elem:
                            if atc.tag == tag('atc-code'):
                                kod = atc.get('code', '')
                                if kod:
                                    atc_codes.append(kod)
                    if atc_codes:
                        atc_map[db_id] = atc_codes
    
    return atc_map

# ATC'leri çek ve binary encode et
hedef_ids = set(ilac_feat['DrugBank_ID'])
atc_map = get_atc_kodlari(DRIVE + 'full database.xml', hedef_ids)

# Unique ATC 3. seviye
tum_atc = set()
for kodlar in atc_map.values():
    tum_atc.update(kodlar)
atc3 = sorted(set(kod[:4] for kod in tum_atc if len(kod) >= 4))

# Binary encoding
for db_id in ilac_feat['DrugBank_ID']:
    ilaç_atc3 = set(kod[:4] for kod in atc_map.get(db_id, [])
                    if len(kod) >= 4)
    for atc in atc3:
        col_name = f'ATC_{atc}'
        if col_name not in ilac_feat.columns:
            ilac_feat[col_name] = 0
        if atc in ilaç_atc3:
            ilac_feat.loc[ilac_feat['DrugBank_ID'] == db_id, col_name] = 1

ilac_feat.to_csv(DRIVE + 'ilac_feature_v5_atc.csv', index=False)
print(f"İlaç feature: {ilac_feat.shape}")


# ═══════════════════════════════════════════════════════════════════════════
# BÖLÜM 6: DRUGBANK XML'DEN İLAÇ-PROTEİN HEDEFLERİ
# ═══════════════════════════════════════════════════════════════════════════
# AMAÇ: Her ilacın hedef proteinlerini (insan + bakteri) çek.
# YÖNTEM: Satır satır oku, drug bloklarını string olarak topla, parse et.
# ÖNEMLİ: iterparse end-event bazen None döndürüyordu, bu yöntem güvenilir.

NS = 'http://www.drugbank.ca'
def tag(name): return f'{{{NS}}}{name}'

def cek_ilac_protein(xml_path, hedef_ids):
    """XML'den ilaç-protein eşleşmelerini çeker."""
    kayitlar = []
    bulunan = set()
    drug_buffer = []
    drug_iceride = False
    
    with open(xml_path, 'r', encoding='utf-8', errors='replace') as f:
        for satir in f:
            stripped = satir.strip()
            if stripped.startswith('<drug ') or stripped == '<drug>':
                drug_buffer = [satir]
                drug_iceride = True
                continue
            if drug_iceride:
                drug_buffer.append(satir)
                if '</drug>' in satir:
                    drug_iceride = False
                    drug_xml = ''.join(drug_buffer)
                    ilk_tag_sonu = drug_xml.index('>')
                    drug_xml = (
                        f'<drug xmlns="{NS}">'
                        + drug_xml[ilk_tag_sonu+1:]
                    )
                    try:
                        elem = ET.fromstring(drug_xml)
                    except:
                        continue
                    
                    # Primary DB ID
                    db_id = None
                    for child in elem:
                        if (child.tag == tag('drugbank-id')
                                and child.get('primary') == 'true'
                                and child.text):
                            db_id = child.text
                            break
                    
                    # İkincil ID kontrolü
                    if db_id not in hedef_ids:
                        tum_ids = [c.text for c in elem
                                   if c.tag == tag('drugbank-id') and c.text]
                        eslesen = [i for i in tum_ids if i in hedef_ids]
                        if eslesen:
                            db_id = eslesen[0]
                        else:
                            continue
                    
                    name_elem = elem.find(tag('name'))
                    drug_name = name_elem.text if name_elem is not None else ''
                    bulunan.add(db_id)
                    
                    # Target'ları çıkar
                    targets = elem.find(tag('targets'))
                    if targets is None:
                        continue
                    
                    for tgt in targets:
                        pp = tgt.find(f'.//{tag("polypeptide")}')
                        if pp is None:
                            continue
                        
                        # UniProt ID
                        uniprot_id = None
                        ext_ids = pp.find(tag('external-identifiers'))
                        if ext_ids is not None and len(ext_ids) > 0:
                            for eid in ext_ids:
                                res = eid.find(tag('resource'))
                                idn = eid.find(tag('identifier'))
                                if (res is not None and idn is not None
                                        and res.text == 'UniProtKB'):
                                    uniprot_id = idn.text
                                    break
                        
                        gene_elem = pp.find(tag('gene-name'))
                        gene_name = (gene_elem.text
                                     if gene_elem is not None else '')
                        
                        org_elem = pp.find(tag('organism'))
                        org = org_elem.text if org_elem is not None else ''
                        
                        seq_elem = pp.find(tag('sequence'))
                        seq = ''
                        if seq_elem is not None and seq_elem.text:
                            seq = seq_elem.text.replace('\n', '').strip()
                        
                        if uniprot_id:
                            kayitlar.append({
                                'DrugBank_ID': db_id,
                                'Drug_Name'  : drug_name,
                                'UniProt_ID' : uniprot_id,
                                'Gene_Name'  : gene_name,
                                'Organizma'  : org,
                                'Sequence'   : seq,
                            })
    
    return pd.DataFrame(kayitlar), bulunan

# Çalıştır
HEDEF_ILAÇLAR = set(se_match['DrugBank_ID'].unique())
df, bulunan = cek_ilac_protein(DRIVE + 'full database.xml', HEDEF_ILAÇLAR)

# Hem insan hem bakteri proteinlerini al (hocanın isteği)
df_insan = df[df['Organizma'] == 'Humans'].copy()
df_bakteri = df[df['Organizma'] != 'Humans'].copy()

# İlaç-protein kenar listesi
ilac_prot = df[['DrugBank_ID', 'Drug_Name', 'UniProt_ID',
                'Gene_Name', 'Organizma']].drop_duplicates()
ilac_prot.to_csv(DRIVE + 'ilac_protein_eslesmesi_v6.csv', index=False)

# Sequence dosyası
df_seq = df[['UniProt_ID', 'Gene_Name', 'Sequence', 'Organizma']]\
           .drop_duplicates(subset='UniProt_ID')
df_seq = df_seq[df_seq['Sequence'].str.len() > 10]
df_seq.to_csv(DRIVE + 'protein_dizileri_v6.csv', index=False)


# ═══════════════════════════════════════════════════════════════════════════
# BÖLÜM 7: PROTEİN FEATURE HESAPLAMA (AAC + GRUP DC + YZ ÖZET)
# ═══════════════════════════════════════════════════════════════════════════
# AMAÇ: Her protein için 51 boyutlu feature vektörü:
#   AAC (20)   : Amino asit kompozisyonu
#   Grup DC (25): Yan zincir grup dipeptit bileşimi
#   YZ özet (5): Asidik/bazik/polar/hidrofobik/aromatik oranı
#   Kalite (1) : UniProt prefix güvenilirliği

TUM_AA = list('ACDEFGHIKLMNPQRSTVWY')
GRUP_ISIMLER = ['Asidik', 'Bazik', 'Polar', 'Hidrofobik', 'Aromatik']
AA_GRUPLARI = {
    'Asidik'    : set('DE'),
    'Bazik'     : set('RKH'),
    'Polar'     : set('STNQ'),
    'Hidrofobik': set('AILMFVP'),
    'Aromatik'  : set('FYW'),
}

def aa_grup(aa):
    for g, u in AA_GRUPLARI.items():
        if aa in u:
            return g
    return None

def hesapla_aac(dizi):
    """Her amino asidin yüzdesini hesapla. → 20 feature"""
    dizi = re.sub(r'[^ACDEFGHIKLMNPQRSTVWY]', '', dizi.upper())
    if not dizi:
        return {aa: 0.0 for aa in TUM_AA}
    c = Counter(dizi)
    return {aa: round(c.get(aa, 0) / len(dizi), 4) for aa in TUM_AA}

def hesapla_grup_dc(dizi):
    """Yan zincir grup dipeptit frekansları. → 25 feature (5×5 grup)"""
    dizi = re.sub(r'[^ACDEFGHIKLMNPQRSTVWY]', '', dizi.upper())
    gdc = {f'{g1}_{g2}': 0.0
           for g1 in GRUP_ISIMLER for g2 in GRUP_ISIMLER}
    if len(dizi) < 2:
        return gdc
    tot = 0
    for i in range(len(dizi) - 1):
        g1, g2 = aa_grup(dizi[i]), aa_grup(dizi[i+1])
        if g1 and g2:
            gdc[f'{g1}_{g2}'] += 1
            tot += 1
    if tot > 0:
        for k in gdc:
            gdc[k] = round(gdc[k] / tot, 4)
    return gdc

def uniprot_kalite(uid):
    """P=1 (yüksek), Q/O=2 (orta), diğer=3 (düşük)"""
    p = str(uid)[0].upper() if uid else 'X'
    return {'P': 1, 'Q': 2, 'O': 2}.get(p, 3)

# Tüm proteinler için feature hesapla
rows = []
for _, row in df_seq.iterrows():
    uid = row['UniProt_ID']
    dizi = row['Sequence']
    
    satir = {
        'UniProt_ID'  : uid,
        'Gene_Name'   : row.get('Gene_Name', ''),
        'Organizma'   : row.get('Organizma', ''),
        'kalite_skoru': uniprot_kalite(uid),
    }
    
    # AAC
    aac = hesapla_aac(dizi)
    for aa, val in aac.items():
        satir[f'AAC_{aa}'] = val
    
    # Grup DC
    gdc = hesapla_grup_dc(dizi)
    for key, val in gdc.items():
        satir[f'DC_{key}'] = val
    
    # YZ özet
    satir['YZ_Asidik']     = round(sum(aac[a] for a in 'DE'), 4)
    satir['YZ_Bazik']      = round(sum(aac[a] for a in 'RKH'), 4)
    satir['YZ_Polar']      = round(sum(aac[a] for a in 'STNQ'), 4)
    satir['YZ_Hidrofobik'] = round(sum(aac[a] for a in 'AILMFVP'), 4)
    satir['YZ_Aromatik']   = round(sum(aac[a] for a in 'FYW'), 4)
    
    rows.append(satir)

prot_feat = pd.DataFrame(rows)
prot_feat.to_csv(DRIVE + 'protein_feature_v6.csv', index=False)
print(f"Protein feature: {prot_feat.shape}")


# ═══════════════════════════════════════════════════════════════════════════
# BÖLÜM 8: HETEROJEN GRAF KURULUMU (PyTorch Geometric)
# ═══════════════════════════════════════════════════════════════════════════
# AMAÇ: 3 düğüm tipi + 3 kenar tipini içeren HeteroData oluştur.

from torch_geometric.data import HeteroData

# Verileri yükle
ilac_feat = pd.read_csv(DRIVE + 'ilac_feature_v5_atc.csv')
prot_feat = pd.read_csv(DRIVE + 'protein_feature_v6.csv')
se_df = pd.read_csv(DRIVE + 'ilac_yan_etki_v5.csv')
ilac_prot = pd.read_csv(DRIVE + 'ilac_protein_eslesmesi_v6.csv')

# Kesişim: SE ∩ Protein olan ilaçlar
se_ilaçlar = set(se_df['DrugBank_ID'])
prot_ilaçlar = set(ilac_prot['DrugBank_ID'])
ilac_ids = sorted(se_ilaçlar & prot_ilaçlar)  # 38 ilaç

ilac_feat = ilac_feat[ilac_feat['DrugBank_ID'].isin(ilac_ids)].reset_index(drop=True)
se_df = se_df[se_df['DrugBank_ID'].isin(ilac_ids)]
ilac_prot = ilac_prot[ilac_prot['DrugBank_ID'].isin(ilac_ids)]

prot_ids = sorted(ilac_prot['UniProt_ID'].unique())
prot_feat = prot_feat[prot_feat['UniProt_ID'].isin(prot_ids)].reset_index(drop=True)
se_kategoriler = sorted(se_df['se_kategori'].unique())

# Düğüm indeksleri
drug_to_idx = {d: i for i, d in enumerate(ilac_ids)}
prot_to_idx = {p: i for i, p in enumerate(prot_ids)}
se_to_idx   = {s: i for i, s in enumerate(se_kategoriler)}

# Feature matrisleri
ilac_sayisal = ['MW_norm', 'LogP_norm', 'HBD_norm', 'HBA_norm', 'TPSA_norm']
atc_cols = [c for c in ilac_feat.columns if c.startswith('ATC_')]
X_drug = torch.tensor(
    ilac_feat[ilac_sayisal + atc_cols].fillna(0).values,
    dtype=torch.float32
)

aac_cols = [c for c in prot_feat.columns if c.startswith('AAC_')]
dc_cols = [c for c in prot_feat.columns if c.startswith('DC_')]
yz_cols = ['YZ_Asidik', 'YZ_Bazik', 'YZ_Polar', 'YZ_Hidrofobik', 'YZ_Aromatik']
prot_feat['kalite_skoru'] = prot_feat['kalite_skoru'].fillna(3)
X_prot = torch.tensor(
    prot_feat[aac_cols + dc_cols + yz_cols + ['kalite_skoru']].values,
    dtype=torch.float32
)

X_se = torch.eye(len(se_to_idx), dtype=torch.float32)  # one-hot

# HeteroData oluştur
data = HeteroData()
data['drug'].x = X_drug
data['protein'].x = X_prot
data['side_effect'].x = X_se

# Kenar 1: İlaç → Protein
dp_src, dp_dst = [], []
for _, row in ilac_prot.iterrows():
    if (row['DrugBank_ID'] in drug_to_idx
            and row['UniProt_ID'] in prot_to_idx):
        dp_src.append(drug_to_idx[row['DrugBank_ID']])
        dp_dst.append(prot_to_idx[row['UniProt_ID']])
data['drug', 'targets', 'protein'].edge_index = torch.tensor(
    [dp_src, dp_dst], dtype=torch.long
)

# Kenar 2: Protein → Protein (PPI) — chunk okuma
ppi_chunks = []
for chunk in pd.read_csv(DRIVE + 'ppi_insan_v3.csv', chunksize=500_000):
    mask = (chunk['protein1_uniprot'].isin(prot_ids) &
            chunk['protein2_uniprot'].isin(prot_ids))
    ppi_chunks.append(chunk[mask])
for chunk in pd.read_csv(DRIVE + 'ppi_bakteri_v3.csv', chunksize=100_000):
    mask = (chunk['protein1_uniprot'].isin(prot_ids) &
            chunk['protein2_uniprot'].isin(prot_ids))
    ppi_chunks.append(chunk[mask])
ppi_df = pd.concat(ppi_chunks, ignore_index=True)

pp_src, pp_dst = [], []
for _, row in ppi_df.iterrows():
    p1, p2 = row['protein1_uniprot'], row['protein2_uniprot']
    if p1 in prot_to_idx and p2 in prot_to_idx:
        pp_src.append(prot_to_idx[p1])
        pp_dst.append(prot_to_idx[p2])
data['protein', 'interacts', 'protein'].edge_index = torch.tensor(
    [pp_src, pp_dst], dtype=torch.long
)

# Kenar 3: İlaç → Yan Etki (Tahmin hedefi)
se_src, se_dst = [], []
for _, row in se_df.iterrows():
    if (row['DrugBank_ID'] in drug_to_idx
            and row['se_kategori'] in se_to_idx):
        se_src.append(drug_to_idx[row['DrugBank_ID']])
        se_dst.append(se_to_idx[row['se_kategori']])
data['drug', 'causes', 'side_effect'].edge_index = torch.tensor(
    [se_src, se_dst], dtype=torch.long
)

torch.save(data, DRIVE + 'heterogen_ag_v6.pt')


# ═══════════════════════════════════════════════════════════════════════════
# BÖLÜM 9: GiG MODEL EĞİTİMİ
# ═══════════════════════════════════════════════════════════════════════════
# AMAÇ: Heterojen graf üzerinde link prediction.
# MİMARİ: 3 ayrı MLP encoder + ilaç-protein agregasyon + tahmin başlığı

class GiGModel(nn.Module):
    """
    Graph-in-Graph (GiG) Modeli
    
    İç ağ: Protein-Protein etkileşimi (encoder ile temsil öğrenir)
    Dış ağ: İlaç-protein-yan etki bilgi akışı
    
    İleri yayılım:
      h_p = MLP_P(x_p)                          # protein gömme
      h_d^(0) = MLP_D(x_d)                       # ilaç temel gömme
      μ_d = mean(h_p for p in N(d))             # protein bilgi aktarımı
      h_d = ReLU(W_agg · [h_d^(0) ∥ μ_d])        # ilaç son gömme
      h_s = MLP_S(x_s)                          # yan etki gömme
      ŷ_ds = σ(MLP_pred([h_d ∥ h_s]))            # link skoru
    """
    def __init__(self, drug_dim, prot_dim, se_dim,
                 hidden_dim=64, out_dim=32):
        super().__init__()
        
        # 3 encoder
        self.drug_enc = nn.Sequential(
            nn.Linear(drug_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, out_dim)
        )
        self.prot_enc = nn.Sequential(
            nn.Linear(prot_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden_dim, out_dim)
        )
        self.se_enc = nn.Sequential(
            nn.Linear(se_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, out_dim)
        )
        
        # İlaç-protein agregasyon
        self.drug_prot_agg = nn.Linear(out_dim * 2, out_dim)
        
        # Link prediction başlığı
        self.predictor = nn.Sequential(
            nn.Linear(out_dim * 2, hidden_dim), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, x_drug, x_prot, x_se, dp_ei,
                pred_drug_idx, pred_se_idx):
        # 1. Protein gömme
        h_prot = self.prot_enc(x_prot)
        
        # 2. İlaç temel gömme
        h_drug_base = self.drug_enc(x_drug)
        
        # 3. İlaç-protein bilgi aktarımı (μ_d)
        if dp_ei.shape[1] > 0:
            agg_prot = torch.zeros(x_drug.shape[0], h_prot.shape[1],
                                   device=x_drug.device)
            counts = torch.zeros(x_drug.shape[0], 1, device=x_drug.device)
            agg_prot.index_add_(0, dp_ei[0], h_prot[dp_ei[1]])
            counts.index_add_(0, dp_ei[0],
                              torch.ones(dp_ei.shape[1], 1,
                                         device=x_drug.device))
            counts = counts.clamp(min=1)
            agg_prot = agg_prot / counts
            h_drug = F.relu(self.drug_prot_agg(
                torch.cat([h_drug_base, agg_prot], dim=1)
            ))
        else:
            h_drug = h_drug_base
        
        # 4. Yan etki gömme
        h_se = self.se_enc(x_se)
        
        # 5. Link prediction
        out = self.predictor(torch.cat(
            [h_drug[pred_drug_idx], h_se[pred_se_idx]], dim=1
        ))
        return out.squeeze(-1)

# Train/test split + negatif örnekleme
data = torch.load(DRIVE + 'heterogen_ag_v6.pt', weights_only=False)
pos_edge_index = data['drug', 'causes', 'side_effect'].edge_index
pos_edges = np.array(pos_edge_index.t().tolist())
pos_set = set(map(tuple, pos_edges))

# Negatif örnekleme: 2× pozitif
np.random.seed(42)
neg_edges = []
while len(neg_edges) < len(pos_edges) * 2:
    d = np.random.randint(0, data['drug'].x.shape[0])
    s = np.random.randint(0, data['side_effect'].x.shape[0])
    if (d, s) not in pos_set:
        neg_edges.append((d, s))

all_edges = np.vstack([pos_edges, np.array(neg_edges)])
all_labels = np.array([1] * len(pos_edges) + [0] * len(neg_edges))

train_idx, test_idx = train_test_split(
    list(range(len(all_edges))),
    test_size=0.2, random_state=42, stratify=all_labels
)

train_edges  = torch.tensor(all_edges[train_idx], dtype=torch.long).to(DEVICE)
test_edges   = torch.tensor(all_edges[test_idx], dtype=torch.long).to(DEVICE)
train_labels = torch.tensor(all_labels[train_idx], dtype=torch.float32).to(DEVICE)
test_labels  = torch.tensor(all_labels[test_idx], dtype=torch.float32).to(DEVICE)

# Model
model = GiGModel(
    drug_dim=data['drug'].x.shape[1],
    prot_dim=data['protein'].x.shape[1],
    se_dim=data['side_effect'].x.shape[1]
).to(DEVICE)

X_drug = data['drug'].x.to(DEVICE)
X_prot = data['protein'].x.to(DEVICE)
X_se   = data['side_effect'].x.to(DEVICE)
dp_ei  = data['drug', 'targets', 'protein'].edge_index.to(DEVICE)

optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
criterion = nn.BCEWithLogitsLoss()

# Eğitim döngüsü
for epoch in range(1, 201):
    model.train()
    optimizer.zero_grad()
    out = model(X_drug, X_prot, X_se, dp_ei,
                train_edges[:, 0], train_edges[:, 1])
    loss = criterion(out, train_labels)
    loss.backward()
    optimizer.step()
    
    if epoch % 20 == 0:
        model.eval()
        with torch.no_grad():
            te_out = model(X_drug, X_prot, X_se, dp_ei,
                           test_edges[:, 0], test_edges[:, 1])
            te_prob = torch.sigmoid(te_out).tolist()
            te_true = test_labels.tolist()
        auroc = roc_auc_score(te_true, te_prob)
        aupr  = average_precision_score(te_true, te_prob)
        print("Epoch %3d | Loss: %.4f | AUROC: %.4f | AUPR: %.4f" % (
            epoch, loss.item(), auroc, aupr
        ))

# Sonuç: AUROC 0.90, AUPR 0.85


# ═══════════════════════════════════════════════════════════════════════════
# BÖLÜM 10: AÇIKLANABİLİRLİK ANALİZİ (XAI)
# ═══════════════════════════════════════════════════════════════════════════
# AMAÇ:
#   Katman 1: Her ilaç için top-5 yan etki tahmini
#   Katman 2: Feature önem analizi (gradient × input)
#   Katman 3: Her ilaç için en etkili 3 protein

# Katman 1 — Top-5 tahmin
model.eval()
tahmin_sonuclari = []
with torch.no_grad():
    for di in range(data['drug'].x.shape[0]):
        d_idx = torch.tensor([di] * data['side_effect'].x.shape[0]).to(DEVICE)
        s_idx = torch.arange(data['side_effect'].x.shape[0]).to(DEVICE)
        out = model(X_drug, X_prot, X_se, dp_ei, d_idx, s_idx)
        skorlar = torch.sigmoid(out).tolist()
        top5_idx = sorted(range(len(skorlar)),
                          key=lambda i: skorlar[i], reverse=True)[:5]
        # ... kayıt

# Katman 2 — Feature önem (gradient × input)
X_drug_g = X_drug.clone().requires_grad_(True)
X_prot_g = X_prot.clone().requires_grad_(True)
pos_d = torch.tensor(pos_edges[:, 0], dtype=torch.long).to(DEVICE)
pos_s = torch.tensor(pos_edges[:, 1], dtype=torch.long).to(DEVICE)
out = model(X_drug_g, X_prot_g, X_se, dp_ei, pos_d, pos_s)
out.sum().backward()
drug_importance = (X_drug_g.grad * X_drug_g).abs().mean(dim=0).cpu().tolist()
prot_importance = (X_prot_g.grad * X_prot_g).abs().mean(dim=0).cpu().tolist()

# Katman 3 — Protein katkı
with torch.no_grad():
    h_prot_all = model.prot_enc(X_prot)
    prot_etki = h_prot_all.abs().sum(dim=1).cpu().tolist()


# ═══════════════════════════════════════════════════════════════════════════
# SON: SONUÇLAR
# ═══════════════════════════════════════════════════════════════════════════
# AUROC: 0.9004
# AUPR : 0.8545
# Top-5 isabet: %84.2
# Klinik doğrulama: Ciprofloxacin → parE, gyrA, parC (literatür uyumlu)
# ═══════════════════════════════════════════════════════════════════════════

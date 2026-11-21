"""Kaydedilmiş QC özetlerinden yerel+Drive WP00 envanteri ve tablolarını üret.

Drive ham CSV'leri kaydedilmez. Yeni Drive ölçümü için bağlantı üzerinden fetch
yanıtları wp00_drive_qc.cjs ile bellekte işlenir; sadece derived JSON güncellenir.
"""
import csv
import json
from pathlib import Path
from wp00_audit import ALLOW, QC_NAMES, PPI_NAMES, STRING_NAMES, source_group, md_cell

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'reports/qa'

def read_json(name):
    return json.loads((QA/name).read_text(encoding='utf-8'))

def main():
    remote = read_json('drive_inventory.json')
    profiles = read_json('drive_profiles.json')
    findings = read_json('drive_findings.json')
    local_path = QA / 'local_inventory.csv'
    if not local_path.exists():
        local_path.write_bytes((QA/'data_inventory.csv').read_bytes())
    with local_path.open(encoding='utf-8-sig', newline='') as f:
        local = list(csv.DictReader(f))
    by_name = {r['name']: r for r in remote if r['name'] in ALLOW}
    combined = []
    for row in local:
        row = dict(row, location='local', local_status=row['status'], remote_status='', file_id='', modified_time='')
        rem = by_name.get(row['name'])
        if rem and row['scope'] != 'allowed_container':
            row['remote_status'] = 'exists'
        if row['status'] == 'missing' and rem:
            row.update(status='exists', path=rem['url'], size_bytes=rem['size_bytes'], location='drive',
                       inspected=rem['inspected'], file_id=rem['id'], modified_time=rem['modified_time'],
                       version='V5/V6 dosya adı; yayın sürümü doğrulanmadı' if row['name'] in QC_NAMES else 'dosya sürümü bilinmiyor',
                       reason=rem['scope'] + '; doğrudan bağlantı, ham CSV diske kaydedilmedi')
        combined.append(row)
    # Dışlanan Drive girdilerinde sadece ad tutulur; metadata/kopya/şema yok.
    keys=list(combined[0])
    for rem in remote:
        if rem['status']=='excluded':
            row={k:'' for k in keys}
            row.update(name=rem['name'], source='out_of_scope', status='excluded', scope='name_only',
                       inspected=False, location='drive', reason='Klasör üst düzey adı; içerik okunmadı.')
            combined.append(row)
    for name in ['data_inventory.csv','source_inventory.csv']:
        with (QA/name).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(combined)

    blocks=['# Drive CSV şemaları ve kalite profilleri','',
            'Yedi CSV doğrudan Google Drive bağlantısından bellekte okundu; ham CSV kopyası yerel diske yazılmadı. '
            'Yanıt UTF-8 bayt uzunluğu yedi dosyada da Drive boyutuyla eşleşti; okuma öncesi/sonrası size ve modified_time değişmedi. '
            'Bunlar kriptografik checksum kontrolü değildir. Sürüm alanı olmayan CSV için dosya adı ve değiştirilme tarihi provenans olarak tutuldu.', '']
    for name,p in profiles.items():
        blocks += [f'## {name}', '', f'Kaynak: [{p["file_id"]}]({p["source_url"]}); değiştirilme: {p["modified_time"]}.',
                   f'Tam CSV: **{p["rows"]} satır × {p["column_count"]} sütun**. Tam satır tekrar fazlası: {p["duplicate_full_rows_excess"]}.', '',
                   '| Alan | Gözlenen tip | Tüm CSV boş | Boş % | İlk en çok 1000 boş / n |', '|---|---|---:|---:|---:|']
        blocks += [f'| {md_cell(c["name"])} | {c["dtype_observed"]} | {c["missing_count"]} | {c["missing_pct"]:.4f} | {c["missing_first_1000"]}/{c["sample_size"]} |' for c in p['columns']]
        blocks += ['', 'İlk üç kayıt (uzun diziler görünüm için kısaltılmıştır):', '', '```json', json.dumps(p['examples'],ensure_ascii=False,indent=2), '```','']
    (QA/'drive_schema_summary.md').write_text('\n'.join(blocks),encoding='utf-8')
    schema=QA/'schema_summary.md'
    text=schema.read_text(encoding='utf-8').split('## Yerelde bulunamayan, Drive doğrulaması bekleyen dosyalar')[0].split('## Drive incelemesi')[0]
    text+='\n## Drive incelemesi\n\nKimlik köprüsü ve yedi CSV incelemesi tamamlandı. Tam sütun listeleri, örnekler ve boşluk oranları '
    text+='[drive_schema_summary.md](drive_schema_summary.md) dosyasında; ölçümler `drive_profiles.json` içinde. '
    text+='Allowlist kaynaklarının tamamı yerelde veya Drive’da mevcut. Yerel eksiklik genel dosya yokluğu değildir.\n'
    schema.write_text(text,encoding='utf-8')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    groups=['DrugBank','SIDER','STRING','V5/V6 QC']
    lc=[sum(r['name'] in ALLOW and r['scope']!='allowed_container' and r['status']=='exists' and source_group(r['name'])==g for r in local) for g in groups]
    rc=[sum(r['name'] in ALLOW and source_group(r['name'])==g for r in remote) for g in groups]
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
    x=list(range(4))
    for offset,counts,label,color in [(-.19,lc,'Yerel','#23788c'),(.19,rc,'Google Drive','#c08235')]:
        bars=ax.bar([i+offset for i in x],counts,.36,label=label,color=color)
        ax.bar_label(bars,padding=4)
    ax.set_xticks(x,groups);ax.set_ylim(0,8.7);ax.set_ylabel('Allowlist dosya sayısı')
    ax.set_title('WP00 · Yerel ve Drive kaynaklarının bulunabilirliği',loc='left',fontweight='bold',pad=15)
    ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False)
    ax.text(0,-.18,'Aynı kaynak iki konumda bulunabilir. 16 benzersiz allowlist dosyası; 7 Drive CSV içeriği incelendi.',transform=ax.transAxes,fontsize=9)
    fig.savefig(ROOT/'reports/figures/source_counts.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
    counts=findings['drug_counts']
    values=[counts['chemistry'],counts['adr'],counts['targets'],counts['three_way']]
    bars=ax.barh(['Kimyasal özellik','Yan etki etiketi','Hedef protein bağı','Üç kümenin kesişimi'],values,color=['#23788c']*3+['#c08235'])
    ax.invert_yaxis();ax.bar_label(bars,padding=5);ax.set_xlim(0,66)
    ax.set_title('WP00 · Gerçek V5/V6 CSV’lerinden ilaç kapsamı',loc='left',fontweight='bold',pad=15)
    ax.set_xlabel('Benzersiz DrugBank ID sayısı');ax.spines[['top','right']].set_visible(False)
    ax.text(0,-.20,'Bu kümeler saf J01 kohortu değildir. 15 etiketli ve kimyalı kayıtta hedef bağlantısı eksik.',transform=ax.transAxes,fontsize=9)
    fig.savefig(ROOT/'reports/figures/legacy_coverage.png',dpi=180);plt.close(fig)
    print('Yerel + Drive envanteri, Drive şemaları ve kapsam görselleri güncellendi.')

if __name__=='__main__':
    main()

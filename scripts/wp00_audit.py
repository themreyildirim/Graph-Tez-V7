"""WP00 salt okunur keşif. Yalnız açık yollar, sınırlı örnekler; API/model yok.

Çalıştır: python scripts/wp00_audit.py
Çıktılar proje içindeki reports/ ve docs/ dizinlerine yazılır.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = Path(r'C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset')
AA = set('ACDEFGHIKLMNPQRSTVWY')
SIDER_COLUMNS = ['flat_id', 'stereo_id', 'umls_cui_from_label', 'meddra_type', 'umls_cui', 'side_effect_name']
QC_NAMES = ['ilac_feature_v5_atc.csv', 'ilac_yan_etki_v5.csv', 'ilac_protein_eslesmesi_v6.csv',
            'protein_dizileri_v6.csv', 'protein_feature_v6.csv', 'sadece_antibiyotikler.csv', 'heterogen_ag_v6.pt']
PPI_NAMES = ['ppi_insan_v3.csv', 'ppi_bakteri_v3.csv']
PRIMARY_NAMES = ['full database.xml', 'meddra_all_se.tsv', 'drug links.csv']
STRING_NAMES = [f'{tax}.protein.{kind}.v12.0.txt' for tax in ['9606', '511145'] for kind in ['links', 'aliases']]
ALLOW = set(PRIMARY_NAMES + QC_NAMES + PPI_NAMES + STRING_NAMES)

def allowed_directories(data_root: Path):
    """Recursion yok: yalnız onaylı kaynak klasörleri ve bilinen açılmış paketler."""
    dirs = [data_root, data_root / 'DrugBank', data_root / 'DrugBank/drugbank_all_full_database.xml',
            data_root / 'SIDER', data_root / 'SIDER/meddra_all_se.tsv', data_root / 'string-db']
    for tax, org in [('9606', 'Homo Sapiens'), ('511145', 'Escherichia coli')]:
        base = data_root / 'string-db' / org
        dirs.append(base)
        dirs.extend(base / f'{tax}.protein.{kind}.v12.0.txt' for kind in ['links', 'aliases'])
    return dirs

def source_group(name):
    if name in STRING_NAMES or name in PPI_NAMES:
        return 'STRING'
    if name == 'meddra_all_se.tsv':
        return 'SIDER'
    if name in QC_NAMES:
        return 'V5/V6 QC'
    return 'DrugBank'

def inventory(data_root):
    rows, found = [], set()
    directories = allowed_directories(data_root)
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            # Kapsam dışı dosyalar: yalnız isim ve klasör/entry, içerik/stat/hash yok.
            included = path.name in ALLOW and path.is_file()
            if not included:
                container = path in directories
                rows.append(dict(name=path.name, path=str(path), source='navigation' if container else 'out_of_scope',
                                 status='exists' if container else 'excluded',
                                 scope='allowed_container' if container else 'name_only', size_bytes='', mtime_ns='', attributes='', inspected=False,
                                 version='', reason='İzinli kaynak klasörü.' if container else 'Allowlist dışında; yalnız ad; içerik okunmadı.'))
                continue
            st = path.stat()
            rows.append(dict(name=path.name, path=str(path), source=source_group(path.name), status='exists',
                             scope='legacy_qc' if path.name in QC_NAMES else 'conditional_ppi' if path.name in STRING_NAMES + PPI_NAMES else 'primary',
                             size_bytes=st.st_size, mtime_ns=st.st_mtime_ns, attributes=getattr(st, 'st_file_attributes', ''),
                             inspected=False, version='v12.0 (dosya adı)' if path.name in STRING_NAMES else 'bilinmiyor',
                             reason='Dosya metadata kontrolü; içerik incelemesi ayrı.'))
            found.add(path.name)
    for name in sorted(ALLOW - found):
        rows.append(dict(name=name, path='', source=source_group(name), status='missing', scope='legacy_qc' if name in QC_NAMES else 'conditional_ppi' if name in PPI_NAMES + STRING_NAMES else 'primary',
                         size_bytes='', mtime_ns='', attributes='', inspected=False, version='bilinmiyor',
                         reason='Yalnız izinli yerel konumlarda bulunamadı; Drive varlığı kullanıcı tarafından bildirildi, erişim/doğrulama bekleniyor.'
                         if name in QC_NAMES + PPI_NAMES + ['drug links.csv'] else 'Yalnız izinli yerel konumlarda bulunamadı.'))
    return rows

def parse_sequence(text):
    """Sadece QC: satır sınırı korunmuş FASTA'yı doğrula, belirsiz birleşik header'ı reddet.

    AAC/DC üretmez, kaynak metnini değiştirmez. X/U/O/B/Z politikası WP05'e bırakılır.
    """
    lines = [s.strip() for s in text.strip().splitlines() if s.strip()]
    if not lines:
        raise ValueError('empty_sequence')
    if lines[0].startswith('>'):
        if len(lines) == 1:
            raise ValueError('header_boundary_lost')
        lines = lines[1:]
    seq = ''.join(lines)
    if not seq or set(seq) - AA:
        raise ValueError('non_standard_amino_acids_or_metadata')
    return seq

def sample_xml(path, limit=3):
    """Yalnız root'un doğrudan drug çocukları; nested drug kayıtları sayılmaz."""
    records, root_attrs, depth = [], {}, 0
    with path.open('rb') as stream:
        for event, elem in ET.iterparse(stream, events=('start', 'end')):
            if event == 'start':
                depth += 1
                if depth == 1:
                    root_attrs = dict(elem.attrib)
                    root_tag = elem.tag
                continue
            if depth == 2 and elem.tag.rsplit('}', 1)[-1] == 'drug':
                ns = elem.tag.split('}')[0] + '}' if '}' in elem.tag else ''
                def val(node, tag):
                    return node.findtext(ns + tag, default='')
                ids = [{'value': c.text, 'primary': c.get('primary', '')} for c in elem.findall(ns + 'drugbank-id')]
                polypeptides = []
                for pp in elem.findall(f'{ns}targets/{ns}target/{ns}polypeptide'):
                    sequences = []
                    for child in pp:
                        local = child.tag.rsplit('}', 1)[-1]
                        if local == 'amino-acid-sequence':
                            raw = child.text or ''
                            try:
                                clean = parse_sequence(raw)
                                qc = 'standard_20_AA'
                                clean_len = len(clean)
                            except ValueError as exc:
                                qc, clean_len = str(exc), None
                            sequences.append({'tag': local, 'format': child.get('format'), 'raw_prefix': raw[:140],
                                              'raw_length': len(raw), 'qc': qc, 'sequence_length': clean_len})
                    polypeptides.append({'id': pp.get('id'), 'source': pp.get('source'), 'organism': val(pp, 'organism'),
                                         'gene_name': val(pp, 'gene-name'), 'child_tags': [c.tag.rsplit('}', 1)[-1] for c in pp],
                                         'identifiers': [{'resource': val(e, 'resource'), 'identifier': val(e, 'identifier')}
                                                         for e in pp.findall(f'{ns}external-identifiers/{ns}external-identifier')],
                                         'sequences': sequences})
                records.append({'ids': ids, 'name': val(elem, 'name'), 'type': elem.get('type'),
                                'atc_codes': [a.get('code') for a in elem.findall(f'{ns}atc-codes/{ns}atc-code')],
                                'external_identifiers': [{'resource': val(e, 'resource'), 'identifier': val(e, 'identifier')}
                                                         for e in elem.findall(f'{ns}external-identifiers/{ns}external-identifier')],
                                'target_polypeptides': polypeptides,
                                'child_tags': [c.tag.rsplit('}', 1)[-1] for c in elem]})
                elem.clear()
                if len(records) >= limit:
                    break
            depth -= 1
        bytes_read = stream.tell()
    return {'kind': 'xml', 'root_tag': root_tag, 'root_attributes': root_attrs, 'sample_size': len(records),
            'bytes_read_including_parser_buffer': bytes_read, 'scope': 'first_3_top_level_drugs', 'examples': records,
            'whole_file_validated': False}

def infer_type(values):
    nonempty = [v for v in values if v.strip()]
    if not nonempty:
        return 'unknown (all empty)'
    if all(re.fullmatch(r'[+-]?\d+', v) for v in nonempty):
        return 'integer-like; identifier may need string'
    try:
        for v in nonempty:
            float(v)
        return 'numeric-like'
    except ValueError:
        return 'string'

def sample_table(path, limit=1000):
    name = path.name
    with path.open('r', encoding='utf-8-sig', newline='') as stream:
        if name == 'meddra_all_se.tsv':
            reader, columns = csv.reader(stream, delimiter='\t'), SIDER_COLUMNS
        elif name in STRING_NAMES and '.links.' in name:
            columns = next(stream).strip().split()
            reader = (line.strip().split() for line in stream)
        elif name in STRING_NAMES and '.aliases.' in name:
            reader = csv.reader(stream, delimiter='\t')
            columns = next(reader)
        else:
            reader = csv.reader(stream)
            columns = next(reader)
        rows = list(islice(reader, limit + 1))
    complete = len(rows) <= limit
    rows = rows[:limit]
    malformed = [i + 1 for i, r in enumerate(rows) if len(r) != len(columns)]
    valid = [r for r in rows if len(r) == len(columns)]
    fields = []
    for i, col in enumerate(columns):
        vals = [r[i] for r in valid]
        missing = sum(not v.strip() for v in vals)
        fields.append({'name': col, 'dtype_observed': infer_type(vals), 'missing_count': missing,
                       'missing_pct': round(100 * missing / len(vals), 4) if vals else None,
                       'distinct_in_sample': len(set(vals)), 'examples': list(dict.fromkeys(vals))[:3]})
    details = {}
    if name == 'meddra_all_se.tsv':
        details['meddra_type_counts'] = dict(Counter(r[3] for r in valid))
        details['unique_stereo_ids'] = len({r[1] for r in valid})
        details['duplicate_stereo_umls_type_excess'] = len(valid) - len({(r[1], r[3], r[4]) for r in valid})
        # Yerel dosyada gözlenen biçim: flat=CID1..., stereo=CID0... . CID dönüşümü yapılmaz.
        details['stitch_pattern_invalid_rows'] = sum(not (re.fullmatch(r'CID1\d+', r[0]) and re.fullmatch(r'CID0\d+', r[1])) for r in valid)
        details['observed_prefixes'] = {'flat': dict(Counter(r[0][:4] for r in valid)), 'stereo': dict(Counter(r[1][:4] for r in valid))}
    if name in STRING_NAMES and '.links.' in name:
        tax = name.split('.')[0]
        details['taxon_prefix_invalid_rows'] = sum(not (r[0].startswith(tax+'.') and r[1].startswith(tax+'.')) for r in valid)
        details['score_min'] = min(int(r[2]) for r in valid)
        details['score_max'] = max(int(r[2]) for r in valid)
        details['self_loops'] = sum(r[0] == r[1] for r in valid)
        details['duplicate_directed_pairs_excess'] = len(valid) - len({(r[0], r[1]) for r in valid})
    if name in STRING_NAMES and '.aliases.' in name:
        details['duplicate_protein_alias_excess'] = len(valid) - len({(r[0], r[1]) for r in valid})
        details['source_values_first_10'] = list(dict.fromkeys(r[2] for r in valid))[:10]
        details['multiple_aliases_expected'] = True
    return {'kind': 'table', 'sample_size': len(rows), 'complete_file_read': complete,
            'scope': 'whole_file' if complete else f'first_{limit}_records', 'columns': fields,
            'malformed_row_numbers_in_sample': malformed, 'duplicate_full_rows_excess': len(valid) - len(set(map(tuple, valid))),
            'examples': [dict(zip(columns, r)) for r in valid[:3]], 'details': details,
            'header_source': 'assigned_from_legacy_code; no file header' if name == 'meddra_all_se.tsv' else 'file_header'}

def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def md_cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')

def write_reports(rows, profiles, out):
    qa = out / 'reports/qa'
    fields = list(rows[0])
    for filename in ['data_inventory.csv', 'source_inventory.csv']:
        with (qa / filename).open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    text = ['# WP00 gerçek dosya şemaları', '',
            'Örnekleme: XML ilk 3 üst düzey ilaç; metin tabloları ilk 1000 kayıt. Bunlar rastgele örnekler değildir. '
            'Eksiklik yalnız boş/whitespace hücredir; biyolojik eksiklik veya geçersiz kimlik aynı şey değildir. '
            'İlk 1001 kayıt okunarak dosyanın bitip bitmediği kontrol edilir; istatistiklere yalnız ilk 1000 girer. '
            'Tam dosya satır sayısı ve genel eksiklik oranı çıkarılmadı.', '']
    for name, profile in profiles.items():
        text += [f'## {name}', '', f'İnceleme kapsamı: `{profile["scope"]}`.', '']
        if profile['kind'] == 'table':
            text += ['| Alan | Gözlenen tip | Boş hücre | Boş % | Örnekte farklı değer |', '|---|---|---:|---:|---:|']
            text += ['| ' + ' | '.join(md_cell(c[k]) for k in ['name', 'dtype_observed', 'missing_count', 'missing_pct', 'distinct_in_sample']) + ' |' for c in profile['columns']]
            text += ['', f'Tam satır tekrar fazlası: {profile["duplicate_full_rows_excess"]}; hatalı sütun sayılı satırlar: {profile["malformed_row_numbers_in_sample"]}.',
                     '', 'Örnek kapsamındaki ek kontroller:', '', '```json', json.dumps(profile['details'], ensure_ascii=False, indent=2), '```']
        else:
            text += [f'Kök etiket: `{profile["root_tag"]}`; metadata: `{profile["root_attributes"]}`.',
                     f'Okunan bayt (parser tamponu dahil): {profile["bytes_read_including_parser_buffer"]}. Tüm XML geçerliliği sınanmadı.']
        text += ['', 'İlk üç gerçek örnek (temsili dağılım iddiası yok):', '', '```json', json.dumps(profile['examples'], ensure_ascii=False, indent=2), '```', '']
    text += ['## Yerelde bulunamayan, Drive doğrulaması bekleyen dosyalar', '', *[f'- `{r["name"]}`: {r["reason"]}' for r in rows if r['status'] == 'missing'], '',
             'Bu dosyalar için şema/eksiklik/tekrar ölçülmedi; eski belgelerdeki tablolar ham CSV yerine geçirilmedi.']
    (qa / 'schema_summary.md').write_text('\n'.join(text), encoding='utf-8')

def figures(rows, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
    available = [r for r in rows if r['status'] == 'exists' and r['size_bytes'] != '']
    available.sort(key=lambda r: r['size_bytes'])
    fig, ax = plt.subplots(figsize=(12, 5.8), layout='constrained')
    vals = [r['size_bytes'] / 1_000_000 for r in available]
    bars = ax.barh([r['name'] for r in available], vals, color=['#23788c' if r['source'] != 'STRING' else '#c08235' for r in available])
    ax.set_xscale('log')
    ax.set_xlim(max(min(vals) * .6, .001), max(vals) * 2.4)
    ax.bar_label(bars, labels=[f'{v:,.2f} MB' for v in vals], padding=5, fontsize=9)
    ax.set_xlabel('Dosya boyutu — MB (1 MB = 1.000.000 bayt), logaritmik eksen')
    ax.set_title('WP00 · İzin verilen mevcut dosyaların boyutları', loc='left', fontweight='bold', pad=14)
    ax.spines[['top','right']].set_visible(False)
    fig.savefig(out / 'reports/figures/source_sizes.png', dpi=180)
    plt.close(fig)
    groups = ['DrugBank', 'SIDER', 'STRING', 'V5/V6 QC']
    counts = {s: [sum(r['source']==g and r['status']==s for r in rows) for g in groups] for s in ['exists','missing','unreadable']}
    fig, ax = plt.subplots(figsize=(10, 5), layout='constrained')
    bottom = [0]*len(groups)
    for status, label, color in [('exists','Mevcut','#23788c'),('missing','İzinli konumlarda bulunamadı','#c08235'),('unreadable','Okunamadı','#a44242')]:
        values = counts[status]
        bars = ax.bar(groups, values, bottom=bottom, label=label, color=color)
        ax.bar_label(bars, labels=[str(v) if v else '' for v in values], label_type='center', color='white', fontweight='bold')
        bottom = [a+b for a,b in zip(bottom, values)]
    ax.set_ylabel('Allowlist dosya sayısı')
    ax.set_title('WP00 · Kaynakların yerel bulunabilirliği', loc='left', fontweight='bold', pad=15)
    ax.set_ylim(0, max(bottom)+2)
    ax.legend(loc='upper right', frameon=False, fontsize=9)
    ax.text(0, -.19, 'Arşiv kopyaları ve kapsam dışı adlar sayılmadı. STRING: 4 ham + 2 işlenmiş dosya beklentisi.', transform=ax.transAxes, fontsize=9)
    ax.spines[['top','right']].set_visible(False)
    fig.savefig(out / 'reports/figures/source_counts.png', dpi=180)
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    if not args.dataset_root.is_dir():
        raise SystemExit('Veri kökü erişilemiyor; inceleme durduruldu.')
    for folder in ['reports/qa', 'reports/figures', 'docs']:
        (ROOT/folder).mkdir(parents=True, exist_ok=True)
    rows, profiles, checks = inventory(args.dataset_root), {}, []
    for row in rows:
        if row['status'] != 'exists' or row['scope'] == 'allowed_container':
            continue
        path = Path(row['path'])
        before = path.stat()
        if path.suffix == '.pt':
            row['reason'] = 'Tarihsel tensör; yalnız metadata; deserialize edilmedi.'
            continue
        try:
            profile = sample_xml(path) if path.suffix == '.xml' else sample_table(path)
            profiles[row['name']] = profile
            row['inspected'], row['reason'] = True, profile['scope']
            if path.suffix == '.xml':
                attrs = profile['root_attributes']
                row['version'] = f'XML kökü: version={attrs.get("version", "yok")}; exported-on={attrs.get("exported-on", "yok")}'
            elif path.name == 'meddra_all_se.tsv':
                row['version'] = '4.1 tarihsel belge iddiası; dosyada sürüm başlığı yok'
        except (OSError, UnicodeError, ValueError, ET.ParseError, StopIteration) as exc:
            row['status'], row['reason'] = 'unreadable', f'{type(exc).__name__}: {exc}'
        after = path.stat()
        checks.append({'path': str(path), 'size_before': before.st_size, 'size_after': after.st_size,
                       'mtime_ns_before': before.st_mtime_ns, 'mtime_ns_after': after.st_mtime_ns,
                       'metadata_unchanged': (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)})
    write_json(ROOT / 'reports/qa/profiles.json', profiles)
    write_json(ROOT / 'reports/qa/read_integrity.json', {'checks': checks, 'method': 'size+mtime before/after; not cryptographic integrity proof',
               'python': sys.version, 'utc': datetime.now(timezone.utc).isoformat(), 'network_calls': 0})
    write_reports(rows, profiles, ROOT)
    (ROOT / 'reports/qa/local_inventory.csv').write_bytes((ROOT / 'reports/qa/data_inventory.csv').read_bytes())
    figures(rows, ROOT)
    if (ROOT / 'reports/qa/drive_profiles.json').exists():
        from wp00_finalize import main as finalize
        finalize()
    print(json.dumps({'status_counts': dict(Counter(r['status'] for r in rows)), 'profiled': list(profiles),
                      'metadata_unchanged': all(c['metadata_unchanged'] for c in checks)}, ensure_ascii=False))

if __name__ == '__main__':
    main()

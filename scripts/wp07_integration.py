"""WP07: kaynak QA'dan kimlik tabanlı inceleme grafı; eğitim girdisi sözleşmesi değil.

PT hedefleri ayrı dosyadadır. Bu modül ham XML/STRING veya ağ/API açmaz.
"""
from pathlib import Path
import hashlib
import json
import sys
import importlib.metadata
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.deps/pyg'))
import torch
import torch_geometric
from torch_geometric.data import HeteroData

QA = ROOT / 'reports/qa/WP07'
ROLES = ('target', 'enzyme', 'transporter', 'carrier')
CHEM = ['MW', 'LogP', 'HBD', 'HBA', 'TPSA']
GROUPS = ['nonpolar_nonaromatic', 'aromatic', 'polar_uncharged', 'basic', 'acidic']
PROTEIN = ['length_aa', 'molecular_weight_Da', 'isoelectric_point',
           'aromaticity_fraction', 'gravy_kyte_doolittle', 'net_charge_pH7']
PROTEIN += ['AAC_' + a for a in 'ACDEFGHIKLMNPQRSTVWY']
PROTEIN += ['group_' + g for g in GROUPS]
PROTEIN += ['DC_' + a + '__' + b for a in GROUPS for b in GROUPS]


def read(relative):
    return pd.read_csv(ROOT / relative, keep_default_na=False)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_prior():
    expected = json.loads((QA / 'prior_outputs_hashes.json').read_text(encoding='utf-8'))
    changed = [p for p, h in expected.items() if digest(ROOT / p) != h]
    if changed:
        raise ValueError(f'Önceki çıktılar değişmiş: {changed}')
    return len(expected)


def index_table(ids, name):
    values = list(ids)
    if not values or any(not isinstance(v, str) or not v for v in values):
        raise ValueError('Boş/uygunsuz kanonik kimlik')
    if len(values) != len(set(values)):
        raise ValueError('Tekrarlı kanonik kimlik')
    return pd.DataFrame({name: sorted(values), 'node_index': range(len(values))})


def feature_schema(frame, id_column, columns):
    """Sayısal tüm sütunları seçmek yerine sürümlü pozitif allowlist."""
    if set(frame.columns) != {id_column, *columns}:
        raise ValueError('Özellik şeması allowlist dışında/eksik alan içeriyor')
    if frame[id_column].duplicated().any():
        raise ValueError('Tekrarlı özellik kimliği')
    numeric = frame[columns].apply(pd.to_numeric, errors='raise')
    if numeric.isin([float('inf'), float('-inf')]).any().any():
        raise ValueError('Sonsuz özellik')
    return numeric


def edge_index(pairs, src, dst):
    values = list(pairs)
    if len(values) != len(set(values)):
        raise ValueError('Tekrarlı tipli kenar')
    if any(a not in src or b not in dst for a, b in values):
        raise ValueError('Kayıtsız kenar ucu')
    return torch.tensor([[src[a], dst[b]] for a, b in values], dtype=torch.long).t().contiguous() if values else torch.empty((2, 0), dtype=torch.long)


def select_ppi(edges, mapping, mode, threshold):
    if mode not in ('human', 'k12_review') or threshold not in (150, 400, 700, 900):
        raise ValueError('Onaysız PPI senaryosu/eşik')
    tax = '9606' if mode == 'human' else '511145'
    status = 'exact_alias_exact_taxon' if mode == 'human' else 'exact_alias_K12_parent_scope_review'
    accepted = mapping[mapping.status.eq(status) & mapping.network_taxid.astype(str).eq(tax)]
    if accepted.string_id.duplicated().any():
        raise ValueError('Çoktan bire STRING eşlemesi')
    lookup = dict(zip(accepted.string_id, accepted.accession))
    output = []
    for row in edges[edges.network_taxid.astype(str).eq(tax)].itertuples():
        if row.score_conflict:
            continue
        if not 0 <= row.combined_score <= 1000 or int(row.combined_score) != row.combined_score:
            raise ValueError('Geçersiz PPI skoru')
        if any(not x.startswith(tax + '.') for x in (row.protein1, row.protein2)):
            raise ValueError('Organizmalar arası PPI')
        if row.protein1 not in lookup or row.protein2 not in lookup:
            raise ValueError('İnceleme/katı kapsam karışması veya context ucu')
        if row.protein1 == row.protein2:
            raise ValueError('Self-loop')
        if row.combined_score >= threshold:
            a, b = sorted((lookup[row.protein1], lookup[row.protein2]))
            output.append((a, b))
    if len(output) != len(set(output)):
        raise ValueError('Tekrarlı yönsüz PPI')
    return sorted(output)


def build_graph(drugs, proteins, pt_ids, typed, masks, ppi=(), scenario='no_ppi'):
    """x/y içermeyen yapısal nesne: PT listesi yalnız ayrı kaynak sözlüğü.

    CUI sözlüğü tüm kohort gözlemi olduğu için gelecekte öğrenilen train sözlüğü
    yerine kullanılamaz. PT düğümleri encoder komşuluğuna bağlı değildir.
    """
    di = dict(zip(drugs.drug_id, drugs.node_index))
    pi = dict(zip(proteins.accession, proteins.node_index))
    if set(typed.role) - set(ROLES):
        raise ValueError('Onaysız rol')
    graph = HeteroData()
    graph.scenario = scenario
    graph.training_ready = False
    graph.purpose = 'WP07_structure_review_only'
    for kind, ids in [('drug', list(drugs.drug_id)), ('protein', list(proteins.accession)), ('se_pt_audit', list(pt_ids))]:
        graph[kind].num_nodes = len(ids)
        graph[kind].canonical_ids = ids
    ordered = masks.set_index('drug_id').loc[drugs.drug_id]
    for col in ('chemistry_qc_available', 'protein_modality_available', 'molecule_review'):
        graph['drug'][col] = torch.tensor(ordered[col].tolist(), dtype=torch.bool)
    for role in ROLES:
        rows = typed[typed.role.eq(role)]
        graph['drug', role, 'protein'].edge_index = edge_index(zip(rows.drug_id, rows.accession), di, pi)
    pairs = list(ppi)
    if pairs:
        relation = 'ppi_human_review' if scenario.startswith('human_') else 'ppi_k12_scope_review'
        if relation == 'ppi_k12_scope_review' and not scenario.startswith('k12_'):
            raise ValueError('Bilinmeyen PPI kapsamı')
        # Kaynak yönsüzdür: PyG'de iki yönlü indeks, çift sayısı ayrıca tutulur.
        bidirectional = pairs + [(b, a) for a, b in pairs]
        graph['protein', relation, 'protein'].edge_index = edge_index(bidirectional, pi, pi)
    validate_review_graph(graph)
    return graph


def validate_review_graph(graph):
    graph.validate(raise_on_error=True)
    if set(graph._global_store.keys()) != {'scenario', 'training_ready', 'purpose'}:
        raise ValueError('Onaysız global veri/etiket alanı')
    if graph.training_ready is not False or graph.purpose != 'WP07_structure_review_only':
        raise ValueError('İnceleme nesnesi eğitim için hazır sayılamaz')
    if set(graph.node_types) != {'drug', 'protein', 'se_pt_audit'}:
        raise ValueError('Onaysız düğüm tipi')
    for node_type in graph.node_types:
        allowed = {'num_nodes', 'canonical_ids'}
        if node_type == 'drug':
            allowed |= {'chemistry_qc_available', 'protein_modality_available', 'molecule_review'}
        if set(graph[node_type].keys()) != allowed:
            raise ValueError('Girdi/etiket/özellik şeması henüz onaylanmadı')
        if len(set(graph[node_type].canonical_ids)) != graph[node_type].num_nodes:
            raise ValueError('Tekrarlı düğüm kimliği')
    for src, relation, dst in graph.edge_types:
        role_edge = src == 'drug' and dst == 'protein' and relation in ROLES
        ppi_edge = src == dst == 'protein' and relation in ('ppi_human_review', 'ppi_k12_scope_review')
        if not (role_edge or ppi_edge):
            raise ValueError('Hedef/reverse hedef veya onaysız kenar engellendi')
        if set(graph[src, relation, dst].keys()) != {'edge_index'}:
            raise ValueError('Kenar skoru/etiket verisi encoder girdisi değil')
        index = graph[src, relation, dst].edge_index
        pairs = list(map(tuple, index.t().tolist()))
        if len(set(pairs)) != len(pairs):
            raise ValueError('Tekrarlı graf kenarı')
        if ppi_edge:
            expected = 'ppi_human_review' if graph.scenario.startswith('human_') else 'ppi_k12_scope_review'
            if relation != expected or any(a == b for a, b in pairs):
                raise ValueError('PPI senaryosu/self-loop')
            if any((b, a) not in set(pairs) for a, b in pairs):
                raise ValueError('Eksik karşı yönlü indeks')
            source_mapping = read('reports/qa/WP06/protein_string_mapping.csv')
            status = 'exact_alias_exact_taxon' if relation == 'ppi_human_review' else 'exact_alias_K12_parent_scope_review'
            eligible = set(source_mapping[source_mapping.status.eq(status)].accession)
            ids = graph['protein'].canonical_ids
            if any(ids[a] not in eligible or ids[b] not in eligible for a, b in pairs):
                raise ValueError('PPI protein taksonomi/kapsam karışması')
    return True


def require_training_approval(graph):
    # Bu pakette üretilebilen bütün graf senaryoları bilerek kilitlidir.
    raise RuntimeError('Nihai etiket, eksik modalite, giriş şeması ve WP08 protokol onayı olmadan eğitim kapalı')


def write_json(name, obj):
    (QA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    QA.mkdir(parents=True, exist_ok=True)
    previous = verify_prior()
    paths = ['reports/qa/WP04/cohort_identity.json', 'reports/qa/WP04/structure_validation.csv',
             'reports/qa/WP04/chemical_features_clean.csv', 'reports/qa/WP05/protein_registry.csv',
             'reports/qa/WP05/protein_features.csv', 'reports/qa/WP05/drug_protein_edges.csv',
             'reports/qa/WP05/drug_coverage.csv', 'reports/qa/WP06/protein_string_mapping.csv',
             'reports/qa/WP06/ppi_induced_edges.csv', 'reports/qa/WP06/ppi_nodes.csv',
             'reports/qa/WP03/drug_pt_positives.csv',
             'reports/qa/WP03/historical_category_projection_audit.csv']
    write_json('input_manifest.json', {p: digest(ROOT / p) for p in paths})
    cohort = pd.DataFrame(json.loads((ROOT / paths[0]).read_text(encoding='utf-8')))
    drugs = index_table(cohort.id, 'drug_id')
    registry = read(paths[3])
    proteins = index_table(registry.accession, 'accession')
    typed = read(paths[5]).sort_values(['role', 'drug_id', 'accession'])
    if len(typed) != 476 or typed.duplicated(['drug_id', 'accession', 'role']).any():
        raise ValueError('WP05 rol kenar sözleşmesi bozulmuş')
    chemistry = pd.read_csv(ROOT / paths[2])
    pf = pd.read_csv(ROOT / paths[4])
    feature_schema(chemistry, 'id', CHEM)
    feature_schema(pf, 'accession', PROTEIN)
    if pf[PROTEIN].isna().any().any() or set(pf.accession) != set(proteins.accession):
        raise ValueError('Protein özellik kapsamı')
    structure = read(paths[1]).set_index('id')
    coverage = read(paths[6]).set_index('id')
    mapping = read(paths[7]); edges = read(paths[8]); nodes = read(paths[9])
    clean = chemistry.set_index('id')[CHEM]
    masks = drugs.merge(cohort.rename(columns={'id': 'drug_id'}), on='drug_id', validate='one_to_one')
    masks['chemistry_qc_available'] = [bool(clean.loc[d].notna().all()) for d in masks.drug_id]
    masks['molecule_review'] = [not bool(structure.loc[d, 'strict_qc_pass']) for d in masks.drug_id]
    masks['protein_modality_available'] = [coverage.loc[d, 'feature_proteins'] > 0 for d in masks.drug_id]
    masks['review_flags'] = [structure.loc[d, 'review_flags'] for d in masks.drug_id]
    for role in ROLES:
        by_drug = typed[typed.role.eq(role)].groupby('drug_id').accession.nunique()
        masks[role + '_protein_count_QA'] = masks.drug_id.map(by_drug).fillna(0).astype(int)
    strict = set(mapping[mapping.status.eq('exact_alias_exact_taxon')].accession)
    review = set(mapping[mapping.status.eq('exact_alias_K12_parent_scope_review')].accession)
    for name, ids in [('human_strict', strict), ('k12_scope_review', review)]:
        counts = typed[typed.accession.isin(ids)].groupby('drug_id').accession.nunique()
        masks[name + '_protein_count_QA'] = masks.drug_id.map(counts).fillna(0).astype(int)
    # Özel QA sayıları nesneye topluca aktarılmaz; build_graph yalnız üç input maskesi alır.
    positives = read(paths[10])
    positives = positives[positives.conservative.eq(True) & positives.id.isin(drugs.drug_id)]
    if positives.duplicated(['id', 'meddra_cui']).any() or set(positives.id) != set(drugs.drug_id):
        raise ValueError('Pozitif kimlik/tekillik/kohort')
    pt = index_table(positives.meddra_cui.unique(), 'pt_cui')
    labels = positives[['id', 'meddra_cui', 'term']].rename(columns={'id': 'drug_id', 'meddra_cui': 'pt_cui'})
    labels['status'] = 'observed_positive'; labels['source'] = paths[10]
    labels.to_csv(QA / 'observed_pt_positives_external.csv', index=False, encoding='utf-8-sig')
    categories = read(paths[11]); categories = categories[categories.conservative.eq(True) & categories.id.isin(drugs.drug_id)]
    catpairs = categories[['id', 'category']].drop_duplicates()
    rows = []
    for strategy, frame, idcol, classcol in [('PT_CUI_audit', labels, 'drug_id', 'pt_cui'), ('historical_30_audit', catpairs, 'id', 'category')]:
        support = frame.groupby(classcol)[idcol].nunique()
        counts = frame.groupby(idcol)[classcol].nunique().reindex(drugs.drug_id, fill_value=0)
        rows.append({'strategy': strategy, 'classes': len(support), 'positive_pairs': len(frame),
                     'drugs_with_positive': frame[idcol].nunique(), 'singleton_classes': int((support == 1).sum()),
                     'classes_under5': int((support < 5).sum()), 'unknown_pairs': len(drugs) * len(support) - len(frame),
                     'median_positive_per_drug_QA': counts.median(), 'min_support': support.min(), 'max_support': support.max()})
    pd.DataFrame(rows).to_csv(QA / 'label_strategy_comparison.csv', index=False, encoding='utf-8-sig')
    context = nodes[nodes.node_role.eq('STRING_context_only')].copy()
    if len(context) != 80 or context.sequence_feature_available.any():
        raise ValueError('Context özellik varsayımı')
    context.to_csv(QA / 'context_inventory_no_features.csv', index=False, encoding='utf-8-sig')
    graphs = {'no_ppi': build_graph(drugs, proteins, pt.pt_cui, typed, masks)}
    ppi_counts = []
    ppi_provenance = []
    for mode, thresholds in [('human', (150, 400, 700, 900)), ('k12_review', (700,))]:
        for threshold in thresholds:
            pairs = select_ppi(edges, mapping, mode, threshold)
            scenario = f'{mode}_{threshold}'
            graphs[scenario] = build_graph(drugs, proteins, pt.pt_cui, typed, masks, pairs, scenario)
            ppi_counts.append({'scenario': scenario, 'threshold': threshold, 'unique_undirected_pairs': len(pairs),
                               'directed_index_columns': 2 * len(pairs), 'final_choice': False})
            tax = '9606' if mode == 'human' else '511145'
            by_string = dict(zip(mapping.string_id, mapping.accession))
            for row in edges[edges.network_taxid.astype(str).eq(tax) & edges.combined_score.ge(threshold)].itertuples():
                if not row.score_conflict:
                    ppi_provenance.append({'scenario': scenario, 'accession1': by_string[row.protein1],
                                           'accession2': by_string[row.protein2], 'string_id1': row.protein1,
                                           'string_id2': row.protein2, 'combined_score_QA_only': row.combined_score,
                                           'source_lines': row.source_lines, 'source_table': paths[8],
                                           'mapping_scope': row.mapping_scope})
    torch.save(graphs, QA / 'heterodata_review_scenarios.pt')
    counts = []
    for scenario, graph in graphs.items():
        for edge_type in graph.edge_types:
            counts.append({'scenario': scenario, 'source_type': edge_type[0], 'relation': edge_type[1],
                           'target_type': edge_type[2], 'edge_index_columns': graph[edge_type].num_edges})
    pd.DataFrame(counts).to_csv(QA / 'edge_counts.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(ppi_counts).to_csv(QA / 'ppi_scenarios.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(ppi_provenance).to_csv(QA / 'ppi_edge_provenance.csv', index=False, encoding='utf-8-sig')
    for name, frame in [('drug_nodes.csv', drugs), ('protein_nodes.csv', proteins), ('pt_audit_nodes.csv', pt),
                        ('drug_modality_QA.csv', masks), ('typed_drug_protein_edges.csv', typed)]:
        frame.to_csv(QA / name, index=False, encoding='utf-8-sig')
    patterns = masks.groupby(['chemistry_qc_available', 'protein_modality_available'], dropna=False).size().rename('drugs').reset_index()
    patterns.to_csv(QA / 'modality_patterns.csv', index=False, encoding='utf-8-sig')
    summary = {'cohort': len(drugs), 'proteins': len(proteins), 'external_pt_classes_audit': len(pt),
               'external_positive_pairs': len(labels), 'typed_drug_protein_edges': len(typed),
               'role_edges': typed.role.value_counts().to_dict(), 'chemistry_qc_available': int(masks.chemistry_qc_available.sum()),
               'molecule_review': int(masks.molecule_review.sum()), 'protein_available': int(masks.protein_modality_available.sum()),
               'strict_human_proteins': len(strict), 'k12_scope_review_proteins': len(review), 'context_without_features': len(context),
               'context_in_review_graphs': 0, 'prior_files_verified': previous, 'scenarios': list(graphs),
               'training_ready': False, 'labels_in_encoder': False, 'negative_samples': 0, 'splits_created': False}
    write_json('integration_summary.json', summary)
    deps = {d.metadata['Name']: d.version for d in importlib.metadata.distributions(path=[str(ROOT / '.deps/pyg')])}
    write_json('environment.json', {'python': sys.version, 'torch': torch.__version__, 'pyg': torch_geometric.__version__,
                                  'project_local_packages': deps, 'new_data_downloads': 0})
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()

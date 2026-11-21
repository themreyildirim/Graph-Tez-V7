"""Kayıtlı küçük WP06 çıktılarından bağımsız özet/kapsam/koruma kontrolleri."""
from pathlib import Path
import json,hashlib
import pandas as pd
from wp06_mapping import ROOT,QA


def main():
    m=pd.read_csv(QA/'protein_string_mapping.csv',dtype={'network_taxid':str},keep_default_na=False)
    induced=pd.read_csv(QA/'ppi_induced_edges.csv',dtype={'network_taxid':str})
    extended=pd.read_csv(QA/'ppi_expanded_edges.csv',dtype={'network_taxid':str})
    edges=pd.read_csv(ROOT/'reports/qa/WP05/drug_protein_edges.csv')
    cohort=pd.read_csv(ROOT/'reports/qa/WP05/drug_coverage.csv')
    strict=set(m[m.strict_taxon_match].accession);review=set(m[m.status.eq('exact_alias_K12_parent_scope_review')].accession)
    coverage=[]
    for row in cohort.itertuples():
        proteins=set(edges[edges.drug_id.eq(row.id)].accession)
        coverage.append({'drug_id':row.id,'drug_name':row.name,'WP05_proteins':len(proteins),
            'strict_human_mapped_proteins':len(proteins&strict),'K12_alias_scope_review_proteins':len(proteins&review),
            'retained_in_62':True})
    pd.DataFrame(coverage).to_csv(QA/'drug_ppi_mapping_coverage.csv',index=False,encoding='utf-8-sig')
    induced[induced.network_taxid.eq('9606')].to_csv(QA/'strict_taxon_induced_edges.csv',index=False,encoding='utf-8-sig')
    summary={'WP05_accessions':len(m),'unique_accession_alias_match':int(m.alias_identity_unique.sum()),
        'strict_accession_and_exact_taxon':int(m.strict_taxon_match.sum()),
        'human_exact':len(strict),'Ecoli_K12_exact_alias_parent_scope_review':len(review),
        'Ecoli_exact_substrain_taxon':0,'unmatched_accession_alias':int(m.status.eq('unmatched_accession_alias').sum()),
        'other_available_network_out_of_scope':int(m.status.eq('out_of_scope_organism').sum()),
        'ambiguous_multiple_STRING_ids':int(m.status.eq('ambiguous_multiple_STRING_ids').sum()),
        'gene_name_similarity_matches_used':0,'cross_organism_edges_created':0,
        'induced_edges_at_source_min_by_network':induced.groupby('network_taxid').size().to_dict(),
        'context_nodes_added_per_network':{'9606':40,'511145':40},
        'global_duplicate_scope':'only retained induced and expanded pairs exact; full-source rows otherwise',
        'confidence_thresholds':[150,400,700,900],'primary_visual_threshold':700,'cohort_drugs_retained':len(coverage),
        'not_in_strict_ppi_scope':len(m)-len(strict),
        'missing_protein_drugs_retained':['DB00684','DB06799'],'GNN_training':False,'PyG_object_created':False}
    (QA/'coverage_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    prior=json.loads((QA/'prior_outputs_hashes.json').read_text(encoding='utf-8'))
    unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in prior.items())
    assert unchanged and len(m)==141 and len(coverage)==62
    assert set(induced.network_taxid)=={'9606','511145'} and not induced.score_conflict.any()
    (QA/'input_manifest.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [ROOT/'reports/qa/WP05/protein_registry.csv',ROOT/'reports/qa/WP05/drug_protein_edges.csv',ROOT/'reports/qa/WP05/drug_coverage.csv',
                  ROOT/'reports/qa/WP04/structure_validation.csv',QA/'alias_evidence.csv']},indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=True,indent=2));print('Prior files unchanged',len(prior))


if __name__=='__main__':main()

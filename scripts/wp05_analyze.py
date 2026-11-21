"""Protein-dışı hedefleri koruyarak rol/kimlik/dizi/özellik QC ve kapsam."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,re,sys,platform
import pandas as pd
from wp05_proteins import parse_sequence,resolve_accession,features,organism_class,AA,GROUPS,Bio

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'reports/qa/WP05'
def read(name):return json.loads((QA/name).read_text(encoding='utf-8'))
def save(name,obj):(QA/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def csv(name,rows):pd.DataFrame(rows).to_csv(QA/name,index=False,encoding='utf-8-sig')


def classify_without_polypeptide(name):
    """Kaynakta görülen açık terimler; enzim adını hücre duvarı yapısı sanma."""
    if name in ['16S ribosomal RNA','23S ribosomal RNA']:return 'nonprotein_rRNA'
    if name in ['DNA','Aerobic bacterial DNA','Anaerobic bacterial DNA','Protozoal DNA']:return 'nonprotein_DNA'
    if name in ['30S ribosomal protein','Peptidoglycan transpeptidase']:return 'protein_named_missing_polypeptide'
    if name in ['Bacterial outer membrane','Cytoplasmic membrane',
        'D-Ala-D-Ala moiety of NAM/NAG peptide subunits of peptidoglycan',
        'Peptidoglycan precursors','Bacterial cell wall peptide bridging segments','Pentaglycyl bridging segment']:
        return 'nonprotein_cell_envelope_or_peptide'
    return 'unresolved_no_polypeptide'


def main():
    records=read('xml_protein_records.json');evidence=[];polys=[];nonprotein=[]
    for d in records:
        for i,r in enumerate(d['relations'],1):
            base={k:r[k] for k in ['drug_id','drug_name','role','relation_id','relation_name','relation_organism','known_action','source_path','xml_record_index']}
            base.update(evidence_id=f"{d['id']}:{i}",actions='|'.join(r['actions']),source='DrugBank XML local')
            if not r['has_polypeptide']:
                kind=classify_without_polypeptide(r['relation_name'])
                row={**base,'relation_qc':kind,'accession':'','sequence_qc':'not_applicable_or_unresolved'}
                nonprotein.append(row);evidence.append(row);continue
            acc,astatus=resolve_accession(r['polypeptide_id'],r['uniprot_external_ids'],r['polypeptide_source'])
            p=parse_sequence(r['raw_sequence']);org=r['organism'];taxid=r['organism_attributes'].get('ncbi-taxonomy-id','')
            row={**base,'relation_qc':'polypeptide','accession':acc,'id_status':astatus,'polypeptide_id':r['polypeptide_id'],
                 'external_ids':'|'.join(r['uniprot_external_ids']),'protein_name':r['protein_name'],'gene_name':r['gene_name'],
                 'organism':org,'taxid':taxid,'organism_group':organism_class(org,taxid),'sequence_qc':p['status'],
                 'header_removed':p['header_removed'],'header':p['header'],'raw_length':p['raw_length'],'length_aa':p['length'],
                 'invalid_characters':p['invalid_characters'],'sequence_sha256':p['sequence_sha256'],
                 'sequence_path':r['sequence_xml_path'],'old_sequence_tag_present':r['old_sequence_tag_present']}
            evidence.append(row);polys.append((row,p))
    grouped=defaultdict(list)
    for row,p in polys:
        if row['accession']:grouped[row['accession']].append((row,p))
    registry=[];seqs=[];feat=[];by_acc={};fasta=[]
    for acc,rows in sorted(grouped.items()):
        variants={p['sequence'] for _,p in rows if p['status']=='valid'}
        taxids={r['taxid'] for r,_ in rows if r['taxid']};names={r['organism'] for r,_ in rows if r['organism']}
        flags=[]
        if len(variants)>1:flags.append('conflicting_sequences_same_accession')
        if any(p['status']!='valid' for _,p in rows):flags.append('missing_or_invalid_sequence_evidence')
        if len(taxids)>1:flags.append('conflicting_taxids_same_accession')
        if not variants:flags.append('no_valid_sequence')
        accepted=not flags
        first=rows[0][0]
        row={'accession':acc,'protein_name':' | '.join(sorted({r['protein_name'] for r,_ in rows})),
            'gene_name':' | '.join(sorted({r['gene_name'] for r,_ in rows if r['gene_name']})),
            'organism':' | '.join(sorted(names)),'taxid':' | '.join(sorted(taxids)),
            'organism_group':first['organism_group'],'source_evidence_count':len(rows),
            'sequence_variants':len(variants),'sequence_validated':accepted,'qc_flags':'|'.join(flags)}
        registry.append(row);by_acc[acc]=row
        if accepted:
            sequence=next(iter(variants));seqs.append({'accession':acc,'sequence':sequence,'sequence_sha256':hashlib.sha256(sequence.encode()).hexdigest(),'length_aa':len(sequence)})
            feat.append({'accession':acc,**features(sequence)})
            fasta.append('>'+acc+' '+row['protein_name']+'\n'+'\n'.join(sequence[i:i+60] for i in range(0,len(sequence),60)))
    csv('relation_evidence.csv',evidence);csv('nonprotein_or_unresolved_targets.csv',nonprotein)
    csv('protein_registry.csv',registry);csv('protein_sequences.csv',seqs);csv('protein_features.csv',feat)
    hashes=defaultdict(list)
    for r in seqs:hashes[r['sequence_sha256']].append(r['accession'])
    csv('identical_sequence_accessions.csv',[{'sequence_sha256':h,'accessions':'|'.join(ids),'accession_count':len(ids)}
        for h,ids in hashes.items() if len(ids)>1])
    (QA/'validated_proteins.fasta').write_text('\n'.join(fasta)+'\n',encoding='utf-8')
    edges={}
    for row,p in polys:
        if row['accession']:
            key=(row['drug_id'],row['accession'],row['role'])
            if key not in edges:edges[key]={'drug_id':row['drug_id'],'accession':row['accession'],'role':row['role'],
                'sequence_available':by_acc[row['accession']]['sequence_validated'],'evidence_ids':[]}
            edges[key]['evidence_ids'].append(row['evidence_id'])
    edge_rows=[{**r,'evidence_ids':'|'.join(r['evidence_ids'])} for r in edges.values()]
    csv('drug_protein_edges.csv',edge_rows)
    coverage=[]
    for d in records:
        rows=[e for e in edge_rows if e['drug_id']==d['id']];targets=[e for e in rows if e['role']=='target']
        pfree=[r for r in nonprotein if r['drug_id']==d['id']]
        coverage.append({'id':d['id'],'name':d['name'],'target_proteins':len({r['accession'] for r in targets}),
            'all_role_proteins':len({r['accession'] for r in rows}),'feature_proteins':len({r['accession'] for r in rows if r['sequence_available']}),
            **{role+'_proteins':len({r['accession'] for r in rows if r['role']==role}) for role in ['enzyme','transporter','carrier']},
            'no_polypeptide_records':len(pfree),'nonprotein_target_names':' | '.join(sorted({r['relation_name'] for r in pfree})),
            'modal_status':'protein_features_available' if any(r['sequence_available'] for r in rows) else 'no_validated_protein_features',
            'retained_in_cohort':True})
    csv('drug_coverage.csv',coverage)
    priority={'DB00254','DB00512','DB00601','DB00684','DB00911','DB00976','DB06799'}
    csv('priority_seven.csv',[r for r in coverage if r['id'] in priority])
    orgs=defaultdict(set)
    for row in registry:orgs[(row['organism'],row['taxid'],row['organism_group'])].add(row['accession'])
    csv('organism_summary.csv',[{'organism':k[0],'taxid':k[1],'group':k[2],'unique_proteins':len(v)} for k,v in sorted(orgs.items())])
    role_summary=[]
    for role in ['target','enzyme','transporter','carrier']:
        er=[r for r in edge_rows if r['role']==role]
        role_summary.append({'role':role,'unique_drug_protein_role_edges':len(er),'drugs':len({r['drug_id'] for r in er}),
            'unique_proteins':len({r['accession'] for r in er}),'no_polypeptide_records':sum(r['role']==role for r in nonprotein)})
    csv('role_summary.csv',role_summary)
    # Eski artefaktlar yalnız karşılaştırma; yeni diziler her durumda XML'den gelir.
    old=read('legacy_reference.json');legacy_qc=[];legacy_org=[];seq_by={r['accession']:r['sequence'] for r in seqs}
    for r in old['seq']['rows']:
        uid=r['UniProt_ID'];raw=r['Sequence'];new=seq_by.get(uid);p=parse_sequence(raw)
        emulated=''.join(c for c in raw.upper() if c in AA)
        matched_suffix=bool(new and raw.endswith(new))
        legacy_qc.append({'accession':uid,'old_organism':r['Organizma'],'raw_length':len(raw),
            'starts_fasta_header':raw.startswith('>'),'strict_parse_status':p['status'],'new_xml_sequence_available':new is not None,
            'exact_new_sequence_suffix':matched_suffix,'new_sequence_length':len(new) if new else None,
            'old_filter_emulated_length':len(emulated),
            'extra_residues_if_old_regex':len(emulated)-len(new) if matched_suffix else None,
            'prefix_sample':raw[:100]})
    for r in old['features']['rows']:
        uid=r['UniProt_ID'];expected={'P':1,'Q':2,'O':2}.get(uid[:1].upper(),3)
        legacy_org.append({'accession':uid,'old_organism':r['Organizma'],'old_quality_score':r['kalite_skoru'],
            'prefix_formula_matches':float(r['kalite_skoru'])==expected,'new_organism':by_acc.get(uid,{}).get('organism',''),
            'new_group':by_acc.get(uid,{}).get('organism_group','not_in_selected_cohort')})
    csv('legacy_sequence_audit.csv',legacy_qc);csv('legacy_identity_organism_audit.csv',legacy_org)
    old_groups={'acidic':'DE','basic':'RKH','polar':'STNQ','hydrophobic':'AILMFVP','aromatic':'FYW'}
    old_counts=Counter(''.join(old_groups.values()))
    csv('amino_acid_group_audit.csv',[{'AA':a,'old_groups':'|'.join(g for g,v in old_groups.items() if a in v),
        'old_membership_count':old_counts[a],'new_group':next(g for g,v in GROUPS.items() if a in v)} for a in AA])
    aa_examples=[]
    aa_names={'A':('Ala','Alanin'),'C':('Cys','Sistein'),'D':('Asp','Aspartat'),'E':('Glu','Glutamat'),
        'F':('Phe','Fenilalanin'),'G':('Gly','Glisin'),'H':('His','Histidin'),'I':('Ile','İzolösin'),
        'K':('Lys','Lizin'),'L':('Leu','Lösin'),'M':('Met','Metiyonin'),'N':('Asn','Asparajin'),
        'P':('Pro','Prolin'),'Q':('Gln','Glutamin'),'R':('Arg','Arjinin'),'S':('Ser','Serin'),
        'T':('Thr','Treonin'),'V':('Val','Valin'),'W':('Trp','Triptofan'),'Y':('Tyr','Tirozin')}
    for a in AA:aa_examples.append({'AA':a,'three_letter':aa_names[a][0],'Turkce_ad':aa_names[a][1],
        'group':next(g for g,v in GROUPS.items() if a in v)})
    csv('amino_acid_dictionary.csv',aa_examples)
    target_old=json.loads((ROOT/'reports/qa/WP02/drug_registry.json').read_text(encoding='utf-8'))
    target_old={r['id']:set(r['protein_ids']) for r in target_old}
    mismatches=[]
    for d in records:
        now={r['accession'] for r in edge_rows if r['drug_id']==d['id'] and r['role']=='target'}
        if now!=target_old[d['id']]:mismatches.append({'id':d['id'],'wp02':sorted(target_old[d['id']]),'wp05':sorted(now)})
    save('wp02_target_consistency.json',{'mismatches':mismatches,'all_match':not mismatches})
    summary={'cohort_drugs':len(records),'with_target_protein':sum(r['target_proteins']>0 for r in coverage),
        'with_any_role_protein':sum(r['all_role_proteins']>0 for r in coverage),
        'with_validated_sequence_features':sum(r['feature_proteins']>0 for r in coverage),
        'unique_proteins':len(registry),'unique_clean_sequence_hashes':len(hashes),'valid_feature_proteins':len(feat),'protein_relation_evidence':len(polys),
        'unique_typed_edges':len(edge_rows),'unique_untyped_drug_protein_pairs':len({(r['drug_id'],r['accession']) for r in edge_rows}),
        'no_polypeptide_records':len(nonprotein),'organism_name_taxid_groups':len(orgs),
        'distinct_nonempty_taxids':len({r['taxid'] for r in registry if r['taxid']}),
        'organism_groups':dict(Counter(r['organism_group'] for r in registry)),
        'sequence_status_evidence':dict(Counter(p['status'] for _,p in polys)),
        'id_status_evidence':dict(Counter(r['id_status'] for r,_ in polys)),
        'header_removed_evidence':sum(p['header_removed'] for _,p in polys),
        'old_sequence_tag_present':sum(r['old_sequence_tag_present'] for r,_ in polys),
        'registry_conflicts':sum(not r['sequence_validated'] for r in registry),
        'legacy_fasta_header_rows':sum(r['starts_fasta_header'] for r in legacy_qc),
        'legacy_prefix_score_formula_matches':sum(r['prefix_formula_matches'] for r in legacy_org),
        'legacy_overlap_with_valid_sequences':sum(r['new_xml_sequence_available'] for r in legacy_qc),
        'biopython_version':Bio.__version__,'python_version':platform.python_version(),'uniprot_api_requests':0,
        'wp02_target_ids_unchanged':not mismatches,'protein_feature_columns':list(pd.DataFrame(feat).columns)}
    save('coverage_summary.json',summary)
    save('method_contract.json',{'date':'2026-11-06','biopython_version':Bio.__version__,
        'standard_amino_acids':AA,'groups':GROUPS,'AAC_denominator':'L; unrounded fractions 0-1',
        'DC_denominator':'L-1; directional; null when L=1','mass':'average; linear unmodified sequence; Da',
        'pI':'Bjellqvist via Bio.SeqUtils.IsoelectricPoint; bisection initial [0,14]',
        'charge':'same pKa model at pH 7.0; elementary charge e','GRAVY':'Biopython default Kyte-Doolittle',
        'aromaticity':'(F+W+Y)/L','invalid_sequence_policy':'hold entire sequence; do not delete non-AA or fill zeros',
        'identity_validation':'local XML attribute/external UniProtKB agreement, format check; no UniProt API',
        'references':['https://biopython.org/docs/latest/api/Bio.SeqUtils.ProtParam.html',
                      'https://biopython.org/docs/latest/api/Bio.SeqUtils.IsoelectricPoint.html',
                      'https://www.uniprot.org/help/accession_numbers']})
    save('input_manifest.json',{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [QA/'xml_protein_records.json',QA/'cohort_identity.json',QA/'legacy_reference.json',ROOT/'reports/qa/WP02/drug_registry.json']})
    print(json.dumps({k:v for k,v in summary.items() if k!='protein_feature_columns'},ensure_ascii=True,indent=2))
    print('REVIEW',[r for r in registry if not r['sequence_validated']])


if __name__=='__main__':main()

"""Outcome-free structure/QC and existing protein/PPI scope. No external predictions."""
import json
from pathlib import Path
import pandas as pd,numpy as np
from wp12_api_security import public_sha
from wp04_chemistry import parse_smiles,identity,descriptors,FEATURES,rdBase
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator,Draw
ROOT=Path(__file__).resolve().parents[1];Q=ROOT/'reports/qa/WP13/tedizolid_preparation_v1';F=ROOT/'reports/figures/WP13/tedizolid_preparation_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 F.mkdir(parents=True,exist_ok=True)
 prior=read(ROOT/'reports/qa/WP13/final_demo_v2/prior_pins.json');prior.update(read(ROOT/'reports/qa/WP13/final_demo_v2/evidence_manifest.json'));prior.pop('run_status.md',None)
 for p,h in prior.items():assert public_sha(ROOT/p)==h,p
 (Q/'prior_pins.json').write_text(json.dumps(prior,indent=2));(Q/'run_status_before.md').write_bytes((ROOT/'run_status.md').read_bytes())
 source=read(Q/'DrugBank_identity_chemistry.json');cohort=pd.read_csv(ROOT/'reports/qa/WP07/drug_modality_QA.csv');structures=pd.read_csv(ROOT/'reports/qa/WP04/structure_validation.csv');reg=read(ROOT/'reports/qa/WP02/drug_registry.json')
 secondary=pd.read_csv(ROOT/'reports/qa/WP02/secondary_ids.csv');salts=pd.read_csv(ROOT/'reports/qa/WP02/salt_parent_links.csv');srcstruct=pd.read_csv(ROOT/'reports/qa/WP04/structure_sources.csv')
 rows=[];similar=[];idchecks=[];fps=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)
 for r in source:
  smiles=next(p['value'] for p in r['properties'] if p['kind']=='SMILES');mol,status=parse_smiles(smiles);ident=identity(mol)
  xmlkey=next(p['value'] for p in r['properties'] if p['kind']=='InChIKey');assert ident['rdkit_inchikey']==xmlkey
  row={'id':r['id'],'name':r['name'],'raw_smiles':smiles,'parse_status':status,'XML_InChIKey':xmlkey,**ident,**descriptors(mol),'descriptor_engine':rdBase.rdkitVersion,'TPSA_includeSandP':False,'source':'DrugBank XML raw full SMILES','QC':'TECHNICAL_PASS_PENDING_REPRESENTATION_APPROVAL'};rows.append(row)
  Draw.MolToFile(mol,str(F/(r['id']+'_structure.png')),size=(950,500))
  aliases={r['id'],*r['ids']};aliases.update(secondary[secondary.parent_id.eq(r['id'])].secondary_id.astype(str));aliases.update(salts[salts.parent_id.eq(r['id'])].salt_id.astype(str))
  cohortids=set(cohort.drug_id)
  keymatch=structures[structures.rdkit_inchikey.eq(xmlkey)]
  connectivity=structures[structures.rdkit_inchikey.fillna('').str.split('-').str[0].eq(xmlkey.split('-')[0])]
  names={str(r['name']).casefold(),*(str(n).casefold() for n in r['synonyms'])}
  namehits=cohort[cohort.name.astype(str).str.casefold().isin(names)]
  idchecks.append({'id':r['id'],'alias_ID_overlap':sorted(aliases&cohortids),'name_overlap':namehits.drug_id.tolist(),'full_key_overlap':keymatch.id.tolist(),'connectivity_overlap':connectivity.id.tolist(),'DBSALT_child_count':len(salts[salts.parent_id.eq(r['id'])]),'secondary_ID_count':len(secondary[secondary.parent_id.eq(r['id'])]),'in_registry':any(x['id']==r['id'] for x in reg),'outside_frozen62':not bool((aliases&cohortids) or len(keymatch) or len(connectivity) or len(namehits))})
  fp=fps.GetFingerprint(mol)
  for _,s in srcstruct.iterrows():
   other,ok=parse_smiles(s.raw_smiles)
   if other:similar.append({'query':r['id'],'cohort_drug':s.id,'similarity':DataStructs.TanimotoSimilarity(fp,fps.GetFingerprint(other)),'method':'Morgan radius2 2048bit; diagnostic only'})
 pd.DataFrame(rows).to_csv(Q/'chemical_QC_features.csv',index=False,encoding='utf-8-sig');(Q/'identity_vs_frozen62.json').write_text(json.dumps(idchecks,indent=2));pd.DataFrame(similar).sort_values(['query','similarity'],ascending=[True,False]).to_csv(Q/'structure_similarity_to62.csv',index=False)
 human=['P21397','P27338'];pf=pd.read_csv(ROOT/'reports/qa/WP05/protein_features.csv');mapping=pd.read_csv(ROOT/'reports/qa/WP06/protein_string_mapping.csv');ppi=pd.read_csv(ROOT/'reports/qa/WP06/ppi_induced_edges.csv');mapping=mapping[mapping.accession.isin(human)&mapping.network_taxid.eq(9606)]
 prots=[];folds=[]
 for acc in human:
  pr=pf[pf.accession.eq(acc)];sid=mapping[mapping.accession.eq(acc)].string_id.iloc[0]
  edges=ppi[(ppi.protein1.eq(sid)|ppi.protein2.eq(sid))&ppi.network_taxid.eq(9606)&(ppi.combined_score>=700)]
  prots.append({'accession':acc,'role_from_XML':'enzyme','taxid':9606,'features56_present':len(pr)==1 and pr.drop(columns=['accession']).shape[1]==56,'finite':len(pr)==1 and np.isfinite(pr.drop(columns=['accession']).to_numpy(float)).all(),'string_id':sid,'strict_PPI700_degree_existing_induced_graph':len(edges)})
 for fold in range(1,6):
  path=ROOT/f'reports/qa/WP09/design_v1/folds/primary_o{fold:02d}_final_train.npz'
  with np.load(path,allow_pickle=False) as z:
   ids=list(z['protein_ids'].astype(str));pairs=z['ppi_pairs_700'].T
   assert pairs.ndim==2 and pairs.shape[1]==2
   for acc in human:
    i=ids.index(acc) if acc in ids else None
    degree=int(np.sum(np.any(pairs==i,axis=1))) if i is not None else 0
    folds.append({'fold':fold,'accession':acc,'in_frozen_train_proteins':i is not None,'PPI700_incident_pairs':degree,'audit_read_only_no_query_executed':True})
 pd.DataFrame(prots).to_csv(Q/'human_protein_QA.csv',index=False);pd.DataFrame(folds).to_csv(Q/'fold_PPI_scope.csv',index=False)
 heads=read(Q/'frozen_B1_head_ids.json');primary=[set(h['classes']) for h in heads if h['context'].startswith('primary')]
 (Q/'model_policy_options.json').write_text(json.dumps({'primary_head_sizes':[len(s) for s in primary],'primary_common_head':len(set.intersection(*primary)),'proposal':'all5 frozen primary B1 separately; optional equal-weight common-head mean only after user approval','single_model_or_ensemble':'PENDING_USER_APPROVAL','representation_proposal':'DB14569 active tedizolid; DB09042 distinct phosphate prodrug sensitivity only if separately approved','external_scoring':'NOT_RUN'},indent=2))
 (Q/'blindness_audit.json').write_text(json.dumps({'SIDER_tedizolid_labels_accessed':False,'SIVEXTRO_PDF_opened':False,'incidental_search_safety_snippets_exposure':True,'strict_analyst_blindness':'COMPROMISED_BY_SEARCH_SNIPPETS','adverse_snippets_used_in_inputs_or_selection':False,'external_scores':0,'chemical_inputs':'only DrugBank SMILES + frozen RDKit descriptor definitions','prodrug_relation_reference':'https://pubmed.ncbi.nlm.nih.gov/24875463/','PubChem_property_requests':'web accessor inaccessible; local request ConnectionError; no PubChem response saved','scope_limit':'No claim of fully prospective analyst-blind experiment; independent reviewer recommended'},indent=2))
 print(pd.DataFrame(rows)[['id',*FEATURES]].to_string(index=False));print(prots);print(folds)
if __name__=='__main__':main()

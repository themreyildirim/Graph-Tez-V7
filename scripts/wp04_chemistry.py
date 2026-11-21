"""Etiketlerden bağımsız yapı doğrulama ve RDKit tanımlayıcıları."""
from pathlib import Path
import sys
import math

ROOT=Path(__file__).resolve().parents[1]
if (ROOT/'.deps/rdkit').exists():sys.path.insert(0,str(ROOT/'.deps/rdkit'))
from rdkit import Chem,rdBase
from rdkit.Chem import Descriptors,Crippen,Lipinski,rdMolDescriptors

FEATURES=('MW','LogP','HBD','HBA','TPSA')
# Yaygın metal atomları; halojenler ve B/Si/As gibi metaloidler bu sınıfta değil.
METALS=set([3,4,11,12,13,19,20,31,37,38,49,50,55,56,81,82,83,87,88])|set(range(21,31))|set(range(39,49))|set(range(57,81))|set(range(89,113))


def parse_smiles(value):
    if not isinstance(value,str) or not value.strip():return None,'missing_smiles'
    with rdBase.BlockLogs():
        mol=Chem.MolFromSmiles(value.strip(),sanitize=False)
        if mol is None:return None,'invalid_smiles_syntax'
        try:
            Chem.SanitizeMol(mol)
            Chem.AssignStereochemistry(mol,cleanIt=True,force=True)
        except Exception as e:return None,'sanitize_error:'+type(e).__name__
    return mol,'valid'


def parse_inchi(value):
    if not isinstance(value,str) or not value.startswith('InChI='):return None,'missing_or_invalid_inchi'
    with rdBase.BlockLogs():mol=Chem.MolFromInchi(value,sanitize=True,removeHs=True)
    return mol,'valid' if mol is not None else 'invalid_inchi'


def identity(mol):
    if mol is None:return {}
    with rdBase.BlockLogs():inchi=Chem.MolToInchi(mol);key=Chem.InchiToInchiKey(inchi) if inchi else ''
    stereo=Chem.FindMolChiralCenters(mol,includeUnassigned=True,useLegacyImplementation=False)
    potential=Chem.FindPotentialStereo(mol)
    legacy=Chem.FindMolChiralCenters(mol,includeUnassigned=True,useLegacyImplementation=True)
    return {'rdkit_isomeric_smiles':Chem.MolToSmiles(mol,canonical=True,isomericSmiles=True),
            'rdkit_nonisomeric_smiles':Chem.MolToSmiles(mol,canonical=True,isomericSmiles=False),
            'rdkit_inchi':inchi,'rdkit_inchikey':key,'formula':rdMolDescriptors.CalcMolFormula(mol),
            'atom_count':mol.GetNumAtoms(),'bond_count':mol.GetNumBonds(),
            'components':len(Chem.GetMolFrags(mol)),
            'formal_charge':sum(a.GetFormalCharge() for a in mol.GetAtoms()),
            'metal_atoms':','.join(sorted({a.GetSymbol() for a in mol.GetAtoms() if a.GetAtomicNum() in METALS})),
            'chiral_assigned':sum(s!='?' for _,s in stereo),'chiral_unassigned':sum(s=='?' for _,s in stereo),
            'legacy_chiral_unassigned':sum(s=='?' for _,s in legacy),
            'double_stereo_assigned':sum(str(b.GetStereo()) not in ['STEREONONE','STEREOANY'] for b in mol.GetBonds()),
            'double_stereo_unassigned':sum(str(s.type)=='Bond_Double' and str(s.specified)=='Unspecified' for s in potential),
            'aromatic_atoms':sum(a.GetIsAromatic() for a in mol.GetAtoms()),
            'aromatic_bonds':sum(b.GetIsAromatic() for b in mol.GetBonds())}


def compare_keys(a,b):
    if not a or not b:return 'missing_identity_evidence'
    if a==b:return 'full_inchikey_match'
    if a.split('-')[0]==b.split('-')[0]:return 'same_connectivity_other_layers_differ'
    return 'connectivity_or_normalization_conflict'


def descriptors(mol):
    """Kaynak yapının tamamı: fragment silme, neutralizasyon, stereo düzeltmesi yok."""
    if mol is None:return {k:None for k in FEATURES}
    result={'MW':Descriptors.MolWt(mol),'LogP':Crippen.MolLogP(mol),
            'HBD':Lipinski.NumHDonors(mol),'HBA':Lipinski.NumHAcceptors(mol),
            'TPSA':rdMolDescriptors.CalcTPSA(mol,includeSandP=False)}
    if not all(math.isfinite(x) for x in result.values()):raise ValueError('Non-finite descriptor')
    return result


def atom_bond_tables(mol):
    """Yalnız öğretici tablo; eğitim tensörü/embedding değildir."""
    atoms=[{'atom_index':a.GetIdx(),'element':a.GetSymbol(),'atomic_number':a.GetAtomicNum(),
            'formal_charge':a.GetFormalCharge(),'aromatic':a.GetIsAromatic(),'degree':a.GetDegree(),
            'implicit_H':a.GetNumImplicitHs(),'explicit_H_count':a.GetNumExplicitHs(),
            'chiral_tag':str(a.GetChiralTag()),'CIP':a.GetProp('_CIPCode') if a.HasProp('_CIPCode') else ''}
           for a in mol.GetAtoms()]
    bonds=[{'bond_index':b.GetIdx(),'begin_atom':b.GetBeginAtomIdx(),'end_atom':b.GetEndAtomIdx(),
            'bond_type':str(b.GetBondType()),'bond_order':b.GetBondTypeAsDouble(),
            'aromatic':b.GetIsAromatic(),'stereo':str(b.GetStereo()),'direction':str(b.GetBondDir())}
           for b in mol.GetBonds()]
    return atoms,bonds

"""FASTA/kimlik QC ve yalnız doğrulanmış 20-AA dizilerinden özellik hesabı."""
from pathlib import Path
from collections import Counter
import hashlib,re,sys

ROOT=Path(__file__).resolve().parents[1]
if (ROOT/'.deps/biopython').exists():sys.path.insert(0,str(ROOT/'.deps/biopython'))
import Bio
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from Bio.SeqUtils.IsoelectricPoint import IsoelectricPoint

AA='ACDEFGHIKLMNPQRSTVWY'
GROUPS={'nonpolar_nonaromatic':'AGILMPV','aromatic':'FWY','polar_uncharged':'CNQST',
        'basic':'HKR','acidic':'DE'}
ACCESSION=re.compile(r'(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(?:-[1-9][0-9]*)?')


def parse_sequence(raw):
    raw=raw if isinstance(raw,str) else ''
    result={'status':'missing','sequence':'','header':'','header_removed':False,'raw_length':len(raw),
            'invalid_characters':'','lowercase_normalized':False,'whitespace_removed':0,'length':0,'sequence_sha256':''}
    if not raw.strip():return result
    lines=raw.strip().splitlines()
    if lines[0].lstrip().startswith('>'):
        result['header']=lines[0].strip()
        if len(lines)==1:result['status']='fasta_missing_sequence_boundary';return result
        if any(x.lstrip().startswith('>') for x in lines[1:]):result['status']='multiple_fasta_records';return result
        result['header_removed']=True;body='\n'.join(lines[1:])
    else:
        if any(x.lstrip().startswith('>') for x in lines):result['status']='embedded_fasta_header';return result
        body='\n'.join(lines)
    compact=re.sub(r'\s','',body)
    if not compact.isascii():
        result['status']='invalid_residues_or_markup';result['invalid_characters']='non_ASCII';return result
    result['whitespace_removed']=len(body)-len(compact)
    result['lowercase_normalized']=compact!=compact.upper();sequence=compact.upper()
    invalid=sorted(set(sequence)-set(AA))
    if invalid:
        result['status']='invalid_residues_or_markup';result['invalid_characters']=''.join(invalid);return result
    if not sequence:return result
    result.update(status='valid',sequence=sequence,length=len(sequence),sequence_sha256=hashlib.sha256(sequence.encode('ascii')).hexdigest())
    return result


def resolve_accession(attribute,external,source='Swiss-Prot'):
    candidates=set(x.strip() for x in [attribute,*external] if isinstance(x,str) and x.strip())
    if not candidates:return '', 'missing_accession'
    if len(candidates)>1:return '', 'conflicting_accessions'
    value=next(iter(candidates))
    if not ACCESSION.fullmatch(value):return '', 'invalid_accession_format'
    if not external and source not in ['Swiss-Prot','UniProtKB','TrEMBL']:return '', 'unconfirmed_attribute_source'
    return value,'xml_identifiers_agree' if external and attribute else 'xml_single_identifier'


def validate_groups(groups=GROUPS):
    assigned=''.join(groups.values())
    if set(assigned)!=set(AA) or len(assigned)!=20:raise ValueError('Groups must partition all 20 residues exactly once')


def features(sequence):
    if not sequence or set(sequence)-set(AA):raise ValueError('Only nonempty validated 20-AA sequence accepted')
    validate_groups();count=Counter(sequence);n=len(sequence);obj=ProteinAnalysis(sequence,monoisotopic=False)
    ip=IsoelectricPoint(sequence)
    # Geniş 0–14 aralığı: standart dar pI aralığına çok uç dizileri sıkıştırma.
    pi=ip.pi(pH=7,min_=0,max_=14)
    result={'length_aa':n,'molecular_weight_Da':obj.molecular_weight(),'isoelectric_point':pi,
            'aromaticity_fraction':obj.aromaticity(),'gravy_kyte_doolittle':obj.gravy(),
            'net_charge_pH7':obj.charge_at_pH(7.0),
            **{'AAC_'+aa:count[aa]/n for aa in AA}}
    group_for={a:g for g,members in GROUPS.items() for a in members}
    for g,members in GROUPS.items():result['group_'+g]=sum(count[x] for x in members)/n
    pairs=Counter((group_for[a],group_for[b]) for a,b in zip(sequence,sequence[1:]))
    # N=1 için dipeptit tanımsız; tümü 0 diyerek veri varmış gibi gösterme.
    for a in GROUPS:
        for b in GROUPS:result[f'DC_{a}__{b}']=pairs[(a,b)]/(n-1) if n>1 else None
    return result


def organism_class(name,taxid=''):
    """Yalnız açık destekli adlar; non-human => bacteria dönüşümü yok."""
    if taxid=='9606' or name in ['Homo sapiens','Humans']:return 'human'
    bacterial=('Escherichia ','Staphylococcus ','Streptococcus ','Bacillus ','Mycobacterium ',
               'Helicobacter ','Pseudomonas ','Enterococcus ','Enterobacter ','Klebsiella ',
               'Salmonella ','Neisseria ','Haemophilus ','Clostridium ','Acinetobacter ',
               'Bacteroides ','Chlamydia ','Chlamydophila ','Mycoplasma ','Thermus ','Streptomyces ','Shigella ')
    if name.startswith(bacterial) or name in ['Bacteria','Bacterial']:return 'bacteria'
    if name.startswith(('Candida ','Saccharomyces ','Aspergillus ')) or name in ['Yeast','Fungi']:return 'fungus'
    if name in ['Mouse','Mus musculus'] or name.startswith('Plasmodium '):return 'other_eukaryote'
    return 'other_or_unresolved' if name else 'unknown'

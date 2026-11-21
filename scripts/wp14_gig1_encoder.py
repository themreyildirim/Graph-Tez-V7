"""GiG-1a: A1P1 omurgasına ilaç → protein mesaj adımı ekleyen kodlayıcı.

A1P1'den tek farkı, protein gömmelerinin PPI adımından ÖNCE kendilerine
bağlanan ilaçların kimyasal/moleküler ön durumundan bir mesaj almasıdır:

    h_d⁽⁰⁾ = ReLU(W_proj · [kimya(8) ⊕ molekül(8) ⊕ maskeler(5)])      # 21 → 32
    z      = ReLU(P · x_p)
    z⁽¹⁾   = z + ReLU(W_dp · mean_{d ∈ N(p)} h_d⁽⁰⁾) · 1[N(p) ≠ ∅]     # YENİ
    h_p    = z⁽¹⁾ + ReLU(S · z⁽¹⁾ + M · mean_komşu(z⁽¹⁾))               # A1P1 ile aynı

Böylece A1P1'in üç temsil sınırı hedeflenir:
  S1  modaliteler arası etkileşim (protein bloğu artık kimya türevi bilgi taşır)
  S2  bağlama uyarlanan protein temsili
  S3  ortak hedef üzerinden kimyasal komşuluk

Sızıntı ve izolasyon:
  * Yan etki etiketi hiçbir aşamada encoder'a girmez.
  * Mesajlar yalnız ÖZELLİK taşır (kimya, molekül, maske) — etiket taşımaz.
  * İlaç → protein mesajı YALNIZ eğitim grafında hesaplanır. Sorgu ilacı
    protein önbelleğini okur, ona yazmaz; görülmemiş proteinler kenarsız
    işlenir. Bu, WP09/WP10'daki önbellek izolasyon kuralını korur.

Mevcut dosyalar değiştirilmemiştir; bu modül yalnızca onları kullanır.
"""
from pathlib import Path
import copy

import torch
from torch import nn

from wp09_encoder import RoleMaskedPPI, ROLES, directed_edges
from wp10_molecular_encoder import (
    BondAwareMolecularEncoder,
    MolecularInput,
    initialized_model as a1p1_initialized_model,
    validate_batch,
    approved_atom_ids,
)
from wp10_molecular_graph import numeric_digest
from torch_geometric.nn import global_mean_pool

ROOT = Path(__file__).resolve().parents[1]
VARIANT = "GiG1a"
DRUG_STATE_INPUT = 21  # kimya 8 + molekül 8 + maske 5
DRUG_STATE_HIDDEN = 32  # protein gizli boyutuyla aynı


def unique_drug_protein_pairs(role_edges, device):
    """Dört rolü birleştirir ve (ilaç, protein) çiftlerini tekilleştirir.

    Bir protein birden çok rolde görünebilir (örn. P02768 hem carrier hem
    target). Tekilleştirme olmadan o çift ortalamada iki kez sayılırdı.
    """
    columns = [role_edges[role] for role in ROLES if role_edges[role].numel()]
    if not columns:
        return torch.empty((2, 0), dtype=torch.long, device=device)
    stacked = torch.cat(columns, dim=1).to(device)
    pairs = torch.unique(stacked.t(), dim=0).t().contiguous()
    return pairs


class GiG1Encoder(nn.Module):
    """A1P1 omurgası + ilaç → protein mesajı. Başlık A1P1 ile birebir aynı."""

    def __init__(self, num_targets=None):
        super().__init__()
        self.base = RoleMaskedPPI(num_targets=None)
        self.molecular = BondAwareMolecularEncoder()
        self.drug_projection = nn.Linear(DRUG_STATE_INPUT, DRUG_STATE_HIDDEN)
        self.drug_message = nn.Linear(DRUG_STATE_HIDDEN, DRUG_STATE_HIDDEN, bias=False)
        self.head = None if num_targets is None else nn.Linear(150, num_targets)
        self.representation_dim = 150

    # --- A1P1 ile aynı doğrulamalar -------------------------------------
    def _check_molecules(self, molecules, ids):
        if not isinstance(molecules, MolecularInput) or molecules.ids != tuple(ids):
            raise ValueError("Ordered molecular IDs must equal requested train/query IDs")
        approved, all_ids = approved_atom_ids()
        expected = torch.tensor([d in approved for d in ids], dtype=torch.bool,
                                device=molecules.atom_mask.device)
        if set(ids) - all_ids or molecules.atom_mask.dtype != torch.bool or not torch.equal(
            expected, molecules.atom_mask
        ):
            raise ValueError("Frozen QC54/8 masks required")
        if molecules.batch.num_graphs != len(ids):
            raise ValueError("One molecular graph per drug")
        validate_batch(molecules.batch)

    # --- bileşenler ------------------------------------------------------
    def molecular_block(self, batch, atom_mask):
        """A1P1'deki moleküler dal; atom maskesi kapalıysa sıfır blok."""
        raw = self.molecular(batch)["molecular_h"]
        return raw * atom_mask[:, None].to(raw.dtype)

    def drug_state(self, chemistry, masks, molecular_block):
        """İlaç ön durumu: yalnız özellik; etiket yok."""
        chem = torch.relu(self.base.chemistry(chemistry)) * masks[:, 0:1].to(chemistry.dtype)
        features = torch.cat([chem, molecular_block, masks.to(chem.dtype)], dim=1)
        if features.shape[1] != DRUG_STATE_INPUT:
            raise ValueError("21 boyutlu ilaç ön durumu bekleniyor")
        return torch.relu(self.drug_projection(features))

    def encode_proteins(self, protein_x, ppi_pairs, role_edges, drug_h, variant):
        """z → (ilaç mesajı) → (PPI mesajı). PPI kolu A1P1 ile aynı denklem."""
        protein = self.base.protein
        if protein_x.ndim != 2 or protein_x.shape[1] != protein.projection.in_features:
            raise ValueError("Protein feature schema")
        z = torch.relu(protein.projection(protein_x))

        pairs = unique_drug_protein_pairs(role_edges, z.device)
        if pairs.numel():
            if int(pairs[0].max()) >= len(drug_h) or int(pairs[1].max()) >= len(z):
                raise ValueError("Drug/protein endpoint index")
            sums = torch.zeros_like(z).index_add(0, pairs[1], drug_h[pairs[0]])
            counts = torch.zeros((len(z), 1), dtype=z.dtype, device=z.device).index_add(
                0, pairs[1], torch.ones((pairs.shape[1], 1), dtype=z.dtype, device=z.device)
            )
            # Bağlı ilacı olmayan protein gerçekten sıfır mesaj alır.
            z = z + torch.relu(self.drug_message(sums / counts.clamp_min(1))) * (counts > 0).to(z.dtype)

        edges = directed_edges(ppi_pairs).to(z.device)
        if variant.endswith("0"):
            edges = edges[:, :0]
        source, destination = edges
        total = torch.zeros_like(z).index_add(0, destination, z[source])
        degree = torch.zeros((len(z), 1), dtype=z.dtype, device=z.device).index_add(
            0, destination, torch.ones((len(destination), 1), dtype=z.dtype, device=z.device)
        )
        neighbor_mean = total / degree.clamp_min(1)
        return z + torch.relu(protein.self_update(z) + protein.message(neighbor_mean))

    def fuse(self, base_output, molecular_block, atom_mask):
        representation = torch.cat(
            [base_output["representation"], molecular_block, atom_mask[:, None].to(molecular_block.dtype)],
            dim=1,
        )
        if representation.shape[1] != 150:
            raise ValueError("150-dimensional fusion required")
        logits = None
        if self.head is not None:
            logits = self.head(representation).masked_fill(~base_output["eligible"][:, None], float("nan"))
        return {"representation": representation, "eligible": base_output["eligible"], "logits": logits}


def initialized_gig1(seed=20261106, num_targets=None, dtype=torch.float32):
    """A1P1 ile AYNI omurga başlangıcı; yalnız yeni katmanlar ek tohumla.

    Böylece GiG-1a ile A1P1 arasındaki fark başlangıçta yalnız eklenen
    yoldan ibarettir; karşılaştırma bu yönüyle denetlenmiş olur.
    """
    reference = a1p1_initialized_model(seed=seed, num_targets=num_targets, dtype=dtype)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(seed) + 14)  # WP14 için ayrı akış
        model = GiG1Encoder(num_targets).to(dtype=dtype)
    model.base.load_state_dict(reference.base.state_dict())
    model.molecular.load_state_dict(reference.molecular.state_dict())
    if num_targets is not None:
        model.head.load_state_dict(reference.head.state_dict())
    return model


# --- hazırlanmış girdiyle ileri geçiş (wp10_training_forward ile aynı desen) ---
class PreparedGiG1:
    __slots__ = ("graph", "molecules", "digest")

    def __init__(self, graph, molecules, digest):
        self.graph = graph
        self.molecules = molecules
        self.digest = digest


def input_digest(graph, molecules):
    return numeric_digest(
        {
            **graph,
            "molecule_x": molecules.batch.x,
            "molecule_edges": molecules.batch.edge_index,
            "molecule_attr": molecules.batch.edge_attr,
            "molecule_batch": molecules.batch.batch,
            "atom_mask": molecules.atom_mask,
        }
    )


def prepare(model, graph, molecules):
    model._check_molecules(molecules, graph["drug_ids"])
    frozen = copy.deepcopy(graph)
    mol = copy.deepcopy(molecules)
    return PreparedGiG1(frozen, mol, input_digest(frozen, mol))


def _role_tensors(graph):
    return {role: torch.as_tensor(graph["role_" + role], dtype=torch.long) for role in ROLES}


def train_forward(model, prepared, variant=VARIANT):
    graph = prepared.graph
    chemistry = torch.as_tensor(graph["chemistry"], dtype=torch.float32)
    masks = torch.as_tensor(graph["masks"], dtype=torch.bool)
    role_edges = _role_tensors(graph)
    block = model.molecular_block(prepared.molecules.batch, prepared.molecules.atom_mask)
    drug_h = model.drug_state(chemistry, masks, block)
    protein_h = model.encode_proteins(
        torch.as_tensor(graph["protein_x"], dtype=torch.float32),
        graph["ppi_pairs_700"],
        role_edges,
        drug_h,
        variant,
    )
    base = model.base.readout(protein_h, chemistry, masks, role_edges)
    return {**model.fuse(base, block, prepared.molecules.atom_mask), "protein_h": protein_h,
            "drug_state": drug_h}


def query_forward(model, prepared, train_protein_h, variant=VARIANT):
    """Sorgu ilacı protein önbelleğini YALNIZ okur; ona yazmaz."""
    query = prepared.graph
    block = model.molecular_block(prepared.molecules.batch, prepared.molecules.atom_mask)
    base = model.base.query_readout(query, train_protein_h)
    return model.fuse(base, block, prepared.molecules.atom_mask)

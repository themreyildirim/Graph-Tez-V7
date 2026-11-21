"""§7.3(5) dejenerasyon kontrolü: ilaç → protein mesajı ayırt edici mi?

Önceden kaydedilmiş kapı maddesiydi: hub proteinlerde `mean` neredeyse
sabit bir vektör üretiyorsa bu oversmoothing kanıtı olarak SONUÇLA
BİRLİKTE raporlanır. Eğitilmiş ağırlıklar yalnız okunur; yeniden fit yok.
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wp09_encoder import ROLES
from wp10_molecular_graph import load_store
from wp10_train import load_bundle
from wp14_gig1_encoder import initialized_gig1, prepare, unique_drug_protein_pairs

QA = ROOT / "reports/qa/WP14/gig1_v1"
MODEL = ROOT / "models/WP14_gig1_v1"


def main():
    store = load_store()
    rows = []
    for fold in range(1, 6):
        context = f"primary_o{fold:02d}_final"
        md = json.loads((MODEL / f"{context}_GiG1a.json").read_text(encoding="utf-8"))
        model = initialized_gig1(int(md["seed"]), num_targets=len(md["fitted_targets"]))
        with np.load(ROOT / md["parameters_file"], allow_pickle=False) as archive:
            model.load_state_dict({k: torch.from_numpy(archive[k].copy()) for k in archive.files})
        model.eval()

        graph = load_bundle(context, "train")
        prepared = prepare(model, graph, store.make_batch(graph["drug_ids"]))
        g = prepared.graph
        chemistry = torch.as_tensor(g["chemistry"], dtype=torch.float32)
        masks = torch.as_tensor(g["masks"], dtype=torch.bool)
        role_edges = {r: torch.as_tensor(g["role_" + r], dtype=torch.long) for r in ROLES}

        with torch.no_grad():
            block = model.molecular_block(prepared.molecules.batch, prepared.molecules.atom_mask)
            drug_h = model.drug_state(chemistry, masks, block)
            pairs = unique_drug_protein_pairs(role_edges, drug_h.device)
            n_p = len(g["protein_x"])
            sums = torch.zeros((n_p, drug_h.shape[1])).index_add(0, pairs[1], drug_h[pairs[0]])
            counts = torch.zeros((n_p, 1)).index_add(
                0, pairs[1], torch.ones((pairs.shape[1], 1))
            )
            mean_dp = sums / counts.clamp_min(1)
            message = torch.relu(model.drug_message(mean_dp)) * (counts > 0).float()
            z = torch.relu(model.base.protein.projection(torch.as_tensor(g["protein_x"], dtype=torch.float32)))

        degree = counts[:, 0].numpy().astype(int)
        connected = degree > 0
        msg = message.numpy()
        base_norm = np.linalg.norm(z.numpy(), axis=1)
        msg_norm = np.linalg.norm(msg, axis=1)

        # Bağlı proteinler arasında mesajın ayırt ediciliği
        sub = msg[connected]
        centroid = sub.mean(0)
        spread = np.linalg.norm(sub - centroid, axis=1)
        rows.append({
            "context": context,
            "proteins": int(n_p),
            "connected_proteins": int(connected.sum()),
            "isolated_proteins": int((~connected).sum()),
            "max_degree": int(degree.max()),
            "mean_message_norm": float(msg_norm[connected].mean()),
            "mean_base_norm": float(base_norm.mean()),
            "message_to_base_ratio": float(msg_norm[connected].mean() / base_norm.mean()),
            "message_spread_over_norm": float(spread.mean() / max(np.linalg.norm(centroid), 1e-12)),
            "hub_message_norm": float(msg_norm[degree >= 10].mean()) if (degree >= 10).any() else float("nan"),
            "low_degree_message_norm": float(msg_norm[(degree >= 1) & (degree <= 2)].mean()) if ((degree >= 1) & (degree <= 2)).any() else float("nan"),
        })

    frame = pd.DataFrame(rows)
    frame.to_csv(QA / "degeneracy_check.csv", index=False, encoding="utf-8-sig", lineterminator="\n")
    print(frame.to_string(index=False))
    print()
    print("Yorum ölçütü: message_spread_over_norm << 1 ise mesaj proteinler arasında")
    print("neredeyse sabittir (oversmoothing). Hub ve düşük dereceli protein")
    print("mesaj normlarının birbirine yakınlığı da aynı yöne işaret eder.")
    summary = {
        "mean_message_to_base_ratio": float(frame.message_to_base_ratio.mean()),
        "mean_message_spread_over_norm": float(frame.message_spread_over_norm.mean()),
        "mean_hub_message_norm": float(frame.hub_message_norm.mean()),
        "mean_low_degree_message_norm": float(frame.low_degree_message_norm.mean()),
        "isolated_protein_share": float((frame.isolated_proteins / frame.proteins).mean()),
        "no_refit": True,
    }
    (QA / "degeneracy_check.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

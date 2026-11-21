"""GiG-1a sentetik kapısı: gerçek eğitimden ÖNCE çalıştırılır.

Doğrulananlar (§7.3):
  1. İlaç → protein mesajının analitik doğruluğu (elle hesaplanmış örnek)
  2. Bağlı ilacı olmayan proteinin gerçekten sıfır mesaj alması
  3. Yeni yolun gradyan taşıması
  4. A1P1 eşdeğerliği: yeni yol sıfırlanınca çıktı A1P1 ile birebir aynı
  5. Rol tekilleştirmesi (aynı çift iki rolde ise bir kez sayılır)
  6. Önbellek izolasyonu: sorgu ilacı protein gömmesini değiştiremez
  7. Etiket bağımsızlığı: etiketler encoder'a hiçbir yoldan girmez

Hiçbir gerçek veri okunmaz; yalnız yapay küçük graflar kullanılır.
"""
from pathlib import Path
import json
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wp09_encoder import ROLES
from wp14_gig1_encoder import GiG1Encoder, unique_drug_protein_pairs

OUT = ROOT / "reports/qa/WP14/gig1_gate_v1"
results = []


def check(name, ok, detail=""):
    results.append({"case": name, "status": "PASS" if ok else "FAIL", "detail": str(detail)[:300]})
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"  :: {detail}" if detail else ""))
    return ok


def role_dict(pairs_by_role):
    out = {}
    for role in ROLES:
        value = pairs_by_role.get(role, [])
        out[role] = torch.tensor(value, dtype=torch.long).reshape(-1, 2).t().contiguous()
    return out


def main():
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    model = GiG1Encoder(num_targets=None).double()
    model.eval()

    # --- yapay kurulum: 3 ilaç, 4 protein -----------------------------
    # p0: d0 ve d1 bağlı (ortak hedef) · p1: yalnız d2 · p2: hiç ilaç yok
    # p3: d0 hem target hem enzyme (tekilleştirme sınaması)
    n_p = 4
    protein_x = torch.arange(n_p * 56, dtype=torch.double).reshape(n_p, 56) / (n_p * 56)
    chemistry = torch.tensor(
        [[0.1, 0.2, 0.3, 0.4, 0.5], [0.9, 0.8, 0.7, 0.6, 0.5], [0.2, 0.2, 0.2, 0.2, 0.2]],
        dtype=torch.double,
    )
    masks = torch.tensor(
        [[True, True, True, False, False],
         [True, True, False, False, False],
         [True, True, False, False, False]]
    )
    block = torch.tensor(
        [[0.5] * 8, [0.25] * 8, [0.75] * 8], dtype=torch.double
    )
    roles = role_dict({
        "target": [(0, 0), (1, 0), (2, 1), (0, 3)],
        "enzyme": [(0, 3)],  # p3 için AYNI çift ikinci rolde
    })
    ppi = torch.empty((2, 0), dtype=torch.long)

    drug_h = model.drug_state(chemistry, masks, block)

    # 1) analitik doğrulama -------------------------------------------
    z = torch.relu(model.base.protein.projection(protein_x))
    expected_p0 = z[0] + torch.relu(model.drug_message((drug_h[0] + drug_h[1]) / 2))
    expected_p1 = z[1] + torch.relu(model.drug_message(drug_h[2]))
    expected_p3 = z[3] + torch.relu(model.drug_message(drug_h[0]))  # tekilleştirme → tek kez

    got = model.encode_proteins(protein_x, ppi, roles, drug_h, "GiG1a")
    # PPI kenarı yok → ikinci adım: z1 + relu(S z1 + M*0)
    def ppi_step(z1):
        return z1 + torch.relu(model.base.protein.self_update(z1) + model.base.protein.message(torch.zeros_like(z1)))

    z1 = z.clone()
    z1[0] = expected_p0
    z1[1] = expected_p1
    z1[3] = expected_p3
    expected = ppi_step(z1)
    check("01_ilac_protein_mesaji_analitik",
          torch.allclose(got, expected, atol=1e-12),
          f"max fark {float((got-expected).abs().max()):.3e}")

    # 2) bağlı ilacı olmayan protein sıfır mesaj alır -------------------
    check("02_baglantisiz_protein_sifir_mesaj",
          torch.allclose(got[2], ppi_step(z)[2], atol=1e-12),
          f"max fark {float((got[2]-ppi_step(z)[2]).abs().max()):.3e}")

    # 3) tekilleştirme --------------------------------------------------
    pairs = unique_drug_protein_pairs(roles, torch.device("cpu"))
    check("03_rol_tekillestirmesi", pairs.shape[1] == 4, f"benzersiz çift {pairs.shape[1]} (beklenen 4)")

    # 4) gradyan akışı ---------------------------------------------------
    grad_model = GiG1Encoder(num_targets=None).double()
    gh = grad_model.drug_state(chemistry, masks, block)
    out = grad_model.encode_proteins(protein_x, ppi, roles, gh, "GiG1a")
    out.sum().backward()
    gw = grad_model.drug_message.weight.grad
    gp = grad_model.drug_projection.weight.grad
    check("04_yeni_yol_gradyan_tasiyor",
          gw is not None and float(gw.norm()) > 0 and gp is not None and float(gp.norm()) > 0,
          f"W_dp {float(gw.norm()):.4f} · W_proj {float(gp.norm()):.4f}")

    # 5) A1P1 eşdeğerliği: yeni yol sıfırlanınca ------------------------
    equiv = GiG1Encoder(num_targets=None).double()
    with torch.no_grad():
        equiv.drug_message.weight.zero_()
    zeroed = equiv.encode_proteins(protein_x, ppi, roles, equiv.drug_state(chemistry, masks, block), "GiG1a")
    za = torch.relu(equiv.base.protein.projection(protein_x))
    a1p1_like = za + torch.relu(equiv.base.protein.self_update(za) + equiv.base.protein.message(torch.zeros_like(za)))
    check("05_sifir_W_dp_ile_A1P1_esdegeri",
          torch.allclose(zeroed, a1p1_like, atol=1e-12),
          f"max fark {float((zeroed-a1p1_like).abs().max()):.3e}")

    # 6) önbellek izolasyonu: sorgu ilacı protein gömmesini değiştiremez
    #    (query yolunda protein_h sabit alınır; burada sözleşme sınanır)
    cache = got.detach().clone()
    before = cache.clone()
    qchem = torch.tensor([[0.33, 0.33, 0.33, 0.33, 0.33]], dtype=torch.double)
    qmask = torch.tensor([[True, True, False, False, False]])
    qblock = torch.tensor([[0.1] * 8], dtype=torch.double)
    qroles = role_dict({"target": [(0, 0)]})
    qout = model.base.readout(cache, qchem, qmask, qroles)
    check("06_onbellek_degismiyor",
          torch.equal(cache, before) and qout["representation"].shape[1] == 141,
          f"temsil {tuple(qout['representation'].shape)}")

    # 7) etiket bağımsızlığı: encode yolunda etiket argümanı yok --------
    import inspect
    sig_enc = set(inspect.signature(model.encode_proteins).parameters)
    sig_drug = set(inspect.signature(model.drug_state).parameters)
    banned = {"labels", "y", "targets", "side_effect", "class_id"}
    check("07_encoder_etiket_almiyor",
          not (sig_enc | sig_drug) & banned,
          f"encode_proteins{sorted(sig_enc)} drug_state{sorted(sig_drug)}")

    # 8) parametre sayısı -------------------------------------------------
    n_new = sum(p.numel() for p in [model.drug_projection.weight, model.drug_projection.bias,
                                    model.drug_message.weight])
    check("08_ek_parametre_1728", n_new == 1728, f"{n_new}")

    OUT.mkdir(parents=True, exist_ok=True)
    failed = [r for r in results if r["status"] == "FAIL"]
    (OUT / "synthetic_gate.json").write_text(
        json.dumps({"checks": results, "passed": len(results) - len(failed),
                    "failed": len(failed), "real_data_read": False,
                    "training_performed": False}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nSentetik kapı: {len(results)-len(failed)}/{len(results)} PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    print("GiG-1a sentetik kapısı")
    sys.exit(main())

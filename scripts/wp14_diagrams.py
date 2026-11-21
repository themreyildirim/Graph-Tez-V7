"""GiG ve A1P1 karşılaştırması için mimari ve veri akışı diyagramları.

Yalnız çizim yapar; model, veri veya sonuç okumaz ve hiçbir şey eğitmez.
Çıktı: reports/figures/WP14/
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/figures/WP14"

ACCENT = "#0f6e7d"
MUTED = "#5b7682"
WARN = "#b4553f"
LIGHT = "#e3eef1"
PAPER = "#f7fafb"
INK = "#10303a"


def box(x, y, w, h, label, sub="", fill=PAPER, stroke=ACCENT, dash=False, fs=13):
    style = f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"'
    if dash:
        style += ' stroke-dasharray="6 4"'
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" {style}/>']
    ty = y + h / 2 + (0 if not sub else -6)
    out.append(
        f'<text x="{x+w/2}" y="{ty}" text-anchor="middle" font-size="{fs}" '
        f'font-weight="600" fill="{INK}">{label}</text>'
    )
    if sub:
        out.append(
            f'<text x="{x+w/2}" y="{ty+16}" text-anchor="middle" font-size="11" '
            f'fill="{MUTED}">{sub}</text>'
        )
    return "".join(out)


def group(x, y, w, h, label, sub="", stroke=ACCENT, dash=False):
    """Kapsayici cerceve; basligi kutunun UST kenarina yazar."""
    style = f'fill="#ffffff" stroke="{stroke}" stroke-width="1.6"'
    if dash:
        style += ' stroke-dasharray="6 4"'
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" {style}/>']
    out.append(
        f'<text x="{x+16}" y="{y+22}" font-size="12.5" font-weight="700" '
        f'fill="{stroke}">{label}</text>'
    )
    if sub:
        out.append(f'<text x="{x+16}" y="{y+38}" font-size="10.5" fill="{MUTED}">{sub}</text>')
    return "".join(out)


def arrow(x1, y1, x2, y2, label="", color=ACCENT, dash=False):
    style = f'stroke="{color}" stroke-width="1.6" fill="none" marker-end="url(#a)"'
    if dash:
        style += ' stroke-dasharray="5 4"'
    out = [f'<path d="M {x1} {y1} L {x2} {y2}" {style}/>']
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        out.append(
            f'<text x="{mx}" y="{my-6}" text-anchor="middle" font-size="10.5" '
            f'fill="{MUTED}">{label}</text>'
        )
    return "".join(out)


def title(x, y, text, fs=16):
    return (
        f'<text x="{x}" y="{y}" font-size="{fs}" font-weight="700" '
        f'fill="{INK}">{text}</text>'
    )


def note(x, y, text, fs=11, color=MUTED):
    return f'<text x="{x}" y="{y}" font-size="{fs}" fill="{color}">{text}</text>'


HEAD = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
    'viewBox="0 0 {w} {h}" font-family="Segoe UI, Calibri, sans-serif">'
    f'<rect width="100%" height="100%" fill="#ffffff"/>'
    '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" '
    'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
    f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{ACCENT}"/></marker></defs>'
)


def mimari():
    """EMT1 GiG tasarımı ile A1P1 uygulamasının yan yana karşılaştırması."""
    W, H = 1500, 880
    s = [HEAD.format(w=W, h=H)]

    # --- sol: EMT1 ---
    s.append(title(40, 42, "EMT1 tasarımı — Graph-in-Graph (rapor §4.3)"))
    s.append(note(40, 62, "Denklem (4.8)–(4.13); iç ağ üzerinde yayılım denklemi tanımlı değil"))
    s.append(f'<rect x="28" y="78" width="690" height="760" rx="10" fill="none" stroke="{LIGHT}" stroke-width="2"/>')

    s.append(group(60, 104, 300, 140, "İç ağ: proteinler", "V_P = 70 düğüm", dash=True))
    s.append(box(78, 162, 120, 56, "x_p", "51 boyut", fill=LIGHT))
    s.append(box(228, 162, 112, 56, "h_p", "MLP_P(x_p)"))
    s.append(arrow(200, 190, 226, 190))
    s.append(f'<rect x="376" y="150" width="210" height="76" rx="7" fill="#fdf1e7" stroke="{WARN}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    s.append(note(390, 174, "E_PP = 70 kenar", fs=12, color=WARN))
    s.append(note(390, 194, "şemada tanımlı,", fs=11.5, color=WARN))
    s.append(note(390, 212, "denklemlerde YOK", fs=11.5, color=WARN))

    s.append(box(60, 268, 140, 56, "x_d", "25 boyut", fill=LIGHT))
    s.append(box(60, 348, 140, 56, "h_d⁽⁰⁾", "MLP_D"))
    s.append(arrow(130, 324, 130, 346))
    s.append(box(230, 348, 150, 56, "μ_d", "mean h_p, N(d)"))
    s.append(arrow(284, 220, 284, 346, "tipsiz ortalama"))

    s.append(box(130, 436, 250, 60, "h_d = ReLU(W_agg·[·∥·])", "eşitlik (4.11)"))
    s.append(arrow(130, 404, 200, 434))
    s.append(arrow(300, 404, 290, 434))

    s.append(group(430, 262, 210, 118, "Yan etki düğümü", "V_S = 30", dash=True))
    s.append(box(448, 312, 72, 52, "x_s", "one-hot", fill=LIGHT, fs=12))
    s.append(box(548, 312, 72, 52, "h_s", "MLP_S", fs=12))
    s.append(arrow(522, 338, 546, 338))

    s.append(box(230, 560, 300, 62, "MLP_pred([h_d ∥ h_s])", "ortak başlık (4.13)"))
    s.append(arrow(255, 496, 330, 558))
    s.append(arrow(560, 382, 450, 558))
    s.append(box(300, 672, 160, 52, "σ → ŷ_ds", fill=LIGHT))
    s.append(arrow(380, 622, 380, 670))
    s.append(note(60, 772, "E_DS = 605 kenar yalnız denetim hedefi (4.14);", fs=11.5))
    s.append(note(60, 790, "mesajlaşmaya girmez → bu tasarımda etiket sızıntısı yok.", fs=11.5))
    s.append(note(60, 814, "İç ağ mesajlaşması bulunmadığı için ad yanıltıcıdır.", fs=11.5, color=WARN))

    # --- sağ: A1P1 ---
    s.append(title(770, 42, "EMT2 uygulaması — A1P1 (WP09 + WP10)"))
    s.append(note(770, 62, "Kod: wp09_encoder.py, wp10_molecular_encoder.py"))
    s.append(f'<rect x="758" y="78" width="712" height="760" rx="10" fill="none" stroke="{LIGHT}" stroke-width="2"/>')

    s.append(group(790, 104, 420, 156, "İç ağ 1: protein–protein", "STRING insan-700 · 63 düğüm · 184 kenar"))
    s.append(box(808, 158, 110, 52, "x_p", "56 boyut", fill=LIGHT, fs=12))
    s.append(box(948, 158, 244, 52, "z + ReLU(S·z + M·mean)", "gerçek mesaj geçişi", fs=11.5))
    s.append(arrow(918, 184, 946, 184))
    s.append(note(808, 236, "kenar silinince ΔL2 = 13,16 · gradyan 0,0040", fs=10.5, color=ACCENT))

    s.append(group(790, 288, 420, 116, "İç ağ 2: atom–bağ grafı", "44 / 14 boyut · tek katman · 54 QC açık"))
    s.append(box(808, 338, 384, 50, "h₀ + ReLU(S·h₀ + mean ReLU(U·h₀ⱼ + V·e_ji)) → pool → 8", fs=11))

    s.append(group(790, 432, 420, 104, "Rol ayrımlı okuma", "target · enzyme · transporter · carrier"))
    s.append(box(808, 478, 384, 44, "4 × maskeli ortalama = 128 boyut", fs=11.5))
    s.append(note(808, 470, "girdi: İç ağ 1 protein gömmeleri (tipli toplama)", fs=10, color=ACCENT))

    s.append(box(1248, 432, 200, 104, "Kimya + maske", "ReLU(Lin(5,8)) + 5"))

    s.append(box(900, 560, 420, 56, "Füzyon: 128 + 8 + 5 + 8 + 1 = 150 boyut"))
    s.append(arrow(1000, 536, 1060, 558))
    s.append(arrow(1348, 536, 1230, 558))
    s.append(arrow(1210, 396, 1286, 558, "", dash=True))

    s.append(box(900, 672, 420, 56, "Linear(150, K) → PT başına bağımsız vektör", fill=LIGHT))
    s.append(arrow(1110, 616, 1110, 670))
    s.append(note(900, 760, "K ≈ 240 → başlık 36.240 parametre; omurga 5.512.", fs=11.5))
    s.append(note(900, 778, "Parametrelerin %86,8'i başlıkta → küçük kohortta yüksek varyans.", fs=11.5, color=WARN))
    s.append(note(900, 802, "Yan etki düğümü yok; sınıf kimliği başlık satırında örtük.", fs=11.5))
    s.append(note(900, 820, "side_effect_edges = False (152/152 iş).", fs=11.5, color=ACCENT))

    s.append("</svg>")
    return "".join(s)


def akis():
    """Girişten yan etki skoruna veri akışı ve sızıntı sınırı."""
    W, H = 1500, 790
    s = [HEAD.format(w=W, h=H)]
    s.append(title(40, 44, "Veri akışı — kaynaktan yan etki skoruna ve sızıntı sınırı"))
    s.append(note(40, 64, "Kutu altı sayılar dondurulmuş dış kat (primary_oNN_final) kapsamıdır"))

    y = 110
    s.append(box(40, y, 180, 86, "DrugBank XML", "62 ilaç · ATC · roller", fill=LIGHT))
    s.append(box(40, y + 110, 180, 86, "PubChem / RDKit", "SMILES → 5 tanımlayıcı", fill=LIGHT))
    s.append(box(40, y + 220, 180, 86, "STRING v12", "insan 9606 · eşik 700", fill=LIGHT))
    s.append(box(40, y + 330, 180, 86, "SIDER 4.1", "1.061 PT · 6.416 pozitif", fill="#fdf1e7", stroke=WARN))

    s.append(box(280, y, 200, 196, "Kimlik köprüsü", "ana etkin madde ↔ stereo CID ↔ accession"))
    s.append(arrow(222, y + 43, 278, y + 70))
    s.append(arrow(222, y + 153, 278, y + 110))

    s.append(box(280, y + 220, 200, 86, "PPI alt grafı", "63 düğüm · 184 çift"))
    s.append(arrow(222, y + 263, 278, y + 263))

    s.append(box(540, y, 230, 120, "Özellik oluşturma", "protein 56 · kimya 5 · atom 44/14"))
    s.append(arrow(482, y + 98, 538, y + 60))

    s.append(box(540, y + 150, 230, 86, "A1P1 omurgası", "150 boyutlu temsil"))
    s.append(arrow(655, y + 120, 655, y + 148))
    s.append(arrow(482, y + 263, 538, y + 215))

    s.append(box(540, y + 280, 230, 86, "Tahmin başlığı", "Linear(150, K)"))
    s.append(arrow(655, y + 236, 655, y + 278))

    s.append(box(840, y + 280, 220, 86, "Sigmoid skor", "kayıt sıralama vekili"))
    s.append(arrow(772, y + 323, 838, y + 323))

    s.append(box(840, y + 400, 220, 86, "Abstention", "girdisiz ilaç → NaN"))
    s.append(arrow(950, y + 366, 950, y + 398))

    # sizinti siniri
    s.append(f'<path d="M 300 {y+480} L 1460 {y+480}" stroke="{WARN}" stroke-width="2" stroke-dasharray="8 5" fill="none"/>')
    s.append(note(306, y + 472, "SIZINTI SINIRI — bu çizginin altındaki hiçbir bilgi encoder'a girmez", fs=12, color=WARN))

    s.append(arrow(130, y + 416, 130, y + 500, "", color=WARN))
    s.append(box(40, y + 500, 260, 76, "Etiket matrisi y_ds", "yalnız kayıp fonksiyonunda", fill="#fdf1e7", stroke=WARN))
    s.append(arrow(300, y + 538, 650, y + 538, "", color=WARN, dash=True))
    s.append(box(650, y + 500, 260, 76, "BCEWithLogits", "gözlenen-kayıt vekili", fill="#fdf1e7", stroke=WARN))
    s.append(arrow(780, y + 498, 700, y + 368, "", color=WARN, dash=True))

    s.append(box(960, y + 500, 500, 76, "Hedef sözlüğü ve ölçekleyici: yalnız train bölmesi", "≥5 pozitif uygun ilaç · ≥2 bağımsız grup", fill="#fdf1e7", stroke=WARN))

    s.append(box(1120, y, 340, 120, "Dondurulmuş bölme", "5 dış × 3 iç · ilaç-ayrık"))
    s.append(box(1120, y + 150, 340, 110, "Query yolu", "görülmemiş protein kenarsız · geri mesaj yok"))
    s.append(arrow(1290, y + 120, 1290, y + 148))
    s.append(arrow(1118, y + 205, 775, y + 205, "", dash=True))

    s.append(note(40, H - 22, "Kanıt: fold_train_validation_test_scope.csv · side_effect_edges = False · heldout_drug_in_training = False (152/152)", fs=11.5))
    s.append("</svg>")
    return "".join(s)


def render(name, svg):
    OUT.mkdir(parents=True, exist_ok=True)
    svg_path = OUT / (name + ".svg")
    svg_path.write_text(svg, encoding="utf-8")
    png_path = OUT / (name + ".png")
    try:
        sys.path.insert(0, str(ROOT / ".deps/pymupdf"))
        import pymupdf

        doc = pymupdf.open(str(svg_path))
        doc[0].get_pixmap(dpi=150).save(str(png_path))
        size = png_path.stat().st_size // 1024
        print(f"  {svg_path.name} + {png_path.name} ({size} KB)")
    except Exception as exc:  # noqa: BLE001
        print(f"  {svg_path.name} yazildi; PNG uretilemedi: {exc}")


if __name__ == "__main__":
    print("WP14 diyagramlari:")
    render("01_mimari_karsilastirma", mimari())
    render("02_veri_akisi", akis())

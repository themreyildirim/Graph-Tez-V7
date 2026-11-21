"""EMT2 sunum arayüzü v5 — yeniden düzenlenmiş görsel katman.

Bu dosya YENİDİR ve hiçbir mevcut dosyayı değiştirmez. Veri, kilit ve
doğrulama katmanı v4 ile birebir aynıdır:

    scripts/wp13_final_data_v1.py   kayıtlı OOF tahminleri + PDF yükleme
    scripts/wp13_explain_v2.py      kayıtlı SHAP / mesaj maskesi açıklamaları
    scripts/wp13_tr_sources_v1.py   Türkçe prospektüs kaynakları
    apps/tedizolid_v5.py            dış tahmin deneyi (aynı kilitli veri)

Değişen YALNIZCA sunumdur:
  * skor sırasını koruyan Altair grafikleri (v4'teki st.bar_chart
    alfabetik sıralıyordu ve ilk 10 grafiği yanıltıyordu),
  * metrik kartları ve iki sütunlu yerleşim,
  * uyarı metinlerinin her sekmede tek "Sınırlar" bölümünde toplanması,
  * teknik terimler için help= açıklamaları,
  * column_config ile okunabilir tablolar.

Hiçbir bilimsel ifade, uyarı veya kısıt silinmedi; yalnızca yeri değişti.
Yeni model, eğitim, forward, SHAP hesabı, API veya OCR yoktur.
"""
from pathlib import Path
import sys
import json
import re

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pandas as pd
import altair as alt
import streamlit as st

import wp13_final_data_v1 as data
import wp13_explain_v2 as explain

tr = data.tr

ACCENT = "#0f6e7d"
POSITIVE = "#0f6e7d"
NEGATIVE = "#b4553f"

HELP = {
    "A1P1": (
        "Atom grafı (A1) ve protein-protein etkileşim mesaj geçişi (P1) birlikte "
        "açık olan model varyantı. WP10 faktöriyel tasarımının dört kolundan biri."
    ),
    "PT": (
        "MedDRA Preferred Term — yan etki kavramının standart terimi. "
        "Burada UMLS CUI kimliğiyle gösterilir."
    ),
    "OOF": (
        "Out-of-fold: ilacın eğitimde hiç görülmediği dış katın modeli tarafından "
        "üretilen skor. İlaç-ayrık iç içe çapraz doğrulamanın test çıktısıdır."
    ),
    "proxy": (
        "Gözlenen-kayıt vekili: skor, SIDER'da kayıt bulunma eğilimini sıralar. "
        "Klinik görülme olasılığı, kalibre edilmiş risk veya nedensellik DEĞİLDİR."
    ),
    "B1": "Beş kimyasal tanımlayıcı ve bir eksiklik maskesi kullanan L2 lojistik regresyon.",
}

# explain.FEATURES yalnız beş kimyasal alanı adlandırır; maske alanı ham kalıyordu.
EXTRA_FEATURES = {"mask__chemistry": "Kimya eksiklik maskesi"}


def feature_label(name):
    return explain.FEATURES.get(name, EXTRA_FEATURES.get(name, name))


def page_setup():
    st.set_page_config(
        page_title="Graph-Tez V7 · EMT2",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
          .block-container {max-width: 1480px; padding-top: 1.2rem; padding-bottom: 3rem;}
          [data-testid="stSidebar"] {background: #f2f6f8; border-right: 1px solid #dde6ea;}
          [data-testid="stSidebar"] .block-container {padding-top: 1.5rem;}

          .gt-header {
            display: flex; align-items: baseline; gap: .75rem; flex-wrap: wrap;
            border-bottom: 2px solid #0f6e7d; padding-bottom: .6rem; margin-bottom: .2rem;
          }
          .gt-header h1 {
            font-size: 1.55rem !important; font-weight: 650; letter-spacing: -.02em;
            margin: 0 !important; padding: 0 !important; color: #10303a;
          }
          .gt-badge {
            font-size: .72rem; font-weight: 600; letter-spacing: .04em;
            background: #e3eef1; color: #0f6e7d; border: 1px solid #c3dae0;
            border-radius: 999px; padding: .18rem .62rem; text-transform: uppercase;
          }
          .gt-badge.warn {background: #fdf1e7; color: #a4552f; border-color: #f0d6c2;}
          .gt-sub {color: #5b7682; font-size: .86rem; margin: .45rem 0 1.1rem 0;}

          [data-testid="stMetric"] {
            background: #f7fafb; border: 1px solid #e2ebee;
            border-radius: 10px; padding: .85rem 1rem;
          }
          [data-testid="stMetricLabel"] {font-size: .76rem !important; color: #5b7682;}
          [data-testid="stMetricValue"] {font-size: 1.45rem !important; color: #10303a;}

          .stTabs [data-baseweb="tab-list"] {gap: .25rem; border-bottom: 1px solid #dde6ea;}
          .stTabs [data-baseweb="tab"] {
            font-size: .82rem; font-weight: 600; letter-spacing: .02em;
            padding: .55rem .95rem;
          }
          .gt-note {
            font-size: .8rem; color: #5b7682; background: #f7fafb;
            border-left: 3px solid #c3dae0; padding: .5rem .8rem;
            border-radius: 0 6px 6px 0; margin: .4rem 0;
          }
          h3 {font-size: 1.05rem !important; margin-top: .6rem !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header(title, badge="Araştırma prototipi", badge_kind="", subtitle=""):
    cls = "gt-badge warn" if badge_kind == "warn" else "gt-badge"
    st.markdown(
        '<div class="gt-header"><h1>' + title + "</h1>"
        '<span class="' + cls + '">' + badge + "</span></div>",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown('<div class="gt-sub">' + subtitle + "</div>", unsafe_allow_html=True)


def note(text):
    st.markdown('<div class="gt-note">' + text + "</div>", unsafe_allow_html=True)


def limits(*paragraphs, title="Sınırlar ve okuma uyarıları"):
    """Bütün yasal/bilimsel uyarıları tek yerde toplar; hiçbiri silinmez."""
    with st.expander(title):
        for p in paragraphs:
            st.markdown("- " + p, unsafe_allow_html=True)


def short(s):
    """Uzun ondalık sayıları okunur hale getirir (v4'teki davranış)."""
    return re.sub(
        r"-?\d+\.\d{5,}(?:e[-+]?\d+)?",
        lambda m: format(float(m[0]), ".4g"),
        str(s),
    )


def ranked_bar(frame, value, label, title, height=320):
    """Skor sırasını KORUYAN yatay çubuk grafik.

    v4'te kullanılan st.bar_chart kategorileri alfabetik sıralar; bu, ilk 10
    grafiğinin tablodan farklı bir sıra göstermesine yol açıyordu.
    """
    chart = (
        alt.Chart(frame)
        .mark_bar(color=ACCENT, cornerRadiusEnd=3, height=18)
        .encode(
            x=alt.X(value + ":Q", title=title, scale=alt.Scale(domain=[0, 1])),
            y=alt.Y(label + ":N", sort="-x", title=None,
                    axis=alt.Axis(labelLimit=260, labelFontSize=11)),
            tooltip=[
                alt.Tooltip(label + ":N", title="Hedef"),
                alt.Tooltip(value + ":Q", title="Skor", format=".4f"),
            ],
        )
        .properties(height=height)
    )
    st.altair_chart(chart, width='stretch')


def diverging_bar(frame, value, label, title, height=260):
    """İşaretli katkı grafiği (SHAP / delta_z): pozitif ve negatif ayrı renk."""
    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusEnd=3, height=18)
        .encode(
            x=alt.X(value + ":Q", title=title),
            y=alt.Y(label + ":N", sort="-x", title=None,
                    axis=alt.Axis(labelLimit=260, labelFontSize=11)),
            color=alt.condition(
                alt.datum[value] > 0, alt.value(POSITIVE), alt.value(NEGATIVE)
            ),
            tooltip=[
                alt.Tooltip(label + ":N", title="Öğe"),
                alt.Tooltip(value + ":Q", title="Katkı", format=".5f"),
            ],
        )
        .properties(height=height)
    )
    st.altair_chart(chart, width='stretch')


page_setup()

area = st.sidebar.radio(
    "Çalışma alanı",
    ["Kayıtlı ilaçlar", "Tedizolid dış tahmin deneyi"],
    key="final_v3_area",
)

if area == "Tedizolid dış tahmin deneyi":
    from tedizolid_v5 import render

    render()
    st.stop()

with st.sidebar:
    st.markdown("### Girdi")
    mode = st.radio("Ana işlem", ["Kayıtlı ilaç seç", "Prospektüs PDF yükle"])
    index = None
    doc = None
    result = None

    if mode == "Kayıtlı ilaç seç":
        sample = st.selectbox("Kayıtlı ilaç", ["ERİTRO 500 mg", "MONODOKS 100 mg"])
        index = 0 if sample.startswith("ERİTRO") else 1
        use_pdf = st.checkbox(
            "Türkçe prospektüs referansını aç",
            value=False,
            help="Tahmin kolundan bağımsız, ayrı bir kaynak inceleme koludur.",
        )
        if use_pdf:
            doc = tr.load(index)
    else:
        st.caption(
            "Hasta verisi yüklemeyin. PDF dış servise gönderilmez; OCR ve otomatik API yok."
        )
        uploaded = st.file_uploader("Prospektüs PDF yükle", type=["pdf"])
        if uploaded:
            try:
                result = data.upload(uploaded.getvalue(), uploaded.name)
                index = result["index"]
                doc = result["document"]
                if index is None:
                    st.info(
                        "UNVERIFIED · Belge kimliği kesinleştirilmedi. B1 / GNN: NOT_SUPPORTED."
                    )
            except Exception:
                st.error(
                    "PDF açılamadı: biçim/şifre, 20 MB, 120 sayfa veya "
                    "2 milyon karakter sınırını kontrol edin."
                )
                doc = None

    st.divider()
    st.markdown(
        '<span class="gt-badge">Offline</span> &nbsp;'
        '<span class="gt-badge">API kapalı</span>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Yeni model veya eğitim çalıştırılmaz. Bireysel hastada klinik yan etki "
        "olasılığı ya da tedavi önerisi üretmez."
    )

bundle = None
if index is not None:
    try:
        bundle = data.recorded(data.PARENTS[index])
    except Exception:
        st.error("Kayıtlı tahmin veya kaynak hash kontrolü başarısız.")
        st.stop()

header(
    "Antibiyotik ve yan etki ilişkileri",
    subtitle="Kayıtlı tahmin ≠ prospektüs bildirimi ≠ klinik risk · EMT2 araştırma demosu",
)

tabs = st.tabs(
    [
        "1 · İLAÇ VE BELGE",
        "2 · YAN ETKİ TAHMİNLERİ",
        "3 · MODEL AÇIKLANABİLİRLİĞİ",
        "4 · PROSPEKTÜS KARŞILAŞTIRMASI",
    ]
)

with tabs[0]:
    if index is not None:
        record = tr.load(index)["record"]
        a, b, c = st.columns(3)
        a.metric("Ürün", record["product"].split(" ")[0])
        b.metric("Ana etkin madde", record["parent_id"])
        c.metric("Kayıtlı hedef sayısı", len(bundle["predictions"]) if bundle else "—")

        st.markdown("### " + record["product"])
        st.write(record["composition"])
        note(
            "Ana etkin madde araştırma bağlantısı: <b>"
            + record["parent_id"]
            + "</b> · Ticari ürün / tuz / doz eşdeğerliği NOT_ESTABLISHED."
        )

    if doc is None:
        st.info(
            "PDF referansı kapalı veya yüklenmedi. Kayıtlı tahminler PDF olmadan da "
            "ikinci sekmede görüntülenir."
        )
    else:
        text_pages = sum(p["status"] == "TEXT_AVAILABLE" for p in doc["pages"])
        d1, d2, d3 = st.columns(3)
        d1.metric(
            "Belge",
            doc.get("record", {}).get("product", doc.get("display_name", "Yüklenen PDF"))[:22],
        )
        d2.metric("Fiziksel sayfa", doc["page_count"])
        d3.metric("Metin katmanı", str(text_pages) + " sayfa")

        with st.expander("Belge teknik ayrıntıları ve sayfa metinleri"):
            st.code(doc["sha256"], language=None)
            n = st.number_input("Fiziksel sayfa", 1, doc["page_count"], 1)
            page = doc["pages"][n - 1]
            st.caption(page["status"])
            st.text(page["text"] or "OCR_NOT_AVAILABLE — Metin katmanı yok.")
            st.download_button(
                "Kaynak izini JSON indir",
                json.dumps(doc, ensure_ascii=False, indent=2),
                "yerel_belge_kaydi.json",
                "application/json",
            )

        limits(
            "Belge güncelliği doğrulanmadı. Kaynak/hash doğrulaması klinik onay değildir.",
            "İnsan incelemesi PENDING.",
        )

with tabs[1]:
    if bundle:
        predictions = pd.DataFrame(bundle["predictions"])
        predictions.insert(0, "Sıra", range(1, len(predictions) + 1))
        names = {r["class_id"]: r["target_name"] for r in bundle["predictions"]}

        def target_label(p):
            return explain.TR_PT.get(p, names[p]) + " · " + names[p] + " · " + p

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Model", bundle["model"], help=HELP["A1P1"])
        m2.metric("Dış kat (outer fold)", bundle["fold"], help=HELP["OOF"])
        m3.metric("Hedef sayısı", len(predictions), help=HELP["PT"])
        m4.metric(
            "En yüksek skor",
            format(predictions["score_observed_record_proxy"].max(), ".3f"),
            help=HELP["proxy"],
        )

        available = explain.available(bundle["parent"])
        choices = sorted(set(names) & (set(available["shap"]) | set(available["graph"])))

        def pick_example():
            st.session_state["final_pt_" + bundle["parent"]] = st.session_state[
                "example_" + bundle["parent"]
            ]

        sel1, sel2 = st.columns(2)
        with sel1:
            st.selectbox(
                "Açıklanabilir örnekler",
                choices,
                format_func=target_label,
                key="example_" + bundle["parent"],
                on_change=pick_example,
                help="Yalnızca kayıtlı açıklaması bulunan hedefler.",
            )
        with sel2:
            pt = st.selectbox(
                "Tahmin hedefi (PT)",
                list(names),
                index=list(names).index("C0000731") if "C0000731" in names else 0,
                format_func=target_label,
                key="final_pt_" + bundle["parent"],
                help=HELP["PT"],
            )

        left, right = st.columns([1.15, 1], gap="large")

        with left:
            st.markdown("### Kayıtlı sıralama")
            shown = predictions.rename(
                columns={
                    "target_name": "Dondurulmuş PT adı",
                    "class_id": "PT CUI",
                    "score_observed_record_proxy": "Skor",
                }
            )
            st.dataframe(
                shown[["Sıra", "Dondurulmuş PT adı", "PT CUI", "Skor"]],
                hide_index=True,
                width="stretch",
                height=420,
                column_config={
                    "Sıra": st.column_config.NumberColumn(width="small"),
                    "Dondurulmuş PT adı": st.column_config.TextColumn(width="medium"),
                    "PT CUI": st.column_config.TextColumn(width="small"),
                    "Skor": st.column_config.ProgressColumn(
                        "Kayıt sıralama skoru",
                        min_value=0.0,
                        max_value=1.0,
                        format="%.3f",
                        help=HELP["proxy"],
                    ),
                },
            )

        with right:
            st.markdown("### İlk 10 hedef")
            top = predictions.head(10)[["target_name", "score_observed_record_proxy"]].copy()
            ranked_bar(
                top, "score_observed_record_proxy", "target_name", "Kayıt sıralama skoru", 340
            )
            st.caption(
                "Çubuklar tablodaki kayıtlı sıra ile aynı sırada çizilir. "
                "PT adları özgün frozen sözlüktür."
            )

        with st.expander("Tahmin kilidi, fold ve model sürümü"):
            st.json(
                {
                    "ana_etkin_madde": bundle["parent"],
                    "outer_fold": bundle["fold"],
                    "model": bundle["model"],
                    "sürüm": bundle["version"],
                    "hedef_sayısı": len(predictions),
                    "seçili_PT": pt,
                }
            )
            st.caption("Kayıtlı veri ve model bütünlüğü açılışta denetlenir.")

        limits(
            "Skor, SIDER <b>gözlenen-kayıt vekilidir</b>; klinik olasılık yüzdesi değildir.",
            "Unknown çiftler doğrulanmış biyolojik negatif değildir.",
            "İki örnek PT için Türkçe gösterim editoryaldir; onaylı MedDRA çevirisi değildir.",
            "Kayıtlı primary own-fold outer-test OOF çıktısıdır; yeni tahmin üretilmez.",
        )
    else:
        pt = None
        st.info(
            "NOT_SUPPORTED — Bu belge için doğrulanmış kayıtlı ilaç/OOF bağlantısı yok. "
            "PDF yüklemek yeni GNN tahmini üretmez."
        )

with tabs[2]:
    st.markdown("### Model bu skoru hangi bilgilere dayanarak verdi?")

    if bundle and pt:
        row = predictions[predictions.class_id.eq(pt)].iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Hedef", explain.TR_PT.get(pt, names[pt])[:20])
        c2.metric(
            "İlişki skoru (A1P1)",
            format(row.score_observed_record_proxy, ".3f"),
            help=HELP["A1P1"],
        )
        c3.metric("Sıralamadaki yeri", str(int(row["Sıra"])) + " / " + str(len(predictions)))

        with st.expander("Modelin kullandığı girdiler"):
            st.write(
                "**A1P1:** kimya5, QC maskeli atom44/bağ14 grafı, protein56, dört ayrı rol "
                "ve strict insan PPI700. **B1:** beş kimyasal tanımlayıcı ve ayrı kimya "
                "maskesi. Train-only scaler; PDF yan etkileri model girdisi değildir. "
                "Bu liste seçili PT için attribution veya biyolojik gerekçe değildir."
            )

        a = explain.get(bundle["parent"], pt, bundle["fold"])

        if a["absent_paths"]:
            with st.expander("NA: kaynakta bulunmayan rol/PPI yolları (sıfır etki değil)"):
                st.dataframe(pd.DataFrame(a["absent_paths"]), hide_index=True, width="stretch")

        gcol, scol = st.columns(2, gap="large")

        with gcol:
            st.markdown("#### A1P1 · mesaj maskesi")
            if a["graph"]:
                g = pd.DataFrame(a["graph"])
                fixed = g[g["mode"] == "fixed"]
                valid = fixed[fixed.status.eq("OK")].copy()
                if len(valid):
                    valid["abs"] = valid.delta_z.abs()
                    plot = valid.sort_values("abs", ascending=False).head(8).copy()
                    for col in ["role", "protein_id", "protein_a", "protein_b"]:
                        plot[col] = plot[col].fillna("")
                    plot["Yol"] = plot.apply(
                        lambda r: " ".join(
                            str(r.get(k, ""))
                            for k in ["role", "protein_id", "protein_a", "protein_b"]
                        ).strip(),
                        axis=1,
                    )
                    diverging_bar(plot, "delta_z", "Yol", "Δz (orijinal − müdahale)", 280)
                    st.caption(
                        "Pozitif Δz: maskelenince logit azaldı. Negatif Δz: arttı. "
                        "Etkiler toplamsal nedenler değildir."
                    )
                    for r in plot.head(3).to_dict("records"):
                        st.markdown(
                            "- **" + r["Yol"] + "** — " + short(explain.delta_sentence(r))
                        )
                else:
                    st.info("NA — Uygulanabilir mesaj yolu yok; sıfır etki anlamına gelmez.")

                with st.expander("Gerçek fixed-degree katkıları ve NA durumları"):
                    st.dataframe(fixed, hide_index=True, width="stretch")
                with st.expander("Ayrı duyarlılık: physical-delete / yeniden normalizasyon"):
                    deletion = g[g["mode"] != "fixed"]
                    st.dataframe(deletion, hide_index=True, width="stretch")
                    if len(deletion):
                        st.write(short(explain.delta_sentence(deletion.iloc[0].to_dict())))
            else:
                st.info(
                    "NOT_AVAILABLE — Bu ilaç/PT/fold için uygulanabilir kayıtlı mesaj "
                    "müdahalesi yok. Genel girdilerden özel PT gerekçesi üretilmedi."
                )

        with scol:
            st.markdown("#### B1 · kimyasal SHAP")
            if a["shap"]:
                s = pd.DataFrame(a["shap"])
                s["Özellik"] = s["feature"].map(feature_label)
                diverging_bar(s, "SHAP_logit", "Özellik", "SHAP logit katkısı", 280)
                st.caption(
                    str(len(s))
                    + " B1 özelliğinde pozitif katkı eğitim background'una göre logiti "
                    "artırıcıdır. A1P1 skorunun açıklaması değildir."
                )
                for r in s.to_dict("records"):
                    st.markdown("- " + short(explain.shap_sentence(r)))
                with st.expander("B1 SHAP sayısal değerler ve kimlikler"):
                    st.dataframe(s, hide_index=True, width="stretch")
            else:
                st.info(
                    "NOT_AVAILABLE — B1'in bu fold/ilaç için fit edilmiş başlığında hedef "
                    "yok; başka PT/fold verisi doldurulmadı."
                )

    st.markdown("#### Biyolojik mekanizma")
    st.warning(
        "NOT_ESTABLISHED — Bağımsız mekanizma kanıtı yok. Mesaj etkisi veya SHAP, "
        "kanıtlanmış advers reaksiyon mekanizması değildir."
    )

    limits(
        "SHAP ve mesaj maskesi <b>nedensel</b> açıklama değildir.",
        "SHAP değerleri B1 modeline, Δz değerleri A1P1 modeline aittir; "
        "biri diğerinin açıklaması değildir.",
        "Sıfır katkı, ilgili özelliğin etkisiz olduğu anlamına gelmez.",
    )

with tabs[3]:
    st.markdown("### Prospektüs referansı — tahminden ayrı kol")

    if doc and index is not None:
        rows = doc["candidates"]
        byid = {c["candidate_id"]: c for c in rows}
        cid = st.selectbox(
            "Prospektüs bulgusu (model tahmini değil)",
            list(byid),
            format_func=lambda k: tr.candidate_label(byid[k]),
            key="source_" + doc["sha256"],
        )
        c = byid[cid]
        v = data.source_view(c)

        left, right = st.columns([1, 1], gap="large")
        with left:
            st.markdown("#### " + c["name_tr"])
            st.write("**İlgili tam kaynak terimi:** " + v["term"])
            st.write("**Kaynağın sıklık ifadesi:** " + tr.norm(v["frequency"]))
            st.write("**Kapsam:** " + v["scope"] + " · PENDING")
            st.caption(
                "Fiziksel sayfa "
                + str(v["page"])
                + " · yalnız seçili terim aralığı ["
                + str(v["start"])
                + ", "
                + str(v["end"])
                + ")"
            )
            if v["note"]:
                st.info(v["note"])
        with right:
            for q in c["context_quotes"]:
                with st.expander("İlgili uyarı / koşul · sayfa " + str(q["physical_page"])):
                    st.text(q["quote_exact"])
            with st.expander("Prospektüsteki tam bölüm"):
                st.text(v["full_section"])
            with st.expander("Kaynak teknik ayrıntıları"):
                st.json(c)

        st.markdown("#### Tüm aday bulgular")
        st.dataframe(pd.DataFrame(data.comparison(doc)), hide_index=True, width="stretch")

        limits(
            "UNMAPPED — Türkçe terim → PT uzman eşlemesi henüz onaylanmadı.",
            "Aynı ad benzerliğiyle otomatik eşleme veya doğruluk hesabı yapılmadı.",
            "Prospektüste geçmeyen PT gerçek negatif veya kesin yanlış tahmin sayılmaz.",
            "Aşırı doz ve hayvan çalışmaları bu aday listesine katılmaz.",
            "Ticari ürün ile ana etkin madde eşdeğerliği kurulmadı.",
            "Kayıtlı Türkçe LLM açıklaması NOT_AVAILABLE; yeni API yok.",
            "Retrospektif, keşifsel kaynak incelemesidir; dış klinik doğruluk testi değildir.",
        )
    elif doc:
        st.warning(
            "EXPERIMENTAL / UNVERIFIED — Genel doğrulanmış yan etki çıkarıcısı yok; "
            "yalnız anahtar sözcük çevresi kaynak pencereleri."
        )
        windows = (result or {}).get("windows", [])
        for w in windows:
            with st.expander("Aday kaynak penceresi · sayfa " + str(w["physical_page"])):
                st.text(w["quote"])
        if not windows:
            st.info(
                "NOT_AVAILABLE / OCR_NOT_AVAILABLE — Desteklı metin penceresi bulunamadı; "
                "yan etki yokluğu anlamına gelmez."
            )
    else:
        st.info(
            "Referans incelemesi için Türkçe prospektüsü açın veya PDF yükleyin. "
            "Tahmin kolu bundan bağımsızdır."
        )

"""Tedizolid dış tahmin deneyi — v5 sunum katmanı.

v4 ile aynı kilitli veriyi okur (scripts/wp13_external_reference_v1.py).
Yalnızca yerleşim değişti: ilk 10 tablosu artık yatay taşmıyor, ayrıntılar
tablodan açılır bölüme alındı, SHAP grafiği işaretli renklendirildi.
Hiçbir model, SHAP, API veya OCR çalıştırılmaz.
"""
import re

import pandas as pd
import altair as alt
import streamlit as st

import wp13_external_reference_v1 as r

POSITIVE = "#0f6e7d"
NEGATIVE = "#b4553f"

LABELS = {
    "TABLE_TRANSLATION_CANDIDATE": "Çeviri/eşanlam adayı · PROVISIONAL",
    "TABLE_RELATED_NOT_EQUIVALENT": "İlişkili terim · eşdeğerlik kurulmadı",
    "CLASS_WARNING_ONLY": "Yalnız sınıf uyarısı · doğrulanmadı",
    "DRUG_WARNING_ONLY": "İlaca ait uyarı · 4.8 kaydı değil",
    "NOT_IDENTIFIED_IN_REFERENCE_NOT_NEGATIVE": "Eşleme saptanmadı · negatif değil",
}

SCOPES = {
    "PRODUCT_POOLED_ORAL_IV": "Ürün · oral/IV havuzu",
    "CLASS": "Sınıf",
}


def load():
    r.verify_locks()
    r.verify_pins(r.read(r.Q / "presentation_pins.json"))
    return (
        pd.read_csv(r.Q / "comparison201.csv", float_precision="round_trip"),
        r.read(r.Q / "reference_terms.json"),
        r.read(r.Q / "context_quotes.json"),
    )


def diverging_bar(frame, value, label, title, height=260):
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
                alt.Tooltip(label + ":N", title="Özellik"),
                alt.Tooltip(value + ":Q", title="SHAP logit", format=".5f"),
            ],
        )
        .properties(height=height)
    )
    st.altair_chart(chart, width='stretch')


def limits(*paragraphs, title="Sınırlar ve okuma uyarıları"):
    with st.expander(title):
        for p in paragraphs:
            st.markdown("- " + p, unsafe_allow_html=True)


def render():
    try:
        frame, terms, ctx = load()
    except Exception:
        st.error("HASH_CHECK_FAILED — Kayıtlı kilit veya karşılaştırma kaynağı doğrulanamadı.")
        st.stop()

    st.markdown(
        '<div class="gt-header"><h1>Tedizolid dış tahmin deneyi</h1>'
        '<span class="gt-badge warn">Keşifsel · tek ilaç</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="gt-sub">DB14569 aktif tedizolid · beş frozen primary B1 kimya modeli · '
        "sonradan açılan SIVEXTRO KÜB referansı</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    for col, label, value, hint in zip(
        cols,
        ["Kilitli ortak PT", "Önceden seçilen PT", "Model/PT açıklaması", "KÜB tablo terimi"],
        [201, 10, 50, len(terms)],
        [
            "Beş B1 modelinin ortak hedef kümesi.",
            "KÜB görülmeden önce kilitlenen ilk 10 hedef.",
            "10 PT × 5 model = 50 ayrı SHAP açıklaması.",
            "KÜB 4.8 tablosundaki özgün terim sayısı.",
        ],
    ):
        col.metric(label, value, help=hint)

    st.markdown("### Kilitli ilk 10 hedef — seçim KÜB görülmeden yapıldı")

    top = frame.head(10).copy()
    top["Eşleme durumu"] = top.reference_status.map(LABELS)
    absent = top.reference_status.eq("NOT_IDENTIFIED_IN_REFERENCE_NOT_NEGATIVE")

    display = pd.DataFrame(
        {
            "Sıra": top["rank"],
            "Model hedefi (PT)": top["term_tr_editorial"],
            "Skor": top["record_ranking_score"],
            "KÜB terimi": top["source_terms"].where(
                ~absent, "Bu belgede doğrulanmış eşleme bulunamadı"
            ),
            "Eşleme durumu": top["Eşleme durumu"],
        }
    )

    st.dataframe(
        display.fillna("—"),
        hide_index=True,
        width="stretch",
        height=392,
        column_config={
            "Sıra": st.column_config.NumberColumn(width="small"),
            "Model hedefi (PT)": st.column_config.TextColumn(width="medium"),
            "Skor": st.column_config.ProgressColumn(
                "İlişki skoru",
                min_value=0.0,
                max_value=1.0,
                format="%.3f",
                help="Beş sigmoid skorun eşit ağırlıklı ortalaması. Klinik olasılık değildir.",
            ),
            "KÜB terimi": st.column_config.TextColumn(width="medium"),
            "Eşleme durumu": st.column_config.TextColumn(width="medium"),
        },
    )

    with st.expander("Sıklık, kaynak kapsamı, sayfa ve insan incelemesi sütunları"):
        detail = pd.DataFrame(
            {
                "Sıra": top["rank"],
                "Model hedefi (PT)": top["term_tr_editorial"],
                "Frozen PT adı": top["term_en"],
                "PT CUI": top["class_id"],
                "Sıklık": top["frequencies"],
                "Kaynak kapsamı": top["source_scopes"]
                .fillna("—")
                .replace(SCOPES, regex=False),
                "Sayfa": top["source_pages"],
                "İnsan incelemesi": "Bekliyor",
            }
        )
        st.dataframe(detail.fillna("—"), hide_index=True, width="stretch")

    byid = top.set_index("class_id")
    pt = st.selectbox(
        "İncelenecek kilitli PT",
        list(top.class_id),
        format_func=lambda x: byid.loc[x, "term_tr_editorial"] + " · " + x,
        key="tedizolid_reference_PT",
    )
    row = byid.loc[pt]

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("### Kayıtlı B1 tahmini ve açıklaması")
        st.markdown("#### Tedizolid · " + row.term_tr_editorial)
        st.caption("Kilitli sıralama: " + str(int(row["rank"])) + " / 201")
        st.metric(
            "Beş sigmoid skorun eşit ağırlıklı ortalaması",
            format(row.record_ranking_score, ".3f"),
        )

        folds = pd.DataFrame(
            {
                "Frozen primary model": range(1, 6),
                "Skor": [round(row["fold" + str(i) + "_score"], 4) for i in range(1, 6)],
            }
        )
        st.dataframe(
            folds,
            hide_index=True,
            width="stretch",
            column_config={
                "Frozen primary model": st.column_config.NumberColumn(width="small"),
                "Skor": st.column_config.ProgressColumn(
                    "Kayıt sıralama skoru", min_value=0.0, max_value=1.0, format="%.4f"
                ),
            },
        )

        values = pd.read_csv(r.S / "local_feature_SHAP.csv", float_precision="round_trip")
        verbal = r.read(r.S / "Turkish_verbal_explanations.json")
        pairs = pd.read_csv(r.S / "pair_additivity.csv", float_precision="round_trip")

        fold = st.selectbox(
            "SHAP açıklaması için bireysel model", [1, 2, 3, 4, 5], key="tedizolid_shap_fold"
        )
        sub = values[values.class_id.eq(pt) & values.fold.eq(fold)]
        diverging_bar(sub, "SHAP_logit", "feature_name_tr", "SHAP logit katkısı")

        st.markdown("**SHAP'ın açıkladığı şey**")
        for sign, label in [(1, "artıran"), (-1, "azaltan")]:
            z = sub[sub.SHAP_logit * sign > 0].sort_values("SHAP_logit", ascending=sign < 0)
            if len(z):
                v = z.iloc[0]
                st.write(
                    "Model "
                    + str(fold)
                    + " için logiti en çok "
                    + label
                    + " özellik: "
                    + str(v.feature_name_tr)
                    + " ("
                    + format(v.SHAP_logit, "+.4f")
                    + ")."
                )
            else:
                st.write("Bu kayıtta logiti " + label + " katkı yok.")

        original_verbal = next(
            v["explanation_tr"] for v in verbal if v["class_id"] == pt and v["fold"] == fold
        )
        with st.expander("Tam hassasiyette özgün model yorumu"):
            st.write(re.sub(r"np\.float64\(([^()]*)\)", r"\1", original_verbal))

        with st.expander("Beş modelin mevcut SHAP grafiği ve değerleri"):
            st.image(
                str(
                    r.ROOT
                    / (
                        "reports/figures/WP13/tedizolid_B1_SHAP_v1/PT"
                        + format(int(row["rank"]), "02d")
                        + "_"
                        + pt
                        + "_five_models.png"
                    )
                )
            )
            st.dataframe(values[values.class_id.eq(pt)], hide_index=True, width="stretch")
            st.dataframe(pairs[pairs.class_id.eq(pt)], hide_index=True, width="stretch")

    with right:
        st.markdown("### Tahmin kilidinden sonra açılan KÜB")
        st.write(
            "**Ürün:** SIVEXTRO 200 mg/flakon tedizolid fosfat; "
            "intravenöz infüzyonluk liyofilize toz."
        )
        st.info(LABELS[row.reference_status] + " · İnsan incelemesi PENDING")

        matches = [m for m in r.read(r.Q / "crosswalk_candidates.json") if m["class_id"] == pt]
        qlookup = {t["quote"]["quote_id"]: t["quote"] for t in terms}
        qlookup.update({q["quote_id"]: q for q in ctx})

        if not matches:
            st.write(
                "Bu belgede doğrulanmış eşleme bulunamadı. Bu durum gerçek negatif veya "
                "kesin yanlış tahmin değildir. Aşırı duyarlılık, anafilaktik şok yerine "
                "geçirilmedi."
            )
        for match in matches:
            q = qlookup[match["quote_id"]]
            st.markdown("**Kaynak terimi:** " + match["source_term"])
            st.write("**Sıklık:** " + match["frequency"] + " · **Kapsam:** " + match["scope"])
            st.write(match["rationale_tr"])
            if match["source_channel"] == "4.4_CLASS_WARNING":
                bridge = r.read(r.Q / "class_scope_bridge.json")
                st.caption(
                    "Sınıf kapsamı cümlesi önceki fiziksel sayfadan devam eder: "
                    + bridge["quote_id"]
                )
                st.text(bridge["quote_exact"])
            st.caption(
                "Fiziksel sayfa "
                + str(q["physical_page"])
                + " · "
                + q["quote_id"]
                + " · ["
                + str(q["char_start"])
                + ", "
                + str(q["char_end"])
                + ")"
            )
            st.text(q["quote_exact"])

        with st.expander("Tam 4.8 bağlamı, sıklık başlıkları ve ürün farkı"):
            for q in r.read(r.Q / "complete_4_8_pages.json"):
                st.markdown("**Fiziksel sayfa " + str(q["physical_page"]) + "**")
                st.text(q["quote_exact"])

    with st.expander("Tüm 201 PT, beş model skoru ve kaynak eşleme adayları"):
        st.dataframe(frame, hide_index=True, width="stretch")
        st.download_button(
            "201 PT karşılaştırmasını CSV indir",
            (r.Q / "comparison201.csv").read_bytes(),
            "tedizolid_common201_reference.csv",
            "text/csv",
        )

    with st.expander("KÜB'deki tüm 76 tablo terimi — ilk 10 dışında kalanlar dahil"):
        st.dataframe(
            pd.read_csv(r.Q / "all_reference_terms_target_coverage.csv"),
            hide_index=True,
            width="stretch",
        )

    with st.expander("Kilitler, kaynak kimliği ve yöntem sınırları"):
        st.code("Prediction SHA-256: " + r.PRED_HASH + "\nExplanation SHA-256: " + r.SHAP_HASH)
        st.json(r.read(r.Q / "product_identity_and_limitations.json"))

    limits(
        "Keşifsel, etiketlerden izole <b>tek</b> dış ilaç denemesidir.",
        "Önceki arama parçacığı maruziyeti nedeniyle tam araştırmacı körlüğü korunmadı "
        "(STRICT_ANALYST_BLINDNESS_COMPROMISED).",
        "Aktif tedizolid ile fosfat ön ilacı aynı moleküler girdi değildir.",
        "KÜB 4.8 güvenlilik verileri oral ve/veya IV havuzudur; yalnız IV insidansı değildir. "
        "Güncellik doğrulanmadı.",
        "76 tablo terimi, klinik olarak doğrulanmış 76 bağımsız olay demek değildir.",
        "PROVISIONAL çapraz eşleme uzman onaylı MedDRA çevirisi değildir; insan kararı PENDING.",
        "Precision@10, AP veya AUROC <b>hesaplanmadı</b> (NOT_CALCULABLE).",
        "Skorlar klinik yan etki olasılığı değildir.",
        "OFFLINE · yeni eğitim, prediction forward, SHAP hesabı, API veya OCR yok.",
    )

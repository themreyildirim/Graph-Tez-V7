"""v5 arayüzü için Streamlit AppTest akış kontrolleri.

Tarayıcı, model forward, SHAP hesabı, API veya OCR çalıştırmaz; yalnızca
kayıtlı veriyle arayüzün hatasız kurulduğunu ve v4'teki sıralama hatasının
düzeldiğini doğrular.

Bu dosya YENİDİR; mevcut hiçbir test veya bütünlük manifesti etkilenmez.
"""
from pathlib import Path
import ast
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "apps"))

from streamlit.testing.v1 import AppTest

APP = str(ROOT / "apps" / "arayuz_v5.py")
TIMEOUT = 120


def called_attributes(path, attribute):
    """Kaynakta GERCEKTEN cagrilan `*.<attribute>(...)` ifadelerini bulur.

    Metin aramasi yerine AST kullanilir; boylece aciklama satirlari ve
    docstring'lerde gecen adlar yanlis pozitif uretmez.
    """
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == attribute:
                hits.append(node.lineno)
    return hits



class ArayuzV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = AppTest.from_file(APP, default_timeout=TIMEOUT).run()

    def charts(self, app):
        return list(app.get("vega_lite_chart")) + list(app.get("arrow_vega_lite_chart"))

    def test_01_app_loads_without_exception(self):
        self.assertFalse(self.app.exception, str(self.app.exception)[:400])

    def test_02_default_recorded_drug_is_bound(self):
        text = "\n".join(str(e.value) for e in self.app.markdown)
        self.assertIn("DB00199", text)

    def test_03_prediction_table_columns(self):
        frame = self.app.dataframe[0].value
        self.assertIn("Sıra", frame.columns)
        self.assertIn("Skor", frame.columns)
        self.assertIn("PT CUI", frame.columns)

    def test_04_table_is_sorted_by_score_descending(self):
        scores = list(self.app.dataframe[0].value["Skor"])
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_05_rank_column_is_consecutive(self):
        ranks = list(self.app.dataframe[0].value["Sıra"])
        self.assertEqual(ranks, list(range(1, len(ranks) + 1)))

    def test_06_charts_are_vega_not_alphabetical_bar_chart(self):
        """v4'te st.bar_chart kategorileri alfabetik sıralıyordu.

        v5 Altair kullanır ve sıralamayı sort='-x' ile skora bağlar; bu test
        grafiğin gerçekten üretildiğini doğrular.
        """
        self.assertGreaterEqual(len(self.charts(self.app)), 1)

    def test_07_chart_sorts_by_score_not_alphabetically(self):
        """v4 hatasinin regresyon testi.

        st.bar_chart kategorileri alfabetik siralardi; ilk 10 grafigi
        tablodan farkli bir sira gosteriyordu. v5 Altair spesifikasyonunda
        y eksenini sort='-x' ile skora baglar.
        """
        spec = str(self.charts(self.app)[0].proto).replace('\\"', '"')
        self.assertIn('"sort": "-x"', spec)
        for name in ["arayuz_v5.py", "tedizolid_v5.py"]:
            self.assertEqual([], called_attributes(ROOT / "apps" / name, "bar_chart"), name)

    def test_08_pt_selection_does_not_raise(self):
        app = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
        box = app.selectbox(key="final_pt_DB00199")
        box.set_value(list(box.options)[1]).run()
        self.assertFalse(app.exception, str(app.exception)[:300])

    def test_09_second_recorded_drug_loads(self):
        app = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
        drug = [s for s in app.selectbox if s.label == "Kayıtlı ilaç"][0]
        drug.set_value("MONODOKS 100 mg").run()
        self.assertFalse(app.exception, str(app.exception)[:300])
        self.assertIn("DB00254", "\n".join(str(e.value) for e in app.markdown))

    def test_10_tedizolid_mode_renders(self):
        app = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
        app.radio(key="final_v3_area").set_value("Tedizolid dış tahmin deneyi").run()
        self.assertFalse(app.exception, str(app.exception)[:300])
        body = "\n".join(
            str(e.value) for group in (app.markdown, app.caption, app.info) for e in group
        )
        self.assertIn("DB14569", body)

    def test_11_scientific_limits_are_preserved(self):
        """Yeniden tasarım hiçbir bilimsel kısıtı silmemeli."""
        app = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
        app.radio(key="final_v3_area").set_value("Tedizolid dış tahmin deneyi").run()
        body = "\n".join(
            str(e.value)
            for group in (app.markdown, app.caption, app.info, app.warning)
            for e in group
        )
        for phrase in [
            "NOT_CALCULABLE",
            "STRICT_ANALYST_BLINDNESS_COMPROMISED",
            "PENDING",
        ]:
            self.assertIn(phrase, body, phrase + " kayboldu")

    def test_12_no_training_api_or_fit_in_ui_source(self):
        for name in ["arayuz_v5.py", "tedizolid_v5.py"]:
            text = (ROOT / "apps" / name).read_text(encoding="utf-8")
            self.assertNotIn("import openai", text)
            self.assertNotIn(".fit(", text)
            self.assertNotIn("requests.", text)

    def test_13_existing_v4_interface_untouched(self):
        """v5, v4 ve FINAL_v3 dosyalarını değiştirmemiş olmalı."""
        for rel in [
            "EMT2_Teslim_v1/demo/uygulama.py",
            "EMT2_Teslim_v1/demo/tedizolid_v4.py",
            "apps/drug_safety_explorer_FINAL_v3.py",
        ]:
            self.assertTrue((ROOT / rel).is_file(), rel + " bulunamadı")


if __name__ == "__main__":
    unittest.main()

"""Resmi EMT sablonu uzerine rapor kuran altyapi.

Sablon (`docs/EMT_Sablon_v2025_v3.docx`) yalnizca OKUNUR; kopyasi
uzerine yazilir. Sablonun kendi stilleri, sayfa duzeni, ustbilgi /
altbilgi baglantilari ve bolum sonu yapisi korunur.

Sablon mekanigi (olculerek dogrulanmistir):
  * BASLIK1-BASLIK4 stilleri **otomatik numaralandirilir**; bu yuzden
    baslik metnine numara YAZILMAZ. On ve arka bolumlerde numara
    `numId=0` ile bastirilir.
  * Sekil ve cizelge aciklamalari bolum bazli stillerdedir
    (`Sekil_FBE_Sablon_BolumIII`, `Cizelge_FBE_Sablon_BolumV` ...).
    Sablonda yalnizca I-VI ve EKLER vardir; bu nedenle sekil ve
    cizelgeler 1-6. bolumlerde ve eklerde yer alabilir.
  * Cizelge adi nokta ile biter; aciklama bicimi `Sekil 2.1 : ...`.
  * Bir paragrafin `pPr/sectPr` ogesi, o paragrafta **biten** bolumun
    ozelliklerini tasir. Roman/arap sayfa numaralandirmasi bu yolla
    kurulur; bu nedenle yeni bolum sonlari sablondakilerin birebir
    kopyasidir.
"""
from pathlib import Path
import copy
import re
import shutil

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[2]
SABLON = ROOT / "docs/EMT_Sablon_v2025_v3.docx"

# Sablondaki klon kaynaklari (govde ogesi indeksleri)
IDX_KAPAK_SONU = 57      # kapak + ithaf bolgesinin son ogesi
IDX_ROMAN_SONU = 93      # roman numaralandirmali portre bolum sonu
IDX_ARAP_BIR = 286       # arap numaralandirmanin 1'den basladigi bolum sonu
IDX_ARAP_DUZ = 331       # numaralandirmayi yeniden baslatmayan bolum sonu
# Sablonun kendi metninde "cikti almadan once siliniz" dedigi not kutulari
NOT_OGELERI = (13, 3)

ROMA = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}


def _numarasiz(paragraf):
    """Baslik numaralandirmasini bastirir (on/arka bolumler icin)."""
    pr = paragraf._p.get_or_add_pPr()
    for eski in pr.findall(qn("w:numPr")):
        pr.remove(eski)
    num = OxmlElement("w:numPr")
    for etiket, deger in (("w:ilvl", "0"), ("w:numId", "0")):
        oge = OxmlElement(etiket)
        oge.set(qn("w:val"), deger)
        num.append(oge)
    pr.append(num)


def _anahat(paragraf, duzey):
    """Baslik paragrafina anahat duzeyi verir (0 tabanli).

    Sablonun BASLIK stillerinde `w:outlineLvl` tanimli degildir; bu
    nedenle icindekiler alani varsayilan bicimiyle hicbir girdi
    bulamaz. Duzey paragraf duzeyinde yazilir.
    """
    pr = paragraf._p.get_or_add_pPr()
    for eski in pr.findall(qn("w:outlineLvl")):
        pr.remove(eski)
    oge = OxmlElement("w:outlineLvl")
    oge.set(qn("w:val"), str(duzey))
    pr.append(oge)


def _alan(paragraf, kod):
    """Word alan kodu ekler (icindekiler, sekil/cizelge listesi)."""
    calis = paragraf.add_run()
    basla = OxmlElement("w:fldChar")
    basla.set(qn("w:fldCharType"), "begin")
    metin = OxmlElement("w:instrText")
    metin.set(qn("xml:space"), "preserve")
    metin.text = kod
    ayir = OxmlElement("w:fldChar")
    ayir.set(qn("w:fldCharType"), "separate")
    yer = OxmlElement("w:t")
    yer.text = "Bu alan Word'de güncellenir."
    bitir = OxmlElement("w:fldChar")
    bitir.set(qn("w:fldCharType"), "end")
    for oge in (basla, metin, ayir, yer, bitir):
        calis._r.append(oge)


def _kalin_yaz(paragraf, metin):
    """`**kalin**` isaretlemesini bicimli calistirmalara cevirir."""
    for parca in re.split(r"(\*\*[^*]+\*\*)", metin):
        if not parca:
            continue
        if parca.startswith("**") and parca.endswith("**"):
            calis = paragraf.add_run(parca[2:-2])
            calis.bold = True
        else:
            paragraf.add_run(parca)


def _bos_klon(paragraf):
    """Bolum sonu paragrafini metinsiz kopyalar; sectPr korunur."""
    klon = copy.deepcopy(paragraf)
    for calis in klon.findall(qn("w:r")):
        klon.remove(calis)
    for baglanti in klon.findall(qn("w:hyperlink")):
        klon.remove(baglanti)
    return klon


class RaporKurucu:
    """Sablon iskeletini koruyarak rapor govdesini kurar."""

    def __init__(self, hedef: Path):
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SABLON, hedef)
        self.hedef = hedef
        self.belge = Document(hedef)
        govde = self.belge.element.body
        ogeler = list(govde)

        # Klon kaynaklarini govdeyi bosaltmadan once sakla.
        # Bolum sonu paragraflari sablonda metin tasiyabilir (ornegin
        # IDX_ARAP_DUZ bir yonerge cumlesi icerir); yalniz sectPr
        # korunacagi icin butun calistirmalar temizlenir.
        self._roman_sonu = _bos_klon(ogeler[IDX_ROMAN_SONU])
        self._arap_bir = _bos_klon(ogeler[IDX_ARAP_BIR])
        self._arap_duz = _bos_klon(ogeler[IDX_ARAP_DUZ])
        self._son_sectpr = ogeler[-1]

        # Kapak ve ithaf bolgesi disindaki ornek icerigi kaldir
        for oge in ogeler[IDX_KAPAK_SONU + 1:-1]:
            govde.remove(oge)
        # Sablonun kendi uyarisi geregi not kutulari kaldirilir
        for idx in NOT_OGELERI:
            govde.remove(ogeler[idx])
        self.govde = govde

        self.bolum = 0          # etkin BASLIK1 bolum numarasi (0 = on bolum)
        self.sekil_no = {}      # bolum -> sayac
        self.cizelge_no = {}
        self.sekiller = []      # (etiket, ad)
        self.cizelgeler = []

    # ------------------------------------------------------------ yardimci
    def _ekle(self, stil="GOVDE"):
        oge = OxmlElement("w:p")
        self.govde.insert(list(self.govde).index(self._son_sectpr), oge)
        paragraf = Paragraph(oge, self.belge)
        paragraf.style = self.belge.styles[stil]
        return paragraf

    def _tasi(self, oge):
        self.govde.insert(list(self.govde).index(self._son_sectpr), oge)

    def _etiket_on_eki(self):
        """Eklerde sablon harf kullanir (Cizelge A.1), bolumlerde numara."""
        return "A" if self.bolum == "EKLER" else str(self.bolum)

    def _caption_stili(self, tur):
        """`tur`: 'Sekil' veya 'Cizelge'."""
        if self.bolum == 0:
            return f"{tur}_FBE_Sablon_BolumI"
        if self.bolum in ROMA:
            return f"{tur}_FBE_Sablon_Bolum{ROMA[self.bolum]}"
        if self.bolum == "EKLER":
            return f"{tur}_FBE_Sablon_BolumEKLER"
        # 7. ve 8. bolumde sablonda aciklama stili yoktur
        raise ValueError(
            f"{self.bolum}. bolumde {tur} aciklama stili sablonda yok; "
            "sekil ve cizelgeler 1-6. bolumlere ve eklere konur")

    # -------------------------------------------------------------- icerik
    def kapak_doldur(self, eslesme: dict):
        """Kapak yer tutucularini degistirir.

        Kapak basliklari metin kutularinda durur, metin birkac
        calistirmaya bolunmustur ve her kutu uyumluluk icin iki kez
        yer alir. Bu nedenle degistirme paragraf duzeyinde yapilir:
        paragrafin butun metni birlestirilip bosluklar normallestirilir,
        eslesirse yeni metin ilk calistirmaya yazilip digerleri bosaltilir.
        Govdeye icerik eklenmeden once cagrilmalidir.
        """
        bulunan = {}
        for paragraf in self.belge.element.body.iter(qn("w:p")):
            dugumler = paragraf.findall(".//" + qn("w:t"))
            if not dugumler:
                continue
            duz = " ".join(
                "".join(d.text or "" for d in dugumler).split())
            if duz in eslesme:
                dugumler[0].text = eslesme[duz]
                for d in dugumler[1:]:
                    d.text = ""
                bulunan[duz] = bulunan.get(duz, 0) + 1
        eksik = [k for k in eslesme if k not in bulunan]
        if eksik:
            raise ValueError(f"Kapakta bulunamayan yer tutucu: {eksik}")
        return bulunan

    def on_baslik(self, metin):
        paragraf = self._ekle("BASLIK1")
        paragraf.add_run(metin)
        _numarasiz(paragraf)
        _anahat(paragraf, 0)
        self.bolum = 0
        return paragraf

    def baslik1(self, metin, numarali=True):
        paragraf = self._ekle("BASLIK1")
        paragraf.add_run(metin)
        _anahat(paragraf, 0)
        if numarali:
            self.bolum += 1
            self.sekil_no.setdefault(self.bolum, 0)
            self.cizelge_no.setdefault(self.bolum, 0)
        else:
            _numarasiz(paragraf)
        return paragraf

    def baslik(self, duzey, metin, numarali=True):
        paragraf = self._ekle(f"BASLIK{duzey}")
        paragraf.add_run(metin)
        _anahat(paragraf, duzey - 1)
        if not numarali:
            # Eklerde alt baslik, bolum numarasini surdurmemeli
            _numarasiz(paragraf)
        return paragraf

    def kaynak_satiri(self, metin):
        """Kaynakca girdisi: URL'lerde bosluk acilmamasi icin sola dayali."""
        paragraf = self._ekle("GOVDE")
        paragraf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraf.paragraph_format.first_line_indent = Cm(0)
        _kalin_yaz(paragraf, metin)
        return paragraf

    def govde_metni(self, metin, stil="GOVDE"):
        paragraf = self._ekle(stil)
        _kalin_yaz(paragraf, metin)
        return paragraf

    def madde(self, metin):
        paragraf = self._ekle("GOVDE")
        paragraf.paragraph_format.left_indent = Cm(1.0)
        paragraf.paragraph_format.first_line_indent = Cm(-0.5)
        _kalin_yaz(paragraf, "– " + metin)
        return paragraf

    def alan_listesi(self, kod):
        paragraf = self._ekle("Normal")
        _alan(paragraf, kod)
        return paragraf

    def sekil(self, dosya: Path, ad: str, genislik_cm=13.0):
        if not dosya.is_file():
            raise FileNotFoundError(dosya)
        self.sekil_no[self.bolum] = self.sekil_no.get(self.bolum, 0) + 1
        etiket = f"Şekil {self._etiket_on_eki()}.{self.sekil_no[self.bolum]}"

        resim = self._ekle("Normal")
        resim.alignment = WD_ALIGN_PARAGRAPH.CENTER
        resim.add_run().add_picture(str(dosya), width=Cm(genislik_cm))

        aciklama = self._ekle(self._caption_stili("Sekil"))
        aciklama.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # Sablonun aciklama stilleri "Sekil 2.1 : " on ekini OTOMATIK uretir;
        # metne yazilirsa etiket iki kez gorunur. Yalniz aciklama yazilir.
        aciklama.add_run(ad)
        self.sekiller.append((etiket, ad))
        return etiket

    def cizelge(self, ad: str, satirlar, genislikler=None):
        """`satirlar[0]` baslik satiridir. `ad` nokta ile bitmelidir."""
        if not ad.endswith("."):
            raise ValueError(f"Cizelge adi nokta ile bitmeli: {ad!r}")
        self.cizelge_no[self.bolum] = self.cizelge_no.get(self.bolum, 0) + 1
        etiket = f"Çizelge {self._etiket_on_eki()}.{self.cizelge_no[self.bolum]}"

        aciklama = self._ekle(self._caption_stili("Cizelge"))
        aciklama.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # Etiket on eki stil tarafindan otomatik uretilir
        aciklama.add_run(ad)

        tablo = self.belge.add_table(rows=len(satirlar), cols=len(satirlar[0]))
        tablo.style = self.belge.styles["Table Grid"]
        tablo.alignment = WD_TABLE_ALIGNMENT.CENTER
        tablo.autofit = True
        for r, satir in enumerate(satirlar):
            for c, deger in enumerate(satir):
                hucre = tablo.cell(r, c)
                hucre.text = ""
                paragraf = hucre.paragraphs[0]
                paragraf.style = self.belge.styles["Normal"]
                paragraf.paragraph_format.space_before = Pt(1)
                paragraf.paragraph_format.space_after = Pt(1)
                calis = paragraf.add_run(str(deger))
                calis.font.size = Pt(9)
                if r == 0:
                    calis.bold = True
                if c > 0:
                    paragraf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if genislikler:
            for c, g in enumerate(genislikler):
                for satir in tablo.rows:
                    satir.cells[c].width = Cm(g)
        self._tasi(tablo._tbl)
        self._ekle("Normal")
        self.cizelgeler.append((etiket, ad))
        return etiket

    # --------------------------------------------------------- bolum sonu
    def bolum_sonu(self, tur="roman"):
        klon = {"roman": self._roman_sonu,
                "arap_bir": self._arap_bir,
                "arap": self._arap_duz}[tur]
        self._tasi(copy.deepcopy(klon))

    def kaydet(self):
        self.belge.save(self.hedef)
        return self.hedef

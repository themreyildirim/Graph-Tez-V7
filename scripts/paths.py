"""Ham veri kokunun tek noktadan cozumlenmesi.

Neden var?
----------
WP00-WP06 scriptleri ham veri yolunu modul duzeyinde sabit kodlanmis bir
`Path` olarak tasir. Bu scriptlerin SHA-256 degerleri WP08/WP09/WP10/WP11
butunluk manifestlerinde (29 ayri manifest) kayitlidir; iceriklerini
degistirmek kabul edilmis sonuc zincirini gecersiz kilar. Bu nedenle o
dosyalar DEGISTIRILMEDI.

Bu modul, bundan sonraki her calistirma ve yeni kod icin tek dogru
kaynaktir: once ortam degiskeni, sonra configs/data_paths.yaml, en son
tarihsel varsayilan.

Kullanim
--------
    from paths import data_root, resolve, describe
    xml = resolve('DrugBank/drugbank_all_full_database.xml/full database.xml')

Tarihsel scriptleri baska bir makinede calistirmak icin:
    $env:GRAPH_TEZ_DATA_ROOT = 'D:\Tez\Dataset'
komutu TEK BASINA yeterli degildir; ilgili script kopyasinda varsayilan
yolun bu modulle degistirilmesi gerekir. Kopya uzerinde calisin, orijinali
degistirmeyin (bkz. GUNCEL_DURUM.md).
"""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "data_paths.yaml"
ENV_VAR = "GRAPH_TEZ_DATA_ROOT"

# WP00-WP06 scriptlerinde gecen tarihsel varsayilan. Buradaki deger yalnizca
# yedek olarak kullanilir; bu modul o scriptleri yonlendirmez.
HISTORICAL_DEFAULT = Path(r"C:\Users\emrey\OneDrive\Masaüstü\Tez Dosyalar\Dataset")


def _read_config_value(key):
    """configs/data_paths.yaml icinden tek bir skaler anahtari okur.

    Kasitli olarak minimal: PyYAML bagimliligi eklemez, yalnizca
    `anahtar: 'deger'` bicimindeki satirlari cozer.
    """
    if not CONFIG.is_file():
        return None
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or ":" not in line:
            continue
        name, _, value = line.partition(":")
        if name.strip() != key:
            continue
        value = value.strip().strip("'\"")
        return value or None
    return None


def data_root(required=False):
    """Etkin ham veri kokunu dondurur.

    required=True ise klasor yoksa FileNotFoundError yukseltir; boylece
    sessiz bos sonuc yerine acik hata alinir.
    """
    candidate = os.environ.get(ENV_VAR) or _read_config_value("dataset_root")
    root = Path(candidate) if candidate else HISTORICAL_DEFAULT
    if required and not root.is_dir():
        raise FileNotFoundError(
            f"Ham veri kokune erisilemedi: {root}. "
            f"{ENV_VAR} ortam degiskenini veya {CONFIG} icindeki dataset_root "
            "degerini guncelleyin."
        )
    return root


def resolve(relative, required=False):
    """Ham veri kokune gore goreli bir yolu cozumler."""
    path = data_root() / relative
    if required and not path.exists():
        raise FileNotFoundError(f"Ham kaynak bulunamadi: {path}")
    return path


def external_reference_pdf():
    """WP13 dis referans belgesinin (SIVEXTRO KUB) yapilandirilmis yolu."""
    value = os.environ.get("GRAPH_TEZ_EXTERNAL_PDF") or _read_config_value("external_reference_pdf")
    return Path(value) if value else None


def describe():
    """Tani amacli: hangi kaynaktan hangi yolun secildigini raporlar."""
    if os.environ.get(ENV_VAR):
        source = f"ortam degiskeni {ENV_VAR}"
    elif _read_config_value("dataset_root"):
        source = f"yapilandirma {CONFIG.relative_to(ROOT).as_posix()}"
    else:
        source = "tarihsel varsayilan (scripts/wp0*.py ile ayni)"
    root = data_root()
    return {"data_root": str(root), "source": source, "exists": root.is_dir()}


if __name__ == "__main__":
    import json

    print(json.dumps(describe(), ensure_ascii=False, indent=2))

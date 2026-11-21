"""Ortak pytest kurulumu: scripts/ modul yolu ve calisma dizini.

Bu dosya yalnizca test TOPLAMA asamasini kolaylastirir. Hicbir test
davranisini, seed'i, veri yolunu veya dogrulama esigini degistirmez.
Mevcut testler kendi `sys.path.insert` satirlarini korur; burada yapilan
ekleme tekrarli olsa da zararsizdir.
"""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# Testlerin bircogu proje kokune gore goreli yol kullanir.
os.chdir(ROOT)

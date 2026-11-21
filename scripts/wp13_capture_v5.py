"""Arayüz v5 ekran görüntülerini CDP üzerinden yakalar.

Neden böyle?
------------
Orijinal `EMT2_Teslim_v1/build/capture.cjs` Node + Playwright gerektirir;
bu makinede Node kurulu değildir. Bu betik aynı işi yalnızca kurulu Chrome
ve `websockets` paketiyle, Chrome DevTools Protocol üzerinden yapar. Yeni
indirme gerektirmez.

Model, SHAP, API veya OCR çalıştırmaz; yalnızca çalışan v5 arayüzünün
ekran görüntüsünü alır.

Kullanım:
    # once arayuzu baslatin (varsayilan 8530)
    .venv_wp13/Scripts/python.exe -I scripts/wp13_capture_v5.py --port 8530
"""
from pathlib import Path
import argparse
import asyncio
import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request

import websockets

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/figures/WP13/arayuz_v5"
WIDTH, HEIGHT = 1640, 1060

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser():
    for path in CHROME_CANDIDATES:
        if Path(path).is_file():
            return path
    raise FileNotFoundError("Chrome veya Edge bulunamadi")


class CDP:
    def __init__(self, ws):
        self.ws = ws
        self.n = 0

    async def send(self, method, **params):
        self.n += 1
        await self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            message = json.loads(await self.ws.recv())
            if message.get("id") == self.n:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})

    async def js(self, expression, wait=0.0):
        result = await self.send(
            "Runtime.evaluate",
            expression=expression,
            awaitPromise=True,
            returnByValue=True,
        )
        if wait:
            await asyncio.sleep(wait)
        return result.get("result", {}).get("value")

    async def rect(self, finder_js):
        """Verilen JS ifadesinin dondurdugu ogenin merkez koordinatini verir."""
        return await self.js(
            "(() => { const el = (%s); if (!el) return null;"
            " const r = el.getBoundingClientRect();"
            " if (!r.width || !r.height) return null;"
            " return {x: r.left + r.width/2, y: r.top + r.height/2}; })()" % finder_js
        )

    async def click_el(self, finder_js, wait=0.0):
        """React bilesenleri sentetik .click() ile her zaman tepki vermez;
        bu nedenle gercek mouse olaylari gonderilir."""
        point = await self.rect(finder_js)
        if not point:
            return "NOT_FOUND"
        for kind in ("mousePressed", "mouseReleased"):
            await self.send(
                "Input.dispatchMouseEvent",
                type=kind,
                x=point["x"],
                y=point["y"],
                button="left",
                clickCount=1,
            )
        if wait:
            await asyncio.sleep(wait)
        return "OK"

    async def type_text(self, text, wait=0.0):
        await self.send("Input.insertText", text=text)
        if wait:
            await asyncio.sleep(wait)

    async def press(self, key, code=None, wait=0.0):
        """Streamlit selectbox listesi fare tiklamasiyla acilmaz; klavye kullanilir."""
        keys = {"Enter": 13, "ArrowDown": 40, "Escape": 27}
        for kind in ("keyDown", "keyUp"):
            await self.send(
                "Input.dispatchKeyEvent",
                type=kind,
                key=key,
                code=code or key,
                windowsVirtualKeyCode=keys.get(key, 0),
                nativeVirtualKeyCode=keys.get(key, 0),
            )
        if wait:
            await asyncio.sleep(wait)

    async def shot(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        data = await self.send("Page.captureScreenshot", format="png")
        target = OUT / (name + ".png")
        target.write_bytes(base64.b64decode(data["data"]))
        print(f"  {target.relative_to(ROOT).as_posix()}  ({target.stat().st_size // 1024} KB)")
        return target


# Streamlit widget'larini metne gore bulup tiklayan yardimci JS.
CLICK_TEXT = """
(() => {
  const want = %s;
  const nodes = [...document.querySelectorAll('p,span,label,div,button')];
  const hit = nodes.find(n => n.textContent.trim() === want && n.offsetParent !== null);
  if (!hit) return 'NOT_FOUND';
  hit.click();
  return 'OK';
})()
"""

CLICK_TAB = """
(() => {
  const tabs = [...document.querySelectorAll('[role=tab]')];
  if (!tabs[%d]) return 'NOT_FOUND';
  tabs[%d].click();
  return tabs[%d].innerText.trim();
})()
"""

SCROLL_TO = """
(() => {
  const want = %s;
  const n = [...document.querySelectorAll('h1,h2,h3,h4,p,span')]
    .find(e => e.textContent.trim().startsWith(want));
  if (!n) return 'NOT_FOUND';
  n.scrollIntoView({block:'start'});
  window.scrollBy(0,-90);
  return 'OK';
})()
"""


async def run(port):
    browser = find_browser()
    profile = tempfile.mkdtemp(prefix="gt_v5_shot_")
    debug_port = 9333
    process = subprocess.Popen(
        [
            browser,
            "--headless=new",
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={profile}",
            f"--window-size={WIDTH},{HEIGHT}",
            "--hide-scrollbars",
            "--disable-gpu",
            "--no-first-run",
            "--force-device-scale-factor=1",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        endpoint = None
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json/version", timeout=1) as r:
                    endpoint = json.load(r)["webSocketDebuggerUrl"]
                break
            except Exception:
                time.sleep(0.5)
        if not endpoint:
            raise RuntimeError("CDP uc noktasi acilmadi")

        async with websockets.connect(endpoint, max_size=60_000_000) as ws:
            cdp = CDP(ws)
            target = await cdp.send("Target.createTarget", url="about:blank")
            sessions = await cdp.send("Target.attachToTarget", targetId=target["targetId"], flatten=True)
            del sessions  # flatten modunda ayri oturum gerekmiyor

            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json"))
            page = next(t for t in tabs if t["type"] == "page" and t["id"] == target["targetId"])

        async with websockets.connect(page["webSocketDebuggerUrl"], max_size=60_000_000) as ws:
            cdp = CDP(ws)
            await cdp.send("Page.enable")
            await cdp.send("Runtime.enable")
            await cdp.send(
                "Emulation.setDeviceMetricsOverride",
                width=WIDTH, height=HEIGHT, deviceScaleFactor=1, mobile=False,
            )
            print(f"Arayuz: http://127.0.0.1:{port}")
            await cdp.send("Page.navigate", url=f"http://127.0.0.1:{port}")
            await asyncio.sleep(9)

            print("1) Varsayilan gorunum")
            await cdp.shot("01_ana_v5")

            print("2) Yan etki tahminleri")
            await cdp.js(CLICK_TAB % (1, 1, 1), wait=4)
            await cdp.shot("02_tahminler_v5")

            print("3) Model aciklanabilirligi")
            await cdp.js(CLICK_TAB % (2, 2, 2), wait=5)
            await cdp.js(SCROLL_TO % json.dumps("A1P1 · mesaj maskesi"), wait=1.2)
            await cdp.shot("03_aciklama_v5")

            print("4) MONODOKS kaynak gorunumu")
            await cdp.click_el(
                "[...document.querySelectorAll('[data-testid=stCheckbox] label')]"
                ".find(e => e.innerText.includes('Türkçe prospektüs'))",
                wait=9,
            )
            await cdp.click_el(
                "document.querySelector('input[aria-label=\"Kayıtlı ilaç\"]')",
                wait=1.5,
            )
            await cdp.type_text("MONODOKS", wait=1.5)
            await cdp.press("Enter", wait=10)
            picked = await cdp.js(
                "document.querySelector('input[aria-label=\"Kayıtlı ilaç\"]')"
                "?.closest('[data-testid=stSelectbox]')?.innerText.trim()"
            )
            print("   secili ilac:", (picked or "?").replace(chr(10), " / "))
            await cdp.js(CLICK_TAB % (3, 3, 3), wait=7)
            state = await cdp.js(
                "document.querySelector('[data-testid=stSelectbox]')?.innerText.trim()"
            )
            print("   secili ilac:", (state or "").replace(chr(10), " / "))
            await cdp.shot("04_monodoks_kaynak_v5")

            print("5) Tedizolid dis deneyi")
            moved = await cdp.click_el(
                "[...document.querySelectorAll('[data-testid=stRadioOption] label,[data-testid=stRadioOption]')]"
                ".find(e => e.innerText.trim().startsWith('Tedizolid'))",
                wait=13,
            )
            print("   tedizolid moduna gecis:", moved)
            await cdp.shot("05_tedizolid_v5")
            await cdp.js(SCROLL_TO % json.dumps("Kayıtlı B1 tahmini"), wait=1.5)
            await cdp.shot("06_tedizolid_shap_v5")

            print("6) Kimligi dogrulanmayan PDF")
            await cdp.click_el(
                "[...document.querySelectorAll('[data-testid=stRadioOption] label,[data-testid=stRadioOption]')]"
                ".find(e => e.innerText.trim().startsWith('Kayıtlı ilaçlar'))",
                wait=11,
            )
            await cdp.click_el(
                "[...document.querySelectorAll('[data-testid=stRadioOption] label,[data-testid=stRadioOption]')]"
                ".find(e => e.innerText.trim().startsWith('Prospektüs PDF'))",
                wait=7,
            )
            sample = ROOT / "EMT2_Teslim_v1/build/ornek.pdf"
            document = await cdp.send("DOM.getDocument", depth=-1)
            node = await cdp.send(
                "DOM.querySelector",
                nodeId=document["root"]["nodeId"],
                selector="input[type=file]",
            )
            if node.get("nodeId"):
                await cdp.send(
                    "DOM.setFileInputFiles", files=[str(sample)], nodeId=node["nodeId"]
                )
                await asyncio.sleep(13)
                await cdp.js(CLICK_TAB % (1, 1, 1), wait=6)
                await cdp.shot("07_dogrulanmayan_pdf_v5")
            else:
                print("   dosya girdisi bulunamadi; adim atlandi")

            print("\nTamamlandi.")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except Exception:
            process.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8530)
    args = parser.parse_args()
    asyncio.run(run(args.port))

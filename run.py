# scraper_runner.py
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

DATA_PATH = Path("data")
COOKIES_PATH = DATA_PATH / "cookies"
SUCURSALES_FILE = DATA_PATH / "sucursales.json"

def scrapear_categoria(supermercado: str, sucursal: str, patron_url: str, paginas: int, tiempo_espera: float) -> list:
    resultados = []

    with open(SUCURSALES_FILE) as f:
        sucursales_data = json.load(f)

    cookies_path = Path(sucursales_data[supermercado][sucursal]["cookies"])
    localstorage_path = Path(sucursales_data[supermercado][sucursal]["localStorage"])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        # Cargar cookies
        if cookies_path.exists():
            with open(cookies_path) as f:
                cookies = json.load(f)
            context.add_cookies(cookies)

        page = context.new_page()

        for i in range(1, paginas + 1):
            url = patron_url.replace("{page}", str(i))
            page.goto(url)
            print(f"📥 Página {i}: {url}")

            page.wait_for_timeout(tiempo_espera * 1000)

            # HTML crudo
            html = page.content()

            # Texto visible
            texto = page.inner_text("body")

            # Extraer <script type="application/ld+json">
            scripts = page.locator('script[type="application/ld+json"]')
            total = scripts.count()
            print(f"🔎 Encontrados {total} bloques <script type='application/ld+json'>")
            json_ld_list = []
            for j in range(total):
                try:
                    content = scripts.nth(j).inner_text()
                    json_ld_list.append(json.loads(content))
                except:
                    continue

            resultados.append({
                "pagina": i,
                "url": url,
                "html": html,
                "texto": texto,
                "json_ld": json_ld_list
            })

        browser.close()

    return resultados

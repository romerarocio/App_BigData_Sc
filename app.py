import json
from pathlib import Path
from playwright.sync_api import sync_playwright

# --- Archivos ---
CONFIG_PATH = Path("config.json")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# --- Cargar configuración ---
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# --- Elegir supermercado ---
supermercados = list(config.keys())
print("\n🛍️ Supermercados disponibles:")
for i, s in enumerate(supermercados, 1):
    print(f"{i}. {s}")
idx = int(input("Seleccioná uno por número: "))
supermercado = supermercados[idx - 1]

# --- Sucursal ---
sucs = config[supermercado]["sucursales"]
print("\n🏪 Sucursales:")
for k, nombre in sucs.items():
    print(f"{k}. {nombre}")
print("0. ➕ Agregar nueva")

op_suc = input("Seleccioná una sucursal por número: ").strip()
if op_suc == "0":
    nueva = input("✏️ Ingresá el nombre de la nueva sucursal: ").strip()
    next_key = str(max(map(int, sucs.keys()), default=0) + 1)
    config[supermercado]["sucursales"][next_key] = nueva
    sucursal = nueva
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
else:
    sucursal = sucs[op_suc]

# --- Categoría ---
cats = config[supermercado]["categorias"]
print("\n📦 Categorías:")
for k, info in cats.items():
    print(f"{k}. {info['nombre']}")
print("0. ➕ Agregar nueva")

op_cat = input("Seleccioná una categoría por número o agregá: ").strip()
if op_cat == "0":
    nombre = input("📁 Nombre de la categoría: ").strip()
    patron = input("🔗 URL con {page}: ").strip()
    next_key = str(max(map(int, cats.keys()), default=0) + 1)
    cats[next_key] = {"nombre": nombre, "patron": patron}
    categoria = nombre
    patron_url = patron
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
else:
    categoria = cats[op_cat]["nombre"]
    patron_url = cats[op_cat]["patron"]

# --- Medición de tiempos ---
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    print(f"\n⏱ Abrí página 1: {patron_url.replace('{page}', '1')}")
    page.goto(patron_url.replace("{page}", "1"))
    input("Presioná ENTER cuando se haya cargado...")
    t1 = page.evaluate("performance.timing.loadEventEnd - performance.timing.navigationStart") / 1000

    print(f"⏱ Abrí página 2: {patron_url.replace('{page}', '2')}")
    page.goto(patron_url.replace("{page}", "2"))
    input("Presioná ENTER cuando se haya cargado...")
    t2 = page.evaluate("performance.timing.loadEventEnd - performance.timing.navigationStart") / 1000

    delay = round((t1 + t2) / 2, 2)
    print(f"⏲️ Tiempo estimado por página: {delay}s")

    n = int(input("📄 ¿Cuántas páginas querés scrapear?: "))

    textos = []
    paginas = []

    for i in range(1, n + 1):
        url = patron_url.replace("{page}", str(i))
        print(f"➡️ Cargando página {i}: {url}")
        page.goto(url)
        page.wait_for_timeout(delay * 1000)

        body = page.inner_text("body")
        textos.append(f"\n--- Página {i} ---\n{body}")
        html = page.content()

        scripts = page.locator('script[type="application/ld+json"]')
        bloque_json = []
        for j in range(scripts.count()):
            try:
                raw = scripts.nth(j).inner_text()
                bloque_json.append(json.loads(raw))
            except:
                continue

        paginas.append({
            "pagina": i,
            "url": url,
            "html": html,
            "texto": body,
            "json_ld": bloque_json
        })

    cat_norm = categoria.lower().replace(" ", "_")
    with open(OUTPUT_DIR / f"resultados_{cat_norm}.json", "w", encoding="utf-8") as f:
        json.dump(paginas, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_DIR / f"textos_{cat_norm}.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(textos))

    print(f"\n✅ Archivos guardados en carpeta 'output/'")
    browser.close()

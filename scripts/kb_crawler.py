#!/usr/bin/env python3
"""
ValidaRótulo IA — KB Crawler v2
Melhorias: Playwright para Planalto, OCR para PDFs escaneados,
acordeons MAPA com clique individual, upsert inteligente (nunca sobrescreve menor).
"""
import asyncio, os, re, io, hashlib
from datetime import datetime
from urllib.parse import urlparse

import httpx

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import pytesseract, pdf2image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
MAX_CHARS    = 7000
MAX_DOCS     = 300

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Referer": "https://www.google.com.br/",
}

MAPA_JS_PAGES = [
    {"url": "https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-vegetal/legislacao-programas-nacionais-e-seguranca-dos-alimentos-1/legislacao/bebidas", "orgao": "MAPA", "categoria": "bebidas", "descricao": "Legislação Bebidas MAPA"},
    {"url": "https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-vegetal/legislacao-programas-nacionais-e-seguranca-dos-alimentos-1/legislacao/legislacaoPOV", "orgao": "MAPA", "categoria": "qualidade_vegetal", "descricao": "Legislação POV"},
    {"url": "https://www.gov.br/agricultura/pt-br/assuntos/defesa-agropecuaria/suasa/regulamentos-tecnicos-de-identidade-e-qualidade-de-produtos-de-origem-animal-1", "orgao": "MAPA", "categoria": "poa", "descricao": "RTIQs POA"},
    {"url": "https://www.gov.br/agricultura/pt-br/assuntos/defesa-agropecuaria/suasa/regulamentos-tecnicos-de-identidade-e-qualidade-de-produtos-de-origem-vegetal", "orgao": "MAPA", "categoria": "qualidade_vegetal", "descricao": "RTIQs Vegetal"},
    {"url": "https://www.gov.br/anvisa/pt-br/assuntos/regulamentacao/legislacao/bibliotecas-tematicas/arquivos/biblioteca-de-alimentos", "orgao": "ANVISA", "categoria": "alimentos", "descricao": "Biblioteca ANVISA Alimentos"},
]

PLANALTO_URLS = [
    ("https://www.planalto.gov.br/ccivil_03/leis/l8918.htm", "PLANALTO", "bebidas", "lei_8918_bebidas"),
    ("https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2009/decreto/d6871.htm", "PLANALTO", "bebidas", "dec_6871_bebidas"),
    ("https://www.planalto.gov.br/ccivil_03/leis/l7678.htm", "PLANALTO", "bebidas", "lei_7678_vinho"),
    ("https://www.planalto.gov.br/ccivil_03/leis/2003/l10831.htm", "PLANALTO", "organicos", "lei_10831_organicos"),
    ("https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/decreto/d6323.htm", "PLANALTO", "organicos", "dec_6323_organicos"),
    ("https://www.planalto.gov.br/ccivil_03/decreto-lei/del0986.htm", "PLANALTO", "geral", "dec_lei_986_1969"),
    ("https://www.planalto.gov.br/ccivil_03/leis/l9972.htm", "PLANALTO", "qualidade", "lei_9972_classificacao"),
    ("https://www.planalto.gov.br/ccivil_03/leis/l10674.htm", "PLANALTO", "rotulagem", "lei_10674_gluten"),
    ("https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2019/decreto/d10083.htm", "PLANALTO", "organicos", "dec_10083_organicos"),
    ("https://www.planalto.gov.br/ccivil_03/decreto/d79094.htm", "PLANALTO", "geral", "dec_79094_alimentos"),
]

ANVISA_PDFS = [
    ("https://antigo.anvisa.gov.br/documents/10181/3882585/RDC_429_2020_.pdf", "ANVISA", "rotulagem", "rdc_429_2020"),
    ("https://antigo.anvisa.gov.br/documents/10181/3882585/IN+75_2020_.pdf", "ANVISA", "rotulagem", "in_75_2020"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+266_2005.pdf", "ANVISA", "alimentos", "rdc_266_sorvetes"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+268_2005.pdf", "ANVISA", "alimentos", "rdc_268_proteina_vegetal"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+264_2005.pdf", "ANVISA", "alimentos", "rdc_264_chocolate"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+270+de+22+de+setembro+de+2005.pdf", "ANVISA", "alimentos", "rdc_270_oleos"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+276_2005.pdf", "ANVISA", "alimentos", "rdc_276_condimentos"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+277_2005.pdf", "ANVISA", "alimentos", "rdc_277_cafe_cha"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+272_2005.pdf", "ANVISA", "alimentos", "rdc_272_vegetais"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+263_2005.pdf", "ANVISA", "alimentos", "rdc_263_cereais"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+265_2005.pdf", "ANVISA", "alimentos", "rdc_265_amido"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+267_2005.pdf", "ANVISA", "alimentos", "rdc_267_cogumelos"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+269_2005.pdf", "ANVISA", "alimentos", "rdc_269_proteinas"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+271_2005.pdf", "ANVISA", "alimentos", "rdc_271_acucar"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+273_2005.pdf", "ANVISA", "alimentos", "rdc_273_enriquecidos"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+274_2005.pdf", "ANVISA", "bebidas", "rdc_274_bebidas"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+278_2005.pdf", "ANVISA", "alimentos", "rdc_278_vinagre"),
    ("https://antigo.anvisa.gov.br/documents/10181/6875868/RDC_920_2024_.pdf", "ANVISA", "alimentos", "rdc_920_2024"),
]

def gerar_chave(url, sugestao=""):
    if sugestao: return sugestao
    nome = urlparse(url).path.split("/")[-1]
    nome = re.sub(r"\.(pdf|htm|html)$", "", nome, flags=re.I)
    nome = re.sub(r"[^a-z0-9_]", "_", nome.lower())[:60]
    return nome or hashlib.md5(url.encode()).hexdigest()[:12]

def extrair_pdf(data: bytes) -> str:
    texto = ""
    if HAS_PYPDF:
        try:
            r = PdfReader(io.BytesIO(data))
            for pg in r.pages:
                texto += pg.extract_text() or ""
                if len(texto) >= MAX_CHARS: break
        except Exception: pass
    if len(texto.strip()) >= 100:
        return texto[:MAX_CHARS].strip()
    if HAS_OCR:
        try:
            imgs = pdf2image.convert_from_bytes(data, dpi=150, first_page=1, last_page=4)
            ocr = ""
            for img in imgs:
                ocr += pytesseract.image_to_string(img, lang="por") + "\n"
                if len(ocr) >= MAX_CHARS: break
            if len(ocr.strip()) >= 100:
                return ocr[:MAX_CHARS].strip()
        except Exception as e:
            print(f"     OCR: {e}")
    return texto[:MAX_CHARS].strip()

def extrair_html(html: str) -> str:
    t = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL|re.I)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.DOTALL|re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)[:MAX_CHARS].strip()

async def get_existing(client, chave):
    try:
        r = await client.get(f"{SUPABASE_URL}/rest/v1/kb_documents",
            headers=HEADERS_SB, params={"select": "tamanho_chars", "chave": f"eq.{chave}"})
        d = r.json() if r.status_code == 200 else []
        return d[0].get("tamanho_chars", 0) if d else 0
    except: return 0

async def salvar(client, doc) -> str:
    """Upsert inteligente — nunca sobrescreve com conteúdo menor."""
    novo = len(doc.get("conteudo", ""))
    if novo < 50: return "vazio"
    existente = await get_existing(client, doc["chave"])
    if existente >= novo: return f"mantido ({existente}>={novo})"
    try:
        r = await client.post(f"{SUPABASE_URL}/rest/v1/kb_documents",
            headers={**HEADERS_SB, "Prefer": "resolution=merge-duplicates"},
            json={**doc, "atualizado_em": datetime.now().isoformat()})
        return f"salvo ({novo}c)" if r.status_code in (200, 201) else f"HTTP {r.status_code}"
    except Exception as e:
        return f"erro: {str(e)[:40]}"

async def crawl_planalto(context, contador):
    salvos = 0
    print(f"\n⚖️  Planalto via Playwright ({len(PLANALTO_URLS)} leis)...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        for url, orgao, cat, chave in PLANALTO_URLS:
            if contador[0] >= MAX_DOCS: break
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                await page.wait_for_timeout(1500)
                texto = extrair_html(await page.content())
                if len(texto) < 100:
                    print(f"   ⚠️  {chave}: vazio")
                    continue
                doc = {"chave": chave, "titulo": chave.replace("_"," ").title(),
                       "fonte": url, "orgao": orgao, "categoria": cat,
                       "conteudo": texto, "tamanho_chars": len(texto)}
                st = await salvar(client, doc)
                icon = "✅" if "salvo" in st else "⏭️ "
                print(f"   {icon} {chave}: {st}")
                if "salvo" in st: salvos += 1; contador[0] += 1
            except Exception as e:
                print(f"   ❌ {chave}: {str(e)[:60]}")
            finally:
                await page.close()
            await asyncio.sleep(0.8)
    return salvos

async def crawl_anvisa_pdfs(contador):
    salvos = 0
    print(f"\n🏥 ANVISA PDFs ({len(ANVISA_PDFS)} docs, OCR={HAS_OCR})...")
    async with httpx.AsyncClient(timeout=30.0, headers=BROWSER_HEADERS, follow_redirects=True) as client:
        for url, orgao, cat, chave in ANVISA_PDFS:
            if contador[0] >= MAX_DOCS: break
            try:
                r = await client.get(url, timeout=25.0)
                if r.status_code != 200:
                    print(f"   ⚠️  {chave}: HTTP {r.status_code}")
                    continue
                texto = extrair_pdf(r.content)
                if len(texto) < 50:
                    print(f"   ⚠️  {chave}: vazio")
                    continue
                doc = {"chave": chave, "titulo": chave.replace("_"," ").title(),
                       "fonte": url, "orgao": orgao, "categoria": cat,
                       "conteudo": texto, "tamanho_chars": len(texto)}
                st = await salvar(client, doc)
                icon = "✅" if "salvo" in st else "⏭️ "
                print(f"   {icon} {chave}: {st}")
                if "salvo" in st: salvos += 1; contador[0] += 1
            except Exception as e:
                print(f"   ❌ {chave}: {str(e)[:60]}")
            await asyncio.sleep(0.4)
    return salvos

async def crawl_js_page(context, info, contador):
    salvos = 0
    print(f"\n🌐 {info['descricao']} — {info['url'][:60]}")
    async with httpx.AsyncClient(timeout=20.0, headers=BROWSER_HEADERS, follow_redirects=True) as client:
        page = await context.new_page()
        try:
            await page.goto(info["url"], wait_until="networkidle", timeout=40000)
            await page.wait_for_timeout(3000)
            # Clica em todos os acordeons individualmente
            for sel in ["[data-toggle='collapse']", "button[aria-expanded='false']", "summary", ".accordion-toggle"]:
                for el in (await page.query_selector_all(sel))[:40]:
                    try:
                        await el.scroll_into_view_if_needed()
                        await el.click(timeout=1500)
                        await page.wait_for_timeout(500)
                    except: pass
            # Scroll para carregar lazy content
            for _ in range(6):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(400)
            await page.wait_for_timeout(2000)

            links = await page.evaluate("""
                () => {
                    const seen = new Set(), out = [];
                    for (const a of document.querySelectorAll('a[href]')) {
                        const h = a.href;
                        if (!h || seen.has(h)) continue;
                        if (h.includes('.pdf') || h.includes('planalto.gov.br') ||
                            h.includes('in.gov.br/web/dou') || h.includes('antigo.anvisa') ||
                            (h.includes('agricultura.gov.br') && h.includes('pdf')) ||
                            h.includes('fao.org')) {
                            seen.add(h);
                            out.push({url: h, texto: (a.textContent||'').trim().slice(0,120)});
                        }
                    }
                    return out;
                }
            """)
            print(f"   📎 {len(links)} links encontrados")

            for lk in links:
                if contador[0] >= MAX_DOCS: break
                url = lk.get("url","")
                if not url or len(url) < 10: continue
                chave = gerar_chave(url)
                try:
                    if ".pdf" in url.lower() or "antigo.anvisa" in url:
                        r = await client.get(url, timeout=20.0)
                        if r.status_code != 200: continue
                        conteudo = extrair_pdf(r.content)
                    elif "planalto.gov.br" in url:
                        p2 = await context.new_page()
                        try:
                            await p2.goto(url, wait_until="domcontentloaded", timeout=15000)
                            await p2.wait_for_timeout(1000)
                            conteudo = extrair_html(await p2.content())
                        finally: await p2.close()
                    else:
                        r = await client.get(url, timeout=15.0)
                        if r.status_code != 200: continue
                        conteudo = extrair_html(r.text)

                    if len(conteudo) < 50: continue
                    doc = {"chave": chave, "titulo": lk.get("texto","") or chave,
                           "fonte": url, "orgao": info["orgao"], "categoria": info["categoria"],
                           "conteudo": conteudo, "tamanho_chars": len(conteudo)}
                    st = await salvar(client, doc)
                    if "salvo" in st:
                        salvos += 1; contador[0] += 1
                        print(f"   ✅ {chave[:50]}: {st}")
                    elif "mantido" in st:
                        print(f"   ⏭️  {chave[:50]}: {st}")
                except Exception as e:
                    print(f"   ❌ {url[:60]}: {str(e)[:50]}")
                await asyncio.sleep(0.3)
        finally:
            await page.close()
    return salvos

async def main():
    print("="*65)
    print(f"ValidaRótulo KB Crawler v2 — {datetime.now().isoformat()}")
    print(f"OCR={HAS_OCR} | Playwright={HAS_PLAYWRIGHT}")
    print("="*65)
    if not HAS_PLAYWRIGHT:
        print("❌ Playwright obrigatório"); return

    total = 0
    contador = [0]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            locale="pt-BR", timezone_id="America/Sao_Paulo")

        total += await crawl_anvisa_pdfs(contador)
        total += await crawl_planalto(context, contador)
        for pi in MAPA_JS_PAGES:
            if contador[0] >= MAX_DOCS: break
            total += await crawl_js_page(context, pi, contador)

        await context.close()
        await browser.close()

    print("\n"+"="*65)
    print(f"✅ Crawler v2 concluído | Salvos: {total} | Total: {contador[0]}")
    print("="*65)

if __name__ == "__main__":
    asyncio.run(main())

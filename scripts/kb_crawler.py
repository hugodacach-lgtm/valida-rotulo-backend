#!/usr/bin/env python3
"""
ValidaRótulo IA — KB Crawler
Usa Playwright (browser headless) para acessar páginas JS do MAPA e ANVISA,
extrai links de PDF, baixa, extrai texto e salva no Supabase.

Roda via GitHub Actions semanalmente. Não requer Render.
"""

import asyncio
import os
import re
import json
import hashlib
from datetime import datetime
from urllib.parse import urljoin, urlparse

import httpx

# Playwright para renderizar páginas JS
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# pypdf para extrair texto
try:
    from pypdf import PdfReader
    import io
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# ── Configuração ──────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]  # service key para escrita

MAX_CHARS = 6000   # máximo de texto por documento
MAX_PDFS  = 200    # limite de segurança total por execução

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}

# ── Páginas-alvo (JS renderizado) ────────────────────────────────────────────
MAPA_JS_PAGES = [
    {
        "url": "https://www.gov.br/agricultura/pt-br/assuntos/defesa-agropecuaria/suasa/regulamentos-tecnicos-de-identidade-e-qualidade-de-produtos-de-origem-vegetal",
        "orgao": "MAPA",
        "categoria": "qualidade_vegetal",
        "descricao": "RTIQs Produtos Origem Vegetal",
    },
    {
        "url": "https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-vegetal/legislacao-programas-nacionais-e-seguranca-dos-alimentos-1/legislacao/bebidas",
        "orgao": "MAPA",
        "categoria": "bebidas",
        "descricao": "Legislação Vinhos e Bebidas",
    },
    {
        "url": "https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-vegetal/legislacao-programas-nacionais-e-seguranca-dos-alimentos-1/legislacao/legislacaoPOV",
        "orgao": "MAPA",
        "categoria": "qualidade_vegetal",
        "descricao": "Legislação Produtos Origem Vegetal",
    },
    {
        "url": "https://www.gov.br/agricultura/pt-br/assuntos/defesa-agropecuaria/suasa/regulamentos-tecnicos-de-identidade-e-qualidade-de-produtos-de-origem-animal-1",
        "orgao": "MAPA",
        "categoria": "poa",
        "descricao": "RTIQs Produtos Origem Animal",
    },
]

ANVISA_JS_PAGES = [
    {
        "url": "https://www.gov.br/anvisa/pt-br/assuntos/regulamentacao/legislacao/bibliotecas-tematicas/arquivos/biblioteca-de-alimentos",
        "orgao": "ANVISA",
        "categoria": "alimentos",
        "descricao": "Biblioteca ANVISA — Alimentos",
    },
]

# URLs diretas (sem JS) — complemento
DIRECT_PDF_URLS = [
    # MAPA POA — RTIQs diretos
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN042000salsichamortadelalinguia.pdf", "MAPA", "poa", "in_4_2000_embutidos"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN202000hamburguerapresuntadofiambrekibepresuntocozido.pdf", "MAPA", "poa", "in_20_2000_carneos"),
    # ANVISA — PDFs diretos antigo.anvisa.gov.br
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
    # Planalto — leis estáticas
    ("https://www.planalto.gov.br/ccivil_03/leis/l8918.htm", "PLANALTO", "bebidas", "lei_8918_bebidas"),
    ("https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2009/decreto/d6871.htm", "PLANALTO", "bebidas", "dec_6871_bebidas"),
    ("https://www.planalto.gov.br/ccivil_03/leis/l7678.htm", "PLANALTO", "bebidas", "lei_7678_vinho"),
    ("https://www.planalto.gov.br/ccivil_03/leis/2003/l10831.htm", "PLANALTO", "organicos", "lei_10831_organicos"),
    ("https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/decreto/d6323.htm", "PLANALTO", "organicos", "dec_6323_organicos"),
    ("https://www.planalto.gov.br/ccivil_03/decreto-lei/del0986.htm", "PLANALTO", "geral", "dec_lei_986_1969"),
]


# ── Utilitários ───────────────────────────────────────────────────────────────
def gerar_chave(url: str) -> str:
    """Gera uma chave única baseada na URL."""
    nome = urlparse(url).path.split("/")[-1]
    nome = re.sub(r"\.(pdf|htm|html)$", "", nome, flags=re.I)
    nome = re.sub(r"[^a-z0-9_]", "_", nome.lower())[:60]
    if not nome:
        nome = hashlib.md5(url.encode()).hexdigest()[:12]
    return nome


def extrair_texto_pdf(conteudo_bytes: bytes, max_chars: int = MAX_CHARS) -> str:
    """Extrai texto de PDF em bytes."""
    if not HAS_PYPDF:
        return ""
    try:
        reader = PdfReader(io.BytesIO(conteudo_bytes))
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() or ""
            if len(texto) >= max_chars:
                break
        return texto[:max_chars].strip()
    except Exception:
        return ""


def extrair_texto_html(html: str, max_chars: int = MAX_CHARS) -> str:
    """Extrai texto limpo de HTML."""
    texto = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.I)
    texto = re.sub(r"<style[^>]*>.*?</style>", " ", texto, flags=re.DOTALL | re.I)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto[:max_chars].strip()


async def salvar_supabase(client: httpx.AsyncClient, doc: dict) -> bool:
    """Upsert de um documento no Supabase."""
    try:
        r = await client.post(
            f"{SUPABASE_URL}/rest/v1/kb_documents",
            headers=HEADERS_SB,
            json=doc,
            timeout=10.0,
        )
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"  ⚠️  Supabase erro: {e}")
        return False


# ── Crawler JS (Playwright) ───────────────────────────────────────────────────
async def crawl_js_page(browser, page_info: dict, client: httpx.AsyncClient, contador: list) -> int:
    """
    Abre uma página JS com Playwright, extrai todos os links de PDF,
    baixa cada um e salva no Supabase.
    """
    salvos = 0
    url = page_info["url"]
    orgao = page_info["orgao"]
    categoria = page_info["categoria"]

    print(f"\n🌐 Crawling: {page_info['descricao']}")
    print(f"   URL: {url}")

    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)  # aguarda JS carregar

        # Clica em todos os acordeons/expandíveis
        expandiveis = await page.query_selector_all("[data-toggle='collapse'], .accordion-toggle, button[aria-expanded]")
        for el in expandiveis[:20]:  # máx 20 para não demorar
            try:
                await el.click(timeout=1000)
                await page.wait_for_timeout(300)
            except Exception:
                pass

        # Extrai todos os links de PDF da página renderizada
        links = await page.evaluate("""
            () => {
                const links = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.href;
                    if (href && (
                        href.toLowerCase().includes('.pdf') ||
                        href.includes('planalto.gov.br') ||
                        href.includes('in.gov.br/web/dou') ||
                        href.includes('sislegis') ||
                        href.includes('legisweb')
                    )) {
                        links.push({
                            url: href,
                            texto: (a.textContent || '').trim().substring(0, 100)
                        });
                    }
                });
                return [...new Set(links.map(l => JSON.stringify(l)))].map(s => JSON.parse(s));
            }
        """)

        print(f"   📎 {len(links)} links encontrados")

        for link in links:
            if contador[0] >= MAX_PDFS:
                print(f"   ⚠️  Limite de {MAX_PDFS} PDFs atingido")
                break

            link_url = link.get("url", "")
            link_texto = link.get("texto", "")

            if not link_url or len(link_url) < 10:
                continue

            chave = gerar_chave(link_url)
            is_pdf = ".pdf" in link_url.lower()

            try:
                r = await client.get(link_url, timeout=15.0, follow_redirects=True)
                if r.status_code != 200:
                    continue

                if is_pdf:
                    conteudo = extrair_texto_pdf(r.content)
                else:
                    conteudo = extrair_texto_html(r.text)

                if not conteudo or len(conteudo) < 50:
                    continue

                doc = {
                    "chave": chave,
                    "titulo": link_texto or chave,
                    "fonte": link_url,
                    "orgao": orgao,
                    "categoria": categoria,
                    "conteudo": conteudo,
                    "tamanho_chars": len(conteudo),
                    "atualizado_em": datetime.now().isoformat(),
                }

                ok = await salvar_supabase(client, doc)
                if ok:
                    salvos += 1
                    contador[0] += 1
                    print(f"   ✅ {chave} ({len(conteudo)} chars)")

            except Exception as e:
                print(f"   ❌ {link_url[:60]}: {e}")
                continue

    finally:
        await page.close()

    return salvos


# ── Crawler direto (sem JS) ───────────────────────────────────────────────────
async def crawl_direct_urls(client: httpx.AsyncClient, contador: list) -> int:
    """Crawl de URLs diretas (PDFs e HTMLs estáticos do Planalto)."""
    salvos = 0
    print("\n📥 Crawling URLs diretas...")

    for url, orgao, categoria, chave_sugerida in DIRECT_PDF_URLS:
        if contador[0] >= MAX_PDFS:
            break

        is_pdf = ".pdf" in url.lower()
        chave = chave_sugerida or gerar_chave(url)

        try:
            r = await client.get(url, timeout=15.0, follow_redirects=True)
            if r.status_code != 200:
                print(f"   ⚠️  {chave}: HTTP {r.status_code}")
                continue

            if is_pdf:
                conteudo = extrair_texto_pdf(r.content)
            else:
                conteudo = extrair_texto_html(r.text)

            if not conteudo or len(conteudo) < 50:
                print(f"   ⚠️  {chave}: vazio")
                continue

            doc = {
                "chave": chave,
                "titulo": chave.replace("_", " ").title(),
                "fonte": url,
                "orgao": orgao,
                "categoria": categoria,
                "conteudo": conteudo,
                "tamanho_chars": len(conteudo),
                "atualizado_em": datetime.now().isoformat(),
            }

            ok = await salvar_supabase(client, doc)
            if ok:
                salvos += 1
                contador[0] += 1
                print(f"   ✅ {chave} ({len(conteudo)} chars)")

        except Exception as e:
            print(f"   ❌ {chave}: {e}")

        await asyncio.sleep(0.5)  # throttle

    return salvos


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    print("=" * 60)
    print("ValidaRótulo IA — KB Crawler")
    print(f"Início: {datetime.now().isoformat()}")
    print("=" * 60)

    total_salvos = 0
    contador = [0]  # lista mutável para compartilhar entre funções

    async with httpx.AsyncClient(
        timeout=20.0,
        headers={"User-Agent": "ValidaRotulo-KB-Crawler/1.0"},
        follow_redirects=True,
    ) as client:

        # 1. URLs diretas (sempre funcionam)
        salvos_diretos = await crawl_direct_urls(client, contador)
        total_salvos += salvos_diretos

        # 2. Páginas JS via Playwright
        if HAS_PLAYWRIGHT:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )

                # MAPA páginas JS
                for page_info in MAPA_JS_PAGES:
                    if contador[0] >= MAX_PDFS:
                        break
                    salvos = await crawl_js_page(browser, page_info, client, contador)
                    total_salvos += salvos

                # ANVISA páginas JS
                for page_info in ANVISA_JS_PAGES:
                    if contador[0] >= MAX_PDFS:
                        break
                    salvos = await crawl_js_page(browser, page_info, client, contador)
                    total_salvos += salvos

                await browser.close()
        else:
            print("\n⚠️  Playwright não instalado — pulando páginas JS")

    print("\n" + "=" * 60)
    print(f"✅ Crawler concluído")
    print(f"   Total salvo no Supabase: {total_salvos} documentos")
    print(f"   Fim: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

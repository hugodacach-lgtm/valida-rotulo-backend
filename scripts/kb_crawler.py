#!/usr/bin/env python3
"""
ValidaRótulo IA — KB Crawler v3
Estratégia: URLs DIRETAS apenas — sem JS, sem Planalto (bloqueado por IP cloud)
Fontes que funcionam no GitHub Actions:
  - gov.br/agricultura/.../*.pdf (MAPA direto)
  - antigo.anvisa.gov.br/documents/.../*.pdf (ANVISA legado)
  - in.gov.br/web/dou/- (DOU - funciona)
  - wikisda.agricultura.gov.br (wiki DIPOA - funciona)
"""
import asyncio, os, re, io, hashlib
from datetime import datetime
from urllib.parse import urlparse
import httpx

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
MAX_CHARS = 7000

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

# ═══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO COMPLETO DE URLS DIRETAS — v3
# Todas testadas e confirmadas acessíveis fora de IPs de datacenter
# ═══════════════════════════════════════════════════════════════════════════════

DIRECT_URLS = [

    # ── MAPA — RTIQs POA (PDFs diretos gov.br/agricultura) ─────────────────
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN042000salsichamortadelalinguia.pdf",
     "MAPA","poa","in_4_2000_embutidos_cozidos"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN202000hamburguerapresuntadofiambrekibepresuntocozido.pdf",
     "MAPA","poa","in_20_2000_hamburguer_presunto"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN222000chouricosanguitelas.pdf",
     "MAPA","poa","in_22_2000_chourico"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN232000paiocopacarnecarne-de-sol.pdf",
     "MAPA","poa","in_23_2000_paio_copa"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN242000bressaola.pdf",
     "MAPA","poa","in_24_2000_bressaola"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN252000carnesalgadaernesala.pdf",
     "MAPA","poa","in_25_2000_carne_salgada"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN262000charque.pdf",
     "MAPA","poa","in_26_2000_charque"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN272000jerked_beef.pdf",
     "MAPA","poa","in_27_2000_jerked_beef"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN302000patefinacrocantepatedefigado.pdf",
     "MAPA","poa","in_30_2000_pate"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN362000queijodecoltagem.pdf",
     "MAPA","poa","in_36_2000_queijo"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN512006sardinha.pdf",
     "MAPA","poa","in_51_2006_sardinha"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN052000embutidoscrus.pdf",
     "MAPA","poa","in_5_2000_embutidos_crus"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN062000embutidosmistas.pdf",
     "MAPA","poa","in_6_2000_embutidos_mistos"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN032000carnesuinatratadasalamediamaturacaoaomanteiga.pdf",
     "MAPA","poa","in_3_2000_carne_suina"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN292000salame.pdf",
     "MAPA","poa","in_29_2000_salame"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN210001bacon.pdf",
     "MAPA","poa","in_21_2000_bacon_barriga"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN162000alevescamarao.pdf",
     "MAPA","poa","in_16_2000_camarao"),
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN182000pescadosalgadossecos.pdf",
     "MAPA","poa","in_18_2000_bacalhau"),

    # ── MAPA — Wiki SDA (DIPOA) — RTIQs em PDF wiki ────────────────────────
    ("https://wikisda.agricultura.gov.br/dipoa_baselegal/in_4-2000_linguica_mortadela_salsicha.pdf",
     "MAPA","poa","wiki_in4_linguica_mortadela"),
    ("https://wikisda.agricultura.gov.br/dipoa_baselegal/in_17-2018_rt_c%C3%A1rneos_temperados.pdf",
     "MAPA","poa","wiki_in17_carneos_temperados"),
    ("https://wikisda.agricultura.gov.br/dipoa_baselegal/in_30-2018_manual_de_metodos_oficiais_de_analises.pdf",
     "MAPA","poa","wiki_in30_metodos_analises"),
    ("https://wikisda.agricultura.gov.br/dipoa_baselegal/in_16-2005_bebida_l%C3%A1ctea.pdf",
     "MAPA","poa","wiki_in16_bebida_lactea"),

    # ── ANVISA — PDFs diretos antigo.anvisa.gov.br ─────────────────────────
    ("https://antigo.anvisa.gov.br/documents/10181/3882585/RDC_429_2020_.pdf",
     "ANVISA","rotulagem","rdc_429_2020_rotulagem_nutri"),
    ("https://antigo.anvisa.gov.br/documents/10181/3882585/IN+75_2020_.pdf",
     "ANVISA","rotulagem","in_75_2020_porcoes"),
    ("https://antigo.anvisa.gov.br/documents/10181/2054761/RDC_727_2022_.pdf",
     "ANVISA","rotulagem","rdc_727_2022_rotulagem_geral"),
    ("https://antigo.anvisa.gov.br/documents/10181/2054761/RDC_715_2022_.pdf",
     "ANVISA","rotulagem","rdc_715_2022_lactose"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+264_2005.pdf",
     "ANVISA","alimentos","rdc_264_chocolate"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+266_2005.pdf",
     "ANVISA","alimentos","rdc_266_sorvetes"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+268_2005.pdf",
     "ANVISA","alimentos","rdc_268_proteina_vegetal"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+270+de+22+de+setembro+de+2005.pdf",
     "ANVISA","alimentos","rdc_270_oleos"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+272_2005.pdf",
     "ANVISA","alimentos","rdc_272_vegetais"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+263_2005.pdf",
     "ANVISA","alimentos","rdc_263_cereais"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+265_2005.pdf",
     "ANVISA","alimentos","rdc_265_amido"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+267_2005.pdf",
     "ANVISA","alimentos","rdc_267_cogumelos"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+269_2005.pdf",
     "ANVISA","alimentos","rdc_269_proteinas"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+271_2005.pdf",
     "ANVISA","alimentos","rdc_271_acucar"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+273_2005.pdf",
     "ANVISA","alimentos","rdc_273_enriquecidos"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+274_2005.pdf",
     "ANVISA","bebidas","rdc_274_bebidas_nao_alc"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+276_2005.pdf",
     "ANVISA","alimentos","rdc_276_condimentos"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+277_2005.pdf",
     "ANVISA","alimentos","rdc_277_cafe_cha"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+278_2005.pdf",
     "ANVISA","alimentos","rdc_278_vinagre"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+259_2002.pdf",
     "ANVISA","rotulagem","rdc_259_2002_rotulagem_geral"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+2+2007+Aromas.pdf",
     "ANVISA","aditivos","rdc_2_2007_aromas"),
    ("https://antigo.anvisa.gov.br/documents/33916/392655/RDC+42_2013_contaminantes.pdf",
     "ANVISA","alimentos","rdc_42_2013_contaminantes"),
    ("https://antigo.anvisa.gov.br/documents/10181/6485886/RDC_843_2024_.pdf",
     "ANVISA","alimentos","rdc_843_2024"),
    ("https://antigo.anvisa.gov.br/documents/10181/6636520/RDC_851_2024_.pdf",
     "ANVISA","alimentos","rdc_851_2024"),
    ("https://antigo.anvisa.gov.br/documents/10181/6875868/RDC_920_2024_.pdf",
     "ANVISA","alimentos","rdc_920_2024"),
    ("https://antigo.anvisa.gov.br/documents/10181/6875868/RDC_916_2024_.pdf",
     "ANVISA","alimentos","rdc_916_2024"),
    ("https://antigo.anvisa.gov.br/documents/10181/2867955/RDC_243_2018_.pdf",
     "ANVISA","suplementos","rdc_243_2018_suplementos"),
    ("https://antigo.anvisa.gov.br/documents/10181/3933482/IN_28_2018_.pdf",
     "ANVISA","suplementos","in_28_2018_suplementos"),

    # ── DOU / in.gov.br — Instruções Normativas MAPA (funciona) ────────────
    ("https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-36-de-20-de-setembro-de-2018-42584174",
     "MAPA","bebidas","in_36_2018_bebidas"),
    ("https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-49-de-23-de-outubro-de-2019-223577337",
     "MAPA","qualidade_vegetal","in_49_2019_qualidade"),
    ("https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-41-de-17-de-julho-de-2019-206395862",
     "MAPA","bebidas","in_41_2019_kombucha"),
    ("https://www.in.gov.br/en/web/dou/-/portaria-mapa-n-521-de-1-de-dezembro-de-2022-447310581",
     "MAPA","qualidade_vegetal","portaria_521_2022"),
    ("https://www.in.gov.br/en/web/dou/-/portaria-mapa-n-586-de-16-de-maio-de-2023-486234511",
     "MAPA","bebidas","portaria_586_2023"),
    ("https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-9-de-22-de-novembro-de-2019-229634516",
     "MAPA","poa","in_9_2019_rotulagem_poa"),
    ("https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-65-de-21-de-novembro-de-2019-229567232",
     "MAPA","bebidas","in_65_2019_cerveja"),
    ("https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-17-de-19-de-junho-de-2020-262948007",
     "MAPA","poa","in_17_2020_sisbi_poa"),
    ("https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-16-de-23-de-junho-de-2015-1139827",
     "MAPA","poa","in_16_2015_agroind_pequeno_porte"),

    # ── CONAR / FAO Codex ───────────────────────────────────────────────────
    ("https://www.conar.org.br/pdf/codigo-conar-2021.pdf",
     "CONAR","publicidade","codigo_conar_2021"),
    ("https://www.fao.org/fao-who-codexalimentarius/codex-texts/dbs/CXS/en/?freetext=labelling",
     "FAO","rotulagem","fao_codex_labelling"),

    # ── INMETRO ─────────────────────────────────────────────────────────────
    ("https://www.inmetro.gov.br/legislacao/rtac/pdf/RTAC002688.pdf",
     "INMETRO","metrologia","rtac_2688_conteudo_liquido"),
    ("https://www.inmetro.gov.br/legislacao/rtac/pdf/RTAC002152.pdf",
     "INMETRO","metrologia","rtac_2152_carnes"),

    # ── Cartilhão de Bebidas MAPA (PDF consolidado) ─────────────────────────
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-vegetal/legislacao-de-produtos-origem-vegetal/biblioteca-de-normas-vinhos-e-bebidas/Instrucao_Normativa_140_2024.pdf",
     "MAPA","bebidas","in_140_2024_cartilhao_bebidas"),

    # ── MAPA — Portaria 146/1996 RTIQs lácteos ─────────────────────────────
    ("https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/portarias/portaria-146.pdf",
     "MAPA","poa","portaria_146_1996_rtiq_lacteos"),

    # ── ADAB/BA — SIE Bahia ─────────────────────────────────────────────────
    ("http://www.adab.ba.gov.br/modules/conteudo/conteudo.php?conteudo=22",
     "ADAB","sie_ba","adab_ba_legislacao"),

    # ── ADAGRI/CE — SIE Ceará ───────────────────────────────────────────────
    ("https://www.adagri.ce.gov.br/legislacao-sie/",
     "ADAGRI","sie_ce","adagri_ce_legislacao_sie"),
]


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
            pass
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
    novo = len(doc.get("conteudo", ""))
    if novo < 50: return "vazio"
    existente = await get_existing(client, doc["chave"])
    if existente >= novo: return f"mantido ({existente}>={novo})"
    try:
        r = await client.post(f"{SUPABASE_URL}/rest/v1/kb_documents",
            headers={**HEADERS_SB, "Prefer": "resolution=merge-duplicates"},
            json={**doc, "atualizado_em": datetime.now().isoformat()})
        return f"salvo ({novo}c)" if r.status_code in (200,201) else f"HTTP {r.status_code}"
    except Exception as e:
        return f"erro: {str(e)[:40]}"


async def main():
    print("="*65)
    print(f"ValidaRótulo KB Crawler v3 — {datetime.now().isoformat()}")
    print(f"Estratégia: URLs diretas | OCR={HAS_OCR} | Total URLs={len(DIRECT_URLS)}")
    print("="*65)

    total_salvos = 0
    total_mantidos = 0
    total_falhos = 0

    async with httpx.AsyncClient(
        timeout=25.0,
        headers=BROWSER_HEADERS,
        follow_redirects=True,
    ) as client:
        for url, orgao, categoria, chave in DIRECT_URLS:
            is_pdf = ".pdf" in url.lower()
            try:
                r = await client.get(url, timeout=20.0)
                if r.status_code != 200:
                    print(f"  ⚠️  {chave}: HTTP {r.status_code}")
                    total_falhos += 1
                    continue

                conteudo = extrair_pdf(r.content) if is_pdf else extrair_html(r.text)

                if len(conteudo) < 50:
                    print(f"  ⚠️  {chave}: vazio (OCR={HAS_OCR})")
                    total_falhos += 1
                    continue

                doc = {
                    "chave": chave,
                    "titulo": chave.replace("_"," ").title(),
                    "fonte": url,
                    "orgao": orgao,
                    "categoria": categoria,
                    "conteudo": conteudo,
                    "tamanho_chars": len(conteudo),
                }
                st = await salvar(client, doc)

                if "salvo" in st:
                    total_salvos += 1
                    print(f"  ✅ {chave}: {st}")
                elif "mantido" in st:
                    total_mantidos += 1
                    print(f"  ⏭️  {chave}: {st}")
                else:
                    total_falhos += 1
                    print(f"  ❌ {chave}: {st}")

            except Exception as e:
                print(f"  ❌ {chave}: {str(e)[:80]}")
                total_falhos += 1

            await asyncio.sleep(0.4)

    print("\n" + "="*65)
    print(f"✅ Salvos: {total_salvos} | ⏭️  Mantidos: {total_mantidos} | ❌ Falhos: {total_falhos}")
    print(f"Total na KB: ~{19 + total_salvos} documentos")
    print(f"Fim: {datetime.now().isoformat()}")
    print("="*65)


if __name__ == "__main__":
    asyncio.run(main())

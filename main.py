import os, base64, json, io, asyncio
import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ValidaRótulo IA v4")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ─── KNOWLEDGE BASE ───────────────────────────────────────────────────────────
MAPA_URLS = {
    "embutidos":     ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN042000salsichamortadelalinguia.pdf"],
    "presunto":      ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7652023RTIQpresunto.pdf"],
    "hamburguer":    ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7242022RThamburguer1.pdf"],
    "bacon":         ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/copy_of_Port7482023RTbacon.pdf"],
    "carne_moida":   ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port6642022RTIQcarnemoda1.pdf"],
    "salame":        ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN222000RTsalamesalaminhocopaprescrupresparmalingcolpepperoni.pdf"],
    "charque":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN922020RTCharqueCarneSalgadaMidoSalgado.pdf"],
    "fiambre":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7062022RTIQfiambre.pdf"],
    "carne_maturada":["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7232022RTcarnematuradabovino.pdf"],
    "nomenclatura":  ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port14852025PadrocategoriaenomeclaturaPOA.pdf"],
}

_kb_cache: dict = {}

async def fetch_pdf_text(url: str) -> str:
    try:
        from pypdf import PdfReader
        async with httpx.AsyncClient(timeout=20.0) as c:
            r = await c.get(url, follow_redirects=True)
            if r.status_code != 200: return ""
            reader = PdfReader(io.BytesIO(r.content))
            return "".join(p.extract_text() or "" for p in reader.pages).strip()[:4000]
    except Exception:
        return ""

async def get_kb_for_category(category: str) -> str:
    if category in _kb_cache: return _kb_cache[category]
    urls = MAPA_URLS.get(category, [])
    if not urls: return ""
    texts = await asyncio.gather(*[fetch_pdf_text(u) for u in urls])
    result = "\n\n".join(t for t in texts if t)
    _kb_cache[category] = result
    return result

def detect_category(obs: str) -> str:
    o = obs.lower()
    if any(w in o for w in ["salsicha","linguiça","mortadela"]): return "embutidos"
    if "presunto" in o: return "presunto"
    if "hamburguer" in o or "hambúrguer" in o: return "hamburguer"
    if "bacon" in o: return "bacon"
    if "carne moida" in o or "carne moída" in o: return "carne_moida"
    if "salame" in o: return "salame"
    if "charque" in o: return "charque"
    if "fiambre" in o: return "fiambre"
    if "mel" in o: return "mel"
    return ""

# ─── SYSTEM PROMPTS ───────────────────────────────────────────────────────────
SP_VALIDACAO = """Você é ValidaRótulo IA — o mais preciso sistema de validação de rótulos de produtos de origem animal do Brasil.

REGRA ABSOLUTA: Você NUNCA pula nenhum dos 12 campos. Se não visível: registre como AUSENTE.
REGRA DE CONSISTÊNCIA: Baseie respostas SOMENTE no que está VISÍVEL na imagem.

{kb_section}

## PASSO 1 — IDENTIFICAÇÃO DO PRODUTO
- Nome completo do produto
- Espécie animal (bovino, suíno, frango/peru, pescado, caprino, bubalino, abelha, etc.)
- Categoria (in natura, embutido cozido, embutido frescal, curado/defumado, laticínio fresco, laticínio maturado, mel, ovo, conserva)
- Tipo de inspeção: SIF (federal), SIE (estadual), SIM (municipal)
- Número de registro no carimbo

## PASSO 2 — LEGISLAÇÕES APLICÁVEIS
NORMAS GERAIS: IN 22/2005 (MAPA) | RDC 429/2020 + IN 75/2020 (ANVISA) | RDC 727/2022 (ANVISA) | INMETRO 249/2021

NORMAS ESPECÍFICAS:
- Queijo fresco: IN 30/2001 + Port. 146/1996 | Mussarela: Port. 352/1997 | Requeijão: Port. 359/1997
- Salsicha/Mortadela/Linguiça: IN 04/2000 | Salame: IN 22/2000 | Presunto: Port. 765/2023
- Bacon: Port. 748/2023 | Hambúrguer: Port. 724/2022 | Carne moída: Port. 664/2022
- Charque: IN 92/2020 | Mel: Port. SDA 795/2023 | Pescado: IN 53/2020 + Port. 570/2023
- Aves: Port. SDA 1485/2025 | Ovos: Port. MAPA 1/2020

## PASSO 3 — VALIDAÇÃO CAMPO A CAMPO (12 campos obrigatórios)

✅ CONFORME — [o que está correto] (norma)
❌ NÃO CONFORME — [problema] → [como corrigir] (norma)
⚠️ AUSENTE — [campo faltando] → [o que deve constar] (norma)

CAMPO 1 — DENOMINAÇÃO DE VENDA: nome específico conforme MAPA/DIPOA. Queijos: Port. 146/96. Embutidos: RTIQ.
CAMPO 2 — LISTA DE INGREDIENTES: "Ingredientes:" em ordem decrescente. Aditivos com função + INS.
CAMPO 3 — CONTEÚDO LÍQUIDO: g/kg ou mL/L no painel principal. Fonte mínima: ≤50g=2mm, 50-200g=3mm, 200g-1kg=4mm, >1kg=6mm. "Peso da embalagem" NÃO substitui.
CAMPO 4 — FABRICANTE: razão social + endereço completo (rua, número, cidade, estado).
CAMPO 5 — LOTE: precedido de "L" ou "Lote". Deve ser legível.
CAMPO 6 — PRAZO DE VALIDADE: "Consumir até" + data. ≤90 dias=dia+mês. >90 dias=mês+ano.
CAMPO 7 — CONSERVAÇÃO: temperatura específica + instruções pós-abertura.
CAMPO 8 — CARIMBO SIF/SIE/SIM: carimbo oval com tipo + número do estabelecimento, legível.
CAMPO 9 — TABELA NUTRICIONAL: energia(kcal+kJ), carboidratos, açúcares totais, açúcares adicionados, proteínas, gorduras totais, saturadas, trans, fibra, sódio. Porção: queijos=30g, embutidos=50g, presunto=30g, carnes=100g, pescado=100g, mel=25g.
CAMPO 10 — LUPA FRONTAL: obrigatória se açúcar adicionado≥15g/100g, gordura saturada≥6g/100g ou sódio≥600mg/100g. Se não visível: NÃO VERIFICÁVEL.
CAMPO 11 — ALÉRGENOS: "Alérgenos:" + todos os presentes. Laticínios: "CONTÉM LEITE E DERIVADOS" obrigatório.
CAMPO 12 — TRANSGÊNICOS: OGM>1%=símbolo T amarelo obrigatório. Se não aplicável: CONFORME.

## PASSO 4 — RELATÓRIO FINAL
### SCORE: [X]/12 campos conformes ([%]%)
### VEREDICTO: APROVADO (11-12) | APROVADO COM RESSALVAS (7-10) | REPROVADO (≤6)
### CORREÇÕES PRIORITÁRIAS: [ordem de importância]
### PONTOS CORRETOS: [campos aprovados]"""

# ─── SEGUNDA LEITURA CRÍTICA (Etapa 4) ───────────────────────────────────────
SP_REVISAO = """Você é um auditor sênior de rotulagem de produtos de origem animal.

Você recebeu o relatório de validação abaixo gerado por um sistema automatizado.
Sua missão é revisar criticamente este relatório e identificar:

1. CAMPOS ESQUECIDOS: algum dos 12 campos obrigatórios não foi avaliado?
2. ERROS DE JULGAMENTO: algum campo foi marcado como CONFORME quando deveria ser NÃO CONFORME ou vice-versa?
3. NORMAS INCORRETAS: alguma norma citada está errada ou desatualizada?
4. OMISSÕES CRÍTICAS: existe algum erro grave que o relatório não apontou?

Os 12 campos obrigatórios são:
1. Denominação de venda | 2. Lista de ingredientes | 3. Conteúdo líquido
4. Fabricante | 5. Lote | 6. Prazo de validade | 7. Conservação
8. Carimbo SIF/SIE/SIM | 9. Tabela nutricional | 10. Lupa frontal
11. Alérgenos | 12. Transgênicos

RELATÓRIO A REVISAR:
{relatorio}

---
Responda APENAS se encontrar problemas reais. Se o relatório estiver correto, responda:
"✅ REVISÃO CONCLUÍDA — Relatório sem inconsistências identificadas."

Se encontrar problemas, liste cada um assim:
⚠️ CORREÇÃO [número]: [campo afetado] — [o que está errado no relatório] → [como deveria ser]

Ao final, se houver correções, apresente o SCORE e VEREDICTO revisados."""


async def call_claude_simple(system: str, user: str) -> str:
    """Chamada simples sem streaming — usada para a revisão crítica."""
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "temperature": 0,
        "system": system,
        "messages": [{"role": "user", "content": user}]
    }
    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        if r.status_code != 200: return ""
        data = r.json()
        return data.get("content", [{}])[0].get("text", "")


async def stream_validation(image_b64: str, mime_type: str, obs: str):
    # 1. Busca KB específica da categoria
    category = detect_category(obs)
    kb_text = await get_kb_for_category(category) if category else ""

    kb_section = ""
    if kb_text:
        kb_section = f"## LEGISLAÇÃO ESPECÍFICA — {category.upper()} (fonte: MAPA oficial)\n{kb_text[:3000]}\n---"

    system_prompt = SP_VALIDACAO.format(kb_section=kb_section)
    user_text = "Analise este rótulo e execute os 4 passos obrigatórios. Não pule nenhum dos 12 campos."
    if obs:
        user_text += f"\nObservações: {obs}"

    # 2. PRIMEIRA LEITURA — streaming para o usuário ver em tempo real
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2500,
        "temperature": 0,
        "stream": True,
        "system": system_prompt,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": image_b64}},
            {"type": "text", "text": user_text}
        ]}]
    }

    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}

    relatorio_completo = ""

    async with httpx.AsyncClient(timeout=90.0) as client:
        async with client.stream("POST", "https://api.anthropic.com/v1/messages", json=payload, headers=headers) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                yield f"data: {json.dumps({'error': error_body.decode()})}\n\n"
                return
            async for line in response.aiter_lines():
                if not line.startswith("data: "): continue
                raw = line[6:].strip()
                if raw == "[DONE]": break
                try:
                    ev = json.loads(raw)
                    if ev.get("type") == "content_block_delta":
                        delta = ev.get("delta", {})
                        if delta.get("type") == "text_delta":
                            chunk = delta.get("text", "")
                            relatorio_completo += chunk
                            yield f"data: {json.dumps({'text': chunk})}\n\n"
                except Exception:
                    continue

    # 3. SEGUNDA LEITURA CRÍTICA — revisão do relatório gerado
    yield f"data: {json.dumps({'text': '\n\n---\n\n## REVISÃO CRÍTICA DO RELATÓRIO\n'})}\n\n"

    revisao_prompt = SP_REVISAO.format(relatorio=relatorio_completo)
    revisao = await call_claude_simple(revisao_prompt, "Revise o relatório acima com rigor técnico.")

    if revisao:
        yield f"data: {json.dumps({'text': revisao})}\n\n"

    yield "data: [DONE]\n\n"


@app.post("/validar")
async def validar_rotulo(imagem: UploadFile = File(...), obs: str = Form(default="")):
    if not ANTHROPIC_API_KEY:
        return {"error": "ANTHROPIC_API_KEY não configurada"}
    contents = await imagem.read()
    image_b64 = base64.b64encode(contents).decode("utf-8")
    mime_map = {"image/jpeg":"image/jpeg","image/jpg":"image/jpeg","image/png":"image/png","image/webp":"image/webp","image/gif":"image/gif"}
    mime_type = mime_map.get(imagem.content_type, "image/jpeg")
    return StreamingResponse(stream_validation(image_b64, mime_type, obs), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

@app.get("/")
def health():
    return {"status": "ok", "service": "ValidaRótulo IA v4", "kb_cached": list(_kb_cache.keys())}

@app.get("/kb/preload")
async def preload_kb():
    results = {}
    for category in MAPA_URLS:
        text = await get_kb_for_category(category)
        results[category] = f"{len(text)} chars"
    return {"status": "ok", "loaded": results}

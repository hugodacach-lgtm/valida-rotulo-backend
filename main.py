import os, base64, json, io, asyncio, re
import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ValidaRótulo IA v5")
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
CAMPOS_NOME = {
    1:"Denominação de venda", 2:"Lista de ingredientes", 3:"Conteúdo líquido",
    4:"Fabricante", 5:"Lote", 6:"Prazo de validade", 7:"Conservação",
    8:"Carimbo SIF/SIE/SIM", 9:"Tabela nutricional", 10:"Lupa frontal",
    11:"Alérgenos", 12:"Transgênicos"
}

SP_VALIDACAO = """Você é ValidaRótulo IA — o mais preciso sistema de validação de rótulos de produtos de origem animal do Brasil.

REGRA ABSOLUTA: Você NUNCA pula nenhum dos 12 campos. Se não visível: registre como AUSENTE.
REGRA DE CONSISTÊNCIA: Baseie respostas SOMENTE no que está VISÍVEL na imagem.

{kb_section}

## PASSO 1 — IDENTIFICAÇÃO DO PRODUTO
- Nome completo, espécie animal, categoria, tipo de inspeção SIF/SIE/SIM, número de registro

## PASSO 2 — LEGISLAÇÕES APLICÁVEIS
NORMAS GERAIS: IN 22/2005 | RDC 429/2020 + IN 75/2020 | RDC 727/2022 | INMETRO 249/2021
NORMAS ESPECÍFICAS: Queijo fresco: IN 30/2001 + Port. 146/1996 | Embutidos: IN 04/2000 | Presunto: Port. 765/2023 | Bacon: Port. 748/2023 | Hambúrguer: Port. 724/2022 | Mel: Port. SDA 795/2023

## PASSO 3 — VALIDAÇÃO CAMPO A CAMPO (12 campos obrigatórios)
✅ CONFORME — [o que está correto] (norma)
❌ NÃO CONFORME — [problema] → [como corrigir] (norma)
⚠️ AUSENTE — [campo faltando] → [o que deve constar] (norma)

CAMPO 1 — DENOMINAÇÃO DE VENDA | CAMPO 2 — LISTA DE INGREDIENTES
CAMPO 3 — CONTEÚDO LÍQUIDO ("Peso da embalagem" NÃO substitui)
CAMPO 4 — FABRICANTE (razão social + endereço completo)
CAMPO 5 — LOTE (precedido de "L") | CAMPO 6 — PRAZO DE VALIDADE
CAMPO 7 — CONSERVAÇÃO | CAMPO 8 — CARIMBO SIF/SIE/SIM
CAMPO 9 — TABELA NUTRICIONAL (energia kcal+kJ, carboidratos, açúcares totais, açúcares adicionados, proteínas, gorduras totais, saturadas, trans, fibra, sódio)
CAMPO 10 — LUPA FRONTAL (obrigatória: açúcar adicionado≥15g/100g, gordura saturada≥6g/100g ou sódio≥600mg/100g)
CAMPO 11 — ALÉRGENOS | CAMPO 12 — TRANSGÊNICOS

## PASSO 4 — RELATÓRIO FINAL
### SCORE: [X]/12 campos conformes ([%]%)
### VEREDICTO: APROVADO (11-12) | APROVADO COM RESSALVAS (7-10) | REPROVADO (≤6)
### CORREÇÕES PRIORITÁRIAS: [lista]
### PONTOS CORRETOS: [lista]"""

SP_REVISAO = """Você é auditor sênior de rotulagem de POA. Revise o relatório abaixo em no máximo 200 palavras.
Verifique APENAS: algum dos 12 campos foi pulado? Algum campo foi julgado errado?

RELATÓRIO:
{relatorio}

Se correto: "✅ REVISÃO — Nenhuma inconsistência encontrada."
Se houver erros: liste apenas os erros reais: ⚠️ Campo X: [problema] → [correção]
Seja extremamente conciso."""

SP_CRIACAO = """Você é um especialista em rotulagem de produtos de origem animal no Brasil.

Com base nas informações fornecidas pelo usuário, gere TODOS os campos obrigatórios do rótulo,
já adequados às legislações vigentes (IN 22/2005, RDC 429/2020, IN 75/2020, RDC 727/2022, INMETRO 249/2021 e RTIQs específicos).

Retorne APENAS um JSON válido, sem markdown, sem explicações, exatamente neste formato:
{{
  "denominacao": "Nome oficial do produto conforme nomenclatura MAPA",
  "ingredientes": "Ingredientes: [lista em ordem decrescente com aditivos e INS]",
  "conteudo_liquido": "XXXg",
  "fabricante": "Razão Social completa\\nEndereço completo, Cidade - UF\\nCNPJ: XX.XXX.XXX/XXXX-XX",
  "lote": "L[XXXXXX]",
  "validade": "Consumir até: [instruções de como preencher]",
  "conservacao": "Manter refrigerado entre X°C e X°C. Após aberto, consumir em X dias.",
  "carimbo": "SIF/SIE/SIM Nº [número]",
  "porcao": "XXg",
  "tabela_nutricional": {{
    "porcao": "XXg (X porções por embalagem)",
    "energia_kcal": "XXX",
    "energia_kj": "XXX",
    "carboidratos": "Xg",
    "acucares_totais": "Xg",
    "acucares_adicionados": "Xg",
    "proteinas": "Xg",
    "gorduras_totais": "Xg",
    "gorduras_saturadas": "Xg",
    "gorduras_trans": "0g",
    "fibra": "Xg",
    "sodio": "XXXmg"
  }},
  "lupa_necessaria": true/false,
  "lupa_motivo": "Se necessária: qual nutriente justifica (ex: sódio 720mg/100g ≥ 600mg)",
  "alergenos": "Alérgenos: CONTÉM [lista]. NÃO CONTÉM GLÚTEN.",
  "transgenicos": "Texto sobre transgênicos ou vazio se não aplicável",
  "legislacoes": ["lista das normas aplicadas"],
  "observacoes_rt": "Instruções importantes para o responsável técnico sobre este rótulo"
}}"""

# ─── HELPERS ──────────────────────────────────────────────────────────────────
async def call_claude_simple(system: str, user: str, max_tokens: int = 350) -> str:
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens, "temperature": 0,
        "system": system,
        "messages": [{"role": "user", "content": user}]
    }
    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        if r.status_code != 200: return ""
        return r.json().get("content", [{}])[0].get("text", "")

def detectar_status_campo(texto: str, campo: int) -> str:
    nome = CAMPOS_NOME.get(campo, "")
    linhas = texto.split("\n")
    for i, linha in enumerate(linhas):
        if f"CAMPO {campo}" in linha.upper() or (nome and nome.upper() in linha.upper()):
            trecho = " ".join(linhas[i:i+5]).upper()
            if "NÃO CONFORME" in trecho or "NAO CONFORME" in trecho: return "NAO_CONFORME"
            elif "AUSENTE" in trecho: return "AUSENTE"
            elif "CONFORME" in trecho: return "CONFORME"
    return "NAO_DETECTADO"

def extrair_score(texto: str):
    m = re.search(r"SCORE[:\s]+(\d+)\s*/\s*12", texto, re.IGNORECASE)
    return int(m.group(1)) if m else None

def extrair_veredicto(texto: str) -> str:
    m = re.search(r"VEREDICTO[:\s]+(APROVADO COM RESSALVAS|APROVADO|REPROVADO)", texto, re.IGNORECASE)
    return m.group(1).upper() if m else "NÃO IDENTIFICADO"

# ─── ENDPOINT: VALIDAR (com imagem) ───────────────────────────────────────────
async def stream_validation(image_b64: str, mime_type: str, obs: str):
    category = detect_category(obs)
    kb_text = await get_kb_for_category(category) if category else ""
    kb_section = f"## LEGISLAÇÃO ESPECÍFICA — {category.upper()} (MAPA)\n{kb_text[:3000]}\n---" if kb_text else ""
    system_prompt = SP_VALIDACAO.format(kb_section=kb_section)

    user_text = "Analise este rótulo e execute os 4 passos. Não pule nenhum dos 12 campos."
    if obs: user_text += f"\nObservações: {obs}"

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2500, "temperature": 0, "stream": True,
        "system": system_prompt,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": image_b64}},
            {"type": "text", "text": user_text}
        ]}]
    }
    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    relatorio = ""

    async with httpx.AsyncClient(timeout=90.0) as client:
        async with client.stream("POST", "https://api.anthropic.com/v1/messages", json=payload, headers=headers) as response:
            if response.status_code != 200:
                yield f"data: {json.dumps({'error': (await response.aread()).decode()})}\n\n"
                return
            async for line in response.aiter_lines():
                if not line.startswith("data: "): continue
                raw = line[6:].strip()
                if raw == "[DONE]": break
                try:
                    ev = json.loads(raw)
                    if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                        chunk = ev["delta"]["text"]
                        relatorio += chunk
                        yield f"data: {json.dumps({'text': chunk})}\n\n"
                except Exception: continue

    yield f"data: {json.dumps({'text': '\n\n---\n\n## REVISÃO CRÍTICA\n'})}\n\n"
    revisao = await call_claude_simple(SP_REVISAO.format(relatorio=relatorio), "Revise com rigor técnico.", 350)
    if revisao: yield f"data: {json.dumps({'text': revisao})}\n\n"
    yield "data: [DONE]\n\n"

@app.post("/validar")
async def validar_rotulo(imagem: UploadFile = File(...), obs: str = Form(default="")):
    if not ANTHROPIC_API_KEY: return {"error": "ANTHROPIC_API_KEY não configurada"}
    contents = await imagem.read()
    image_b64 = base64.b64encode(contents).decode("utf-8")
    mime_map = {"image/jpeg":"image/jpeg","image/jpg":"image/jpeg","image/png":"image/png","image/webp":"image/webp","image/gif":"image/gif"}
    mime_type = mime_map.get(imagem.content_type, "image/jpeg")
    return StreamingResponse(stream_validation(image_b64, mime_type, obs),
        media_type="text/event-stream", headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ─── ENDPOINT: CRIAR RÓTULO ───────────────────────────────────────────────────
async def stream_criacao(dados: dict):
    """Gera os campos do rótulo e depois valida automaticamente."""

    # Monta contexto do produto
    categoria = dados.get("categoria", "")
    kb_text = await get_kb_for_category(categoria) if categoria else ""
    kb_context = f"\nLEGISLAÇÃO ESPECÍFICA ({categoria.upper()}):\n{kb_text[:2000]}" if kb_text else ""

    user_text = f"""Gere o rótulo completo para este produto de origem animal.

INFORMAÇÕES DO PRODUTO:
- Produto: {dados.get('produto', '')}
- Categoria: {dados.get('categoria', '')}
- Espécie animal: {dados.get('especie', '')}
- Órgão de inspeção: {dados.get('orgao', '')} Nº {dados.get('num_registro', '')}
- Peso/Volume: {dados.get('peso', '')}
- Fabricante: {dados.get('fabricante', '')}
- Endereço: {dados.get('endereco', '')}
- CNPJ: {dados.get('cnpj', '')}
- Ingredientes (informados pelo produtor): {dados.get('ingredientes', '')}
- Informações nutricionais (se disponível): {dados.get('nutricional', '')}
- Observações adicionais: {dados.get('obs', '')}
{kb_context}

Retorne APENAS o JSON conforme especificado no system prompt."""

    # Etapa 1: Gerar campos do rótulo
    resultado_json = await call_claude_simple(SP_CRIACAO, user_text, max_tokens=1500)

    # Limpa possível markdown
    resultado_json = resultado_json.strip()
    if resultado_json.startswith("```"):
        resultado_json = re.sub(r"```[a-z]*\n?", "", resultado_json).strip().rstrip("```").strip()

    # Envia os campos gerados para o frontend
    yield f"data: {json.dumps({'tipo': 'campos', 'dados': resultado_json})}\n\n"

    # Etapa 2: Valida os campos gerados (sem imagem — valida o texto)
    try:
        campos = json.loads(resultado_json)
    except Exception:
        yield f"data: {json.dumps({'tipo': 'erro', 'msg': 'Erro ao gerar campos do rótulo'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Monta texto para validar
    texto_rotulo = f"""RÓTULO GERADO PARA VALIDAÇÃO:
Denominação: {campos.get('denominacao', '')}
Ingredientes: {campos.get('ingredientes', '')}
Conteúdo líquido: {campos.get('conteudo_liquido', '')}
Fabricante: {campos.get('fabricante', '')}
Lote: {campos.get('lote', '')}
Validade: {campos.get('validade', '')}
Conservação: {campos.get('conservacao', '')}
Carimbo: {campos.get('carimbo', '')}
Tabela nutricional: {json.dumps(campos.get('tabela_nutricional', {}), ensure_ascii=False)}
Lupa necessária: {campos.get('lupa_necessaria', False)} — {campos.get('lupa_motivo', '')}
Alérgenos: {campos.get('alergenos', '')}
Transgênicos: {campos.get('transgenicos', 'Não aplicável')}"""

    sp_val_texto = SP_VALIDACAO.format(kb_section="") + "\n\nNOTA: Não há imagem. Valide com base no texto do rótulo gerado."

    val_payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000, "temperature": 0, "stream": True,
        "system": sp_val_texto,
        "messages": [{"role": "user", "content": f"Valide este rótulo gerado:\n\n{texto_rotulo}"}]
    }
    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    relatorio = ""

    yield f"data: {json.dumps({'tipo': 'validacao_inicio'})}\n\n"

    async with httpx.AsyncClient(timeout=90.0) as client:
        async with client.stream("POST", "https://api.anthropic.com/v1/messages", json=val_payload, headers=headers) as response:
            if response.status_code != 200: return
            async for line in response.aiter_lines():
                if not line.startswith("data: "): continue
                raw = line[6:].strip()
                if raw == "[DONE]": break
                try:
                    ev = json.loads(raw)
                    if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                        chunk = ev["delta"]["text"]
                        relatorio += chunk
                        yield f"data: {json.dumps({'tipo': 'validacao_texto', 'text': chunk})}\n\n"
                except Exception: continue

    yield "data: [DONE]\n\n"

@app.post("/criar")
async def criar_rotulo(
    produto: str = Form(...),
    categoria: str = Form(default=""),
    especie: str = Form(default=""),
    orgao: str = Form(default="SIM"),
    num_registro: str = Form(default=""),
    peso: str = Form(default=""),
    fabricante: str = Form(default=""),
    endereco: str = Form(default=""),
    cnpj: str = Form(default=""),
    ingredientes: str = Form(default=""),
    nutricional: str = Form(default=""),
    obs: str = Form(default=""),
    documento: UploadFile = File(default=None)
):
    if not ANTHROPIC_API_KEY: return {"error": "ANTHROPIC_API_KEY não configurada"}

    dados = {
        "produto": produto, "categoria": categoria, "especie": especie,
        "orgao": orgao, "num_registro": num_registro, "peso": peso,
        "fabricante": fabricante, "endereco": endereco, "cnpj": cnpj,
        "ingredientes": ingredientes, "nutricional": nutricional, "obs": obs
    }

    # Se enviou documento, extrai texto
    if documento and documento.filename:
        try:
            content = await documento.read()
            if documento.content_type == "application/pdf":
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content))
                doc_text = " ".join(p.extract_text() or "" for p in reader.pages)
                dados["obs"] += f"\nCONTEÚDO DO DOCUMENTO:\n{doc_text[:3000]}"
        except Exception:
            pass

    return StreamingResponse(stream_criacao(dados),
        media_type="text/event-stream", headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ─── EVAL ENDPOINT ────────────────────────────────────────────────────────────
@app.post("/eval")
async def avaliar_rotulo(imagem: UploadFile = File(...), gabarito: str = Form(...)):
    if not ANTHROPIC_API_KEY: return JSONResponse({"error": "ANTHROPIC_API_KEY não configurada"})
    try: gab = json.loads(gabarito)
    except Exception: return JSONResponse({"error": "Gabarito inválido"})

    contents = await imagem.read()
    image_b64 = base64.b64encode(contents).decode("utf-8")
    mime_map = {"image/jpeg":"image/jpeg","image/jpg":"image/jpeg","image/png":"image/png","image/webp":"image/webp"}
    mime_type = mime_map.get(imagem.content_type, "image/jpeg")

    categoria = gab.get("categoria", "")
    obs = f"{gab.get('produto','')} {categoria}".strip()
    kb_text = await get_kb_for_category(detect_category(obs))
    kb_section = f"## LEGISLAÇÃO ({categoria.upper()})\n{kb_text[:3000]}\n---" if kb_text else ""
    system_prompt = SP_VALIDACAO.format(kb_section=kb_section)

    user_text = f"Valide este rótulo. Produto: {obs}"
    payload = {
        "model": "claude-sonnet-4-20250514", "max_tokens": 2500, "temperature": 0, "stream": True,
        "system": system_prompt,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": image_b64}},
            {"type": "text", "text": user_text}
        ]}]
    }
    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    relatorio = ""

    async with httpx.AsyncClient(timeout=90.0) as client:
        async with client.stream("POST", "https://api.anthropic.com/v1/messages", json=payload, headers=headers) as response:
            if response.status_code != 200: return JSONResponse({"error": "Erro na API"})
            async for line in response.aiter_lines():
                if not line.startswith("data: "): continue
                raw = line[6:].strip()
                if raw == "[DONE]": break
                try:
                    ev = json.loads(raw)
                    if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                        relatorio += ev["delta"]["text"]
                except Exception: continue

    erros_conhecidos = gab.get("erros_conhecidos", [])
    detalhes = [{"campo": e["campo"], "nome": CAMPOS_NOME.get(e["campo"],""), "esperado": e["status"],
                 "detectado": detectar_status_campo(relatorio, e["campo"]),
                 "acertou": detectar_status_campo(relatorio, e["campo"]) == e["status"],
                 "descricao_gabarito": e.get("descricao",""), "norma": e.get("norma","")} for e in erros_conhecidos]

    total = len(detalhes)
    acertos = sum(1 for d in detalhes if d["acertou"])
    return JSONResponse({
        "produto": gab.get("produto",""), "relatorio_completo": relatorio,
        "score_agente": extrair_score(relatorio), "score_esperado": gab.get("score_esperado"),
        "veredicto_agente": extrair_veredicto(relatorio), "veredicto_esperado": gab.get("veredicto_esperado","").upper(),
        "precisao_pct": round(acertos/total*100) if total > 0 else 100,
        "erros_avaliados": total, "erros_acertados": acertos, "detalhes": detalhes
    })


# ─── ENDPOINT: GERAR RÓTULO COM IA (SVG) ─────────────────────────────────────
SP_DESIGNER = """Você é um designer gráfico especialista em rótulos de produtos alimentícios brasileiros.

Sua tarefa é gerar um rótulo COMPLETO em formato SVG, pronto para impressão, com design profissional.

REGRAS OBRIGATÓRIAS:
1. Retorne APENAS o código SVG completo, começando com <svg e terminando com </svg>
2. Sem explicações, sem markdown, sem código fora do SVG
3. O SVG deve ter todos os textos dos campos fornecidos
4. Design limpo, profissional e legível
5. Use cores harmoniosas baseadas na cor principal fornecida
6. A tabela nutricional deve ser visualmente clara e completa
7. Inclua todos os campos obrigatórios da legislação brasileira (IN 22/2005)
8. Se houver logo em base64, inclua-a no SVG usando <image>
9. Tamanho padrão: viewBox="0 0 800 500" para retangular, "0 0 500 500" para redondo

ESTRUTURA ESPERADA DO RÓTULO:
- Topo: nome do produto em destaque + logo da empresa
- Corpo esquerdo: ingredientes, fabricante, conservação, alérgenos
- Corpo direito: tabela nutricional completa
- Rodapé: lote, validade, carimbo SIF/SIE/SIM, código de barras simulado
- Borda e divisores visuais que separam as seções"""

@app.post("/gerar-rotulo")
async def gerar_rotulo_ia(
    produto:      str = Form(...),
    categoria:    str = Form(default=""),
    cor_principal:str = Form(default="#1e3a5f"),
    forma:        str = Form(default="retangular"),
    campos_json:  str = Form(default="{}"),
    logo:         UploadFile = File(default=None)
):
    if not ANTHROPIC_API_KEY:
        return JSONResponse({"error": "ANTHROPIC_API_KEY não configurada"})

    try:
        campos = json.loads(campos_json)
    except Exception:
        campos = {}

    # Monta logo em base64 se enviada
    logo_b64 = ""
    logo_mime = "image/png"
    if logo and logo.filename:
        logo_bytes = await logo.read()
        logo_b64 = base64.b64encode(logo_bytes).decode()
        logo_mime = logo.content_type or "image/png"

    # Monta o prompt com todos os dados
    tn = campos.get("tabela_nutricional", {})
    tn_texto = ""
    if tn:
        tn_texto = f"""Tabela Nutricional (porção {tn.get('porcao','—')}):
- Energia: {tn.get('energia_kcal','—')} kcal / {tn.get('energia_kj','—')} kJ
- Carboidratos: {tn.get('carboidratos','—')}
- Açúcares totais: {tn.get('acucares_totais','—')}
- Açúcares adicionados: {tn.get('acucares_adicionados','—')}
- Proteínas: {tn.get('proteinas','—')}
- Gorduras totais: {tn.get('gorduras_totais','—')}
- Gorduras saturadas: {tn.get('gorduras_saturadas','—')}
- Gorduras trans: {tn.get('gorduras_trans','0g')}
- Fibra alimentar: {tn.get('fibra','—')}
- Sódio: {tn.get('sodio','—')}"""

    lupa = campos.get('lupa_necessaria', False)
    lupa_motivo = campos.get('lupa_motivo', '')

    user_prompt = f"""Crie um rótulo profissional com estas informações:

PRODUTO: {campos.get('denominacao', produto)}
CATEGORIA: {categoria}
FORMA: {forma}
COR PRINCIPAL: {cor_principal}
{'LOGO: fornecida em base64 (inclua no SVG usando <image href="data:' + logo_mime + ';base64,' + logo_b64[:50] + '...">)' if logo_b64 else 'SEM LOGO (crie um placeholder elegante)'}

CAMPOS OBRIGATÓRIOS:
- Ingredientes: {campos.get('ingredientes', '—')}
- Conteúdo líquido: {campos.get('conteudo_liquido', '—')}
- Fabricante: {campos.get('fabricante', '—')}
- Lote: {campos.get('lote', 'L: ______')}
- Validade: {campos.get('validade', 'Consumir até: __/__/____')}
- Conservação: {campos.get('conservacao', '—')}
- Carimbo: {campos.get('carimbo', 'SIM Nº 001')}
- Alérgenos: {campos.get('alergenos', '—')}
- Transgênicos: {campos.get('transgenicos', 'Não contém ingredientes transgênicos')}
{'- LUPA FRONTAL OBRIGATÓRIA: ' + lupa_motivo if lupa else ''}

{tn_texto}

{'Logo em base64 completa: data:' + logo_mime + ';base64,' + logo_b64 if logo_b64 else ''}

Gere o SVG completo agora. Seja criativo e profissional. O rótulo deve parecer feito por um designer gráfico experiente."""

    # Chama Claude para gerar SVG
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "temperature": 1,  # Mais criatividade para design
        "system": SP_DESIGNER,
        "messages": [{"role": "user", "content": user_prompt}]
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        if r.status_code != 200:
            return JSONResponse({"error": "Erro na API Claude: " + str(r.status_code)})
        data = r.json()
        svg_text = data.get("content", [{}])[0].get("text", "")

    # Extrai só o SVG
    import re
    svg_match = re.search(r'<svg[\s\S]*?</svg>', svg_text, re.IGNORECASE | re.DOTALL)
    if svg_match:
        svg_clean = svg_match.group(0)
    else:
        svg_clean = svg_text.strip()

    return JSONResponse({"svg": svg_clean, "produto": produto})


@app.get("/")
def health():
    return {"status": "ok", "service": "ValidaRótulo IA v5", "endpoints": ["/validar","/criar","/eval"]}

@app.get("/kb/preload")
async def preload_kb():
    results = {}
    for cat in MAPA_URLS:
        text = await get_kb_for_category(cat)
        results[cat] = f"{len(text)} chars"
    return {"status": "ok", "loaded": results}

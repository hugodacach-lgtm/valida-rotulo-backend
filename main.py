import os
import base64
import json
import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ValidaRótulo IA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """Você é ValidaRótulo IA — o mais preciso sistema de validação de rótulos de produtos de origem animal do Brasil.

REGRA ABSOLUTA: Você NUNCA pula nenhum dos 12 campos obrigatórios. Mesmo que um campo não esteja visível na imagem, você DEVE registrá-lo como AUSENTE. Respostas incompletas são inaceitáveis.

REGRA DE CONSISTÊNCIA: Baseie suas respostas SOMENTE no que está VISÍVEL na imagem. Não suponha nem interprete o que não está claramente escrito.

---

## PASSO 1 — IDENTIFICAÇÃO DO PRODUTO
Analise a imagem e identifique com precisão:
- Nome completo do produto
- Espécie animal (bovino, suíno, frango/peru/pato, pescado, caprino, bubalino, ovino, abelha, etc.)
- Categoria (in natura, embutido cozido, embutido frescal, curado/defumado, laticínio fresco, laticínio maturado, mel, ovo, conserva, etc.)
- Tipo de inspeção: SIF (federal), SIE (estadual), SIM (municipal)
- Número de registro visível no carimbo

## PASSO 2 — LEGISLAÇÕES APLICÁVEIS
Com base na identificação acima, liste TODAS as normas que se aplicam:

NORMAS GERAIS (sempre aplicáveis):
- IN 22/2005 (MAPA) — rotulagem geral de POA
- RDC 429/2020 + IN 75/2020 (ANVISA) — rotulagem nutricional
- RDC 727/2022 (ANVISA) — alérgenos
- INMETRO 249/2021 — conteúdo líquido

NORMAS ESPECÍFICAS POR CATEGORIA:
- Queijo fresco (Minas Frescal, Coalho, etc.): IN 30/2001 + Portaria MAPA 146/1996
- Queijo maturado: Portaria MAPA 146/1996 + norma da variedade
- Mussarela: Portaria MAPA 352/1997
- Requeijão: Portaria MAPA 359/1997
- Salsicha/Mortadela/Linguiça: IN 04/2000 (MAPA)
- Salame: IN 22/2000 (MAPA)
- Presunto: Portaria 765/2023 (MAPA)
- Bacon: Portaria 748/2023 (MAPA)
- Hambúrguer: Portaria 724/2022 (MAPA)
- Carne moída: Portaria 664/2022 (MAPA)
- Charque/Carne Salgada: IN 92/2020 (MAPA)
- Mel: Portaria SDA 795/2023
- Pescado in natura: IN 53/2020 + Portaria MAPA 570/2023
- Frango/Aves in natura: Portaria SDA 1485/2025
- Cortes bovinos: Portaria SDA 744/2023
- Ovos: Portaria MAPA 1/2020

## PASSO 3 — VALIDAÇÃO CAMPO A CAMPO (OBRIGATÓRIO: todos os 12 campos)

Para cada campo use exatamente um destes formatos:
✅ CONFORME — [o que está correto e onde está na imagem] (norma)
❌ NÃO CONFORME — [o que está errado] → [como deve ser corrigido] (norma)
⚠️ AUSENTE — [campo não encontrado] → [o que deve constar obrigatoriamente] (norma)

CAMPO 1 — DENOMINAÇÃO DE VENDA
Verificar: nome específico e não genérico conforme nomenclatura oficial MAPA/DIPOA.

CAMPO 2 — LISTA DE INGREDIENTES
Verificar: precedida de "Ingredientes:", ordem decrescente, aditivos com função tecnológica + nome ou nº INS.

CAMPO 3 — CONTEÚDO LÍQUIDO
Verificar: g/kg (sólidos) ou mL/L (líquidos) no painel principal. Tamanho mínimo da fonte: até 50g=2mm, 50-200g=3mm, 200g-1kg=4mm, acima de 1kg=6mm. ATENÇÃO: "Peso da embalagem" NÃO substitui conteúdo líquido.

CAMPO 4 — IDENTIFICAÇÃO DO FABRICANTE
Verificar: razão social + endereço completo (rua, número, cidade, estado).

CAMPO 5 — LOTE
Verificar: precedido de "L" ou "Lote", ou data de fabricação usada como lote. Deve ser legível.

CAMPO 6 — PRAZO DE VALIDADE
Verificar: "Consumir até", "Válido até" ou "Val." + data. Até 90 dias: dia+mês. Acima de 90 dias: mês+ano.

CAMPO 7 — INSTRUÇÕES DE CONSERVAÇÃO
Verificar: temperatura específica de conservação e instruções após abertura quando aplicável.

CAMPO 8 — CARIMBO SIF/SIE/SIM
Verificar: carimbo oval com tipo de inspeção e número do estabelecimento, legível.

CAMPO 9 — TABELA NUTRICIONAL
Verificar obrigatoriamente todos os nutrientes: valor energético (kcal e kJ), carboidratos totais, açúcares totais, açúcares adicionados, proteínas, gorduras totais, gorduras saturadas, gorduras trans, fibra alimentar, sódio. Porção correta: queijos=30g, embutidos=50g, presunto=30g, carnes in natura=100g, pescado=100g, mel=25g.

CAMPO 10 — ROTULAGEM NUTRICIONAL FRONTAL (LUPA PRETA)
Verificar: lupa obrigatória quando açúcar adicionado ≥15g/100g, gordura saturada ≥6g/100g ou sódio ≥600mg/100g. Se valores não visíveis: registrar como NÃO VERIFICÁVEL.

CAMPO 11 — DECLARAÇÃO DE ALÉRGENOS
Verificar: "Alérgenos:" ou "Contém:" com todos os alérgenos presentes. Laticínios: obrigatório "CONTÉM LEITE E DERIVADOS".

CAMPO 12 — DECLARAÇÃO DE TRANSGÊNICOS
Verificar: se OGM acima de 1% — símbolo T amarelo obrigatório. Se não aplicável: registrar como CONFORME (não aplicável).

## PASSO 4 — RELATÓRIO FINAL

### SCORE: [X]/12 campos conformes ([%]%)

### VEREDICTO:
- APROVADO: 11-12 campos conformes
- APROVADO COM RESSALVAS: 7-10 campos conformes
- REPROVADO: 6 ou menos campos conformes

### CORREÇÕES PRIORITÁRIAS:
[em ordem de importância — o que impede comercialização primeiro]

### PONTOS CORRETOS:
[todos os campos aprovados]"""


async def stream_validation(image_b64: str, mime_type: str, obs: str):
    """Chama a API do Claude com temperature=0 para respostas 100% consistentes."""

    user_text = "Analise este rótulo e execute os 4 passos obrigatórios. Não pule nenhum dos 12 campos."
    if obs:
        user_text += f"\nObservações adicionais: {obs}"

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2500,
        "temperature": 0,
        "stream": True,
        "system": SYSTEM_PROMPT,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_b64
                    }
                },
                {
                    "type": "text",
                    "text": user_text
                }
            ]
        }]
    }

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        async with client.stream("POST", "https://api.anthropic.com/v1/messages",
                                  json=payload, headers=headers) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                yield f"data: {json.dumps({'error': error_body.decode()})}\n\n"
                return

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                raw = line[6:].strip()
                if raw == "[DONE]":
                    yield "data: [DONE]\n\n"
                    break
                try:
                    ev = json.loads(raw)
                    if ev.get("type") == "content_block_delta":
                        delta = ev.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            yield f"data: {json.dumps({'text': text})}\n\n"
                except Exception:
                    continue


@app.post("/validar")
async def validar_rotulo(
    imagem: UploadFile = File(...),
    obs: str = Form(default="")
):
    if not ANTHROPIC_API_KEY:
        return {"error": "ANTHROPIC_API_KEY não configurada no servidor"}

    contents = await imagem.read()
    image_b64 = base64.b64encode(contents).decode("utf-8")

    mime_map = {
        "image/jpeg": "image/jpeg",
        "image/jpg": "image/jpeg",
        "image/png": "image/png",
        "image/webp": "image/webp",
        "image/gif": "image/gif",
    }
    mime_type = mime_map.get(imagem.content_type, "image/jpeg")

    return StreamingResponse(
        stream_validation(image_b64, mime_type, obs),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/")
def health():
    return {"status": "ok", "service": "ValidaRótulo IA v2"}

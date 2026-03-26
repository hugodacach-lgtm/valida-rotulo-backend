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
    allow_origins=["*"],  # Em produção, trocar pelo domínio do seu frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """Você é ValidaRótulo IA — especialista em validação de rótulos de produtos de origem animal no Brasil.

Analise a imagem do rótulo enviada e siga EXATAMENTE os 4 passos abaixo:

## PASSO 1 — IDENTIFICAÇÃO DO PRODUTO
Identifique:
- Nome do produto
- Espécie animal (bovino, suíno, aves, pescado, caprino, bubalino, etc.)
- Categoria (in natura, embutido, curado, laticínio, mel, ovo, etc.)
- Tipo de inspeção visível: SIF (federal), SIE (estadual) ou SIM (municipal)

## PASSO 2 — LEGISLAÇÕES APLICÁVEIS
Liste as normas específicas para este produto:
- Norma geral de rotulagem: IN 22/2005 (MAPA)
- Norma nutricional: RDC 429/2020 + IN 75/2020 (ANVISA)
- Alérgenos: RDC 727/2022 (ANVISA)
- Conteúdo líquido: INMETRO 249/2021
- RTIQ específico do produto (ex: IN 04/2000 para salsicha/linguiça/mortadela)
- Outras normas aplicáveis

## PASSO 3 — VALIDAÇÃO CAMPO A CAMPO
Para cada campo, use exatamente:
✅ CONFORME — [descrição] (norma)
❌ NÃO CONFORME — [problema] → [como corrigir] (norma)
⚠️ AUSENTE — [campo faltando] → [o que deve constar] (norma)

Campos obrigatórios:
1. Denominação de venda
2. Lista de ingredientes
3. Conteúdo líquido
4. Identificação do fabricante
5. Lote
6. Prazo de validade
7. Instruções de conservação
8. Carimbo SIF/SIE/SIM
9. Tabela nutricional
10. Rotulagem nutricional frontal (lupa)
11. Declaração de alérgenos
12. Declaração de transgênicos (se aplicável)

## PASSO 4 — RELATÓRIO FINAL
### SCORE: [X]/12 campos conformes ([%]%)
### VEREDICTO: APROVADO | APROVADO COM RESSALVAS | REPROVADO
### CORREÇÕES PRIORITÁRIAS:
[lista numerada das correções mais urgentes]
### PONTOS CORRETOS:
[lista do que está em conformidade]"""


async def stream_validation(image_b64: str, mime_type: str, obs: str):
    """Chama a API do Claude e faz streaming da resposta."""

    user_text = "Valide este rótulo de produto de origem animal conforme a legislação brasileira vigente."
    if obs:
        user_text += f"\nObservações do usuário: {obs}"

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
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

    async with httpx.AsyncClient(timeout=60.0) as client:
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
    """Recebe imagem do rótulo e retorna validação em streaming."""

    if not ANTHROPIC_API_KEY:
        return {"error": "ANTHROPIC_API_KEY não configurada no servidor"}

    # Lê e converte imagem para base64
    contents = await imagem.read()
    image_b64 = base64.b64encode(contents).decode("utf-8")

    # Detecta mime type
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
    return {"status": "ok", "service": "ValidaRótulo IA"}

"""
Curador Autônomo de Feedbacks — Inspect-IA / ValidaRótulo IA
=============================================================

FASE 1: Apenas observação. Não escreve na KB.

Lógica:
  1. Busca feedbacks dos últimos 7 dias na tabela `validacoes`
     onde feedback IN ('incorreto', 'parcialmente_correto')
  2. Para cada item, identifica os campos marcados como 'incorreto'
     no JSON `campos_json` + comentários do RT
  3. Busca normas potencialmente relevantes na `kb_documents`
  4. Pede ao Claude que classifique: VALIDADO / REJEITADO / INCONCLUSIVO
  5. Envia relatório semanal por email via Resend

Se não houver feedback negativo na semana, envia um email curto de status
(para Hugo saber que o curador rodou e está vivo).
"""

import os
import json
import sys
import datetime as dt
from typing import Any

import requests
from anthropic import Anthropic

# ───────────────────────────────────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────────────────────────────────

SUPABASE_URL      = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY      = os.environ["SUPABASE_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
RESEND_API_KEY    = os.environ["RESEND_API_KEY"]
EMAIL_DESTINO     = os.environ.get("EMAIL_DESTINO", "hugodacach@gmail.com")

MODELO_CLAUDE = "claude-sonnet-4-5"  # Sonnet 4.5 — rápido, suficiente para classificação
DIAS_LOOKBACK = 7
MAX_NORMAS_KB = 5  # quantas normas mandar pro Claude por feedback

SUPA_HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
}

claude = Anthropic(api_key=ANTHROPIC_API_KEY)


# ───────────────────────────────────────────────────────────────────────────
# 1. BUSCA FEEDBACKS DOS ÚLTIMOS 7 DIAS
# ───────────────────────────────────────────────────────────────────────────

def buscar_feedbacks_negativos() -> list[dict[str, Any]]:
    """Retorna validações com feedback 'incorreto' ou 'parcialmente_correto' nos últimos N dias."""
    cutoff = (dt.datetime.utcnow() - dt.timedelta(days=DIAS_LOOKBACK)).isoformat()
    url = (
        f"{SUPABASE_URL}/rest/v1/validacoes"
        f"?select=*"
        f"&feedback=in.(incorreto,parcialmente_correto)"
        f"&created_at=gte.{cutoff}"
        f"&order=created_at.desc"
    )
    r = requests.get(url, headers=SUPA_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def buscar_normas_relevantes(categoria: str, keywords: str) -> list[dict[str, Any]]:
    """
    Busca até MAX_NORMAS_KB normas na kb_documents que possam ser relevantes
    para o feedback. Estratégia simples: filtrar por categoria + busca textual
    no conteúdo (keywords extraídas do comentário do RT).
    """
    normas: list[dict[str, Any]] = []
    seen_chaves: set[str] = set()

    # Tentativa 1: por categoria exata
    if categoria:
        url = (
            f"{SUPABASE_URL}/rest/v1/kb_documents"
            f"?select=chave,titulo,fonte,orgao,categoria,conteudo"
            f"&categoria=eq.{categoria}"
            f"&limit={MAX_NORMAS_KB}"
        )
        try:
            r = requests.get(url, headers=SUPA_HEADERS, timeout=30)
            if r.status_code == 200:
                for n in r.json():
                    if n["chave"] not in seen_chaves:
                        normas.append(n)
                        seen_chaves.add(n["chave"])
        except Exception:
            pass

    # Tentativa 2: busca textual nos comentários (full-text simples via ilike)
    if keywords and len(normas) < MAX_NORMAS_KB:
        # extrai 2-3 palavras-chave mais distintivas (>4 chars)
        palavras = [w.strip(".,;:()[]{}").lower()
                    for w in keywords.split()
                    if len(w.strip(".,;:()[]{}")) > 4][:3]
        for palavra in palavras:
            if len(normas) >= MAX_NORMAS_KB:
                break
            url = (
                f"{SUPABASE_URL}/rest/v1/kb_documents"
                f"?select=chave,titulo,fonte,orgao,categoria,conteudo"
                f"&conteudo=ilike.*{palavra}*"
                f"&limit=3"
            )
            try:
                r = requests.get(url, headers=SUPA_HEADERS, timeout=30)
                if r.status_code == 200:
                    for n in r.json():
                        if n["chave"] not in seen_chaves and len(normas) < MAX_NORMAS_KB:
                            normas.append(n)
                            seen_chaves.add(n["chave"])
            except Exception:
                pass

    return normas


# ───────────────────────────────────────────────────────────────────────────
# 2. CLASSIFICAÇÃO PELO CLAUDE
# ───────────────────────────────────────────────────────────────────────────

PROMPT_CURADOR = """Você é um curador especialista em legislação brasileira de rotulagem de \
alimentos (RDC ANVISA, IN MAPA, RIISPOA). Sua missão é decidir se uma alegação de \
erro feita por um Responsável Técnico contra um relatório de validação automatizada \
está correta, à luz da legislação vigente fornecida.

CONTEXTO DA VALIDAÇÃO:
• Produto: {produto}
• Categoria: {categoria}
• Órgão regulador: {orgao}
• Caminho normativo: {caminho_np}

FEEDBACK GERAL DO RT: {feedback_geral}
COMENTÁRIO DO RT: {rt_comment}

CAMPOS QUE O RT MARCOU COMO INCORRETOS (com justificativa):
{campos_incorretos}

ERROS QUE O RT DIZ QUE O AGENTE NÃO DETECTOU:
{erros_nao_detectados}

FALSOS POSITIVOS APONTADOS PELO RT:
{falsos_positivos}

NORMAS POTENCIALMENTE RELEVANTES NA NOSSA BASE DE CONHECIMENTO:
{normas_kb}

TAREFA:
Para cada alegação distinta do RT, classifique em UMA das três categorias:

  • VALIDADO    — A norma fornecida confirma a alegação do RT. O agente errou.
  • REJEITADO   — A norma fornecida contradiz a alegação do RT. O agente acertou.
  • INCONCLUSIVO — A norma fornecida não é suficiente para decidir. Pode ser norma \
faltante na base, ou alegação ambígua/sem base legal verificável.

Seja CONSERVADOR. Em caso de dúvida, classifique como INCONCLUSIVO. \
Nunca invente normas que não estão na lista fornecida.

Responda APENAS em JSON válido, sem markdown, sem comentários adicionais, no formato:
{{
  "alegacoes": [
    {{
      "campo_ou_topico": "string curta — ex: 'Campo 2: ordem de ingredientes'",
      "alegacao_rt": "string — o que o RT alega",
      "veredicto": "VALIDADO" | "REJEITADO" | "INCONCLUSIVO",
      "justificativa": "string curta — explica em 1-2 frases citando a norma específica",
      "norma_relevante": "string — chave da norma na KB (ex: 'rdc_429_2020') ou 'NENHUMA'",
      "acao_sugerida": "string — ex: 'Adicionar IN MAPA xx/yyyy à KB' ou 'Nenhuma' ou 'Investigar manualmente'"
    }}
  ],
  "resumo_executivo": "string — 1-2 frases sobre o caso como um todo"
}}"""


def montar_prompt(feedback: dict[str, Any], normas: list[dict[str, Any]]) -> str:
    # Extrai campos incorretos do JSON
    campos_incorretos_str = "(nenhum campo individual marcado)"
    try:
        campos = json.loads(feedback.get("campos_json") or "{}")
        if isinstance(campos, dict):
            linhas = []
            for num, dados in campos.items():
                if isinstance(dados, dict) and dados.get("status") == "incorreto":
                    cm = dados.get("comentario") or "(sem comentário)"
                    linhas.append(f"  • Campo {num}: {cm}")
            if linhas:
                campos_incorretos_str = "\n".join(linhas)
    except Exception:
        pass

    # Formata normas da KB (limita conteúdo de cada uma para não estourar contexto)
    if normas:
        normas_str = "\n\n".join(
            f"### [{n['chave']}] {n.get('titulo','(sem título)')} — "
            f"{n.get('orgao','?')} / {n.get('categoria','?')}\n"
            f"{(n.get('conteudo') or '')[:3500]}"
            for n in normas
        )
    else:
        normas_str = "(NENHUMA NORMA RELEVANTE ENCONTRADA NA KB — provável GAP de cobertura.)"

    return PROMPT_CURADOR.format(
        produto=feedback.get("produto") or "(não informado)",
        categoria=feedback.get("categoria") or "(não informada)",
        orgao=feedback.get("orgao") or "(não informado)",
        caminho_np=feedback.get("caminho_np") or "(não informado)",
        feedback_geral=feedback.get("feedback") or "?",
        rt_comment=feedback.get("rt_comment") or "(sem comentário geral)",
        campos_incorretos=campos_incorretos_str,
        erros_nao_detectados=feedback.get("erros_nao_detectados") or "(nenhum)",
        falsos_positivos=feedback.get("falsos_positivos") or "(nenhum)",
        normas_kb=normas_str,
    )


def classificar(feedback: dict[str, Any]) -> dict[str, Any]:
    """Chama o Claude para classificar um feedback. Retorna dict com alegações."""
    normas = buscar_normas_relevantes(
        categoria=feedback.get("categoria", ""),
        keywords=" ".join(filter(None, [
            feedback.get("rt_comment", ""),
            feedback.get("erros_nao_detectados", ""),
            feedback.get("falsos_positivos", ""),
        ])),
    )

    prompt = montar_prompt(feedback, normas)

    try:
        resp = claude.messages.create(
            model=MODELO_CLAUDE,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = resp.content[0].text.strip()
        # remove cercas de código se o Claude colocar
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
            texto = texto.strip()
        return json.loads(texto)
    except json.JSONDecodeError as e:
        return {
            "alegacoes": [],
            "resumo_executivo": f"⚠️ Erro: Claude não retornou JSON válido. {e}",
            "_raw": texto[:500] if 'texto' in dir() else "",
        }
    except Exception as e:
        return {
            "alegacoes": [],
            "resumo_executivo": f"⚠️ Erro na chamada ao Claude: {e}",
        }


# ───────────────────────────────────────────────────────────────────────────
# 3. MONTA RELATÓRIO HTML
# ───────────────────────────────────────────────────────────────────────────

def montar_relatorio_html(resultados: list[dict[str, Any]]) -> tuple[str, str]:
    """Retorna (assunto, html) do email."""
    total = len(resultados)
    todas_alegacoes = []
    for r in resultados:
        for a in r["analise"].get("alegacoes", []):
            todas_alegacoes.append({**a, "_caso": r["feedback"]})

    n_validados   = sum(1 for a in todas_alegacoes if a.get("veredicto") == "VALIDADO")
    n_rejeitados  = sum(1 for a in todas_alegacoes if a.get("veredicto") == "REJEITADO")
    n_inconclusivos = sum(1 for a in todas_alegacoes if a.get("veredicto") == "INCONCLUSIVO")

    semana = dt.datetime.utcnow().strftime("%d/%m/%Y")
    assunto = (
        f"[Curador Inspect-IA] {total} feedback(s) | "
        f"✅{n_validados} ❌{n_rejeitados} ⚠️{n_inconclusivos} — semana {semana}"
    )

    css = """
    <style>
      body { font-family: -apple-system, system-ui, sans-serif; max-width: 720px;
             margin: 0 auto; padding: 24px; color: #111827; background: #f9fafb; }
      .header { background: #16a34a; color: white; padding: 16px 24px;
                border-radius: 9px; margin-bottom: 24px; }
      .header h1 { margin: 0; font-size: 20px; }
      .header p { margin: 4px 0 0; opacity: 0.9; font-size: 14px; }
      .resumo { background: white; padding: 16px; border-radius: 9px;
                margin-bottom: 24px; border: 1px solid #e5e7eb; }
      .stat { display: inline-block; margin-right: 16px; font-size: 14px; }
      .stat strong { font-size: 20px; display: block; }
      .bucket { background: white; padding: 16px; border-radius: 9px;
                margin-bottom: 16px; border: 1px solid #e5e7eb;
                border-left-width: 4px; }
      .bucket.validado    { border-left-color: #16a34a; }
      .bucket.rejeitado   { border-left-color: #dc2626; }
      .bucket.inconclusivo{ border-left-color: #d97706; }
      .bucket h3 { margin: 0 0 8px; font-size: 16px; }
      .meta { color: #6b7280; font-size: 13px; margin-bottom: 8px; }
      .alegacao { background: #f9fafb; padding: 12px; border-radius: 6px;
                  margin-top: 8px; font-size: 14px; }
      .acao { background: #ecfdf5; padding: 8px 12px; border-radius: 6px;
              margin-top: 8px; font-size: 13px; color: #065f46;
              border-left: 3px solid #16a34a; }
      .case-id { font-family: monospace; font-size: 12px; color: #6b7280; }
      .empty { background: white; padding: 32px; border-radius: 9px;
               text-align: center; color: #6b7280; }
    </style>
    """

    if total == 0:
        html = f"""
        {css}
        <div class="header">
          <h1>Curador Semanal — Inspect-IA</h1>
          <p>Semana de {semana}</p>
        </div>
        <div class="empty">
          <p><strong>Sem feedbacks negativos esta semana.</strong></p>
          <p>O curador rodou normalmente. Próxima execução: segunda às 09h BRT.</p>
        </div>
        """
        return assunto, html

    # Agrupa por veredicto
    por_veredicto = {"VALIDADO": [], "REJEITADO": [], "INCONCLUSIVO": []}
    for a in todas_alegacoes:
        v = a.get("veredicto", "INCONCLUSIVO")
        por_veredicto.setdefault(v, []).append(a)

    def render_alegacao(a: dict[str, Any]) -> str:
        caso = a["_caso"]
        cls = a.get("veredicto", "INCONCLUSIVO").lower()
        return f"""
        <div class="bucket {cls}">
          <h3>{a.get('campo_ou_topico', '(sem tópico)')}</h3>
          <div class="meta">
            <span class="case-id">case_id: {caso.get('case_id','?')}</span> ·
            {caso.get('produto','?')} · {caso.get('categoria','?')}
          </div>
          <div class="alegacao">
            <strong>Alegação do RT:</strong> {a.get('alegacao_rt','?')}<br><br>
            <strong>Justificativa:</strong> {a.get('justificativa','?')}<br>
            <strong>Norma:</strong> <code>{a.get('norma_relevante','NENHUMA')}</code>
          </div>
          <div class="acao"><strong>Ação sugerida:</strong> {a.get('acao_sugerida','Nenhuma')}</div>
        </div>
        """

    secoes = []
    if por_veredicto["VALIDADO"]:
        secoes.append("<h2 style='color:#16a34a'>✅ Validados — incorporar à KB</h2>")
        secoes.extend(render_alegacao(a) for a in por_veredicto["VALIDADO"])
    if por_veredicto["INCONCLUSIVO"]:
        secoes.append("<h2 style='color:#d97706'>⚠️ Inconclusivos — investigar</h2>")
        secoes.extend(render_alegacao(a) for a in por_veredicto["INCONCLUSIVO"])
    if por_veredicto["REJEITADO"]:
        secoes.append("<h2 style='color:#dc2626'>❌ Rejeitados — descartados</h2>")
        secoes.extend(render_alegacao(a) for a in por_veredicto["REJEITADO"])

    html = f"""
    {css}
    <div class="header">
      <h1>Curador Semanal — Inspect-IA</h1>
      <p>Semana de {semana} · {total} feedback(s) negativos analisados</p>
    </div>
    <div class="resumo">
      <div class="stat" style="color:#16a34a"><strong>{n_validados}</strong>Validados</div>
      <div class="stat" style="color:#d97706"><strong>{n_inconclusivos}</strong>Inconclusivos</div>
      <div class="stat" style="color:#dc2626"><strong>{n_rejeitados}</strong>Rejeitados</div>
    </div>
    {''.join(secoes)}
    <p style="color:#6b7280;font-size:12px;margin-top:32px">
      FASE 1 — observação apenas. Nenhuma alteração foi feita na KB.
      Para incorporar um item validado: copie o bloco e cole no chat com Claude dizendo "incorporar".
    </p>
    """
    return assunto, html


# ───────────────────────────────────────────────────────────────────────────
# 4. ENVIO POR RESEND
# ───────────────────────────────────────────────────────────────────────────

def enviar_email(assunto: str, html: str) -> None:
    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type":  "application/json",
        },
        json={
            "from":    "Curador Inspect-IA <onboarding@resend.dev>",
            "to":      [EMAIL_DESTINO],
            "subject": assunto,
            "html":    html,
        },
        timeout=30,
    )
    r.raise_for_status()
    print(f"[OK] Email enviado para {EMAIL_DESTINO}: {assunto}")


# ───────────────────────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────────────────────

def main() -> int:
    print(f"[curador] início — janela={DIAS_LOOKBACK}d, modelo={MODELO_CLAUDE}")

    try:
        feedbacks = buscar_feedbacks_negativos()
    except Exception as e:
        print(f"[curador] ERRO ao buscar feedbacks: {e}", file=sys.stderr)
        return 1

    print(f"[curador] {len(feedbacks)} feedback(s) negativo(s) encontrados")

    resultados = []
    for i, fb in enumerate(feedbacks, 1):
        print(f"[curador] classificando {i}/{len(feedbacks)}: case_id={fb.get('case_id','?')}")
        analise = classificar(fb)
        resultados.append({"feedback": fb, "analise": analise})

    assunto, html = montar_relatorio_html(resultados)

    try:
        enviar_email(assunto, html)
    except Exception as e:
        print(f"[curador] ERRO ao enviar email: {e}", file=sys.stderr)
        return 1

    print("[curador] fim — sucesso")
    return 0


if __name__ == "__main__":
    sys.exit(main())

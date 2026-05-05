"""
Curador Diário V2 — InspectIA  (revisão Dev.8: foto + IA-vs-RT + relatório linkado)

Roda toda manhã às 8h Brasília via GitHub Action.

Fluxo:
1. Busca todos os feedbacks pendentes de revisão (status_curador='pendente_revisao')
2. Para cada feedback: extrai discordâncias campo a campo
3. Cria token único por discordância (um pra aprovar, um pra rejeitar)
4. Monta email HTML rico — agora com:
   - Resumo executivo no topo (volume, top campo questionado, estimativa)
   - Foto do rótulo (clicável → tamanho real)
   - Comparação lado-a-lado: o que a IA disse no campo X vs o que o RT contestou
   - Botão "Ver relatório completo" linkando endpoint /curador/relatorio/{case_id}
5. Envia pra RT senior (Giovanna)
6. Loga resultado no GitHub Actions

Não escreve nada na KB ainda — só prepara revisão humana.
A escrita na KB acontece quando RT senior clica nos links.
"""

import os
import re
import sys
import json
import secrets
import hashlib
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

# ─── Config ───────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")  # não usado nesta fase, opcional
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
BACKEND_URL = os.environ.get("BACKEND_URL", "https://valida-rotulo-backend.onrender.com").rstrip("/")
RT_SENIOR_EMAIL = os.environ.get("RT_SENIOR_EMAIL", "gipbosco@gmail.com")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "hugodacach@gmail.com")
TOKEN_TTL_DAYS = 14  # Token expira em 14 dias

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# Headers específicos pra GET (sem Content-Type, evita 400 em algumas versões PostgREST)
SUPABASE_HEADERS_GET = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Accept": "application/json",
}


def log(msg: str) -> None:
    """Log estruturado pro GitHub Actions."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ─── 1. Buscar feedbacks pendentes ────────────────────────────────────────
def _query_validacoes_safe(query_string: str) -> list[dict] | None:
    """
    Faz query GET na tabela validacoes com headers corretos pro PostgREST.
    Retorna lista de dicts, ou None se der erro (logado).
    """
    url = f"{SUPABASE_URL}/rest/v1/validacoes{query_string}"
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(url, headers=SUPABASE_HEADERS_GET)
            if r.status_code == 200:
                return r.json() or []
            log(f"WARN: query falhou status={r.status_code}")
            log(f"  URL: {url[:200]}")
            log(f"  Body: {r.text[:500]}")
            return None
    except Exception as e:
        log(f"WARN: exceção na query: {e}")
        return None


def buscar_pendentes() -> list[dict]:
    """
    Busca feedbacks pendentes de revisão.

    Estratégia em 3 níveis (vai tentando até funcionar):
      1. Filtro completo: status_curador + janela 30d
      2. Sem janela 30d: só status_curador
      3. Sem nenhum filtro PostgREST: pega tudo recente, filtra Python-side

    Filtra Python-side em todos os casos: só registros com `feedback` preenchido.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
    seen_ids: set[str] = set()
    todos: list[dict] = []

    queries_to_try = [
        f"?status_curador=eq.pendente_revisao&created_at=gte.{cutoff}&order=created_at.desc&limit=100",
        f"?status_curador=eq.pendente_revisao&order=created_at.desc&limit=100",
        f"?order=created_at.desc&limit=200",
    ]

    for i, q in enumerate(queries_to_try, start=1):
        rows = _query_validacoes_safe(q)
        if rows is None:
            log(f"  Tentativa {i}/{len(queries_to_try)}: falhou, tentando próxima...")
            continue

        log(f"  Tentativa {i}/{len(queries_to_try)}: ok ({len(rows)} registros)")
        for row in rows:
            cid = row.get("case_id", "")
            if not cid or cid in seen_ids:
                continue
            if not row.get("feedback"):
                continue
            if i == 3:
                status = (row.get("status_curador") or "").lower()
                if status and status not in ("pendente_revisao", ""):
                    continue
            seen_ids.add(cid)
            todos.append(row)
        break

    log(f"Total de feedbacks pendentes encontrados: {len(todos)}")
    return todos


# ─── 2. Buscar normas relevantes na KB ─────────────────────────────────────
def buscar_normas_relevantes(categoria: str, limit: int = 5) -> list[dict]:
    """
    Busca docs da KB filtrados pela categoria do produto.
    Contexto opcional pra Giovanna no email. Falha silenciosa.
    """
    if not categoria:
        return []
    from urllib.parse import quote
    cat_safe = quote(categoria, safe="")
    url = (
        f"{SUPABASE_URL}/rest/v1/kb_documents"
        f"?or=(tags.ilike.*{cat_safe}*,categoria.ilike.*{cat_safe}*)"
        f"&limit={limit}"
    )
    with httpx.Client(timeout=20.0) as client:
        try:
            r = client.get(url, headers=SUPABASE_HEADERS_GET)
            if r.status_code != 200:
                url2 = f"{SUPABASE_URL}/rest/v1/kb_documents?limit={limit}"
                r2 = client.get(url2, headers=SUPABASE_HEADERS_GET)
                if r2.status_code == 200:
                    return r2.json() or []
                return []
            return r.json() or []
        except Exception:
            return []


# ─── 3. Tokens de aprovação ───────────────────────────────────────────────
def gerar_token() -> str:
    """Gera token único de 32 chars hex."""
    return secrets.token_hex(16)


def salvar_tokens(tokens: list[dict]) -> bool:
    """Insere tokens em batch na tabela curador_tokens."""
    if not tokens:
        return True
    url = f"{SUPABASE_URL}/rest/v1/curador_tokens"
    headers = {**SUPABASE_HEADERS, "Prefer": "return=minimal"}
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, headers=headers, json=tokens)
        if r.status_code not in (200, 201, 204):
            log(f"ERRO ao salvar tokens: status={r.status_code} body={r.text[:300]}")
            return False
    return True


# ─── 4. Extrair discordâncias do feedback ─────────────────────────────────
NOMES_CAMPOS = {
    1: "Denominação de Venda",
    2: "Lista de Ingredientes",
    3: "Conteúdo Líquido",
    4: "Identificação do Fabricante",
    5: "Declaração de Glúten",
    6: "Declaração de Lactose",
    7: "Instruções de Conservação",
    8: "Carimbo de Inspeção",
    9: "Tabela Nutricional",
    10: "Lupa Frontal",
    11: "Alérgenos",
    12: "Transgênicos",
    13: "Lote e Validade",
    14: "Porção Padrão",
}


def extrair_discordancias(feedback: dict) -> list[dict]:
    """
    De um registro da tabela validacoes, extrai a lista de discordâncias do RT.
    Formato esperado de 'campos' (jsonb):
      { "1": {"status": "correto"|"incorreto", "comentario": "..."}, ... }
    """
    campos_raw = feedback.get("campos") or {}
    if isinstance(campos_raw, str):
        try:
            campos_raw = json.loads(campos_raw)
        except Exception:
            campos_raw = {}

    discordancias = []
    for num_str, dados in campos_raw.items():
        if not isinstance(dados, dict):
            continue
        comentario = (dados.get("comentario") or "").strip()
        if not comentario:
            continue  # Sem comentário = RT concorda implicitamente
        try:
            num = int(num_str)
        except (ValueError, TypeError):
            continue
        discordancias.append({
            "campo_num": num,
            "campo_nome": NOMES_CAMPOS.get(num, f"Campo {num}"),
            "status_rt": dados.get("status", "incorreto"),
            "comentario": comentario,
        })
    # Ordena por campo_num pra leitura previsível
    discordancias.sort(key=lambda d: d["campo_num"])
    return discordancias


# ─── 4.5 Extrair trecho da IA pro campo específico ────────────────────────
def extrair_trecho_ia(relatorio_completo: str, campo_num: int) -> dict:
    """
    Do relatório completo da IA, extrai o que ela disse sobre um campo específico.
    Retorna {"status": "CONFORME|COM RESSALVAS|NÃO CONFORME|—", "texto": "..."}.

    Tenta dois padrões:
      1. "CAMPO N — ..." (com nome) seguido de status e justificativa
      2. "CAMPO N" sozinho (alguns formatos antigos)
    """
    if not relatorio_completo or not campo_num:
        return {"status": "—", "texto": ""}

    # Captura bloco "CAMPO N" até "CAMPO N+1" ou final
    pattern = rf"CAMPO\s*{campo_num}\b.*?(?=CAMPO\s*\d+\b|$)"
    m = re.search(pattern, relatorio_completo, re.DOTALL | re.IGNORECASE)
    if not m:
        return {"status": "—", "texto": ""}

    bloco = m.group(0).strip()
    # Detecta status do campo
    status = "—"
    bloco_upper = bloco.upper()
    if "NÃO CONFORME" in bloco_upper or "NAO CONFORME" in bloco_upper:
        status = "NÃO CONFORME"
    elif "COM RESSALVAS" in bloco_upper:
        status = "COM RESSALVAS"
    elif "CONFORME" in bloco_upper:
        status = "CONFORME"

    # Limpa: remove prefixo "CAMPO N — Nome" da primeira linha
    linhas = bloco.split("\n")
    if linhas:
        linhas[0] = re.sub(rf"^CAMPO\s*{campo_num}[^\n]*", "", linhas[0]).strip(" :—-")
        linhas = [l for l in linhas if l.strip()]

    # Junta as primeiras 6 linhas significativas (evita texto gigante)
    texto = "\n".join(linhas[:6]).strip()
    # Remove markdown bold pra ficar texto limpo
    texto = re.sub(r"\*\*([^*]+)\*\*", r"\1", texto)
    # Trunca pra evitar email gigante
    if len(texto) > 380:
        texto = texto[:377] + "..."

    return {"status": status, "texto": texto}


# ─── 4.6 Score visual (14 quadradinhos coloridos) ─────────────────────────
def render_score_visual(feedback: dict) -> str:
    """
    Retorna HTML com 14 quadradinhos coloridos representando os campos do score IA.
    Usa erros_auto e ressalvas_auto pra deduzir status de cada campo.
    Campos não citados nesses dois → assumidos CONFORME (verde).
    """
    erros = feedback.get("erros_auto", "") or ""
    ressalvas = feedback.get("ressalvas_auto", "") or ""

    # Extrai números dos campos NÃO CONFORME e COM RESSALVAS
    erros_nums = set(int(n) for n in re.findall(r"C(\d+)", erros))
    ressalvas_nums = set(int(n) for n in re.findall(r"C(\d+)", ressalvas))

    quadrados = []
    for n in range(1, 15):
        if n in erros_nums:
            cor = "#992F2A"  # vermelho
        elif n in ressalvas_nums:
            cor = "#C7891E"  # amarelo
        else:
            cor = "#166534"  # verde
        quadrados.append(
            f'<span style="display:inline-block;width:10px;height:10px;background:{cor};'
            f'margin-right:2px;border-radius:2px;" title="Campo {n}"></span>'
        )
    return "".join(quadrados)


# ─── 5. Montar email HTML ─────────────────────────────────────────────────
def render_resumo_executivo(feedbacks_com_discordancias: list[dict],
                            total_feedbacks: int) -> str:
    """
    Resumo de 3 linhas no topo do email — Giovanna escaneia em 5 segundos
    e sabe o tamanho do trabalho do dia.
    """
    total_disc = sum(len(f["discordancias"]) for f in feedbacks_com_discordancias)
    estimativa_min = max(2, round(total_disc * 0.5))  # ~30s por discordância

    # Top campo questionado
    todos_campos = []
    for f in feedbacks_com_discordancias:
        for d in f["discordancias"]:
            todos_campos.append(d["campo_num"])
    top_campo_html = ""
    if todos_campos:
        cnt = Counter(todos_campos)
        top_num, top_count = cnt.most_common(1)[0]
        top_nome = NOMES_CAMPOS.get(top_num, f"Campo {top_num}")
        if top_count >= 2:
            top_campo_html = (
                f'· top campo questionado: <strong>C{top_num} ({top_nome}) '
                f'— {top_count}×</strong>'
            )

    return f"""
<div style="background:#0F2A20;color:#fff;border-radius:10px;padding:18px 22px;margin-bottom:20px;">
  <div style="font-size:11px;letter-spacing:1.5px;text-transform:uppercase;opacity:0.75;margin-bottom:8px;">📊 RESUMO DE HOJE</div>
  <div style="font-size:15px;line-height:1.6;">
    <strong>{total_feedbacks}</strong> feedback{'s' if total_feedbacks != 1 else ''} ·
    <strong>{total_disc}</strong> correç{'ões' if total_disc != 1 else 'ão'} pra revisar ·
    estimativa <strong>~{estimativa_min} min</strong>
  </div>
  <div style="font-size:12px;line-height:1.6;opacity:0.85;margin-top:6px;">
    {top_campo_html}
  </div>
</div>
"""


def render_email_html(feedbacks_com_discordancias: list[dict], total_feedbacks: int) -> str:
    """Monta email HTML rico com todos os feedbacks e botões de aprovar/rejeitar."""
    hoje = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")
    total_discordancias = sum(len(f["discordancias"]) for f in feedbacks_com_discordancias)

    # ─── HEADER ───
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>InspectIA · Curadoria diária</title>
</head>
<body style="margin:0;padding:0;font-family:'Helvetica Neue',Arial,sans-serif;background:#f0ede3;color:#0f2a20;">
<div style="max-width:720px;margin:0 auto;padding:24px 16px;">

<!-- HEADER -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0F2A20;border-radius:10px;padding:20px 22px;margin-bottom:20px;">
  <tr>
    <td>
      <div style="color:#fff;font-size:14px;font-weight:600;letter-spacing:0.5px;">📋 InspectIA · Curadoria diária</div>
      <div style="color:#a8a4a0;font-size:12px;margin-top:4px;">{hoje}</div>
    </td>
  </tr>
</table>

{render_resumo_executivo(feedbacks_com_discordancias, total_feedbacks)}

<!-- INTRO -->
<div style="background:#fff;border:1px solid #e2ded2;border-radius:10px;padding:18px 22px;margin-bottom:20px;line-height:1.55;">
  <div style="font-size:14px;color:#0f2a20;margin-bottom:10px;">
    Olá Giovanna,
  </div>
  <div style="font-size:13px;color:#0f2a20;">
    Recebemos <strong>{total_feedbacks}</strong> feedback{"s" if total_feedbacks != 1 else ""} de RTs nas últimas 24h, totalizando
    <strong>{total_discordancias}</strong> correç{"ões" if total_discordancias != 1 else "ão"} para revisar.
  </div>
  <div style="font-size:12px;color:#6b6757;margin-top:10px;line-height:1.6;">
    Cada correção tem 2 botões: <strong>Aprovar</strong> (vira aprendizado da IA) ou <strong>Rejeitar</strong> (descarta).
    A IA reformulará o texto técnico antes de gravar — sua aprovação é o que autoriza isso.
  </div>
</div>
"""

    # ─── FEEDBACKS ───
    for idx, item in enumerate(feedbacks_com_discordancias, start=1):
        fb = item["feedback"]
        discord = item["discordancias"]
        produto = fb.get("produto", "—") or "—"
        categoria = fb.get("categoria", "—") or "—"
        orgao = fb.get("orgao", "") or ""
        score_agente = fb.get("score_agente")
        score_real = fb.get("score_real")
        case_id = fb.get("case_id", "")
        case_id_short = case_id[:24]
        imagem_url = (fb.get("imagem_url") or "").strip()
        relatorio_completo = fb.get("relatorio_completo", "") or ""

        score_text = ""
        if score_agente is not None:
            score_text = f"IA: <strong>{score_agente}/14</strong>"
            if score_real is not None and score_real != score_agente:
                delta = score_real - score_agente
                sinal = "+" if delta > 0 else ""
                score_text += f' → RT: <strong>{score_real}/14</strong> <span style="color:#9C5A0E;">(Δ {sinal}{delta})</span>'

        score_visual = render_score_visual(fb)
        link_relatorio = f"{BACKEND_URL}/curador/relatorio/{case_id}" if case_id else ""

        # ── HEADER DO CARD (com foto à esquerda, info à direita) ──
        if imagem_url:
            img_tag = f'''<a href="{imagem_url}" target="_blank" rel="noopener" style="display:block;text-decoration:none;">
                <img src="{imagem_url}" alt="Rótulo {html_escape(produto)}" width="240" height="240"
                     style="display:block;width:240px;height:240px;object-fit:cover;border-radius:8px;border:1px solid #e2ded2;">
            </a>
            <div style="font-size:10px;color:#a8a4a0;margin-top:4px;text-align:center;">clique pra ampliar</div>'''
        else:
            img_tag = '''<div style="width:240px;height:240px;background:#f0ede3;border:1px dashed #d9d2be;
                         border-radius:8px;display:flex;align-items:center;justify-content:center;color:#a8a4a0;
                         font-size:11px;text-align:center;padding:0 12px;line-height:1.5;">Foto não disponível<br>(validação anterior à<br>v.com-foto)</div>'''

        html += f"""
<!-- FEEDBACK #{idx} -->
<div style="background:#fff;border:1px solid #e2ded2;border-radius:10px;margin-bottom:24px;overflow:hidden;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0ede3;border-bottom:1px solid #e2ded2;">
    <tr>
      <td valign="top" width="260" style="padding:16px 16px 16px 22px;">
        {img_tag}
      </td>
      <td valign="top" style="padding:16px 22px 16px 8px;">
        <div style="font-size:11px;color:#6b6757;text-transform:uppercase;letter-spacing:1px;font-weight:600;">FEEDBACK #{idx}</div>
        <div style="font-size:17px;color:#091a14;font-weight:600;margin-top:6px;line-height:1.3;">{html_escape(produto)}</div>
        <div style="font-size:12px;color:#6b6757;margin-top:6px;">
          {html_escape(categoria)}{' · ' + html_escape(orgao) if orgao else ''}
        </div>
        <div style="font-size:13px;color:#0f2a20;margin-top:10px;">{score_text}</div>
        <div style="margin-top:10px;">{score_visual}</div>
        <div style="font-size:10px;color:#a8a4a0;margin-top:10px;font-family:monospace;">case: {html_escape(case_id_short)}</div>
        {f'''<div style="margin-top:12px;">
          <a href="{link_relatorio}" target="_blank" rel="noopener" style="display:inline-block;font-size:12px;color:#166534;text-decoration:underline;font-weight:500;">📄 Ver relatório completo</a>
        </div>''' if link_relatorio else ''}
      </td>
    </tr>
  </table>
"""

        # ── DISCORDÂNCIAS DO FEEDBACK (cada campo questionado) ──
        for disc in discord:
            num = disc["campo_num"]
            nome = disc["campo_nome"]
            comentario = disc["comentario"]
            url_aprovar = f"{BACKEND_URL}/curador/aprovar/{disc['token_aprovar']}"
            url_rejeitar = f"{BACKEND_URL}/curador/rejeitar/{disc['token_rejeitar']}"

            # Extrai o que a IA disse sobre esse campo
            ia_data = extrair_trecho_ia(relatorio_completo, num)
            ia_status = ia_data["status"]
            ia_texto = ia_data["texto"]

            # Cor da pílula de status da IA
            status_cor = {
                "CONFORME":       ("#166534", "#E8F0EA"),  # verde
                "COM RESSALVAS":  ("#9C5A0E", "#F5EBD8"),  # amarelo
                "NÃO CONFORME":   ("#992F2A", "#F0DDDB"),  # vermelho
                "—":              ("#6b6757", "#f0ede3"),  # cinza neutro
            }.get(ia_status, ("#6b6757", "#f0ede3"))

            # Bloco do que a IA disse
            if ia_texto:
                ia_block = f'''
            <div style="background:{status_cor[1]};border-left:3px solid {status_cor[0]};padding:12px 14px;border-radius:4px;margin-bottom:10px;">
              <div style="font-size:11px;color:{status_cor[0]};font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">
                🤖 IA: {ia_status}
              </div>
              <div style="font-size:13px;color:#0f2a20;line-height:1.55;">{html_escape(ia_texto)}</div>
            </div>'''
            else:
                ia_block = f'''
            <div style="background:#fbfaf6;border:1px dashed #d9d2be;padding:10px 14px;border-radius:4px;margin-bottom:10px;font-size:12px;color:#a8a4a0;font-style:italic;">
              🤖 IA: análise específica deste campo não localizada no relatório
            </div>'''

            html += f"""
  <div style="padding:18px 22px;border-bottom:1px solid #f0ede3;">
    <div style="font-size:11px;color:#6b6757;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:10px;">
      Campo {num} — {html_escape(nome)}
    </div>
    {ia_block}
    <div style="background:#fff;border:1px solid #d9d2be;border-left:3px solid #9C5A0E;padding:12px 14px;border-radius:4px;margin-bottom:14px;">
      <div style="font-size:11px;color:#9C5A0E;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">
        👤 RT corrige
      </div>
      <div style="font-size:13px;color:#0f2a20;line-height:1.55;">"{html_escape(comentario)}"</div>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="left">
          <a href="{url_aprovar}" style="display:inline-block;background:#166534;color:#fff;text-decoration:none;font-weight:600;font-size:12px;padding:10px 20px;border-radius:6px;margin-right:8px;">
            ✓ Aprovar correção
          </a>
          <a href="{url_rejeitar}" style="display:inline-block;background:#fff;color:#992f2a;text-decoration:none;font-weight:600;font-size:12px;padding:10px 20px;border-radius:6px;border:1px solid #992f2a;">
            ✗ Rejeitar
          </a>
        </td>
      </tr>
    </table>
  </div>
"""

        # ── NORMAS KB RELACIONADAS (collapsed via <details>) ──
        normas_kb = item.get("normas_kb", [])
        if normas_kb:
            normas_lis = "".join(
                f'<div style="font-size:11px;color:#6b6757;line-height:1.6;">· {html_escape((n.get("titulo") or n.get("chave") or "—")[:80])}</div>'
                for n in normas_kb[:5]
            )
            html += f"""
  <details style="background:#fbfaf6;padding:10px 22px;border-top:1px solid #f0ede3;">
    <summary style="font-size:10px;color:#6b6757;text-transform:uppercase;letter-spacing:1px;font-weight:600;cursor:pointer;outline:none;">📚 Normas relevantes na KB ({len(normas_kb)})</summary>
    <div style="margin-top:8px;">{normas_lis}</div>
  </details>
"""

        html += "</div>\n"

    # ─── FOOTER ───
    html += f"""
<div style="background:#fff;border:1px solid #e2ded2;border-radius:10px;padding:16px 22px;margin-top:20px;font-size:11px;color:#6b6757;line-height:1.6;text-align:center;">
  <strong style="color:#0f2a20;">InspectIA</strong> · Validador de Rótulos com IA<br>
  Curadoria automática · Email enviado em {hoje} às 8h Brasília<br>
  <span style="color:#a8a4a0;">Cada token expira em {TOKEN_TTL_DAYS} dias e só pode ser usado uma vez.</span>
</div>

</div>
</body>
</html>"""

    return html


def html_escape(s: Any) -> str:
    """Escape básico pra HTML."""
    if s is None:
        return ""
    s = str(s)
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&#39;"))


# ─── 6. Enviar email via Resend ───────────────────────────────────────────
def enviar_email(to: str, subject: str, html: str, cc: list[str] | None = None,
                 _is_retry: bool = False) -> bool:
    """
    Envia email via Resend API.

    Workaround Resend sandbox: se der 403 (domínio não verificado), faz retry
    enviando SÓ pro ADMIN_EMAIL, com aviso no topo do email.
    Permite testar fluxo completo enquanto domínio próprio não está configurado.
    """
    payload = {
        "from": "InspectIA Curadoria <onboarding@resend.dev>",
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if cc:
        payload["cc"] = cc

    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if r.status_code in (200, 201, 202):
            log(f"Email enviado para {to} (id={r.json().get('id', '—')})")
            return True

        body_txt = r.text[:500]
        log(f"ERRO ao enviar email: status={r.status_code} body={body_txt[:300]}")

        if (not _is_retry
            and r.status_code == 403
            and "verify a domain" in body_txt
            and to != ADMIN_EMAIL):
            log("⚠ Resend em modo sandbox — enviando SÓ pro admin como fallback")
            aviso = f"""<div style="background:#F5EBD8;border:2px solid #9c5a0e;border-radius:8px;padding:14px 18px;margin-bottom:16px;font-size:13px;color:#0f2a20;">
<strong>⚠ Modo sandbox Resend</strong><br>
Este email seria enviado para <strong>{to}</strong>, mas o domínio próprio ainda não está verificado no Resend.<br>
Por enquanto, todo o conteúdo está vindo só pra você (admin). Para enviar pra outros destinatários, configure um domínio em <a href="https://resend.com/domains">resend.com/domains</a>.
</div>"""
            html_with_warn = aviso + html
            return enviar_email(ADMIN_EMAIL, f"[SANDBOX] {subject}", html_with_warn, cc=None, _is_retry=True)
        return False


# ─── 7. Marcar feedbacks como já-emailed ──────────────────────────────────
def marcar_email_enviado(case_ids: list[str]) -> None:
    """
    Atualiza status_curador='aguardando_aprovacao' nos feedbacks que foram emailed.
    Próxima rodada do curador não os pega de novo.
    """
    if not case_ids:
        return
    for cid in case_ids:
        url = f"{SUPABASE_URL}/rest/v1/validacoes?case_id=eq.{cid}"
        with httpx.Client(timeout=20.0) as client:
            try:
                r = client.patch(
                    url,
                    headers={**SUPABASE_HEADERS, "Prefer": "return=minimal"},
                    json={"status_curador": "aguardando_aprovacao"},
                )
                if r.status_code not in (200, 201, 204):
                    log(f"WARN: falha ao marcar {cid}: status={r.status_code}")
            except Exception as e:
                log(f"WARN: exceção ao marcar {cid}: {e}")


# ─── 8. Email "nada hoje" pro admin ───────────────────────────────────────
def enviar_email_silencioso() -> None:
    """Envia email curto pro admin quando não há feedbacks pendentes."""
    hoje = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")
    html = f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;color:#0f2a20;background:#f0ede3;padding:20px;">
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;padding:24px;">
  <h2 style="font-size:16px;color:#0f2a20;margin:0 0 12px;">📋 InspectIA · Curadoria diária</h2>
  <p style="font-size:13px;color:#6b6757;line-height:1.6;">
    {hoje} — Sem feedbacks pendentes hoje. Nenhum email enviado pra Giovanna.
  </p>
</div></body></html>"""
    enviar_email(ADMIN_EMAIL, f"InspectIA · Curadoria diária ({hoje}) · Nada novo", html)


# ─── 9. Pipeline principal ────────────────────────────────────────────────
def main():
    log("=" * 60)
    log("Curador Diário V2 — InspectIA (rev. com foto + IA-vs-RT)")
    log("=" * 60)
    log(f"RT senior: {RT_SENIOR_EMAIL}")
    log(f"Admin: {ADMIN_EMAIL}")
    log(f"Backend: {BACKEND_URL}")
    log("")

    pendentes = buscar_pendentes()
    log(f"Encontrados {len(pendentes)} feedback(s) pendentes de revisão.")

    if not pendentes:
        log("Nenhum feedback pendente. Enviando notificação silenciosa pro admin.")
        enviar_email_silencioso()
        log("Curador concluído (sem trabalho).")
        return

    feedbacks_com_discordancias = []
    tokens_a_salvar = []
    case_ids_emailed = []
    expires_at = (datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS)).isoformat()

    for fb in pendentes:
        case_id = fb.get("case_id", "")
        if not case_id:
            log(f"WARN: feedback sem case_id, pulando")
            continue

        discordancias = extrair_discordancias(fb)
        if not discordancias:
            log(f"  · {case_id[:16]}: feedback sem discordâncias (RT só confirmou) — marcado como aprovado_sem_correcoes")
            with httpx.Client(timeout=20.0) as client:
                client.patch(
                    f"{SUPABASE_URL}/rest/v1/validacoes?case_id=eq.{case_id}",
                    headers={**SUPABASE_HEADERS, "Prefer": "return=minimal"},
                    json={"status_curador": "aprovado_sem_correcoes"},
                )
            continue

        for disc in discordancias:
            t_aprovar = gerar_token()
            t_rejeitar = gerar_token()
            disc["token_aprovar"] = t_aprovar
            disc["token_rejeitar"] = t_rejeitar
            tokens_a_salvar.append({
                "token": t_aprovar,
                "case_id": case_id,
                "campo_num": disc["campo_num"],
                "acao": "aprovar",
                "rt_senior_email": RT_SENIOR_EMAIL,
                "expires_at": expires_at,
            })
            tokens_a_salvar.append({
                "token": t_rejeitar,
                "case_id": case_id,
                "campo_num": disc["campo_num"],
                "acao": "rejeitar",
                "rt_senior_email": RT_SENIOR_EMAIL,
                "expires_at": expires_at,
            })

        normas = buscar_normas_relevantes(fb.get("categoria", ""), limit=5)

        feedbacks_com_discordancias.append({
            "feedback": fb,
            "discordancias": discordancias,
            "normas_kb": normas,
        })
        case_ids_emailed.append(case_id)

    if not feedbacks_com_discordancias:
        log("Todos os feedbacks pendentes eram confirmações sem correções. Nada para Giovanna revisar.")
        enviar_email_silencioso()
        return

    log(f"Gerando {len(tokens_a_salvar)} tokens (aprovar/rejeitar).")
    if not salvar_tokens(tokens_a_salvar):
        log("ERRO CRÍTICO: tokens não foram salvos. Abortando envio de email.")
        sys.exit(1)

    total_feedbacks = len(feedbacks_com_discordancias)
    total_disc = sum(len(f["discordancias"]) for f in feedbacks_com_discordancias)
    hoje_br = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")
    subject = f"InspectIA · Curadoria diária ({hoje_br}) · {total_disc} correç{'ões' if total_disc != 1 else 'ão'} para revisar"
    html = render_email_html(feedbacks_com_discordancias, total_feedbacks)

    ok = enviar_email(RT_SENIOR_EMAIL, subject, html, cc=[ADMIN_EMAIL])
    if not ok:
        log("ERRO CRÍTICO: email não enviado. Tokens já gerados — feedbacks NÃO marcados como emailed.")
        sys.exit(1)

    marcar_email_enviado(case_ids_emailed)
    log(f"Curador concluído com sucesso: {total_feedbacks} feedback(s), {total_disc} correç{'ões' if total_disc != 1 else 'ão'}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

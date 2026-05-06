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
    """Resumo no topo do email — escaneável em 5 segundos."""
    total_disc = sum(len(f["discordancias"]) for f in feedbacks_com_discordancias)
    estimativa_min = max(2, round(total_disc * 0.5))

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
                f'<div style="margin-top:14px;padding-top:14px;border-top:1px solid #E8E5DD;'
                f'font-size:12px;color:#6B6757;">Campo mais questionado: '
                f'<strong style="color:#091A14;">C{top_num} · {top_nome}</strong> '
                f'<span style="color:#9C5A0E;">({top_count}× hoje)</span></div>'
            )

    return f"""
<!-- Resumo executivo -->
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 24px;">
  <tr>
    <td style="background:#FBFAF6;border:1px solid #E2DED2;border-radius:10px;padding:22px;">
      <div style="font-family:'Geist Mono',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#6B6757;margin-bottom:14px;">Hoje</div>
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td valign="top" style="padding-right:8px;">
            <div style="font-family:'Geist',-apple-system,BlinkMacSystemFont,sans-serif;font-size:32px;font-weight:600;color:#091A14;line-height:1;">{total_feedbacks}</div>
            <div style="font-size:11px;color:#6B6757;margin-top:4px;letter-spacing:0.3px;">{'feedbacks' if total_feedbacks != 1 else 'feedback'}</div>
          </td>
          <td valign="top" style="padding:0 8px;border-left:1px solid #E8E5DD;padding-left:20px;">
            <div style="font-family:'Geist',-apple-system,BlinkMacSystemFont,sans-serif;font-size:32px;font-weight:600;color:#091A14;line-height:1;">{total_disc}</div>
            <div style="font-size:11px;color:#6B6757;margin-top:4px;letter-spacing:0.3px;">{'correções' if total_disc != 1 else 'correção'} pra revisar</div>
          </td>
          <td valign="top" style="padding-left:20px;border-left:1px solid #E8E5DD;">
            <div style="font-family:'Geist',-apple-system,BlinkMacSystemFont,sans-serif;font-size:32px;font-weight:600;color:#166534;line-height:1;">~{estimativa_min}</div>
            <div style="font-size:11px;color:#6B6757;margin-top:4px;letter-spacing:0.3px;">minutos estimados</div>
          </td>
        </tr>
      </table>
      {top_campo_html}
    </td>
  </tr>
</table>
"""


def render_email_html(feedbacks_com_discordancias: list[dict], total_feedbacks: int) -> str:
    """
    Email HTML com identidade InspectIA limpa e profissional.
    Paleta: branco + verde escuro #0F2A20 + warm bone #FBFAF6 + accent #166534.
    Tipografia: Geist (com fallback para system-ui em clientes que não suportam).
    """
    hoje = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")
    total_discordancias = sum(len(f["discordancias"]) for f in feedbacks_com_discordancias)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>InspectIA · Curadoria diária · {hoje}</title>
</head>
<body style="margin:0;padding:0;background:#FFFFFF;font-family:'Geist',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#091A14;">
<!-- Wrapper externo -->
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FFFFFF;">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <!-- Container principal -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:680px;background:#FFFFFF;">

        <!-- HEADER minimalista -->
        <tr>
          <td style="padding:0 0 28px;border-bottom:1px solid #E8E5DD;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td valign="middle">
                  <div style="display:inline-block;width:8px;height:8px;background:#166534;border-radius:50%;vertical-align:middle;margin-right:10px;"></div>
                  <span style="font-family:'Geist Mono',monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#091A14;font-weight:500;vertical-align:middle;">InspectIA</span>
                </td>
                <td align="right" valign="middle">
                  <span style="font-family:'Geist Mono',monospace;font-size:11px;color:#6B6757;letter-spacing:0.5px;">{hoje}</span>
                </td>
              </tr>
            </table>
            <div style="margin-top:24px;">
              <h1 style="font-family:'Geist',sans-serif;font-size:28px;font-weight:600;color:#091A14;margin:0;letter-spacing:-0.5px;line-height:1.2;">Curadoria diária</h1>
              <p style="font-size:14px;color:#6B6757;margin:8px 0 0;line-height:1.5;">Olá Giovanna — feedbacks de RTs aguardando sua revisão.</p>
            </div>
          </td>
        </tr>

        <!-- Espaçamento -->
        <tr><td style="height:24px;"></td></tr>

        <!-- Resumo executivo -->
        <tr><td>{render_resumo_executivo(feedbacks_com_discordancias, total_feedbacks)}</td></tr>

        <!-- Instruções -->
        <tr>
          <td style="padding:0 0 28px;">
            <p style="font-size:13px;color:#6B6757;margin:0;line-height:1.6;">
              Para cada correção abaixo, você pode <strong style="color:#166534;">aprovar</strong>
              (vira aprendizado da IA) ou <strong style="color:#992F2A;">rejeitar</strong> (descarta).
              A IA reformula o texto técnico antes de gravar — sua aprovação é o que autoriza.
            </p>
          </td>
        </tr>
"""

    # ─── FEEDBACKS ───────────────────────────────────────────────────────────
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

        # Score visual
        score_text_html = ""
        if score_agente is not None:
            score_text_html = f'<span style="color:#091A14;">IA: <strong>{score_agente}/14</strong></span>'
            if score_real is not None and score_real != score_agente:
                delta = score_real - score_agente
                sinal = "+" if delta > 0 else ""
                score_text_html += (
                    f' <span style="color:#6B6757;">→</span> '
                    f'<span style="color:#091A14;">RT: <strong>{score_real}/14</strong></span> '
                    f'<span style="color:#9C5A0E;font-size:12px;">(Δ {sinal}{delta})</span>'
                )

        score_visual_quadrados = render_score_visual(fb)
        link_relatorio = f"{BACKEND_URL}/curador/relatorio/{case_id}" if case_id else ""

        # Foto do rótulo (250x250 ou placeholder)
        if imagem_url:
            img_block = f'''<a href="{imagem_url}" target="_blank" rel="noopener" style="display:block;text-decoration:none;line-height:0;">
                <img src="{imagem_url}" alt="{html_escape(produto)}" width="250" height="250" style="display:block;width:250px;height:250px;object-fit:cover;border-radius:8px;border:1px solid #E2DED2;">
            </a>
            <div style="font-family:'Geist Mono',monospace;font-size:9px;letter-spacing:1px;color:#A8A4A0;text-align:center;margin-top:8px;text-transform:uppercase;">clique pra ampliar</div>'''
        else:
            img_block = '''<div style="width:250px;height:250px;background:#FBFAF6;border:1px dashed #D9D2BE;border-radius:8px;display:table-cell;vertical-align:middle;text-align:center;color:#A8A4A0;font-size:11px;line-height:1.6;padding:0 16px;">📷<br>Foto não<br>disponível</div>'''

        html += f"""
<!-- FEEDBACK #{idx} -->
<tr>
  <td style="padding:0 0 32px;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FFFFFF;border:1px solid #E2DED2;border-radius:12px;overflow:hidden;">

      <!-- Card header: foto + meta -->
      <tr>
        <td style="background:#FBFAF6;padding:24px;border-bottom:1px solid #E8E5DD;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td valign="top" width="270" style="padding-right:24px;">
                {img_block}
              </td>
              <td valign="top">
                <div style="font-family:'Geist Mono',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#6B6757;font-weight:500;margin-bottom:8px;">Feedback #{idx}</div>
                <h2 style="font-family:'Geist',sans-serif;font-size:18px;font-weight:600;color:#091A14;margin:0 0 8px;line-height:1.3;letter-spacing:-0.2px;">{html_escape(produto)}</h2>
                <div style="font-size:13px;color:#6B6757;margin-bottom:14px;">
                  {html_escape(categoria)}{' · ' + html_escape(orgao) if orgao else ''}
                </div>
                <div style="font-size:13px;margin-bottom:14px;line-height:1.4;">{score_text_html}</div>
                <div style="margin-bottom:14px;">{score_visual_quadrados}</div>
                <div style="font-family:'Geist Mono',monospace;font-size:10px;color:#A8A4A0;letter-spacing:0.5px;margin-bottom:14px;">{html_escape(case_id_short)}</div>
                {f'''<a href="{link_relatorio}" target="_blank" rel="noopener" style="display:inline-block;font-size:12px;color:#166534;text-decoration:none;font-weight:500;border-bottom:1px solid #166534;padding-bottom:1px;">Ver relatório completo →</a>''' if link_relatorio else ''}
              </td>
            </tr>
          </table>
        </td>
      </tr>
"""

        # ── DISCORDÂNCIAS — cada campo questionado ──
        for disc in discord:
            num = disc["campo_num"]
            nome = disc["campo_nome"]
            comentario = disc["comentario"]
            url_aprovar = f"{BACKEND_URL}/curador/aprovar/{disc['token_aprovar']}"
            url_rejeitar = f"{BACKEND_URL}/curador/rejeitar/{disc['token_rejeitar']}"

            ia_data = extrair_trecho_ia(relatorio_completo, num)
            ia_status = ia_data["status"]
            ia_texto = ia_data["texto"]

            # Cor da pílula de status da IA
            status_cor = {
                "CONFORME":      ("#166534", "#E8F0EA"),
                "COM RESSALVAS": ("#9C5A0E", "#F5EBD8"),
                "NÃO CONFORME":  ("#992F2A", "#F0DDDB"),
                "—":             ("#6B6757", "#FBFAF6"),
            }.get(ia_status, ("#6B6757", "#FBFAF6"))

            if ia_texto:
                ia_block = f'''<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{status_cor[1]};border-radius:6px;margin-bottom:12px;">
                  <tr>
                    <td style="padding:14px 16px;border-left:3px solid {status_cor[0]};">
                      <div style="font-family:'Geist Mono',monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:{status_cor[0]};font-weight:600;margin-bottom:6px;">IA · {ia_status}</div>
                      <div style="font-size:13px;color:#091A14;line-height:1.6;">{html_escape(ia_texto)}</div>
                    </td>
                  </tr>
                </table>'''
            else:
                ia_block = '''<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FBFAF6;border-radius:6px;margin-bottom:12px;border:1px dashed #D9D2BE;">
                  <tr>
                    <td style="padding:12px 16px;font-size:12px;color:#A8A4A0;font-style:italic;">
                      IA: análise específica deste campo não disponível no relatório
                    </td>
                  </tr>
                </table>'''

            html += f"""
      <tr>
        <td style="padding:24px;border-bottom:1px solid #F0EDE3;">
          <div style="font-family:'Geist Mono',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#6B6757;font-weight:500;margin-bottom:14px;">
            Campo {num} · {html_escape(nome)}
          </div>

          {ia_block}

          <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FFFFFF;border:1px solid #E8E5DD;border-radius:6px;margin-bottom:18px;">
            <tr>
              <td style="padding:14px 16px;border-left:3px solid #9C5A0E;">
                <div style="font-family:'Geist Mono',monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#9C5A0E;font-weight:600;margin-bottom:6px;">RT · Correção proposta</div>
                <div style="font-size:13px;color:#091A14;line-height:1.6;">{html_escape(comentario)}</div>
              </td>
            </tr>
          </table>

          <table cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="padding-right:8px;">
                <a href="{url_aprovar}" style="display:inline-block;background:#166534;color:#FFFFFF;text-decoration:none;font-family:'Geist',sans-serif;font-weight:500;font-size:13px;padding:11px 22px;border-radius:6px;letter-spacing:0.2px;">Aprovar correção</a>
              </td>
              <td>
                <a href="{url_rejeitar}" style="display:inline-block;background:#FFFFFF;color:#6B6757;text-decoration:none;font-family:'Geist',sans-serif;font-weight:500;font-size:13px;padding:11px 22px;border-radius:6px;border:1px solid #D9D2BE;letter-spacing:0.2px;">Rejeitar</a>
              </td>
            </tr>
          </table>
        </td>
      </tr>
"""

        # Normas KB (collapsed via details)
        normas_kb = item.get("normas_kb", [])
        if normas_kb:
            normas_lis = "".join(
                f'<div style="font-size:12px;color:#6B6757;line-height:1.7;">· {html_escape((n.get("titulo") or n.get("chave") or "—")[:80])}</div>'
                for n in normas_kb[:5]
            )
            html += f"""
      <tr>
        <td style="background:#FBFAF6;padding:14px 24px;">
          <details>
            <summary style="font-family:'Geist Mono',monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#6B6757;font-weight:500;cursor:pointer;outline:none;">Normas relevantes na KB ({len(normas_kb)})</summary>
            <div style="margin-top:10px;">{normas_lis}</div>
          </details>
        </td>
      </tr>
"""

        html += "    </table>\n  </td>\n</tr>\n"

    # ─── FOOTER ─────────────────────────────────────────────────────────────
    html += f"""
        <!-- Footer -->
        <tr>
          <td style="padding:32px 0 0;border-top:1px solid #E8E5DD;text-align:center;">
            <div style="display:inline-block;width:6px;height:6px;background:#166534;border-radius:50%;margin-right:8px;vertical-align:middle;"></div>
            <span style="font-family:'Geist Mono',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#091A14;font-weight:500;vertical-align:middle;">InspectIA</span>
            <div style="font-size:11px;color:#A8A4A0;margin-top:12px;line-height:1.7;">
              Validador de rótulos com IA · Curadoria automática<br>
              Email enviado em {hoje} · Cada token expira em {TOKEN_TTL_DAYS} dias e só pode ser usado uma vez
            </div>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
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

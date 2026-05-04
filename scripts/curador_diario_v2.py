"""
Curador Diário V2 — InspectIA

Roda toda manhã às 8h Brasília via GitHub Action.

Fluxo:
1. Busca todos os feedbacks pendentes de revisão (status_curador='pendente_revisao')
2. Para cada feedback: extrai discordâncias campo a campo
3. Cria token único por discordância (um pra aprovar, um pra rejeitar)
4. Monta email HTML rico com botões de ação
5. Envia pra RT senior (Giovanna)
6. Loga resultado no GitHub Actions

Não escreve nada na KB ainda — só prepara revisão humana.
A escrita na KB acontece quando RT senior clica nos links.
"""

import os
import sys
import json
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

# ─── Config ───────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
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


def log(msg: str) -> None:
    """Log estruturado pro GitHub Actions."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ─── 1. Buscar feedbacks pendentes ────────────────────────────────────────
def buscar_pendentes() -> list[dict]:
    """
    Busca todos os feedbacks com status_curador='pendente_revisao'.
    Limite: feedbacks dos últimos 14 dias (evita acúmulo infinito).
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    url = (
        f"{SUPABASE_URL}/rest/v1/validacoes"
        f"?status_curador=eq.pendente_revisao"
        f"&feedback=not.is.null"
        f"&created_at=gte.{cutoff}"
        f"&order=created_at.desc"
        f"&limit=100"
    )
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, headers=SUPABASE_HEADERS)
        r.raise_for_status()
        return r.json() or []


# ─── 2. Buscar normas relevantes na KB (contexto pra o RT senior) ──────────
def buscar_normas_relevantes(categoria: str, limit: int = 5) -> list[dict]:
    """
    Busca docs da KB filtrados pela categoria do produto.
    Contexto opcional pra Giovanna no email.
    """
    if not categoria:
        return []
    # Filtro simplificado: usa ilike no campo tags ou categoria
    url = (
        f"{SUPABASE_URL}/rest/v1/kb_documents"
        f"?or=(tags.ilike.*{categoria}*,categoria.ilike.*{categoria}*)"
        f"&limit={limit}"
    )
    with httpx.Client(timeout=20.0) as client:
        try:
            r = client.get(url, headers=SUPABASE_HEADERS)
            r.raise_for_status()
            return r.json() or []
        except Exception:
            return []


# ─── 3. Tokens de aprovação ───────────────────────────────────────────────
def gerar_token() -> str:
    """Gera token único de 32 chars hex."""
    return secrets.token_hex(16)


def salvar_tokens(tokens: list[dict]) -> bool:
    """
    Insere tokens em batch na tabela curador_tokens.
    """
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
    return discordancias


# ─── 5. Montar email HTML ─────────────────────────────────────────────────
def render_email_html(feedbacks_com_discordancias: list[dict], total_feedbacks: int) -> str:
    """
    Monta email HTML rico com todos os feedbacks e botões de aprovar/rejeitar.

    Cada item de feedbacks_com_discordancias tem:
      {
        "feedback": {...},  # registro original da tabela validacoes
        "discordancias": [{campo_num, campo_nome, status_rt, comentario, token_aprovar, token_rejeitar}],
        "normas_kb": [{...}],
      }
    """
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
<div style="max-width:680px;margin:0 auto;padding:24px 16px;">

<!-- HEADER -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0F2A20;border-radius:10px;padding:20px 22px;margin-bottom:20px;">
  <tr>
    <td>
      <div style="color:#fff;font-size:14px;font-weight:600;letter-spacing:0.5px;">📋 InspectIA · Curadoria diária</div>
      <div style="color:#a8a4a0;font-size:12px;margin-top:4px;">{hoje}</div>
    </td>
  </tr>
</table>

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
        score_agente = fb.get("score_agente")
        score_real = fb.get("score_real")
        case_id = fb.get("case_id", "")[:24]

        score_text = ""
        if score_agente is not None:
            score_text = f"Score agente: <strong>{score_agente}/14</strong>"
            if score_real is not None and score_real != score_agente:
                score_text += f" → RT corrigiu para <strong>{score_real}/14</strong>"

        html += f"""
<!-- FEEDBACK #{idx} -->
<div style="background:#fff;border:1px solid #e2ded2;border-radius:10px;margin-bottom:20px;overflow:hidden;">
  <div style="background:#f0ede3;padding:14px 22px;border-bottom:1px solid #e2ded2;">
    <div style="font-size:11px;color:#6b6757;text-transform:uppercase;letter-spacing:1px;font-weight:600;">FEEDBACK #{idx}</div>
    <div style="font-size:15px;color:#091a14;font-weight:600;margin-top:4px;">{html_escape(produto)}</div>
    <div style="font-size:12px;color:#6b6757;margin-top:4px;">
      Categoria: <strong>{html_escape(categoria)}</strong>
      {' · ' + score_text if score_text else ''}
    </div>
    <div style="font-size:10px;color:#a8a4a0;margin-top:6px;font-family:monospace;">case: {html_escape(case_id)}</div>
  </div>
"""

        # Discordâncias do feedback
        for disc in discord:
            num = disc["campo_num"]
            nome = disc["campo_nome"]
            comentario = disc["comentario"]
            url_aprovar = f"{BACKEND_URL}/curador/aprovar/{disc['token_aprovar']}"
            url_rejeitar = f"{BACKEND_URL}/curador/rejeitar/{disc['token_rejeitar']}"

            html += f"""
  <div style="padding:18px 22px;border-bottom:1px solid #f0ede3;">
    <div style="font-size:11px;color:#6b6757;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:6px;">
      Campo {num} — {html_escape(nome)}
    </div>
    <div style="background:#f5ebd8;border-left:3px solid #9c5a0e;padding:10px 14px;border-radius:4px;margin-bottom:10px;font-size:13px;color:#0f2a20;line-height:1.6;">
      <strong style="color:#9c5a0e;">👤 RT corrige:</strong> "{html_escape(comentario)}"
    </div>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="left">
          <a href="{url_aprovar}" style="display:inline-block;background:#166534;color:#fff;text-decoration:none;font-weight:600;font-size:12px;padding:9px 18px;border-radius:6px;margin-right:8px;">
            ✓ Aprovar correção
          </a>
          <a href="{url_rejeitar}" style="display:inline-block;background:#fff;color:#992f2a;text-decoration:none;font-weight:600;font-size:12px;padding:9px 18px;border-radius:6px;border:1px solid #992f2a;">
            ✗ Rejeitar
          </a>
        </td>
      </tr>
    </table>
  </div>
"""

        # Normas KB relacionadas (rodapé do feedback)
        normas_kb = item.get("normas_kb", [])
        if normas_kb:
            html += f"""
  <div style="background:#fbfaf6;padding:12px 22px;border-top:1px solid #f0ede3;">
    <div style="font-size:10px;color:#6b6757;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:6px;">📚 Normas relevantes na KB ({len(normas_kb)})</div>
    <div style="font-size:11px;color:#6b6757;line-height:1.5;">
"""
            for norma in normas_kb[:5]:
                titulo = norma.get("titulo", norma.get("chave", "—"))[:80]
                html += f'      <div>· {html_escape(titulo)}</div>\n'
            html += """    </div>\n  </div>\n"""

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
def enviar_email(to: str, subject: str, html: str, cc: list[str] | None = None) -> bool:
    """Envia email via Resend API."""
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
        else:
            log(f"ERRO ao enviar email: status={r.status_code} body={r.text[:300]}")
            return False


# ─── 7. Marcar feedbacks como já-emailed (evita reenviar) ─────────────────
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


# ─── 8. Email de "nada hoje" pra você (admin) ────────────────────────────
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
    log("Curador Diário V2 — InspectIA")
    log("=" * 60)
    log(f"RT senior: {RT_SENIOR_EMAIL}")
    log(f"Admin: {ADMIN_EMAIL}")
    log(f"Backend: {BACKEND_URL}")
    log("")

    # 1. Busca pendentes
    pendentes = buscar_pendentes()
    log(f"Encontrados {len(pendentes)} feedback(s) pendentes de revisão.")

    if not pendentes:
        log("Nenhum feedback pendente. Enviando notificação silenciosa pro admin.")
        enviar_email_silencioso()
        log("Curador concluído (sem trabalho).")
        return

    # 2. Para cada feedback, extrai discordâncias e prepara tokens
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
            # Marca direto como aprovado, sem precisar de revisão da Giovanna
            with httpx.Client(timeout=20.0) as client:
                client.patch(
                    f"{SUPABASE_URL}/rest/v1/validacoes?case_id=eq.{case_id}",
                    headers={**SUPABASE_HEADERS, "Prefer": "return=minimal"},
                    json={"status_curador": "aprovado_sem_correcoes"},
                )
            continue

        # Cria 2 tokens por discordância (aprovar/rejeitar)
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

        # Busca normas relevantes da KB
        normas = buscar_normas_relevantes(fb.get("categoria", ""), limit=5)

        feedbacks_com_discordancias.append({
            "feedback": fb,
            "discordancias": discordancias,
            "normas_kb": normas,
        })
        case_ids_emailed.append(case_id)

    # Se todos os pendentes eram só "confirmação" (sem discordância), nada a enviar
    if not feedbacks_com_discordancias:
        log("Todos os feedbacks pendentes eram confirmações sem correções. Nada para Giovanna revisar.")
        enviar_email_silencioso()
        return

    # 3. Salva tokens no Supabase
    log(f"Gerando {len(tokens_a_salvar)} tokens (aprovar/rejeitar).")
    if not salvar_tokens(tokens_a_salvar):
        log("ERRO CRÍTICO: tokens não foram salvos. Abortando envio de email.")
        sys.exit(1)

    # 4. Monta email
    total_feedbacks = len(feedbacks_com_discordancias)
    total_disc = sum(len(f["discordancias"]) for f in feedbacks_com_discordancias)
    hoje_br = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")
    subject = f"InspectIA · Curadoria diária ({hoje_br}) · {total_disc} correç{'ões' if total_disc != 1 else 'ão'} para revisar"
    html = render_email_html(feedbacks_com_discordancias, total_feedbacks)

    # 5. Envia email pra Giovanna (com cópia pro admin)
    ok = enviar_email(RT_SENIOR_EMAIL, subject, html, cc=[ADMIN_EMAIL])
    if not ok:
        log("ERRO CRÍTICO: email não enviado. Tokens já gerados — feedbacks NÃO marcados como emailed.")
        sys.exit(1)

    # 6. Marca feedbacks como emailed
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

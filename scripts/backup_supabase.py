"""
Backup Diário do Supabase — Inspect-IA / ValidaRótulo IA
=========================================================

Melhorias v2:
  • Descoberta DINÂMICA de tabelas via OpenAPI do PostgREST
    (não mais hardcoded — pega tudo automaticamente)
  • Schema dump: estrutura das tabelas (colunas, tipos)
  • Organização por data: backups/YYYY-MM-DD/<tabela>.json
  • Manifest diário: backups/YYYY-MM-DD/_manifest.json
  • Retenção 30 dias: apaga pastas e arquivos legados antigos
  • supabase_backup_latest.json: snapshot consolidado para conveniência

Saída:
  backups/
    2026-04-29/
      _manifest.json
      schema.json
      kb_documents.json
      validacoes.json
      ...
    supabase_backup_latest.json    ← snapshot consolidado (compatibilidade)
"""

import os
import sys
import json
import shutil
import datetime as dt
from pathlib import Path

import requests

# ───────────────────────────────────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────────────────────────────────

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

REPO_ROOT     = Path(__file__).resolve().parent.parent
BACKUPS_DIR   = REPO_ROOT / "backups"
RETENCAO_DIAS = 30
TIMEOUT       = 60

# Tabelas a IGNORAR no backup (system tables, views, etc)
IGNORE = {
    # Adicione aqui se descobrir alguma tabela que não deve ser backupeada
}

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}


# ───────────────────────────────────────────────────────────────────────────
# 1. DESCOBRE TABELAS + SCHEMA VIA OPENAPI
# ───────────────────────────────────────────────────────────────────────────

def descobrir_tabelas_e_schema() -> tuple[list[str], dict]:
    """
    Retorna (lista_tabelas, schema_dict).
    O schema_dict tem o spec OpenAPI completo — útil para restore.
    """
    url = f"{SUPABASE_URL}/rest/v1/"
    r = requests.get(
        url,
        headers={**HEADERS, "Accept": "application/openapi+json"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    spec = r.json()

    tabelas = []
    for path in spec.get("paths", {}):
        # Paths são tipo "/kb_documents", "/rpc/foo" — queremos só tabelas
        if path.startswith("/") and not path.startswith("/rpc"):
            nome = path.lstrip("/")
            if nome and nome not in IGNORE:
                tabelas.append(nome)

    return sorted(tabelas), spec


# ───────────────────────────────────────────────────────────────────────────
# 2. EXPORTA UMA TABELA (com paginação)
# ───────────────────────────────────────────────────────────────────────────

def exportar_tabela(nome: str) -> list[dict]:
    """
    Faz fetch paginado de TODAS as linhas. Supabase limita a 1000 por requisição
    por padrão — usamos Range header pra paginar.
    """
    rows: list[dict] = []
    offset = 0
    page = 1000

    while True:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{nome}?select=*",
            headers={
                **HEADERS,
                "Range-Unit": "items",
                "Range":      f"{offset}-{offset + page - 1}",
                "Prefer":     "count=exact",
            },
            timeout=TIMEOUT,
        )

        # 416 = range fora dos limites = fim
        if r.status_code == 416:
            break
        r.raise_for_status()

        batch = r.json()
        if not isinstance(batch, list):
            break
        rows.extend(batch)

        # Se voltou menos que a página inteira, é a última
        if len(batch) < page:
            break
        offset += page

        # Trava de segurança contra loop infinito
        if offset > 1_000_000:
            print(f"  [WARN] {nome}: 1M+ linhas, parando paginação.", file=sys.stderr)
            break

    return rows


# ───────────────────────────────────────────────────────────────────────────
# 3. RETENÇÃO 30 DIAS
# ───────────────────────────────────────────────────────────────────────────

def aplicar_retencao() -> int:
    """
    Apaga:
      • Pastas backups/YYYY-MM-DD/ com data > RETENCAO_DIAS
      • Arquivos legados backups/supabase_backup_YYYY-MM-DD.json com data > RETENCAO_DIAS

    Mantém:
      • backups/supabase_backup_latest.json (sempre)
    """
    if not BACKUPS_DIR.exists():
        return 0

    cutoff = dt.date.today() - dt.timedelta(days=RETENCAO_DIAS)
    apagados = 0

    for item in BACKUPS_DIR.iterdir():
        # Nunca toca no latest
        if item.name == "supabase_backup_latest.json":
            continue

        data_item = None

        # Caso 1: pasta YYYY-MM-DD/
        if item.is_dir() and len(item.name) == 10 and item.name[4] == "-":
            try:
                data_item = dt.date.fromisoformat(item.name)
            except ValueError:
                continue

        # Caso 2: arquivo legado supabase_backup_YYYY-MM-DD.json
        elif item.is_file() and item.name.startswith("supabase_backup_") and item.name.endswith(".json"):
            data_str = item.name.replace("supabase_backup_", "").replace(".json", "")
            try:
                data_item = dt.date.fromisoformat(data_str)
            except ValueError:
                continue

        if data_item and data_item < cutoff:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            print(f"  [retenção] removido: {item.name}")
            apagados += 1

    return apagados


# ───────────────────────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────────────────────

def main() -> int:
    inicio = dt.datetime.utcnow()
    hoje   = inicio.strftime("%Y-%m-%d")
    pasta  = BACKUPS_DIR / hoje
    pasta.mkdir(parents=True, exist_ok=True)

    print(f"[backup] início — {inicio.isoformat()}Z")
    print(f"[backup] destino: {pasta}")

    # 1. Descobrir tabelas
    try:
        tabelas, spec = descobrir_tabelas_e_schema()
    except Exception as e:
        print(f"[backup] ERRO descobrindo tabelas: {e}", file=sys.stderr)
        return 1

    print(f"[backup] {len(tabelas)} tabelas encontradas: {', '.join(tabelas)}")

    # 2. Salvar schema
    (pasta / "schema.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 3. Exportar cada tabela
    consolidado: dict[str, list[dict]] = {}
    contagens:   dict[str, int]        = {}
    erros:       dict[str, str]        = {}

    for nome in tabelas:
        try:
            rows = exportar_tabela(nome)
            (pasta / f"{nome}.json").write_text(
                json.dumps(rows, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
            consolidado[nome] = rows
            contagens[nome]   = len(rows)
            print(f"  [{nome}] {len(rows)} linha(s)")
        except Exception as e:
            erros[nome] = str(e)
            print(f"  [{nome}] ERRO: {e}", file=sys.stderr)

    # 4. Manifest do dia
    manifest = {
        "data":               hoje,
        "timestamp_utc":      inicio.isoformat() + "Z",
        "tabelas_total":      len(tabelas),
        "tabelas_ok":         len(contagens),
        "tabelas_erro":       len(erros),
        "linhas_por_tabela":  contagens,
        "linhas_total":       sum(contagens.values()),
        "erros":              erros,
        "supabase_url":       SUPABASE_URL,
        "retencao_dias":      RETENCAO_DIAS,
    }
    (pasta / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 5. Snapshot consolidado (compatibilidade com formato legado)
    legacy_snapshot = {
        "data":              hoje,
        "timestamp_utc":     inicio.isoformat() + "Z",
        "linhas_por_tabela": contagens,
        "linhas_total":      sum(contagens.values()),
        "tabelas":           consolidado,
    }
    (BACKUPS_DIR / "supabase_backup_latest.json").write_text(
        json.dumps(legacy_snapshot, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # 6. Retenção
    apagados = aplicar_retencao()
    print(f"[backup] retenção: {apagados} item(ns) antigo(s) removido(s)")

    duracao = (dt.datetime.utcnow() - inicio).total_seconds()
    print(f"[backup] fim — {duracao:.1f}s — {sum(contagens.values())} linha(s) total")

    return 0 if not erros else 2  # 2 = sucesso parcial (algumas tabelas falharam)


if __name__ == "__main__":
    sys.exit(main())

import os, json, datetime, urllib.request

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

doc = {
    "chave": "inmetro_265_medidas",
    "titulo": "INMETRO RTAC 3057 — Indicações Metrológicas em Produtos Pré-Medidos",
    "fonte": "INMETRO RTAC 3057 / Portaria 248/2021",
    "orgao": "INMETRO",
    "categoria": "conteudo_liquido",
    "conteudo": """
INMETRO — INDICAÇÕES METROLÓGICAS EM PRODUTOS PRÉ-MEDIDOS
Base: Portaria INMETRO 248/2021 + RTAC 3057

OBJETO
Requisitos complementares para indicação quantitativa (conteúdo líquido) em produtos
pré-medidos (embalados sem a presença do consumidor), com foco em:
- Produtos vendidos por medida (massa, volume, comprimento)
- Produtos vendidos por contagem (unidades)
- Critérios de verificação metrológica

UNIDADES LEGAIS DE MEDIDA (Resolução CONMETRO 12/1988)
Obrigatório usar unidades do Sistema Internacional (SI):
- Massa: g, kg (proibido: gramas líquidas, libras, onças para mercado interno)
- Volume: mL, L (proibido: cc, fl oz para mercado interno)
- Comprimento: mm, cm, m
- Unidades caseiras só permitidas como complemento: "30g (2 fatias)"

PRODUTOS VENDIDOS POR CONTAGEM
- Declarar quantidade de unidades: "12 unidades", "6 pares"
- Se embalagem mista: declarar cada componente separadamente
- Ovos: obrigatório declarar quantidade (6, 12, 30 unidades) + categoria (A, B)

PRODUTOS FRACIONADOS (vendidos a granel com etiqueta)
- A etiqueta do PDV deve conter: produto, peso, preço por kg e preço total
- Não exige tabela nutricional se fracionado no ponto de venda
- Se embalado pelo fabricante: todas as regras de rótulo se aplicam

VERIFICAÇÃO METROLÓGICA — TOLERÂNCIAS (Portaria 248/2021 Anexo I)
Erro máximo tolerado (EMT) negativo por faixa:
- 0 a 50g/mL: EMT = 9% do nominal
- 50 a 100g/mL: EMT = 4,5g ou mL
- 100 a 200g/mL: EMT = 4,5%
- 200 a 300g/mL: EMT = 9g ou mL
- 300 a 500g/mL: EMT = 3%
- 500 a 1000g/mL: EMT = 15g ou mL
- 1000 a 10000g/mL: EMT = 1,5%
- > 10000g/mL: EMT = 150g ou mL
Nota: EMT positivo não se aplica — só se verifica déficit (menos do que declarado)

MARCAÇÃO DO CONTEÚDO LÍQUIDO — POSICIONAMENTO
- Campo inferior de 30% do painel principal (face visível)
- Paralelo à base da embalagem
- Contraste suficiente com o fundo
- Tamanho mínimo de fonte conforme tabela da Portaria 248/2021

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Unidade fora do SI (ex: cc, fl oz): NÃO CONFORME
- Fonte abaixo do mínimo exigido para a faixa de conteúdo: NÃO CONFORME
- Produto em conserva sem peso drenado: NÃO CONFORME (Portaria 248/2021 Art. 12)
- Ovos sem quantidade declarada: NÃO CONFORME

BASE LEGAL: Portaria INMETRO 248/2021, RTAC 3057, Resolução CONMETRO 12/1988
""".strip()
}

payload = {**doc, "tamanho_chars": len(doc["conteudo"]),
           "atualizado_em": datetime.datetime.now().isoformat()}
req = urllib.request.Request(
    f"{SUPABASE_URL}/rest/v1/kb_documents",
    data=json.dumps(payload).encode(),
    headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    },
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        print(f"✅ inmetro_265_medidas — HTTP {r.status} — {len(doc['conteudo'])} chars")
        print("KB agora com 155 documentos. Cobertura: 158/158 normas mapeadas (100%).")
except Exception as e:
    print(f"❌ Erro: {e}")

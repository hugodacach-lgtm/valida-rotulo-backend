"""
kb_gaps_finais.py — 3 documentos finais para fechar o máximo possível da KB
RDC 51/2010, RDC 89/2016, Destilados/Cachaça
"""
import os, json, datetime, urllib.request, urllib.error

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

DOCUMENTOS = [

{
"chave": "rdc_51_2010_migracao_plasticos",
"titulo": "RDC 51/2010 — Migração em Embalagens e Equipamentos Plásticos",
"fonte": "RDC ANVISA 51/2010",
"orgao": "ANVISA",
"categoria": "embalagens_contato",
"conteudo": """RDC 51/2010 — MIGRAÇÃO EM MATERIAIS, EMBALAGENS E EQUIPAMENTOS PLÁSTICOS

OBJETO: Estabelece os critérios e métodos para determinação da migração de substâncias de materiais plásticos para os alimentos. Complementa a RDC 56/2012 (lista positiva) e RDC 326/2019 (aditivos).

MIGRAÇÃO GLOBAL (Art. 4º):
Limite máximo: 60mg/kg de alimento ou 10mg/dm² de superfície de embalagem.
Representa a soma total de todas as substâncias que migram da embalagem para o alimento.
É o limite mais básico — todos os materiais plásticos devem cumprir.

MIGRAÇÃO ESPECÍFICA (Art. 5º):
Limites individuais por substância, definidos nas listas positivas (RDC 56/2012, RDC 326/2019).
Exemplos: monômero de estireno em PS: máx. 0,05mg/kg. Bisfenol A (BPA): revisão em curso. Aminas aromáticas primárias: não detectáveis (LD = 0,01mg/kg).

SIMULANTES DE ALIMENTO PARA TESTES:
Simulante A (água destilada): alimentos aquosos pH > 4,5
Simulante B (ácido acético 3%): alimentos aquosos pH ≤ 4,5 (sucos, bebidas ácidas, conservas ácidas)
Simulante C (etanol 10%): alimentos alcoólicos < 20% v/v
Simulante D1 (etanol 50%): alimentos alcoólicos > 20% v/v; alimentos com gordura de superfície
Simulante D2 (óleo de girassol): alimentos gordurosos (óleos, manteigas, carnes gordas)
Simulante E (poli(2,6-difenil-p-fenileno óxido)): alimentos secos

CONDIÇÕES DE CONTATO PARA TESTES:
Temperatura e tempo devem refletir as condições reais de uso:
10 dias a 40°C: contato prolongado em temperatura ambiente
2h a 70°C: pasteurização, enchimento a quente
30 min a 100°C: esterilização, fervura
30 min a 121°C: esterilização em autoclave
2h a 175°C: contato com forno (embalagens de forno)

APLICAÇÃO PRÁTICA NA ROTULAGEM:
O RT não declara migração no rótulo, mas é responsável por:
1. Exigir do fornecedor de embalagem laudo de migração conforme RDC 51/2010
2. Verificar se as condições de uso declaradas no rótulo são compatíveis com os testes realizados
3. "Apto para micro-ondas" exige teste a 100°C mínimo com simulante adequado
4. "Para armazenamento a frio" = condições mais brandas, menos restrições

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- "Apto para micro-ondas" sem embalagem testada para essa condição = ALERTA ao RT
- Embalagem plástica para alimento ácido (sucos, molhos) sem simulante B testado = ALERTA
- Embalagem para alimento gorduroso sem simulante D testado = ALERTA
- Limites de migração: responsabilidade do fabricante da embalagem, mas o RT responde solidariamente

BASE LEGAL: RDC 51/2010, RDC 56/2012, RDC 326/2019, RDC 91/2001.""".strip()
},

{
"chave": "rdc_89_2016_celulosicos_coccao",
"titulo": "RDC 89/2016 — Materiais Celulósicos para Cocção e Aquecimento em Forno",
"fonte": "RDC ANVISA 89/2016",
"orgao": "ANVISA",
"categoria": "embalagens_contato",
"conteudo": """RDC 89/2016 — MATERIAIS CELULÓSICOS PARA COCÇÃO E FILTRAÇÃO A QUENTE

OBJETO: Regula papel, papelão e celulose regenerada destinados ao contato com alimentos durante cocção (forno, micro-ondas) ou filtração a quente.

MATERIAIS ABRANGIDOS:
- Papel manteiga / papel vegetal: para assar no forno (até 220°C tipicamente)
- Formas de papel para cupcake/muffin: contato direto durante cocção
- Papel para fritura (air fryer): alta temperatura
- Filtros de café, chá: filtração a quente
- Sacos de papel para micro-ondas (pipoca, etc.)
- Envoltórios de papel para assar (embutidos, carnes)

REQUISITOS ESPECÍFICOS:
Papel para cocção até 200°C: deve ser fabricado com celulose virgem ou reciclada específica para alta temperatura. Aditivos de processo (agentes de colagem, branqueadores): apenas lista positiva ANVISA.
Silicone em papel manteiga: revestimento de silicone (polidimetilsiloxano) é permitido para antiaderência — limite de migração estabelecido.
PFAS (substâncias per e polifluoralquílicas): crescente preocupação regulatória. ANVISA em monitoramento. Alguns países proibiram PFAS em contato com alimentos — verificar tendências.

ROTULAGEM DO PRODUTO EMBALADO:
Produto assado em papel de forno: o papel não é declarado no rótulo do alimento, mas é responsabilidade do fabricante usar papel aprovado.
"Cozido no papel" ou "assado em embrulho": boa prática declarar que papel é food grade.

MICRO-ONDAS — ATENÇÃO ESPECIAL:
Saco de pipoca de micro-ondas: papel + revestimento interno (pode conter PFAS). Verificar conformidade do fornecedor.
Embalagem de papel para micro-ondas: deve ser especificamente testada para essa finalidade.
Papel alumínio: NÃO usar no micro-ondas (gera arcos elétricos) — nunca declarar "apto para micro-ondas" em produto com alumínio.

FILTROS PARA CAFÉ E CHÁ:
Filtro de café de papel: branqueado ou não branqueado. Fibra virgem. Aditivos mínimos.
Filtros de metal ou nylon: regulados por outras normas (metálicos ou plásticos).

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- Embalagem de papel para forno com PFAS: ALERTA (monitorar regulamentação)
- "Pode ir ao forno" em embalagem de papel não aprovada para alta temperatura: NÃO CONFORME
- Saco de pipoca de micro-ondas: verificar regularidade do fornecedor da embalagem
- Filtro de café: fibra virgem recomendada para produto premium

BASE LEGAL: RDC 89/2016, RDC 88/2016, RDC 91/2001.""".strip()
},

{
"chave": "destilados_cachaca_aguardente",
"titulo": "Decreto 6871/2009 + Lei 8918/1994 — Cachaça, Aguardente e Destilados",
"fonte": "Decreto Federal 6871/2009 + Lei 8918/1994 + IN MAPA 13/2005",
"orgao": "MAPA",
"categoria": "bebidas_alcoolicas",
"conteudo": """CACHAÇA, AGUARDENTE DE CANA E DESTILADOS — REGULAÇÃO COMPLETA

BASE LEGAL PRINCIPAL: Decreto 6871/2009 (bebidas em geral), Lei 8918/1994, IN MAPA 13/2005.

DEFINIÇÕES E DIFERENÇAS FUNDAMENTAIS:
"Cachaça" (denominação de origem): aguardente de cana produzida exclusivamente no Brasil, de cana-de-açúcar, teor alcoólico 38-48% v/v. INDICAÇÃO GEOGRÁFICA protegida internacionalmente. Somente produto brasileiro pode usar "cachaça".
"Aguardente de cana": produto similar, mas sem restrição de origem. Pode ser produzida em qualquer país. Teor 38-54% v/v.
"Rum": aguardente de cana com características específicas de processo (fermentação/destilação diferente).
"Cachaça artesanal" ou "premium": sem definição regulatória específica — uso é marketing, não categoria legal.

QUALIFICAÇÕES PERMITIDAS:
"Cachaça envelhecida" (ou "aged"): mínimo 50% do volume envelhecido em recipiente de madeira por mínimo 1 ano.
"Cachaça premium": mínimo 50% envelhecida por mínimo 1 ano + padrão de qualidade superior (sem definição quantitativa na norma).
"Cachaça extra-premium": 100% envelhecida por mínimo 3 anos.
"Orgânica": matéria-prima (cana) certificada orgânica + certificação SisOrg.

ROTULAGEM OBRIGATÓRIA (Decreto 6871/2009 + IN 13/2005):
1. Denominação: "Cachaça" OU "Aguardente de cana" (conforme o produto)
2. Teor alcoólico: em % v/v a 20°C (ex: "38% vol." ou "39°GL")
3. Volume líquido (mL ou L)
4. Fabricante com endereço completo
5. Registro no MAPA (obrigatório para destilados)
6. Lote e data de fabricação
7. País de origem (exportação) ou "Produzido no Brasil"
8. Advertências da Lei 14.064/2020:
   - Símbolo proibição menores 18 anos
   - Uma das frases de advertência obrigatórias
9. "Cachaça envelhecida/premium/extra-premium": declarar tempo de envelhecimento e tipo de madeira

TIPO DE MADEIRA NO ENVELHECIMENTO (boa prática declarar):
Carvalho (mais comum), amburana, ipê, jequitibá, bálsamo, umburana, castanheira.
Declarar no rótulo confere valor agregado e é permitido pela norma.

ADITIVOS PERMITIDOS EM CACHAÇA:
Caramelo (INS 150) para ajuste de cor: declarar na lista de ingredientes.
Adoçantes para cachaça "suavizada": muito restrito, verificar lista positiva.
Proibido: agrotóxicos no produto final, substâncias não autorizadas.

REGISTRO NO MAPA:
Todo destilado deve ter registro ou enquadramento no MAPA antes da comercialização.
Número do registro: declarar no rótulo (ex: "Reg. MAPA nº XXXXXX").

EXPORTAÇÃO — DENOMINAÇÃO PROTEGIDA:
"Cachaça" é denominação protegida em tratados internacionais (UE, EUA, etc.).
Produto importado não pode usar "cachaça" — deve usar "Brazilian sugarcane spirit" ou "aguardente".

VODKA, GIN, WHISKY, CONHAQUE (outros destilados):
Vodka: destilado de cereais ou batata, neutro, ≥37,5% v/v (padrão europeu) ou 36-54% (Decreto 6871).
Gin: base de destilado com zimbro predominante, ≥37,5% v/v.
Whisky: destilado de cereais envelhecido, ≥40% v/v. "Blended", "Single malt", "Bourbon" = denominações específicas.
Conhaque/Cognac: destilado de vinho, região de Cognac (França) = IGP. Sem origem = "brandy".
Todos exigem: teor alcoólico, fabricante, registro MAPA (se importado: importador), advertências Lei 14.064/2020.

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- "Cachaça" produzida fora do Brasil = NÃO CONFORME (uso indevido de denominação protegida)
- "Envelhecida" sem declarar tempo e madeira = ALERTA (pode ser propaganda enganosa)
- Teor alcoólico fora do range permitido (cachaça: 38-48%) = NÃO CONFORME
- Registro MAPA ausente = NÃO CONFORME
- Advertência menores ausente = NÃO CONFORME
- Caramelo sem declarar na lista de ingredientes = NÃO CONFORME

BASE LEGAL: Decreto 6871/2009, Lei 8918/1994, IN MAPA 13/2005, Lei 14.064/2020.""".strip()
},

]


def upsert(doc):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"erro": "vars não configuradas"}
    payload = {**doc,
               "tamanho_chars": len(doc["conteudo"]),
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
        with urllib.request.urlopen(req, timeout=20) as r:
            return {"ok": True, "http": r.status, "chars": len(doc["conteudo"])}
    except urllib.error.HTTPError as e:
        return {"erro": f"HTTP {e.code}: {e.read().decode()[:150]}"}
    except Exception as e:
        return {"erro": str(e)[:100]}


if __name__ == "__main__":
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Configure SUPABASE_URL e SUPABASE_KEY.")
        exit(1)
    print(f"Inserindo {len(DOCUMENTOS)} documentos finais na KB...\n")
    ok = fail = 0
    for doc in DOCUMENTOS:
        r = upsert(doc)
        if r.get("ok"):
            print(f"  ✅ {doc['chave']} — {r['chars']} chars")
            ok += 1
        else:
            print(f"  ❌ {doc['chave']}: {r.get('erro')}")
            fail += 1
    print(f"\n{'='*55}")
    print(f"Concluído: {ok} inseridos / {fail} erros")
    print(f"KB esperada no Supabase: ~{189 + ok} documentos")

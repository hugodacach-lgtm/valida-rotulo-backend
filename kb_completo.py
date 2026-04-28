"""
Script de inserção completa da KB — ValidaRótulo IA
Cobre as 46 normas que o crawler automático não consegue acessar.
Prioridade: POA crítico → ANVISA gerais → Não-POA completo

Execução no Shell do Render:
python3 - << 'EOF'
<cole o conteúdo deste arquivo>
EOF
"""

import os, json, datetime, urllib.request, urllib.error

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

DOCUMENTOS = [

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 1 — POA CRÍTICO (normas de acesso restrito do MAPA/ANVISA para POA)
# ══════════════════════════════════════════════════════════════════════════════

{
"chave": "moluscos_cefalopodes",
"titulo": "Port. 1022/2024 — RTIQ Moluscos Cefalópodes (Lula, Polvo, Pota)",
"fonte": "Portaria MAPA 1022/2024 — gov.br",
"orgao": "MAPA",
"categoria": "pescado_poa",
"conteudo": """
PORTARIA MAPA Nº 1022/2024 — RTIQ MOLUSCOS CEFALÓPODES

PRODUTO: Moluscos cefalópodes frescos, resfriados, congelados e processados
ESPÉCIES: Lula (Doryteuthis spp.), Polvo (Octopus spp.), Pota (Dosidicus gigas)
ÓRGÃO DE INSPEÇÃO: SIF/DIPOA (produto de origem animal)

DENOMINAÇÕES DE VENDA (conforme Art. 3º)
- "Lula fresca", "Lula resfriada", "Lula congelada"
- "Polvo fresco", "Polvo resfriado", "Polvo congelado"
- "Pota fresca", "Pota congelada"
- Produtos processados: acrescentar forma de processamento (ex: "Lula em anéis congelada")
- Proibido denominar "lula" produto que não seja da espécie correta

REQUISITOS DE COMPOSIÇÃO E QUALIDADE
- Produto deve ser íntegro, limpo e livre de parasitas visíveis
- Temperatura: fresco/resfriado ≤ 4°C; congelado ≤ -18°C
- Glaceamento (quando aplicável): declarar percentual líquido e peso drenado
- Aditivos: conforme lista positiva ANVISA vigente (IN 211/2023)
- Proibido: uso de polifosfatos para retenção excessiva de água

ROTULAGEM OBRIGATÓRIA (Art. 7º)
- Denominação de venda conforme padrão
- Espécie científica (quando exigível pelo mercado de exportação)
- Peso líquido e peso drenado (quando em meio líquido ou glaceado)
- Declaração de glaceamento: "X% de glaceamento" ou "Peso líquido sem glaceamento: Xg"
- Data de fabricação e validade
- Temperatura de conservação
- Carimbo SIF
- País de origem (para produtos importados)
- Alérgenos: cefalópodes são crustáceos/moluscos — declarar "CONTÉM MOLUSCOS"

VALIDAÇÃO — PONTOS CRÍTICOS
Campo Denominação: verificar se espécie declarada corresponde ao produto
Campo Conteúdo Líquido: se glaceado, exige peso drenado declarado
Campo Alérgenos: moluscos são alérgenos obrigatórios (RDC 727/2022 Art. 41)
Campo Conservação: temperatura obrigatória para produto congelado/resfriado
""".strip()
},

{
"chave": "regularizacao_rdc843",
"titulo": "RDC 843/2024 — Marco de Regularização de Alimentos ANVISA",
"fonte": "RDC ANVISA 843/2024 + IN 281/2024",
"orgao": "ANVISA",
"categoria": "regularizacao",
"conteudo": """
RDC Nº 843/2024 — MARCO DE REGULARIZAÇÃO DE ALIMENTOS
IN Nº 281/2024 — Categorias e documentação por tipo de regularização
VIGÊNCIA: 01/09/2024

MODELO DE TRÊS VIAS (por critério de risco sanitário)

1. REGISTRO (maior risco — aprovação prévia obrigatória)
Categorias: fórmulas infantis, fórmulas para nutrição enteral, alimentos para
erros inatos do metabolismo, fórmulas de seguimento para lactentes.
Processo: submissão de dossiê completo + aprovação formal pela ANVISA antes da comercialização.
Rótulo: deve conter número de registro ANVISA (ex: "Reg. MS nº XXXXXXXX.XXX.XXXX.XXX")

2. NOTIFICAÇÃO (risco intermediário — sem aprovação prévia, mas comunicação obrigatória)
Categorias obrigadas à notificação:
- Suplementos alimentares (prazo encerrado: 01/09/2025)
- Alimentos para controle de peso
- Alimentos para gestantes e nutrizes
- Cereais para alimentação infantil
Processo: notificação eletrônica no sistema SOLICITA/ANVISA antes da comercialização.
Rótulo: deve indicar "Notificado na ANVISA sob nº XX.XXX.XXXX"
ATENÇÃO: Suplementos sem notificação após 01/09/2025 são IRREGULARES.

3. COMUNICAÇÃO (menor risco — apenas comunicação às autoridades locais)
Categorias: alimentos convencionais em geral, bebidas, condimentos,
produtos de panificação industriais, conservas, etc.
Processo: comunicação simplificada à vigilância sanitária municipal/estadual.
Rótulo: não exige número de registro/notificação ANVISA para alimentos convencionais.

IMPACTO NA ROTULAGEM
- Alimentos convencionais: NÃO precisam de número de registro no rótulo
- Suplementos: DEVEM ter número de notificação no rótulo após 01/09/2025
- Fórmulas: DEVEM ter número de registro no rótulo
- A ausência de número de registro/notificação em produto que exige é IRREGULARIDADE

BASE LEGAL: RDC 843/2024, IN 281/2024, RDC 243/2018 (suplementos), RDC 241/2018 (fórmulas)
""".strip()
},

{
"chave": "rotulagem_anvisa_rdc715",
"titulo": "RDC 715/2022 — Lactose: Declaração Obrigatória em Rótulos",
"fonte": "RDC ANVISA 715/2022",
"orgao": "ANVISA",
"categoria": "rotulagem_especial",
"conteudo": """
RDC Nº 715/2022 — DECLARAÇÃO DE LACTOSE EM ALIMENTOS EMBALADOS
VIGÊNCIA: 02/01/2023 (prazo de adequação)

OBJETO
Estabelece critérios para declaração do teor de lactose em alimentos embalados,
complementando a RDC 727/2022 (rotulagem geral).

CATEGORIAS E CRITÉRIOS DE DECLARAÇÃO (Art. 4º)
1. "ZERO LACTOSE" ou "SEM LACTOSE": teor ≤ 0,01g lactose por 100g ou 100mL do produto
2. "BAIXO TEOR DE LACTOSE": teor > 0,01g e ≤ 1g por 100g ou 100mL
3. "CONTÉM LACTOSE": teor > 1g por 100g ou 100mL (obrigatório quando presente)
4. Produtos naturalmente sem lactose (ex: sucos, carnes): não precisam declarar

DECLARAÇÃO OBRIGATÓRIA — Art. 5º
Qualquer produto que contenha lactose deve declarar no painel principal ou
painel de informações: "CONTÉM LACTOSE" ou o teor quantitativo.

RELAÇÃO COM ALÉRGENOS (RDC 727/2022 Art. 41)
- Lactose é derivado de leite → leite e derivados são alérgenos obrigatórios
- Declaração de alérgenos: "CONTÉM LEITE" (obrigatório se contiver lactose)
- A declaração "CONTÉM LACTOSE" não substitui "CONTÉM LEITE E DERIVADOS"

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Produto lácteo sem declaração de lactose: ALERTA (verificar se é zero lactose)
- Produto com "zero lactose" deve ter teor comprovado ≤ 0,01g/100g
- Queijo curado com baixo teor: pode ser "baixo teor" ou "zero lactose"
- Iogurte: geralmente "baixo teor" — verificar declaração
- Leite integral/desnatado: "CONTÉM LACTOSE" obrigatório

BASE LEGAL: RDC 715/2022, RDC 727/2022 (rotulagem geral), RDC 26/2015 (alérgenos — revogada e incorporada à RDC 727/2022)
""".strip()
},

{
"chave": "aromatizantes_rdc725",
"titulo": "RDC 725/2022 — Aromas e Aromatizantes em Alimentos",
"fonte": "RDC ANVISA 725/2022",
"orgao": "ANVISA",
"categoria": "aditivos_rotulagem",
"conteudo": """
RDC Nº 725/2022 — AROMAS E AROMATIZANTES EM ALIMENTOS
VIGÊNCIA: 02/01/2023

OBJETO
Estabelece a lista positiva de aromas/aromatizantes autorizados e as condições de uso
e declaração na rotulagem de alimentos.

TIPOS DE AROMATIZANTES (Art. 3º)
1. AROMA NATURAL: derivado de matéria-prima animal ou vegetal por processos físicos,
   microbiológicos ou enzimáticos. Ex: "aroma natural de baunilha", "extrato de fumaça"
2. AROMA ARTIFICIAL: sintetizado quimicamente, mesmo que idêntico ao natural.
   Ex: "aroma artificial de morango"
3. AROMA IDÊNTICO AO NATURAL: estrutura química idêntica ao natural, mas obtido sinteticamente
4. AROMA DE FUMAÇA (líquida ou condensada): obtido por condensação de fumaça.
   Declarar: "aroma de fumaça" ou "extrato natural de fumaça"
5. AROMA DE REAÇÃO (Maillard): gerado por reação térmica de aminoácidos + açúcares

DECLARAÇÃO NA LISTA DE INGREDIENTES (Art. 15º)
- Obrigatório declarar a função: "aroma", "aromatizante" ou "aroma natural"
- Não é obrigatório declarar o nome específico do composto aromático
- Exemplos corretos: "aroma de morango", "aroma natural de baunilha", "aromatizante"
- Extrato natural de fumaça: declarar como "extrato natural de fumaça" ou "aroma de fumaça"
- Proibido: usar "natural" para aromas artificiais ou idênticos ao natural

PONTOS CRÍTICOS PARA VALIDAÇÃO
- "Aroma" sem especificação: permitido, mas verificar se produto usa "natural" indevidamente
- Extrato de fumaça em embutidos: comum e permitido — declarar corretamente
- "Aroma idêntico ao natural" rotulado como "aroma natural": NÃO CONFORME
- Aromatizantes devem estar na lista positiva da RDC 725/2022

BASE LEGAL: RDC 725/2022, IN 211/2023 (lista de aditivos inclui aromatizantes)
""".strip()
},

{
"chave": "irradiacao_rdc21",
"titulo": "RDC 21/2001 — Irradiação de Alimentos: Rotulagem Obrigatória",
"fonte": "RDC ANVISA 21/2001",
"orgao": "ANVISA",
"categoria": "rotulagem_especial",
"conteudo": """
RDC Nº 21/2001 — IRRADIAÇÃO DE ALIMENTOS
(Ainda vigente para rotulagem — complementada por normas posteriores)

OBJETO
Regulamenta o uso de irradiação ionizante em alimentos e as exigências de rotulagem.

DECLARAÇÃO OBRIGATÓRIA NO RÓTULO (Art. 7º)
Qualquer alimento submetido a tratamento de irradiação deve declarar no rótulo:
- "ALIMENTO IRRADIADO" — com letras de tamanho visível no painel principal
- OU o símbolo internacional de irradiação (radura — círculo verde com planta estilizada)
- Dose utilizada (em kGy) — exigível nas informações técnicas

ALIMENTOS COMUMENTE IRRADIADOS NO BRASIL
- Especiarias e temperos secos (pimenta, orégano, alho em pó): redução microbiana
- Frutas tropicais (manga, mamão): controle de pragas para exportação
- Frango e carnes: controle de Salmonella
- Cereais e grãos: controle de insetos

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Especiarias e temperos: verificar se foram irradiados e se há declaração
- Ingredientes irradiados em produto composto: também exige declaração
- Ausência de "ALIMENTO IRRADIADO" em produto irradiado: NÃO CONFORME

BASE LEGAL: RDC 21/2001, Decreto 72.718/1973 (normas gerais de alimentos irradiados)
""".strip()
},

{
"chave": "nova_formula_rdc902",
"titulo": "RDC 902/2024 — Rotulagem de Nova Fórmula / Alteração de Composição",
"fonte": "RDC ANVISA 902/2024",
"orgao": "ANVISA",
"categoria": "rotulagem_especial",
"conteudo": """
RDC Nº 902/2024 — DECLARAÇÃO DE NOVA FÓRMULA EM ALIMENTOS

OBJETO
Estabelece critérios para declaração de "NOVA FÓRMULA" ou "FÓRMULA MELHORADA"
em rótulos de alimentos, quando há alteração relevante na composição do produto.

QUANDO DECLARAR "NOVA FÓRMULA" (Art. 3º)
Obrigatório quando houver alteração que afete:
a) Características sensoriais perceptíveis pelo consumidor (sabor, textura, cor)
b) Valor nutricional significativo (redução de sódio, açúcar, gordura trans)
c) Substituição de ingrediente principal

PRAZO DE MANUTENÇÃO DA DECLARAÇÃO
- Mínimo: 12 meses a partir do início da comercialização com nova fórmula
- Máximo: 24 meses (após isso, retirar o selo "nova fórmula")

POSICIONAMENTO NO RÓTULO (Art. 6º)
- Painel principal, próximo à denominação de venda
- Fonte legível, destaque adequado (não pode ser menor que denominação)
- Não pode induzir ao erro sobre benefícios não comprovados

VEDAÇÕES (Art. 8º)
- Proibido usar "nova fórmula" sem alteração real na composição
- Proibido manter "nova fórmula" por mais de 24 meses
- Proibido associar a claims de saúde não autorizados pela ANVISA

PONTOS CRÍTICOS PARA VALIDAÇÃO
- "Nova Fórmula" presente: verificar se está há mais de 24 meses (irregular se sim)
- Alteração de composição sem "Nova Fórmula": não é exigência (apenas quando produto quer comunicar)
- Associação com claim não autorizado: NÃO CONFORME

BASE LEGAL: RDC 902/2024, RDC 727/2022 (rotulagem geral)
""".strip()
},

{
"chave": "regularizacao_in281",
"titulo": "IN 281/2024 — Categorias de Alimentos por Tipo de Regularização",
"fonte": "IN ANVISA 281/2024",
"orgao": "ANVISA",
"categoria": "regularizacao",
"conteudo": """
INSTRUÇÃO NORMATIVA Nº 281/2024 — CATEGORIAS POR TIPO DE REGULARIZAÇÃO
Complementa a RDC 843/2024. VIGÊNCIA: 01/09/2024

CATEGORIA A — REGISTRO (aprovação prévia ANVISA)
- Fórmulas infantis para lactentes e crianças de primeira infância
- Fórmulas de seguimento para lactentes
- Fórmulas para nutrição enteral
- Alimentos para erros inatos do metabolismo
Documentação: dossiê técnico completo, estudos de estabilidade, laudos analíticos

CATEGORIA B — NOTIFICAÇÃO (sem aprovação prévia, comunicação obrigatória)
Prazo de notificação encerrado em 01/09/2025 para:
- Suplementos alimentares (RDC 243/2018 + IN 28/2018)
- Alimentos para controle de peso (redução calórica)
- Alimentos para gestantes e nutrizes
- Cereais para alimentação infantil (6-36 meses)
- Compostos proteicos para fins esportivos
Documentação para notificação: formulário eletrônico + rótulo + especificação técnica

CATEGORIA C — COMUNICAÇÃO (alimentos convencionais)
Inclui a maioria dos alimentos industrializados:
- Bebidas (sucos, refrigerantes, águas, cervejas, vinhos)
- Laticínios convencionais (leite, queijo, iogurte — exceto fórmulas)
- Produtos de panificação, cereais, massas
- Conservas, molhos, condimentos
- Chocolates, doces, sorvetes
- Carnes e derivados (POA — também regulados pelo MAPA/SIF)
Não exigem número de registro/notificação ANVISA no rótulo

ALIMENTOS ISENTOS DE REGULARIZAÇÃO
- Frutas frescas, hortaliças e legumes in natura
- Carnes frescas não processadas
- Ovos in natura
- Mel in natura (sujeito ao MAPA)
- Pescado fresco

IMPACTO NO CAMPO DE VALIDAÇÃO "FABRICANTE"
- Suplementos: verificar se número de notificação está declarado no rótulo
- Fórmulas infantis: verificar número de registro MS
- Alimentos convencionais: não exigir número de registro
""".strip()
},

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 2 — ANVISA ROTULAGEM GERAL (normas base inacessíveis ao crawler)
# ══════════════════════════════════════════════════════════════════════════════

{
"chave": "rdc_429_rotulagem_nutri",
"titulo": "RDC 429/2020 — Rotulagem Nutricional de Alimentos Embalados",
"fonte": "RDC ANVISA 429/2020",
"orgao": "ANVISA",
"categoria": "rotulagem_nutricional",
"conteudo": """
RDC Nº 429/2020 — ROTULAGEM NUTRICIONAL DE ALIMENTOS EMBALADOS
VIGÊNCIA PLENA: outubro/2022. Complementada pela IN 75/2020.

TABELA DE INFORMAÇÃO NUTRICIONAL — REQUISITOS (Art. 8º a 20º)
Declaração obrigatória por porção E por 100g ou 100mL:
- Valor energético (kcal e kJ)
- Carboidratos totais (g)
- Açúcares totais (g) — NOVIDADE vs norma anterior
- Açúcares adicionados (g) — NOVIDADE
- Proteínas (g)
- Gorduras totais (g)
- Gorduras saturadas (g)
- Gorduras trans (g)
- Fibra alimentar (g)
- Sódio (mg)

PORÇÃO PADRÃO (Art. 5º): conforme Anexo II da IN 75/2020 por categoria de alimento.

LUPA FRONTAL — DECLARAÇÃO OBRIGATÓRIA (Art. 21º a 26º)
Ícone circular com lupa no painel principal, declarando quantidade ALTA de:
- Açúcares adicionados: > 15g por 100g (sólidos) ou > 7,5g por 100mL (líquidos)
- Gorduras saturadas: > 6g por 100g (sólidos) ou > 3g por 100mL (líquidos)
- Sódio: > 600mg por 100g (sólidos) ou > 300mg por 100mL (líquidos)
Declarar TODOS os nutrientes críticos que ultrapassam os limites.
A lupa NÃO substitui a tabela nutricional.

CÁLCULO DE VALOR ENERGÉTICO (Anexo I)
- Carboidratos: 4 kcal/g
- Proteínas: 4 kcal/g
- Gorduras: 9 kcal/g
- Fibra alimentar: 2 kcal/g
- Álcool: 7 kcal/g
- Polióis: 2,4 kcal/g
- Eritritol: 0 kcal/g

TOLERÂNCIAS ANALÍTICAS (Art. 19º)
- Nutrientes com valor declarado ≤ limite máximo: tolerância de ±20%
- Vitaminas e minerais: ±20% em relação ao declarado

DECLARAÇÕES OPCIONAIS
Vitaminas e minerais: podem ser declarados se ≥ 5% da IDR por porção.

BASE LEGAL: RDC 429/2020, IN 75/2020, RDC 727/2022 Art. 19 (remissão à rotulagem nutricional)
""".strip()
},

{
"chave": "in_75_porcoes",
"titulo": "IN 75/2020 — Porções de Alimentos para Rotulagem Nutricional",
"fonte": "IN ANVISA 75/2020",
"orgao": "ANVISA",
"categoria": "rotulagem_nutricional",
"conteudo": """
INSTRUÇÃO NORMATIVA Nº 75/2020 — PORÇÕES PARA ROTULAGEM NUTRICIONAL
Complementa a RDC 429/2020. Define porção padrão por categoria.

PRINCIPAIS PORÇÕES POR CATEGORIA (Anexo II)

CARNES E DERIVADOS
- Carnes frescas (bovina, suína, aves, pescado): 100g
- Embutidos (salsicha, linguiça, mortadela): 50g
- Presunto, apresuntado: 30g
- Charque, carne seca: 45g
- Hambúrguer: 100g (unidade se ≤ 120g)

LATICÍNIOS
- Leite fluido: 200mL
- Iogurte: 100g (ou embalagem individual se ≤ 200g)
- Queijo maturado (parmesão, provolone): 30g
- Queijo fresco (minas, mussarela): 30g
- Requeijão, cream cheese: 30g
- Manteiga, margarina: 10g
- Leite em pó: 26g

BEBIDAS
- Bebidas em geral (sucos, refrigerantes, isotônicos): 200mL
- Bebidas alcoólicas: 350mL (cerveja), 150mL (vinho), 50mL (destilados)
- Água: sem obrigação de tabela nutricional

CEREAIS E DERIVADOS
- Pão de forma: 50g
- Biscoito salgado (cracker): 30g
- Biscoito doce: 30g
- Macarrão seco: 80g; cozido: 140g
- Farinha de trigo: 50g
- Arroz cru: 50g; cozido: 125g
- Aveia em flocos: 40g

AÇÚCAR E DOCES
- Açúcar refinado/cristal: 5g
- Chocolate (barra): 25g
- Sorvete: 60g
- Mel: 15g
- Doce de leite: 30g

ÓLEOS E GORDURAS
- Óleos vegetais: 10mL
- Azeite: 10mL

OVOS
- Ovo: 50g (1 unidade média)

OBSERVAÇÃO IMPORTANTE
A porção padrão deve constar no rótulo como "Porção: Xg (medida caseira)"
Ex: "Porção: 30g (2 fatias)" para presunto; "Porção: 50g (1 gomo)" para linguiça

BASE LEGAL: IN 75/2020, RDC 429/2020
""".strip()
},

{
"chave": "inmetro_251_requisitos",
"titulo": "INMETRO Port. 248/2021 — Conteúdo Líquido: Requisitos e Tolerâncias",
"fonte": "Portaria INMETRO 248/2021 / RTAC 249/2021",
"orgao": "INMETRO",
"categoria": "conteudo_liquido",
"conteudo": """
PORTARIA INMETRO Nº 248/2021 — CONTEÚDO LÍQUIDO EM PRODUTOS PRÉ-MEDIDOS
(Revogou a Portaria 157/2002. Vigente desde 01/01/2022)

DECLARAÇÃO OBRIGATÓRIA (Art. 5º)
Todo produto embalado deve declarar o conteúdo líquido em unidade legal (SI):
- Produtos sólidos: gramas (g) ou quilogramas (kg)
- Produtos líquidos: mililitros (mL) ou litros (L)
- Produtos viscosos/pastosos: gramas (g) ou mililitros (mL)

POSICIONAMENTO NO RÓTULO (Art. 8º)
- Painel principal (face visível ao consumidor)
- Altura mínima dos algarismos conforme conteúdo:
  • ≤ 50g ou 50mL: 2mm mínimo
  • 50 a 200g ou 200mL: 3mm mínimo
  • 200 a 1000g ou 1000mL: 4mm mínimo
  • > 1000g ou 1000mL: 6mm mínimo

TOLERÂNCIAS PERMITIDAS (Erro Médio — Anexo I)
As tolerâncias são "T" (negativa apenas):
- Até 100g/mL: T = 4,5g ou 4,5mL
- 100 a 200g/mL: T = 4,5% do nominal
- 200 a 300g/mL: T = 9g ou 9mL
- 300 a 500g/mL: T = 3%
- 500 a 1000g/mL: T = 15g ou 15mL
- 1000 a 10000g/mL: T = 1,5%
- > 10000g/mL: T = 150g ou 150mL

DECLARAÇÃO DE PESO DRENADO (Art. 12º)
Obrigatório para produtos em meio líquido (conservas, atum em óleo, palmito, etc.):
- Declarar: "Peso líquido: Xg — Peso drenado: Yg"
- Ambos no mesmo campo e com mesma destaque

UNIDADES PROIBIDAS
- Não usar "quilos" (abreviação incorreta de kg)
- Não usar "cc" (centímetros cúbicos) — usar mL
- Não usar unidades caseiras como "xícara" isoladamente

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Produto em conserva sem peso drenado: NÃO CONFORME
- Tamanho da fonte abaixo do mínimo para o conteúdo: NÃO CONFORME
- Unidade incorreta (cc, quilos): NÃO CONFORME

BASE LEGAL: Portaria INMETRO 248/2021, RTAC 249/2021
""".strip()
},

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 3 — ANVISA NÃO-POA: ÓLEOS, GORDURAS, CHOCOLATES, CONDIMENTOS
# ══════════════════════════════════════════════════════════════════════════════

{
"chave": "oleos_gorduras",
"titulo": "RDC 270/2005 + RDC 716/2022 — Óleos e Gorduras Vegetais",
"fonte": "RDC ANVISA 270/2005 atualizada pela RDC 716/2022",
"orgao": "ANVISA",
"categoria": "nao_poa_oleos",
"conteudo": """
RDC Nº 270/2005 — ÓLEOS VEGETAIS, GORDURAS VEGETAIS E CREME VEGETAL
Atualizada e complementada pela RDC 716/2022. Vigente.

DENOMINAÇÕES DE VENDA
- "Óleo de soja": extraído exclusivamente de soja (Glycine max)
- "Óleo de girassol": extraído de sementes de girassol (Helianthus annuus)
- "Óleo de canola": extraído de Brassica napus e B. rapa
- "Óleo de milho": extraído do germe de milho (Zea mays)
- "Óleo de palma" (dendê): extraído do mesocarpo de Elaeis guineensis
- "Óleo de coco": extraído da polpa de coco (Cocos nucifera)
- "Óleo composto" ou "mistura de óleos": quando houver combinação — declarar espécies
- "Margarina": produto com ≥ 80% gordura total; "Creme vegetal": 40-80% gordura
- "Gordura vegetal hidrogenada": obrigatório declarar o processo

ROTULAGEM OBRIGATÓRIA
- Denominação de venda precisa conforme produto
- Se mistura: listar óleos em ordem decrescente
- Azeite de oliva: vedado denominar produto que não seja Olea europaea
- "Extra virgem": acidez ≤ 0,8% — obrigatório quando usar esta qualificação
- Gordura trans: declarar na tabela nutricional (RDC 429/2020)

PONTOS CRÍTICOS PARA VALIDAÇÃO
Campo Denominação: verificar se o nome do óleo corresponde à espécie declarada
Campo Lista de Ingredientes: óleos na lista devem corresponder à denominação
Campo Nutricional: gorduras saturadas e trans obrigatórias
Azeite "extra virgem" sem comprovação de acidez: ALERTA

BASE LEGAL: RDC 270/2005, RDC 716/2022
""".strip()
},

{
"chave": "margarina",
"titulo": "RDC 270/2005 — Margarina e Creme Vegetal",
"fonte": "RDC ANVISA 270/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_oleos",
"conteudo": """
MARGARINA E CREME VEGETAL — RDC 270/2005

DEFINIÇÕES E TEORES DE GORDURA
- Margarina: emulsão (água em óleo), teor de gordura ≥ 80%
- Margarina light: teor de gordura < 80% (declarar % real)
- Creme vegetal: emulsão com gordura entre 40% e menos de 80%
- "Halvarina" ou "creme culinário": formas regionais do creme vegetal

INGREDIENTES TÍPICOS
Óleos vegetais parcialmente hidrogenados ou interesterificados, água, sal,
emulsificantes (lecitina, INS 471, 472), vitaminas A e D (adição obrigatória),
corantes carotenóides (quando aplicável), conservantes (benzoato, sorbato).

ADIÇÃO OBRIGATÓRIA DE VITAMINAS
Margarina e creme vegetal devem conter vitaminas A e D adicionadas:
- Vitamina A: 750 UI a 1500 UI por 100g
- Vitamina D: 75 UI a 150 UI por 100g
Declarar na lista de ingredientes: "Vitamina A (palmitato de retinol)" e "Vitamina D3"

GORDURA TRANS
- Regulada pela RDC 332/2019 e RDC 429/2020
- Óleos parcialmente hidrogenados podem gerar gordura trans
- Declaração obrigatória na tabela nutricional (mesmo se < 0,2g, declarar 0)
- "Zero trans" ou "sem gordura trans": permitido se < 0,1g por porção

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Creme vegetal denominado como "margarina" sem 80% gordura: NÃO CONFORME
- Ausência de vitaminas A e D: NÃO CONFORME
- Gordura trans não declarada: NÃO CONFORME
""".strip()
},

{
"chave": "chocolate_cacau",
"titulo": "RDC 264/2005 — Chocolate e Produtos de Cacau",
"fonte": "RDC ANVISA 264/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_doces",
"conteudo": """
RDC Nº 264/2005 — CHOCOLATE E PRODUTOS DE CACAU

DENOMINAÇÕES E COMPOSIÇÃO MÍNIMA
- "Chocolate amargo" / "chocolate meio amargo": ≥ 35% de sólidos totais de cacau
- "Chocolate ao leite": ≥ 25% sólidos totais de cacau + leite
- "Chocolate branco": ≥ 20% manteiga de cacau + leite; SEM massa de cacau
- "Chocolate diet": sem adição de sacarose — usar adoçante(s) permitido(s)
- "Cobertura de chocolate": composição similar ao chocolate, para uso culinário
- "Produto de cacau" ou "produto sabor chocolate": < percentuais mínimos acima

SUBSTITUIÇÃO DE MANTEIGA DE CACAU (Art. 6º)
Permitida substituição de até 5% da manteiga de cacau por outras gorduras vegetais
(exceto hidrogenadas tipo laurílicas), sem alterar a denominação.
Se > 5%: denominar "cobertura" ou "produto sabor chocolate", não "chocolate"

ALEGAÇÕES PROIBIDAS
- "Puro cacau" se contiver substituintes
- "Chocolate" se não atingir os mínimos de sólidos de cacau
- "Diet" sem comprovação de equivalência calórica

ALÉRGENOS
- Chocolate ao leite: "CONTÉM LEITE E DERIVADOS"
- Chocolate amargo: verificar se processo usa equipamento compartilhado com leite
  → Declarar "PODE CONTER LEITE" (contaminação cruzada)
- Lecitina de soja: "CONTÉM SOJA"

ROTULAGEM
- Declarar % de cacau no painel principal (ex: "70% cacau")
- Tabela nutricional obrigatória (RDC 429/2020)
- Porção: 25g (barra) conforme IN 75/2020

BASE LEGAL: RDC 264/2005
""".strip()
},

{
"chave": "condimentos_temperos",
"titulo": "RDC 276/2005 — Especiarias, Temperos e Molhos",
"fonte": "RDC ANVISA 276/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_condimentos",
"conteudo": """
RDC Nº 276/2005 — ESPECIARIAS, TEMPEROS, MOLHOS E CONDIMENTOS

DEFINIÇÕES
- Especiaria: parte de planta (folha, semente, casca, raiz, fruto) usada para temperar
  Ex: pimenta, canela, noz-moscada, cravo, coentro, orégano, açafrão, cúrcuma
- Tempero composto: mistura de especiarias + outros ingredientes (sal, glutamato, etc.)
- Condimento: produto pronto para consumo que confere sabor/aroma ao alimento
- Molho: produto líquido ou semilíquido para temperar (ketchup, mostarda, maionese)

DENOMINAÇÃO DE VENDA
- Especiaria simples: nome da planta ou parte usada ("Orégano", "Pimenta-do-reino")
- Tempero composto: nome descritivo ("Tempero para churrasco", "Tempero baiano")
- Proibido: omitir o teor de sal quando sal for ingrediente predominante

ROTULAGEM DE ESPECIARIAS (Art. 7º)
- Lista de ingredientes: obrigatória se mais de um componente
- Especiaria simples (ex: orégano puro): pode omitir lista de ingredientes
- Irradiação: se irradiada, declarar "ESPECIARIA IRRADIADA" (muito comum para controle microbiano)
- Alérgenos: celery (aipo) é alérgeno — verificar se presente em misturas

MOLHOS — REQUISITOS ESPECÍFICOS
- Ketchup: mínimo 33% de extrato de tomate; declarar "tomate" como 1º ingrediente
- Maionese: ≥ 65% óleos vegetais + ≥ 2% gema de ovo; se light, declarar % de gordura
- Mostarda: base de sementes de mostarda; declarar "CONTÉM MOSTARDA" (alérgeno EU — verificar exportação)
- Molho de soja (shoyu): "CONTÉM SOJA E TRIGO/GLÚTEN"

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Tempero com glutamato (INS 621): declarar "Realçador de sabor: glutamato monossódico (INS 621)"
- Sal em excesso no tempero: verificar se sódio está declarado na tabela nutricional
- Especiaria irradiada sem declaração: NÃO CONFORME

BASE LEGAL: RDC 276/2005
""".strip()
},

{
"chave": "molhos_ketchup",
"titulo": "RDC 276/2005 — Molhos, Ketchup, Maionese, Mostarda",
"fonte": "RDC ANVISA 276/2005 — Seção Molhos",
"orgao": "ANVISA",
"categoria": "nao_poa_condimentos",
"conteudo": """
MOLHOS, KETCHUP, MAIONESE E MOSTARDA — RDC 276/2005

KETCHUP / CATSUP
- Composição: mínimo 33% de extrato de tomate (base sólida)
- Ingredientes típicos: tomate (como 1º ingrediente), açúcar, vinagre, sal, especiarias
- Aditivos comuns: conservante (INS 211 — benzoato de sódio), espessante, corante natural
- Denominação "ketchup light": redução ≥ 25% do valor calórico ou do açúcar vs produto convencional

MAIONESE
- Composição obrigatória: ≥ 65% óleos vegetais + ≥ 2% gema de ovo
- "Maionese light" ou "maionese com menos gordura": teor < 65% óleos, declarar % real
- Alérgenos: "CONTÉM OVO" obrigatório; verificar lecitina de soja
- Risco microbiológico: produto com ovo cru deve mencionar temperatura de conservação
- "Maionese vegana": sem ovo — usar denominação diferente ("molho cremoso") ou declarar

MOLHO DE TOMATE / EXTRATO DE TOMATE
- Molho de tomate: produto à base de tomate sem concentração mínima específica
- Extrato de tomate: versão mais concentrada (pasta de tomate > 28% sólidos)
- Declarar o grau de concentração quando relevante

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Maionese com < 65% de óleos sem indicação "light": NÃO CONFORME
- Ketchup sem tomate como 1º ingrediente: VERIFICAR composição mínima
- Ausência de declaração de ovo na maionese: NÃO CONFORME (alérgeno)
- Conservantes: declarar função + INS (ex: "Conservante: benzoato de sódio (INS 211)")
""".strip()
},

{
"chave": "vinagre",
"titulo": "RDC 278/2005 — Vinagre: Denominação e Rotulagem",
"fonte": "RDC ANVISA 278/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_condimentos",
"conteudo": """
RDC Nº 278/2005 — VINAGRE

DEFINIÇÃO
Vinagre é o produto obtido por fermentação acética de líquidos alcoólicos ou
líquidos alcoólicos parcialmente fermentados, ou de líquidos açucarados
fermentados, com acidez mínima de 4% (em ácido acético).

DENOMINAÇÕES DE VENDA
- "Vinagre de vinho": obtido do vinho (Vitis vinifera) — mais comum
- "Vinagre de maçã": obtido de suco de maçã fermentado
- "Vinagre de álcool": obtido de álcool etílico — mais barato
- "Vinagre balsâmico": obtido de mosto de uva; origem Módena (IGP italiana)
- "Vinagre de arroz": obtido de sake/sakê
Proibido denominar "vinagre" produto com < 4% de acidez.

ACIDEZ OBRIGATÓRIA NO RÓTULO (Art. 6º)
Declarar: "Acidez: X% (em ácido acético)" ou "Acidez total: X g/100mL (em ácido acético)"

ADITIVOS
Poucos aditivos permitidos: caramelo (corante), conservantes limitados.
Sulfitos: se presentes (ex: vinagre de vinho), declarar "CONTÉM SULFITOS" — alérgeno.

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Acidez não declarada: NÃO CONFORME
- Vinagre de vinho com uvas não declaradas: verificar
- Sulfitos sem declaração: NÃO CONFORME (alérgeno obrigatório)
- Vinagre balsâmico: se não for da IGP Módena, não pode usar "aceto balsamico di Modena"

BASE LEGAL: RDC 278/2005
""".strip()
},

{
"chave": "cafe_cevada_cha",
"titulo": "RDC 277/2005 — Café, Cevada, Chá e Erva-Mate",
"fonte": "RDC ANVISA 277/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_bebidas",
"conteudo": """
RDC Nº 277/2005 — CAFÉ, CEVADA, CHÁ, ERVA-MATE E SIMILARES

CAFÉ
- "Café torrado e moído": Coffea arabica e/ou Coffea canephora (robusta/conilon) torrados e moídos
- "Café solúvel" ou "café instantâneo": extrato seco de café
- "Café descafeinado": máximo 0,1% de cafeína na base seca
- Mistura com cevada: denominar "Café com Cevada X%" — declarar % de cevada
- Proibido: vender cevada ou outra adição como "café puro"
- Rotulagem: declarar origem (quando aplicável) e processo de torra

CHÁ E INFUSÕES
- "Chá": infusão de folhas de Camellia sinensis (verde, preto, oolong, branco)
- Outros "chás" (camomila, erva-cidreira, hortelã): tecnicamente "infusão" ou "tisana"
  mas denominação "chá de [planta]" é consagrada e aceita
- Chá pronto para beber: verificar teor de açúcar e lupa frontal (RDC 429/2020)
- Chá funcional com alegação: exige aprovação da alegação pela ANVISA (RES 18/1999)

ERVA-MATE
- Chimarrão: erva-mate verde (Ilex paraguariensis) não torrada
- Tererê: semelhante ao chimarrão, consumido gelado
- Chá-mate torrado: erva-mate torrada (mais escura, sabor diferente)
- Composto de erva-mate: admite adição de ervas aromáticas — declarar ingredientes

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Café com cevada sem declarar % de cevada: NÃO CONFORME
- Chá com alegações funcionais sem aprovação: NÃO CONFORME
- Teor de cafeína: não é obrigatório declarar (exceto para energéticos)
- Erva-mate com aditivos não autorizados: verificar lista positiva

BASE LEGAL: RDC 277/2005
""".strip()
},

{
"chave": "sorvete_gelado",
"titulo": "RDC 266/2005 — Gelados Comestíveis (Sorvetes e Picolés)",
"fonte": "RDC ANVISA 266/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_doces",
"conteudo": """
RDC Nº 266/2005 — GELADOS COMESTÍVEIS (SORVETES E PRODUTOS SIMILARES)

DENOMINAÇÕES E COMPOSIÇÃO
- "Sorvete de leite" ou "sorvete": base láctea — mínimo de proteínas lácteas e gordura láctea
- "Sorvete de leite light": redução ≥ 25% gordura ou caloria vs referência
- "Sorvete de creme": maior teor de gordura láctea (cream)
- "Sorvete de fruta": base de fruta sem componente lácteo predominante
- "Picolé": produto em palito congelado (com ou sem base láctea)
- "Sherbet": base de fruta com pequena fração láctea
- "Gelato": sorvete estilo italiano — sem definição regulatória específica no Brasil

INGREDIENTES TÍPICOS
Leite/creme, açúcar, emulsificantes (lecitina, mono e diglicerídeos — INS 471),
estabilizantes (goma xantana, goma guar, CMC — INS 466), aromas, corantes.

ALÉRGENOS EM SORVETES
- Base láctea: "CONTÉM LEITE E DERIVADOS"
- Amendoim/castanhas: declarar se presentes ou em risco de contaminação cruzada
- Ovo (sorvete de creme): "CONTÉM OVO"
- Glúten (biscoito, wafer, cone): "CONTÉM GLÚTEN"

ROTULAGEM
- Temperatura de conservação obrigatória: "Manter a -18°C" ou temperatura específica
- Porção padrão: 60g conforme IN 75/2020
- Tabela nutricional obrigatória
- Lupa frontal: verificar teor de açúcar adicionado (frequentemente alto)

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Sorvete base água denominado "sorvete de leite": NÃO CONFORME
- Ausência de temperatura de conservação: NÃO CONFORME
- Ausência de alérgenos (leite, ovo, amendoim): NÃO CONFORME

BASE LEGAL: RDC 266/2005, RDC 713/2022
""".strip()
},

{
"chave": "doces_geleias",
"titulo": "RDC 272/2005 — Conservas Vegetais e Produtos de Frutas",
"fonte": "RDC ANVISA 272/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_vegetais",
"conteudo": """
RDC Nº 272/2005 — PRODUTOS DE FRUTAS, HORTALIÇAS E FUNGOS COMESTÍVEIS

PRODUTOS DE FRUTAS — DENOMINAÇÕES
- "Geleia": produto obtido de fruta + açúcar + pectina. Mínimo 35% fruta
- "Geleia de alta qualidade" ou "extra": ≥ 45% fruta
- "Geleia light": redução ≥ 25% açúcar — usar adoçante
- "Compota": frutas em calda de açúcar — inteiras ou em pedaços
- "Doce em pasta" ou "doce": purê de fruta com açúcar (ex: doce de goiaba, marmelada)
- "Purê de fruta": sem adição de açúcar (diferente do doce)
- "Polpa de fruta": fruta processada sem casca/semente, sem adição de água ou açúcar

CONSERVAS VEGETAIS
- "Palmito": Euterpe oleracea (açaí) ou Bactris gasipaes (pupunha) — declarar espécie
- "Azeitona": Olea europaea — declarar tipo (verde, preta, recheada)
- "Milho em conserva": Zea mays em salmoura ou ao natural
- "Ervilha em conserva": Pisum sativum
- Declarar peso líquido + peso drenado obrigatoriamente

FUNGOS COMESTÍVEIS
- "Cogumelo": Agaricus bisporus (champignon), Lentinula edodes (shitake), etc.
- Declarar espécie e forma de processamento (fresco, em conserva, desidratado)

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Geleia sem declaração de % mínima de fruta: verificar composição mínima
- Conserva sem peso drenado: NÃO CONFORME
- Palmito sem declaração de espécie: ALERTA (Euterpe edulis é ameaçado — CITES)
- Polpa com açúcar denominada "polpa": NÃO CONFORME

BASE LEGAL: RDC 272/2005
""".strip()
},

{
"chave": "cereais_pao_massa",
"titulo": "RDC 711/2022 — Cereais, Pães, Massas, Biscoitos e Similares",
"fonte": "RDC ANVISA 711/2022",
"orgao": "ANVISA",
"categoria": "nao_poa_cereais",
"conteudo": """
RDC Nº 711/2022 — CEREAIS, PÃES, MASSAS, BISCOITOS E PRODUTOS DE PANIFICAÇÃO

DENOMINAÇÕES E DEFINIÇÕES

FARINHAS E AMIDOS
- "Farinha de trigo": moagem do grão de trigo — deve ser enriquecida com ferro e ácido fólico
- "Farinha integral": produto com o farelo do grão incluído (mínimo % de fibras)
- "Amido": polissacarídeo extraído de cereais ou tubérculos
- "Fécula": amido de tubérculos (batata, mandioca/tapioca/polvilho)
- "Polvilho doce": fécula de mandioca
- "Polvilho azedo": fécula de mandioca fermentada

PÃES
- "Pão": produto assado à base de farinha de trigo (e/ou outros cereais)
- "Pão integral": ≥ 50% de farinha integral ou farelo na composição
- "Pão sem glúten": verificar contaminação cruzada + certificação
- "Pão de queijo": massa de polvilho + queijo — não exige trigo (naturalmente sem glúten)
- Conservantes em pão: propionato de cálcio/sódio (INS 282/281) é comum e permitido

MASSAS ALIMENTÍCIAS
- "Massa fresca" ou "macarrão fresco": aw elevada, prazo curto, refrigerado
- "Massa seca" ou "macarrão seco": produto desidratado, prazo longo
- "Massa com ovos" ou "massa ao ovo": ≥ 1 ovo inteiro por kg de farinha
- "Massa integral": ≥ 30% farinha integral

BISCOITOS E BOLACHAS
- "Biscoito salgado" ou "cracker": baixo teor de açúcar
- "Biscoito doce" ou "bolacha": com açúcar significativo
- "Wafer": biscoito em folhas finas com recheio
- "Cookie": biscoito artesanal ou industrial com pedaços (gotas de chocolate, castanhas)

ENRIQUECIMENTO OBRIGATÓRIO (Portaria 31/1998 + Dec. Lei 986/1969)
Farinhas de trigo e milho devem ser enriquecidas com:
- Ferro: mínimo 4,2mg por 100g de farinha
- Ácido fólico: mínimo 150μg por 100g de farinha
Declarar na lista de ingredientes e na tabela nutricional

ALÉRGENOS
- Trigo (glúten): "CONTÉM GLÚTEN" obrigatório se contiver trigo, aveia, cevada, centeio
- "Sem glúten": teor < 10mg/kg e certificação ACELBRA ou similar

BASE LEGAL: RDC 711/2022, Portaria 31/1998 (enriquecimento farinha)
""".strip()
},

{
"chave": "alimentos_integrais",
"titulo": "RDC 712/2022 — Definição e Requisitos de Alimentos Integrais",
"fonte": "RDC ANVISA 712/2022",
"orgao": "ANVISA",
"categoria": "nao_poa_cereais",
"conteudo": """
RDC Nº 712/2022 — DEFINIÇÃO REGULATÓRIA DE ALIMENTOS INTEGRAIS

OBJETO
Primeira norma brasileira a definir tecnicamente o que é um "alimento integral"
para fins de rotulagem, evitando uso indiscriminado do termo.

DEFINIÇÃO (Art. 3º)
Alimento integral: produto que contém, em sua composição, ingredientes integrais
(farinha integral, flocos integrais, grãos inteiros) como ingrediente principal,
em proporção mínima estabelecida por categoria.

PERCENTUAIS MÍNIMOS PARA USO DO TERMO "INTEGRAL" (Anexo)
- Pão integral: ≥ 50% farinha de trigo integral (ou mistura de cereais integrais)
  na composição da farinha total usada
- Biscoito integral: ≥ 30% ingredientes integrais
- Macarrão integral: ≥ 30% farinha integral
- Cereal matinal integral: ≥ 50% ingredientes integrais
- Produto de granola: ≥ 51% ingredientes integrais

USO DO TERMO NO RÓTULO (Art. 6º)
- Permitido em denominação: "Pão Integral", "Macarrão Integral"
- Deve corresponder aos percentuais mínimos
- Proibido: usar "integral" apenas por conter pequena fração de farinha integral
- Proibido: usar "com grãos", "multigrãos", "com fibras" para simular "integral"

PONTOS CRÍTICOS PARA VALIDAÇÃO
- "Pão integral" com farinha integral como 2º ou 3º ingrediente: VERIFICAR % (possível NÃO CONFORME)
- "Multigrãos" ou "com grãos" sem atingir % mínimo: não pode ser "integral"
- Biscoito "integral" com < 30% ingredientes integrais: NÃO CONFORME

BASE LEGAL: RDC 712/2022
""".strip()
},

{
"chave": "suplementos_rdc243_v2",
"titulo": "RDC 243/2018 + RDC 786/2023 — Suplementos Alimentares",
"fonte": "RDC ANVISA 243/2018 atualizada pela RDC 786/2023",
"orgao": "ANVISA",
"categoria": "nao_poa_suplementos",
"conteudo": """
RDC Nº 243/2018 — SUPLEMENTOS ALIMENTARES
Atualizada pela RDC 786/2023. Complementada pela IN 28/2018 e IN 76/2020.

DEFINIÇÃO
Suplemento alimentar: produto destinado a suplementar a alimentação com nutrientes,
substâncias bioativas, enzimas ou probióticos, para fins de suprir necessidades
nutricionais específicas de indivíduos saudáveis.

CATEGORIAS DE SUPLEMENTOS (Anexo I)
1. Vitaminas e minerais
2. Proteínas e aminoácidos (whey protein, BCAA, creatina)
3. Fibras alimentares
4. Substâncias bioativas (cafeína, taurina, ômega-3, coenzima Q10)
5. Enzimas
6. Probióticos e prebióticos
7. Compostos para fins esportivos

NOTIFICAÇÃO OBRIGATÓRIA (após RDC 843/2024)
Suplementos devem ser notificados na ANVISA antes da comercialização.
Prazo encerrado: 01/09/2025. Suplementos sem notificação após este prazo: IRREGULARES.
Rótulo deve conter: "Notificado na ANVISA sob nº XX.XXX.XXXX"

ROTULAGEM OBRIGATÓRIA
- Denominação: "Suplemento Alimentar de [ingrediente principal]"
- Tabela nutricional por porção e por 100g
- Quantidade e %VD dos nutrientes por porção
- Advertência obrigatória: "Este produto não é um medicamento e não deve ser usado como substituto de uma alimentação variada e equilibrada."
- Público-alvo: "Destinado a adultos saudáveis" ou especificação
- Indicação de uso: como e quando consumir
- Restrições de uso (gestantes, crianças — avisos)
- Número de notificação ANVISA

ALEGAÇÕES PERMITIDAS
Conforme lista da IN 28/2018 — apenas alegações pré-aprovadas.
Ex: "Contribui para a manutenção da massa muscular" (proteínas), "Auxilia na hidratação" (eletrólitos)
Proibido: claims terapêuticos ou medicinais ("cura", "trata", "previne doenças")

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Whey protein sem número de notificação ANVISA: NÃO CONFORME (após 01/09/2025)
- Alegação não aprovada: NÃO CONFORME
- Advertência obrigatória ausente: NÃO CONFORME
- Dose máxima diária não declarada: NÃO CONFORME

BASE LEGAL: RDC 243/2018, IN 28/2018, RDC 786/2023, RDC 843/2024
""".strip()
},

{
"chave": "suplementos_in28_v2",
"titulo": "IN 28/2018 — Listas de Constituintes e Alegações de Suplementos",
"fonte": "IN ANVISA 28/2018 atualizada",
"orgao": "ANVISA",
"categoria": "nao_poa_suplementos",
"conteudo": """
INSTRUÇÃO NORMATIVA Nº 28/2018 — SUPLEMENTOS ALIMENTARES
Listas de constituintes, doses máximas e alegações permitidas.

LISTAS VINCULADAS (Anexos)
Anexo I: Vitaminas — doses mínimas e máximas por porção (ex: Vitamina C: mín 7,5mg, máx 1000mg)
Anexo II: Minerais — doses mínimas e máximas (ex: Ferro: mín 2,1mg, máx 45mg)
Anexo III: Aminoácidos — lista de aminoácidos permitidos
Anexo IV: Proteínas — whey, caseína, proteína de soja, colágeno, etc.
Anexo V: Fibras — inulina, FOS, psyllium, etc.
Anexo VI: Substâncias bioativas — cafeína (máx 400mg/dia), ômega-3, resveratrol, etc.
Anexo VII: Enzimas — amilase, protease, lipase, etc.
Anexo VIII: Alegações de propriedade funcional permitidas por ingrediente

ALEGAÇÕES APROVADAS (Exemplos)
- Proteínas: "Contribui para a manutenção da massa muscular" e "Contribui para o crescimento da massa muscular"
- Vitamina D: "Contribui para a absorção e utilização do cálcio e fósforo"
- Magnésio: "Contribui para a função muscular normal"
- Cafeína: "Contribui para aumentar a resistência durante o exercício de resistência prolongado"
- Ômega-3 (EPA+DHA): "Contribui para a manutenção de níveis normais de triglicerídeos no sangue"
- Probióticos: "Contribui para o equilíbrio da flora intestinal"

DOSES QUE EXIGEM ADVERTÊNCIA ESPECIAL
- Cafeína > 150mg/porção: "Contém cafeína. Indivíduos sensíveis à cafeína devem evitar o consumo."
- Vitamina B6 > 10mg/dia: advertência sobre neuropatia periférica
- Ferro > 45mg/dia: advertência sobre toxicidade

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Alegação não listada no Anexo VIII: NÃO CONFORME
- Dose acima do máximo do Anexo: NÃO CONFORME
- Suplemento com ingrediente não listado nos Anexos I-VII: NÃO CONFORME (ingrediente não autorizado)

BASE LEGAL: IN 28/2018 e atualizações posteriores
""".strip()
},

{
"chave": "formula_infantil",
"titulo": "RDC 241/2018 — Fórmulas Infantis para Lactentes e Crianças",
"fonte": "RDC ANVISA 241/2018",
"orgao": "ANVISA",
"categoria": "nao_poa_especiais",
"conteudo": """
RDC Nº 241/2018 — FÓRMULAS INFANTIS PARA LACTENTES E CRIANÇAS DE PRIMEIRA INFÂNCIA

DEFINIÇÕES
- Fórmula infantil para lactentes: produto em pó ou líquido, para 0 a 6 meses
- Fórmula de seguimento para lactentes: para 6 a 12 meses
- Fórmula infantil para crianças de primeira infância: para 1 a 3 anos
- Fórmula hipoalergênica: proteínas extensamente hidrolisadas
- Fórmula para erros inatos: fenilcetonúria, galactosemia, etc.

REGISTRO OBRIGATÓRIO (Art. 4º)
Fórmulas infantis exigem REGISTRO na ANVISA antes da comercialização.
Rótulo deve conter número de registro MS.
Prazo de adequação ao RDC 843/2024: manter registro.

ROTULAGEM ESPECÍFICA (Art. 15º a 30º)
Proibições expressas no rótulo de fórmulas infantis:
- Proibido: imagens de bebês, mães amamentando ou qualquer imagem que idealize o uso da fórmula
- Proibido: alegações de saúde ou benefícios além dos aprovados pela ANVISA
- Proibido: comparação com leite materno
- Proibido: termos como "maternizado", "humanizado"
- Obrigatório: "O Ministério da Saúde adverte: Este produto somente deve ser usado na alimentação de crianças menores de 1 ano com indicação expressa de médico ou nutricionista. O aleitamento materno evita infecções e alergias e é recomendado até os 2 anos ou mais."
- Obrigatório: modo de preparo detalhado e avisos de higiene

COMPOSIÇÃO MÍNIMA REGULADA
Teores mínimos e máximos de: proteínas, lipídeos, carboidratos, vitaminas (A, D, E, K, C, B-complex),
minerais (cálcio, fósforo, ferro, zinco, iodo, selênio) e ácidos graxos essenciais (LA, ALA).

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Ausência do texto obrigatório do Ministério da Saúde: NÃO CONFORME
- Imagem de bebê ou mãe: NÃO CONFORME
- Ausência de número de registro MS: NÃO CONFORME
- Comparação com leite materno: NÃO CONFORME

BASE LEGAL: RDC 241/2018, RDC 843/2024 (regularização)
""".strip()
},

{
"chave": "rdc_243_alimentos_funcionais",
"titulo": "RES 18/1999 + RDC 243/2018 — Alegações Funcionais e Propriedades de Saúde",
"fonte": "Resolução ANVISA 18/1999 — Alegações Funcionais",
"orgao": "ANVISA",
"categoria": "alegacoes_funcionais",
"conteudo": """
RESOLUÇÃO ANVISA Nº 18/1999 — ALEGAÇÕES DE PROPRIEDADE FUNCIONAL E DE SAÚDE

OBJETO
Regulamenta as alegações que podem ser usadas nos rótulos de alimentos convencionais,
complementos alimentares e alimentos funcionais.

TIPOS DE ALEGAÇÃO
1. ALEGAÇÃO DE PROPRIEDADE NUTRICIONAL: sobre conteúdo de nutriente
   Ex: "Rico em fibras", "Fonte de vitamina C", "Baixo teor de sódio"
   Base: RDC 429/2020 (limites para cada alegação)

2. ALEGAÇÃO DE PROPRIEDADE FUNCIONAL (Lista Positiva ANVISA)
   Sobre papel de nutriente/substância no crescimento, desenvolvimento ou funções do corpo.
   Ex: "As fibras alimentares auxiliam o funcionamento do intestino"
   EXIGE substância na quantidade mínima por porção declarada.

3. ALEGAÇÃO DE PROPRIEDADE DE SAÚDE (Lista Positiva ANVISA)
   Relação entre alimento/nutriente e risco de doença.
   Ex: "Uma dieta com baixo teor de gordura saturada e colesterol pode reduzir o risco de doença cardíaca"
   EXIGE aprovação prévia pela ANVISA.

ALEGAÇÕES FUNCIONAIS APROVADAS (exemplos — lista completa em Resolução ANVISA 2/2002 atualizada)
- Fibras: "auxiliam o funcionamento do intestino" — mínimo 2,5g de fibra/porção
- Ômega-3: "auxilia na manutenção de níveis saudáveis de triglicerídeos no sangue"
- Probióticos (Lactobacillus, Bifidobacterium): "contribui para o equilíbrio da flora intestinal"
- Licopeno: "ação antioxidante que protege as células contra danos do estresse oxidativo"
- Vitamina E: "protege as células dos radicais livres"
- Cálcio: "auxilia na manutenção de ossos e dentes saudáveis"

ALEGAÇÕES PROIBIDAS (Art. 7º)
- Claims terapêuticos: "cura", "trata", "previne" qualquer doença
- Claims não aprovados pela ANVISA sem comprovação
- Claims sobre doenças graves (câncer, diabetes, hipertensão)
- Superlativos: "o mais saudável", "o melhor para sua saúde"

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Alegação funcional sem substância na quantidade mínima: NÃO CONFORME
- Alegação não listada na lista positiva: NÃO CONFORME
- Claim terapêutico: NÃO CONFORME (grave — pode configurar propaganda enganosa de medicamento)

BASE LEGAL: Resolução 18/1999, Resolução 2/2002 (lista atualizada), RDC 243/2018
""".strip()
},

{
"chave": "in_mapa_49_2018_suco",
"titulo": "IN MAPA 49/2018 — Sucos, Néctares e Bebidas de Frutas",
"fonte": "IN MAPA 49/2018",
"orgao": "MAPA",
"categoria": "nao_poa_bebidas",
"conteudo": """
INSTRUÇÃO NORMATIVA MAPA Nº 49/2018 — SUCOS, NÉCTARES E BEBIDAS DE FRUTAS

DENOMINAÇÕES E COMPOSIÇÃO MÍNIMA

SUCO (integral ou puro)
- Líquido obtido da fruta madura in natura por processo tecnológico adequado
- NÃO permite adição de água, açúcar ou qualquer aditivo (exceto conservante permitido)
- Denominação: "Suco de [fruta]" — ex: "Suco de laranja"
- Pasteurização permitida, não configura adulteração
- Refrigerado (curto prazo) ou UHT (longa vida)

SUCO CONCENTRADO
- Suco do qual foi removida parte da água
- Denominação: "Suco concentrado de [fruta]" — indicar o nível de concentração
- Para consumo: reconstituir com água conforme indicação do rótulo

NÉCTAR
- Mínimo de 30% a 50% de polpa de fruta (variável por espécie), completado com água e açúcar
- Percentuais mínimos de polpa por espécie: acerola 20%, açaí 20%, caju 10%, laranja 50%,
  maracujá 25%, uva 45%, manga 40%
- Pode conter aditivos permitidos (acidulante, conservante, corante natural)
- Denominação: "Néctar de [fruta]"

BEBIDA DE FRUTA (ou "refresco")
- Mínimo 10% de suco ou polpa de fruta
- Pode ter açúcar, aditivos, flavorizantes
- Denominação: "Bebida de [fruta]" ou "Refresco de [fruta]" ou "[Fruta]ade"
- Ex: "Bebida de caju", "Laranjada" — não pode ser "Suco de laranja" se < 50% polpa

PRODUTO À BASE DE POLPA (sem água adicionada)
- Polpa de fruta: fruta despolpada, sem água adicionada, congelada ou pasteurizada
- Denominação: "Polpa de [fruta]"

PONTOS CRÍTICOS PARA VALIDAÇÃO
- "Suco" com açúcar ou água adicionados: NÃO CONFORME — denominação errada
- "Néctar" com < mínimo de polpa da espécie: NÃO CONFORME
- Corante artificial em suco ou néctar: NÃO CONFORME (apenas natural é permitido)
- Denominação de espécie: se mistura de frutas, listar todas (ex: "Néctar de tropical")

BASE LEGAL: IN MAPA 49/2018, Dec. 6.871/2009 (bebidas em geral)
""".strip()
},

{
"chave": "in_mapa_41_2019_kombucha",
"titulo": "IN MAPA 41/2019 — Kombucha: Definição e Requisitos",
"fonte": "IN MAPA 41/2019",
"orgao": "MAPA",
"categoria": "nao_poa_bebidas",
"conteudo": """
INSTRUÇÃO NORMATIVA MAPA Nº 41/2019 — KOMBUCHA

DEFINIÇÃO
Kombucha: bebida obtida por fermentação de chá (Camellia sinensis) adoçado,
utilizando cultura simbiótica de bactérias e leveduras (SCOBY — Symbiotic Culture
Of Bacteria and Yeast).

COMPOSIÇÃO E PADRÕES
- Base: infusão de chá + açúcar fermentada por SCOBY
- Teor alcoólico máximo: 0,5% v/v (bebida não alcoólica) ou > 0,5% v/v (bebida alcoólica — sujeita à tributação)
- pH final: tipicamente 2,5 a 3,5 (ácido)
- Acidez total (em ácido acético): mínimo 0,3g/100mL

DENOMINAÇÃO
- "Kombucha": produto conforme os padrões da IN 41/2019
- Sabores permitidos: adição de frutas, especiarias, ervas após fermentação primária

ROTULAGEM
- Denominação de venda: "Kombucha" (seguida de sabor, se houver)
- Declarar teor alcoólico se > 0,5% v/v
- Se alcoólico: proibida venda para menores de 18 anos — declarar no rótulo
- Pasteurização pós-fermentação: permitida; declarar "Pasteurizado" se aplicável
- Conteúdo líquido, fabricante, validade, lote — obrigatórios (RDC 727/2022)
- Probióticos no rótulo: apenas se com evidência técnica de quantidade viável

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Kombucha alcoólico (> 0,5%) sem declaração de teor alcoólico: NÃO CONFORME
- Alegação de probióticos sem comprovação de UFC viáveis: ALERTA
- Kombucha denominado "suco" ou "chá": NÃO CONFORME
- Ausência de pH ou acidez — não é exigido no rótulo consumidor, mas é dado técnico relevante

BASE LEGAL: IN MAPA 41/2019, Dec. 6.871/2009
""".strip()
},

{
"chave": "dieta_diabetico",
"titulo": "Portaria SVS 29/1998 — Alimentos para Fins Especiais (Dietas)",
"fonte": "Portaria SVS/MS 29/1998",
"orgao": "ANVISA",
"categoria": "nao_poa_especiais",
"conteudo": """
PORTARIA SVS/MS Nº 29/1998 — ALIMENTOS PARA FINS ESPECIAIS
(Inclui diet, light e alimentos para grupos específicos)

DEFINIÇÕES

DIET
Produto com ausência total de determinado nutriente (não apenas redução).
Mais comum: "sem açúcar" (sacarose) para diabéticos.
REGRA: "diet" implica ausência de pelo menos um nutriente regulado.
Pode ter calorias iguais ou superiores ao produto convencional (ex: chocolate diet com mais gordura).

LIGHT
Produto com redução mínima de 25% em pelo menos um nutriente ou valor calórico
em comparação com o produto convencional de referência.
Declarar obrigatoriamente: qual nutriente foi reduzido e o % de redução.
Ex: "Light em gorduras — 30% menos gordura que o [produto referência]"

ALIMENTOS PARA CONTROLE DE PESO
- Redução calórica ≥ 25% vs produto convencional
- Podem usar adoçantes permitidos em substituição ao açúcar

ADOÇANTES — DECLARAÇÕES OBRIGATÓRIAS
- Sacarína: "Contém Sacarina — não recomendado para crianças e gestantes"
- Ciclamato: "Contém Ciclamato — não recomendado para crianças, gestantes e hipertensos"
- Aspartame: "FENILCETONÚRICOS: CONTÉM FENILALANINA"
- Todos os adoçantes: declarar o nome químico e INS na lista de ingredientes

PONTOS CRÍTICOS PARA VALIDAÇÃO
- "Diet" sem ausência comprovada do nutriente: NÃO CONFORME
- "Light" sem declarar o % de redução e nutriente reduzido: NÃO CONFORME
- Aspartame sem advertência de fenilalanina: NÃO CONFORME
- "Sem açúcar" com outros açúcares (frutose, maltose, mel): VERIFICAR e alertar

BASE LEGAL: Portaria SVS 29/1998, RDC 429/2020 (nova rotulagem nutricional)
""".strip()
},

{
"chave": "barrinha_cereal",
"titulo": "RDC 263/2005 — Cereais para Alimentação Humana (Barras e Similares)",
"fonte": "RDC ANVISA 263/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_cereais",
"conteudo": """
RDC Nº 263/2005 — CEREAIS PARA ALIMENTAÇÃO HUMANA

PRODUTOS ABRANGIDOS
- Grãos de cereais processados (arroz, milho, trigo, aveia, centeio, cevada, sorgo)
- Flocos de cereais (aveia em flocos, flocos de milho, granola)
- Farinhas e amidos (farinha de trigo, fubá, amido de milho, fécula de mandioca)
- Misturas para preparações (mix de panificação, preparado para bolo)
- Cereais matinais (corn flakes, muesli, granola)
- Barras de cereais

BARRAS DE CEREAIS — ESPECIFICAÇÕES
Não há RTIQ específico para barras de cereais — aplicam-se as normas gerais:
- Composição: cereais + mel ou açúcar ou xarope + frutas secas + sementes/castanhas
- Denominação: "Barra de cereais [sabor/ingrediente]"
- Porção: 30g conforme IN 75/2020
- Alérgenos: declarar glúten (se trigo/aveia), amendoim, castanhas, soja (se presentes)
- Prazo de validade: tipicamente 6-12 meses

GRANOLA
- Mistura de flocos de cereais (preferencialmente aveia) + mel/açúcar + frutas secas + oleaginosas
- Toasted (assada) ou crua
- Denominação: "Granola [sabor]" ou "Mix de cereais"
- Porção: 40g conforme IN 75/2020

ENRIQUECIMENTO NUTRICIONAL
Farinhas de trigo e milho: ferro (≥ 4,2mg/100g) e ácido fólico (≥ 150μg/100g) — OBRIGATÓRIO
Cereais matinais: enriquecimento vitamínico/mineral é facultativo mas deve ser declarado

PONTOS CRÍTICOS PARA VALIDAÇÃO
- Barra de cereal com amendoim sem declarar alérgeno: NÃO CONFORME
- Granola com glúten (aveia) sem declarar: NÃO CONFORME
- Farinha de trigo sem enriquecimento de ferro e ácido fólico: NÃO CONFORME

BASE LEGAL: RDC 263/2005, Portaria 31/1998 (enriquecimento)
""".strip()
},

{
"chave": "amendoim_castanhas",
"titulo": "Normas para Amendoim, Castanhas e Oleaginosas",
"fonte": "RDC 276/2005 + legislação MAPA",
"orgao": "ANVISA/MAPA",
"categoria": "nao_poa_vegetais",
"conteudo": """
AMENDOIM, CASTANHAS E OLEAGINOSAS — NORMAS APLICÁVEIS

DENOMINAÇÕES
- "Amendoim": Arachis hypogaea — leguminosa (não é castanha tecnicamente, mas tratado como oleaginosa)
- "Castanha-do-brasil" ou "castanha-do-pará": Bertholletia excelsa
- "Castanha de caju" ou "castanha de cajú": Anacardium occidentale
- "Amêndoa": Prunus dulcis
- "Noz" ou "noz-pecã": Carya illinoensis
- "Macadâmia": Macadamia spp.
- "Pistache": Pistacia vera
- "Avelã": Corylus avellana

ALÉRGENOS — CRÍTICO (RDC 727/2022 Art. 41)
- Amendoim: alérgeno de declaração obrigatória — "CONTÉM AMENDOIM"
- Castanhas (nozes, amêndoas, caju, avelã, macadâmia, noz-pecã, pistache, castanha-do-brasil):
  alérgenos de declaração obrigatória — "CONTÉM [NOME DA CASTANHA]" ou "CONTÉM CASTANHAS"
- Contaminação cruzada: instalações que processam múltiplas oleaginosas devem declarar
  "PODE CONTER AMENDOIM E/OU CASTANHAS"

AFLATOXINAS — RISCO CRÍTICO
RDC 722/2022 e IN 160/2022: limites máximos de contaminantes.
Aflatoxinas B1+B2+G1+G2 em amendoim: máximo 10 μg/kg (10 ppb)
Aflatoxina B1 em amendoim: máximo 5 μg/kg
Declaração de aflatoxinas não é exigida no rótulo, mas a conformidade é responsabilidade do fabricante.

ROTULAGEM
- Origem: quando for produto unitário (castanha a granel ou embalada)
- Sal: se tostado com sal, declarar "Tostado e salgado" e conteúdo de sódio
- "Sem glúten": amendoim e castanhas in natura são naturalmente sem glúten,
  mas processo pode ter contaminação cruzada com trigo — verificar

BASE LEGAL: RDC 727/2022 (alérgenos), RDC 722/2022 (contaminantes), Portaria MAPA (classificação)
""".strip()
},

]


def upsert(doc):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"erro": "vars não configuradas"}
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
        with urllib.request.urlopen(req, timeout=20) as r:
            return {"ok": True, "http": r.status, "chars": len(doc["conteudo"])}
    except urllib.error.HTTPError as e:
        return {"erro": f"HTTP {e.code}: {e.read().decode()[:150]}"}
    except Exception as e:
        return {"erro": str(e)[:100]}


if __name__ == "__main__":
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ SUPABASE_URL e SUPABASE_KEY não encontrados nas variáveis de ambiente.")
        exit(1)

    print(f"Inserindo {len(DOCUMENTOS)} documentos na KB...\n")
    ok_count = 0
    fail_count = 0

    for doc in DOCUMENTOS:
        r = upsert(doc)
        if r.get("ok"):
            print(f"  ✅ {doc['chave']} — {r['chars']} chars")
            ok_count += 1
        else:
            print(f"  ❌ {doc['chave']}: {r.get('erro')}")
            fail_count += 1

    print(f"\n{'='*50}")
    print(f"Concluído: {ok_count} inseridos, {fail_count} com erro")
    print(f"Total kb_documents esperado: ~{124 + ok_count}")

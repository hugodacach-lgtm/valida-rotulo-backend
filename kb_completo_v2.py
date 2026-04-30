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



# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 2 — 19 gaps não-POA
# ══════════════════════════════════════════════════════════════════════════════

{
"chave": "conservas_vegetais",
"titulo": "RDC 272/2005 — Conservas Vegetais: Palmito, Azeitona, Milho, Ervilha",
"fonte": "RDC ANVISA 272/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_vegetais",
"conteudo": """RDC 272/2005 — CONSERVAS VEGETAIS

PALMITO: espécies permitidas: açaí (Euterpe oleracea), pupunha (Bactris gasipaes), precatória. PROIBIDO Euterpe edulis (juçara — ameaçada/CITES). Declarar espécie. Peso drenado OBRIGATÓRIO.

AZEITONA (Olea europaea): verde (imatura) ou preta (madura/tratada). Formas: inteira, fatiada, recheada. Recheio de anchova → "CONTÉM PEIXE". Peso drenado obrigatório.

MILHO EM CONSERVA: "Milho em conserva" ou "Milho em grão". Peso drenado obrigatório.

ERVILHA EM CONSERVA: "Ervilha em conserva". Peso drenado obrigatório.

ROTULAGEM OBRIGATÓRIA: denominação precisa + lista de ingredientes + peso líquido E peso drenado (ambos obrigatórios — Portaria INMETRO 248/2021 Art. 12) + fabricante + validade + lote.

PONTOS CRÍTICOS: conserva sem peso drenado = NÃO CONFORME. Palmito de juçara = irregularidade ambiental. Recheio com alérgeno não declarado = NÃO CONFORME.

BASE LEGAL: RDC 272/2005, Portaria INMETRO 248/2021.""".strip()
},

{
"chave": "cogumelos",
"titulo": "RDC 272/2005 — Cogumelos e Fungos Comestíveis",
"fonte": "RDC ANVISA 272/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_vegetais",
"conteudo": """RDC 272/2005 — FUNGOS COMESTÍVEIS

ESPÉCIES E DENOMINAÇÕES: Champignon (Agaricus bisporus), Shitake (Lentinula edodes), Shimeji (Hypsizygus tessellatus / Pleurotus ostreatus), Portobello (Agaricus bisporus grande), Porcini (Boletus edulis).

FORMAS: fresco (≤7 dias refrigerado), resfriado (0°C a 5°C), congelado (≤-18°C), desidratado (prazo longo), em conserva (peso drenado obrigatório), em pó.

COGUMELOS FUNCIONAIS: Reishi (Ganoderma lucidum), Lion's mane (Hericium erinaceus), Cordyceps. Se vendidos com alegação de saúde → exige aprovação ANVISA (Resolução 18/1999). Se vendidos como suplemento → RDC 243/2018 + notificação ANVISA.

ROTULAGEM: declarar espécie + forma de apresentação + temperatura de conservação (obrigatória para frescos e congelados) + peso drenado (conservas).

PONTOS CRÍTICOS: cogumelo em conserva sem peso drenado = NÃO CONFORME. Cogumelo funcional com alegação não aprovada = NÃO CONFORME. Claim medicinal = NÃO CONFORME.

BASE LEGAL: RDC 272/2005.""".strip()
},

{
"chave": "refrigerante",
"titulo": "Decreto 6871/2009 — Refrigerantes e Bebidas Gaseificadas",
"fonte": "Decreto Federal 6871/2009",
"orgao": "MAPA",
"categoria": "nao_poa_bebidas",
"conteudo": """DECRETO 6871/2009 — REFRIGERANTES

DEFINIÇÃO: bebida gaseificada com água potável + açúcar e/ou edulcorantes + corantes + aromatizantes.

DENOMINAÇÕES: "Refrigerante de [fruta]" = contém suco/polpa real. "Refrigerante sabor [fruta]" = pode usar aromatizante artificial. "Cola"/"Guaraná" = denominações consagradas. "Água tônica" = com quinina (mínimo 60mg/L). "Soda" = água gaseificada pura sem aromatizante.

ADITIVOS COMUNS: acidulante ácido cítrico (INS 330) ou fosfórico (INS 338). Conservante benzoato de sódio (INS 211) — limite 150mg/L. Edulcorantes: aspartame (INS 951), acessulfame-K (INS 950), sacarina (INS 954).

ADVERTÊNCIAS OBRIGATÓRIAS: aspartame → "FENILCETONÚRICOS: CONTÉM FENILALANINA". Cafeína > 20mg/100mL → declarar teor. Cola contém cafeína naturalmente → declarar.

LUPA FRONTAL: refrigerantes convencionais com açúcar geralmente excedem 15g açúcar adicionado/100mL → lupa frontal OBRIGATÓRIA.

PONTOS CRÍTICOS: "Refrigerante de [fruta]" sem suco real = NÃO CONFORME (usar "sabor"). Benzoato > 150mg/L = NÃO CONFORME. Aspartame sem advertência = NÃO CONFORME. Lupa ausente em produto açucarado = NÃO CONFORME.

BASE LEGAL: Decreto 6871/2009.""".strip()
},

{
"chave": "agua_mineral",
"titulo": "Lei 9433/1997 + Portaria MS 888/2021 — Água Mineral e Potável Envasada",
"fonte": "Lei 9433/1997 + Portaria MS 888/2021 + RDC 717/2022",
"orgao": "MAPA/MS/ANVISA",
"categoria": "nao_poa_bebidas",
"conteudo": """ÁGUA MINERAL E POTÁVEL ENVASADA

TIPOS: "Água mineral natural" = fonte natural com minerais constantes + registro ANM (Agência Nacional de Mineração). "Água mineral com gás" = CO2 adicionado. "Água potável de mesa" = água tratada sem origem mineral. "Água saborizada" = água + aromatizantes → sujeita à rotulagem nutricional completa.

ROTULAGEM OBRIGATÓRIA DA ÁGUA MINERAL: denominação + origem da fonte + composição química (Ca, Mg, Na, K, F, HCO3, Cl, SO4 em mg/L) + número de registro ANM + validade + lote.

TABELA NUTRICIONAL: água mineral pura = ISENTA. Água saborizada com açúcar = tabela obrigatória (RDC 429/2020).

FLUORETO: teor > 1,5mg/L → "IMPRÓPRIA PARA CONSUMO DE CRIANÇAS ABAIXO DE 3 ANOS" obrigatório.

PONTOS CRÍTICOS: água mineral sem registro ANM = ALERTA. Fluoreto > 1,5mg/L sem advertência = NÃO CONFORME. Água saborizada com açúcar sem tabela nutricional = NÃO CONFORME. Composição química ausente = NÃO CONFORME.

BASE LEGAL: Lei 9433/1997, Portaria MS 888/2021, RDC 717/2022.""".strip()
},

{
"chave": "cerveja",
"titulo": "Decreto 6871/2009 + Portaria MAPA 65/2021 — Cerveja e Chope",
"fonte": "Decreto 6871/2009 + Portaria MAPA 65/2021",
"orgao": "MAPA",
"categoria": "nao_poa_bebidas",
"conteudo": """CERVEJA E CHOPE

DEFINIÇÃO: bebida obtida por fermentação alcoólica do mosto de malte de cevada + água + lúpulo. Teor: 0,5% a 14% v/v.

CLASSIFICAÇÕES: "Sem álcool" < 0,5% v/v. "Leve/Light" 0,5-2,0% v/v. "Puro malte" = 100% malte sem adjuntos. Cerveja comum = até 45% adjuntos (milho, arroz, trigo). "Cerveja especial" = mínimo 55% malte. Estilos (Portaria 65/2021): Lager, Pilsen, Ale, IPA, Weizen, Stout, Porter, Bock.

ROTULAGEM OBRIGATÓRIA: denominação + teor alcoólico em % v/v + "CONTÉM GLÚTEN" (malte de cevada) + símbolo proibição menores de 18 anos + volume + validade + fabricante.

ALÉRGENOS: "CONTÉM GLÚTEN" obrigatório. Cerveja de trigo: "CONTÉM GLÚTEN". Cerveja com mel: "CONTÉM MEL" (boa prática).

PONTOS CRÍTICOS: teor alcoólico não declarado = NÃO CONFORME. Símbolo menores ausente = NÃO CONFORME. "CONTÉM GLÚTEN" ausente = NÃO CONFORME. "Puro malte" com adjuntos = NÃO CONFORME.

BASE LEGAL: Decreto 6871/2009, Portaria MAPA 65/2021.""".strip()
},

{
"chave": "vinho",
"titulo": "Lei 7678/1988 + Decreto 8198/2014 — Vinho e Derivados da Uva",
"fonte": "Lei 7678/1988 + Decreto 8198/2014",
"orgao": "MAPA",
"categoria": "nao_poa_bebidas",
"conteudo": """VINHO E DERIVADOS DA UVA

TIPOS: Vinho de mesa (8,6-14% v/v): fino (Vitis vinifera) ou colonial. Vinho espumante (≥4 atm). Vinho frisante (1-3 atm). Vinho licoroso (14-18% v/v). Vinho sem álcool (<0,5% v/v).

DENOMINAÇÕES VARIETAIS: pode usar nome da uva se ≥75% da variedade declarada. Ex: Cabernet Sauvignon, Chardonnay, Merlot.

SAFRA: se declarada, ≥85% das uvas devem ser da safra indicada.

INDICAÇÕES GEOGRÁFICAS: Vale dos Vinhedos, Pinto Bandeira, etc. Uso exige conformidade com o conselho regulador.

ROTULAGEM OBRIGATÓRIA: denominação + tipo + teor alcoólico (ex: "12,5% vol.") + volume + "CONTÉM SULFITOS" (obrigatório — sulfito é alérgeno) + símbolo proibição menores + lote + fabricante/importador + país de origem (importados).

ALÉRGENOS: "CONTÉM SULFITOS" = OBRIGATÓRIO (SO2 presente em praticamente todos os vinhos). Clarificantes com ovo ou leite: "PODE CONTER LEITE/OVO".

PONTOS CRÍTICOS: "CONTÉM SULFITOS" ausente = NÃO CONFORME (grave). Teor alcoólico ausente = NÃO CONFORME. Símbolo menores ausente = NÃO CONFORME.

BASE LEGAL: Lei 7678/1988, Decreto 8198/2014.""".strip()
},

{
"chave": "bebida_energetica",
"titulo": "Regulação Bebidas Energéticas — Cafeína, Taurina e Advertências",
"fonte": "Resolução ANVISA 18/1999 + RDC 727/2022",
"orgao": "ANVISA",
"categoria": "nao_poa_bebidas",
"conteudo": """BEBIDAS ENERGÉTICAS

DEFINIÇÃO: bebida não alcoólica com cafeína + outros estimulantes (taurina, inositol, glucuronolactona, vitaminas B).

LIMITES DE INGREDIENTES (por 100mL): Cafeína máx. 32mg. Taurina máx. 400mg. Inositol máx. 20mg. Glucuronolactona máx. 240mg. Lata 250mL = máx. 80mg cafeína.

ADVERTÊNCIAS OBRIGATÓRIAS NO RÓTULO: "ESTE PRODUTO NÃO DEVE SER CONSUMIDO POR CRIANÇAS, GESTANTES, IDOSOS E PORTADORES DE ENFERMIDADES". "NÃO MISTURE COM BEBIDA ALCOÓLICA". "CONTÉM CAFEÍNA" com teor declarado por porção.

TABELA NUTRICIONAL: porção 200mL. Declarar cafeína. Verificar lupa frontal para açúcar.

BEBIDA ENERGÉTICA ALCOÓLICA: proibida no Brasil.

PONTOS CRÍTICOS: cafeína > 32mg/100mL = NÃO CONFORME. Advertências ausentes = NÃO CONFORME. Sugestão de mistura com álcool no rótulo = NÃO CONFORME. Teor de cafeína não declarado = NÃO CONFORME.

BASE LEGAL: Resolução ANVISA 18/1999, RDC 727/2022.""".strip()
},

{
"chave": "isotonica",
"titulo": "RDC 18/2010 — Bebidas Isotônicas e Repositores Hidroeletrolíticos",
"fonte": "RDC 18/2010 + IN 28/2018",
"orgao": "ANVISA",
"categoria": "nao_poa_bebidas",
"conteudo": """BEBIDAS ISOTÔNICAS — REPOSITORES HIDROELETROLÍTICOS

DEFINIÇÃO: bebida para reposição de água e eletrólitos em atividade física. Osmolalidade: 270-330 mOsm/kg.

COMPOSIÇÃO OBRIGATÓRIA (por 100mL): Sódio 46-115mg. Cloreto 52-128mg. Carboidratos 4-8g (glicose, frutose, sacarose, maltodextrina). Potássio opcional (20-50mg se adicionado).

DENOMINAÇÃO: "Repositor hidroeletrolítico [sabor]" ou "Bebida isotônica [sabor]". Não pode ser denominado "suco", "néctar" ou "água".

ROTULAGEM: tabela nutricional obrigatória. Porção 200mL. Indicação de uso: "para reposição durante e após atividade física". Proibido claims terapêuticos.

DIFERENÇAS: hipotônica (<270 mOsm) = absorção rápida. Isotônica (270-330) = exercícios moderados. Hipertônica (>330) = recuperação intensa. Se fora da faixa isotônica → não pode usar o nome "isotônica".

PONTOS CRÍTICOS: sódio fora de 46-115mg/100mL = NÃO CONFORME. Carboidratos fora de 4-8g/100mL = NÃO CONFORME. Claim terapêutico = NÃO CONFORME.

BASE LEGAL: RDC 18/2010, IN 28/2018.""".strip()
},

{
"chave": "acucar_derivados",
"titulo": "Dec-Lei 986/1969 + Dec. 6268/2007 — Açúcar e Derivados",
"fonte": "Dec-Lei 986/1969 + Decreto 6268/2007",
"orgao": "MAPA/ANVISA",
"categoria": "nao_poa_acucar",
"conteudo": """AÇÚCAR E DERIVADOS

TIPOS E DENOMINAÇÕES: "Açúcar refinado/branco" = sacarose ≥99,8%. "Açúcar cristal" = cristais maiores. "Açúcar demerara" = com melaço parcial — dourado. "Açúcar mascavo" = integral sem refino, com melaço. "Açúcar de coco" = do néctar da palmeira. "Rapadura" = sólido do caldo de cana sem centrifugação. "Melado" = xarope do caldo de cana. "Melaço" = subproduto da refinação (diferente do melado).

XAROPE DE MILHO (HFCS/Glucose): declarar na lista de ingredientes. Milho pode ser transgênico → verificar declaração (Decreto 4680/2003).

ORGÂNICO: certificado SisOrg obrigatório + selo.

ADOÇANTES: aspartame → "FENILCETONÚRICOS: CONTÉM FENILALANINA". Sacarina → "não recomendado para crianças e gestantes". Ciclamato → "não recomendado para crianças, gestantes e hipertensos".

ROTULAGEM: denominação precisa + tabela nutricional (porção 5g) + validade + fabricante.

PONTOS CRÍTICOS: HFCS de milho GM sem declaração transgênico = NÃO CONFORME. "Açúcar diet" com sacarose = NÃO CONFORME. Rapadura com corante caramelo = ALERTA (adulteração).

BASE LEGAL: Dec-Lei 986/1969, Decreto 6268/2007, RDC 713/2022.""".strip()
},

{
"chave": "azeite_oliva",
"titulo": "RDC 270/2005 — Azeite de Oliva: Categorias e Rotulagem",
"fonte": "RDC ANVISA 270/2005 + Codex STAN 33",
"orgao": "ANVISA",
"categoria": "nao_poa_oleos",
"conteudo": """AZEITE DE OLIVA — RDC 270/2005

CATEGORIAS: "Azeite de oliva extra virgem" (EVOO): processos físicos/mecânicos, acidez ≤0,8%, sem defeitos sensoriais — MELHOR QUALIDADE. "Azeite de oliva virgem": acidez ≤2,0%, leves defeitos permitidos. "Azeite de oliva" (sem qualificativo): mistura de azeite refinado + virgem, acidez ≤1,0%. "Azeite de bagaço": do resíduo de extração, qualidade inferior.

DENOMINAÇÕES PROIBIDAS: "Azeite puro" sem ser extra virgem. "Azeite extra virgem" com acidez >0,8%. "Azeite" para produto que não seja Olea europaea.

ROTULAGEM OBRIGATÓRIA: categoria + acidez máxima declarada (ex: "Acidez: máx. 0,5%") — OBRIGATÓRIO NO BRASIL + origem das azeitonas (país/região) + validade (18-24 meses).

"Prensado a frio" ou "Extração a frio": permitido se T<27°C.

PONTOS CRÍTICOS: acidez não declarada = NÃO CONFORME. "Extra virgem" sem acidez ≤0,8% = ALERTA. Mistura com outros óleos sem declarar = NÃO CONFORME. Origem não declarada = ALERTA.

BASE LEGAL: RDC 270/2005, Codex Alimentarius CODEX STAN 33.""".strip()
},

{
"chave": "leguminosas_graos",
"titulo": "Dec-Lei 986/1969 — Leguminosas: Feijão, Lentilha, Grão-de-bico, Soja",
"fonte": "Dec-Lei 986/1969 + Decreto 4680/2003",
"orgao": "MAPA/ANVISA",
"categoria": "nao_poa_graos",
"conteudo": """LEGUMINOSAS E GRÃOS

PRINCIPAIS ESPÉCIES: Feijão (Phaseolus vulgaris — carioca, preto, branco; Vigna unguiculata — fradinho, caupi). Lentilha (Lens culinaris — verde, vermelha, preta). Grão-de-bico (Cicer arietinum). Ervilha seca (Pisum sativum). Soja (Glycine max). Amendoim (Arachis hypogaea — alérgeno obrigatório).

SOJA — ATENÇÃO ESPECIAL: ≥85% da soja brasileira é geneticamente modificada. Obrigatório declarar transgênico se ≥1% do ingrediente for GM (Decreto 4680/2003 + símbolo "T"). "Leite de soja" ou "bebida de soja": ANVISA aceita "bebida à base de soja".

ALÉRGENOS OBRIGATÓRIOS: "CONTÉM SOJA". "CONTÉM AMENDOIM".

FORMAS: grão inteiro, farinha de leguminosa, proteína texturizada (PTS), massa de leguminosa (sem glúten).

ROTULAGEM: denominação precisa + transgênicos se GM + tabela nutricional (porção 50g cru) + origem (se importado) + validade + fabricante.

PONTOS CRÍTICOS: soja GM sem declaração = NÃO CONFORME. "Contém Soja" ausente em produto com soja = NÃO CONFORME. "Contém Amendoim" ausente = NÃO CONFORME.

BASE LEGAL: Dec-Lei 986/1969, Decreto 4680/2003, RDC 727/2022.""".strip()
},

{
"chave": "feijao_ervilha_graos",
"titulo": "MAPA — Classificação de Feijão, Ervilha e Grãos",
"fonte": "IN MAPA 12/2008 + Dec-Lei 986/1969",
"orgao": "MAPA",
"categoria": "nao_poa_graos",
"conteudo": """FEIJÃO, ERVILHA E GRÃOS — CLASSIFICAÇÃO MAPA

FEIJÃO — TIPOS DE QUALIDADE (IN MAPA 12/2008): Tipo 1 = até 5% grãos defeituosos (melhor). Tipo 2 = até 15%. Tipo 3 = até 35%.

VARIEDADES: Carioca (rajado bege-rosado, mais consumido). Preto (padrão RJ e Sul). Branco (cannellini, sopas). Fradinho (Nordeste). Feijão-de-corda/Vigna (Nordeste).

ERVILHA: "Ervilha seca" = grão maduro desidratado. "Ervilha partida" = split pea sem casca. "Ervilha verde" = grão imaturo (conserva — ver RDC 272/2005). Classificação: tipo 1, 2, 3 por % defeitos.

GRÃO-DE-BICO: Cabuli (grande, bege — mais comum no BR). Homus = grão-de-bico + tahine (pasta).

ROTULAGEM: denominação + espécie/variedade + peso líquido + validade + fabricante. Tipo de classificação não é obrigatório no rótulo ao consumidor, mas é boa prática. Feijão, ervilha e grão-de-bico: NÃO são GM no Brasil atualmente.

PONTOS CRÍTICOS: validade não declarada = NÃO CONFORME. Importado sem país de origem = NÃO CONFORME.

BASE LEGAL: Dec-Lei 986/1969, IN MAPA 12/2008.""".strip()
},

{
"chave": "farinhas_amidos",
"titulo": "RDC 711/2022 — Farinhas, Amidos, Féculas e Tapioca",
"fonte": "RDC ANVISA 711/2022 + Portaria MS 31/1998",
"orgao": "ANVISA",
"categoria": "nao_poa_cereais",
"conteudo": """FARINHAS, AMIDOS E FÉCULAS — RDC 711/2022

FARINHA DE TRIGO: "Farinha de trigo" ou "Farinha de trigo integral". ENRIQUECIMENTO OBRIGATÓRIO (Portaria MS 31/1998): Ferro ≥4,2mg/100g + Ácido fólico ≥150μg/100g. Declarar na lista de ingredientes e tabela nutricional. "CONTÉM GLÚTEN" obrigatório.

FARINHA DE MILHO/FUBÁ: enriquecimento ferro + ácido fólico igual ao trigo. Verificar milho transgênico (Decreto 4680/2003).

FARINHA DE ARROZ: naturalmente sem glúten — pode declarar "SEM GLÚTEN" se livre de contaminação.

AMIDOS E FÉCULAS: "Amido de milho" (maisena). "Fécula de batata". "Fécula de mandioca" / "Polvilho doce". "Polvilho azedo" = fécula fermentada. "Amido modificado" = declarar tipo de modificação.

TAPIOCA: granulado de fécula de mandioca hidratado/aquecido — produto diferente da fécula crua.

PONTOS CRÍTICOS: farinha de trigo sem ferro e ácido fólico = NÃO CONFORME. "Sem glúten" em farinha de trigo = impossível — NÃO CONFORME. Amido modificado sem declaração = ALERTA. Farinha de milho GM sem declaração transgênico = NÃO CONFORME.

BASE LEGAL: RDC 711/2022, Portaria MS 31/1998.""".strip()
},

{
"chave": "biscoito_bolacha",
"titulo": "RDC 711/2022 — Biscoitos, Bolachas, Wafers e Cookies",
"fonte": "RDC ANVISA 711/2022",
"orgao": "ANVISA",
"categoria": "nao_poa_cereais",
"conteudo": """BISCOITOS E BOLACHAS — RDC 711/2022

DENOMINAÇÕES: "Biscoito salgado/cracker" = baixo açúcar, salgado. "Biscoito doce/bolacha" = com açúcar. "Wafer" = folhas finas com recheio cremoso. "Cookie" = com pedaços (gotas, castanhas). "Biscoito recheado" = com camada de recheio. "Biscoito revestido" = com cobertura de chocolate/açúcar.

BISCOITO SEM GLÚTEN: base arroz/milho/mandioca. "SEM GLÚTEN" = garantir ausência de contaminação cruzada.

ADITIVOS TÍPICOS: lecitina de soja (INS 322) → "CONTÉM SOJA". Propionato de cálcio (INS 282) = conservante em biscoitos macios. Gordura hidrogenada pode gerar gordura trans → declarar na tabela.

ROTULAGEM: denominação precisa + lista ingredientes + tabela nutricional (porção 30g — IN 75/2020) + alérgenos (glúten, soja, leite, ovos, amendoim, castanhas).

LUPA FRONTAL: biscoito doce frequentemente tem alto açúcar adicionado e gordura saturada → verificar lupa.

COBERTURA CHOCOLATE: "Cobertura de chocolate" ≠ "Chocolate" — composição diferente (RDC 264/2005).

PONTOS CRÍTICOS: "Sem glúten" com trigo = NÃO CONFORME. Gordura trans não declarada = NÃO CONFORME. Lecitina de soja sem "CONTÉM SOJA" = NÃO CONFORME. Lupa frontal ausente = NÃO CONFORME.

BASE LEGAL: RDC 711/2022.""".strip()
},

{
"chave": "macarrao_massa",
"titulo": "RDC 711/2022 — Massas Alimentícias: Macarrão, Lasanha, Nhoque",
"fonte": "RDC ANVISA 711/2022",
"orgao": "ANVISA",
"categoria": "nao_poa_cereais",
"conteudo": """MASSAS ALIMENTÍCIAS — RDC 711/2022

TIPOS: "Massa seca" = desidratada, prazo longo. "Massa fresca" = maior aw, refrigerada. "Massa pré-cozida" = parcialmente cozida.

QUALIFICAÇÕES: "Massa ao ovo" = mínimo 1 ovo inteiro por kg de farinha → "CONTÉM OVO". "Massa integral" = ≥30% farinha integral. "Massa de sêmola/trigo durum" = melhor textura. "Massa sem glúten" = base arroz/milho/quinoa, sem trigo.

FORMATOS: espaguete, penne, fusilli, lasanha, talharim, nhoque (batata + farinha), conchinha, farfalle, rigatoni.

ENRIQUECIMENTO: farinha de trigo usada já deve ser enriquecida (Portaria 31/1998).

ROTULAGEM: denominação (formato + qualificação) + "CONTÉM GLÚTEN" se trigo/cevada/centeio + porção 80g seca ou 140g cozida (IN 75/2020) + tabela nutricional + alérgenos.

PONTOS CRÍTICOS: "Massa ao ovo" sem ovo ou menos de 1/kg = NÃO CONFORME. "Massa integral" <30% integral = NÃO CONFORME. "Sem glúten" com trigo = NÃO CONFORME. Corante em massa colorida não declarado = NÃO CONFORME.

BASE LEGAL: RDC 711/2022.""".strip()
},

{
"chave": "salgadinhos_snacks",
"titulo": "RDC 711/2022 — Salgadinhos, Snacks e Chips",
"fonte": "RDC ANVISA 711/2022 + RDC 429/2020",
"orgao": "ANVISA",
"categoria": "nao_poa_cereais",
"conteudo": """SALGADINHOS, SNACKS E CHIPS — RDC 711/2022

CATEGORIAS: "Salgadinho de milho" = extrudado de fubá/milho. "Chips de batata" = fatias fritas/assadas. "Chips de mandioca". "Pipoca" = milho estourado. "Snack de arroz" = arroz expandido. "Mix de snacks" = mistura — declarar todos os componentes.

PROCESSOS: extrusão (mais comum para milho), frito, assado ("light"/"sem óleo").

ADITIVOS COMUNS: glutamato monossódico (INS 621) = realçador de sabor muito comum → declarar "Realçador de sabor: glutamato monossódico (INS 621)". Tartrazina (INS 102) em snacks coloridos. Leite em pó (sabor queijo) → "CONTÉM LEITE E DERIVADOS".

LUPA FRONTAL: salgadinhos frequentemente têm sódio > 600mg/100g → lupa OBRIGATÓRIA para sódio. Verificar também gordura saturada.

ROTULAGEM: denominação + lista ingredientes + tabela nutricional (porção 25-30g) + alérgenos (leite, soja, glúten, amendoim).

PONTOS CRÍTICOS: sódio alto sem lupa frontal = NÃO CONFORME (muito comum). Glutamato sem função + INS = NÃO CONFORME. Leite nos ingredientes sem alérgeno = NÃO CONFORME.

BASE LEGAL: RDC 711/2022, RDC 429/2020.""".strip()
},

{
"chave": "frutas_processadas",
"titulo": "RDC 272/2005 — Frutas Processadas: Polpa, Purê, Compota, Desidratadas",
"fonte": "RDC ANVISA 272/2005",
"orgao": "ANVISA",
"categoria": "nao_poa_vegetais",
"conteudo": """FRUTAS PROCESSADAS — RDC 272/2005

DENOMINAÇÕES: "Polpa de fruta" = despolpada, SEM adição de água ou açúcar (pasteurizada/congelada é permitida). "Purê de fruta" = polpa homogeneizada. "Compota" = fruta em calda de açúcar, inteira ou em pedaços + PESO DRENADO OBRIGATÓRIO. "Doce em pasta" = fruta cozida + açúcar (ex: doce de goiaba, marmelada). "Geleia" = fruta + açúcar + pectina, mínimo 35% fruta (45% para "extra"). "Fruta desidratada/seca" = tâmara, damasco, uva-passa, ameixa. "Chips de fruta" = fruta desidratada em fatias.

POLPA — REGRA CRÍTICA: se adicionou açúcar → denominação muda para "polpa adoçada" ou "doce", NÃO pode ser "polpa".

SULFITOS EM FRUTAS SECAS: dióxido de enxofre (SO2) = conservante comum em damasco/abricó e uva-passa → "CONTÉM SULFITOS" obrigatório (alérgeno).

ORGÂNICOS: sem sulfito — certificado SisOrg necessário.

PONTOS CRÍTICOS: "Polpa" com açúcar sem indicar = NÃO CONFORME. Fruta seca com sulfito sem declarar "CONTÉM SULFITOS" = NÃO CONFORME. Compota sem peso drenado = NÃO CONFORME. Geleia com <35% fruta = NÃO CONFORME.

BASE LEGAL: RDC 272/2005.""".strip()
},

{
"chave": "proteina_po",
"titulo": "RDC 243/2018 + IN 28/2018 — Proteína em Pó (Whey, Caseína, Vegetal)",
"fonte": "RDC 243/2018 + IN 28/2018 + RDC 843/2024",
"orgao": "ANVISA",
"categoria": "nao_poa_suplementos",
"conteudo": """PROTEÍNA EM PÓ — SUPLEMENTOS PROTEICOS

PRODUTOS: Whey protein (concentrado 70-80% proteína, isolado ≥90%, hidrolisado). Caseína (micelar, caseinato). Proteína de soja/ervilha (alternativas veganas). BCAA. Albumina (clara de ovo em pó). Colágeno hidrolisado (aminograma incompleto — não substitui proteína completa).

NOTIFICAÇÃO ANVISA (RDC 843/2024): prazo encerrado 01/09/2025. Todos os suplementos proteicos DEVEM estar notificados. Rótulo: "Notificado na ANVISA sob nº XX.XXX.XXXX".

ROTULAGEM OBRIGATÓRIA: denominação "Suplemento alimentar de proteínas — [nome]" + tabela nutricional com perfil de aminoácidos por porção + %VD + porção sugerida + advertência "Este produto não é um medicamento..." + público-alvo "adultos saudáveis praticantes de atividade física" + alérgenos.

ALÉRGENOS: whey/caseína → "CONTÉM LEITE E DERIVADOS". Proteína de soja → "CONTÉM SOJA". Albumina → "CONTÉM OVO".

ALEGAÇÕES PERMITIDAS (IN 28/2018): "Contribui para a manutenção e crescimento da massa muscular". "Contribui para a recuperação muscular após exercício". PROIBIDO: claims de emagrecimento, queima de gordura sem aprovação.

PONTOS CRÍTICOS: whey sem notificação ANVISA após 01/09/2025 = NÃO CONFORME. "Queima gordura" sem aprovação = NÃO CONFORME. "CONTÉM LEITE" ausente em whey = NÃO CONFORME. Advertência ausente = NÃO CONFORME.

BASE LEGAL: RDC 243/2018, IN 28/2018, RDC 843/2024.""".strip()
},

{
"chave": "vitaminas_minerais",
"titulo": "IN 28/2018 + RDC 243/2018 — Suplementos de Vitaminas e Minerais",
"fonte": "IN ANVISA 28/2018 + RDC 243/2018",
"orgao": "ANVISA",
"categoria": "nao_poa_suplementos",
"conteudo": """SUPLEMENTOS DE VITAMINAS E MINERAIS

CATEGORIAS: vitamínico, mineral, vitamínico-mineral (multivitamínico), vitamina única.

DOSES MÁXIMAS POR PORÇÃO (IN 28/2018 — principais): Vitamina C máx. 1000mg. Vitamina D máx. 100μg (4000 UI). Vitamina E máx. 268mg. Ácido fólico máx. 1000μg. Ferro máx. 45mg. Zinco máx. 25mg. Cálcio máx. 1500mg. Magnésio máx. 350mg. Selênio máx. 300μg. Iodo máx. 600μg.

NOTIFICAÇÃO ANVISA OBRIGATÓRIA: prazo 01/09/2025 encerrado. Rótulo com número de notificação.

ROTULAGEM OBRIGATÓRIA: denominação "Suplemento alimentar de vitamina [X]" + quantidade por porção + %IDR + forma química declarada (ex: "Vitamina D3 (colecalciferol)" não só "Vitamina D") + porção diária + advertência "Este produto não é um medicamento..." + advertências específicas por nutriente.

ALEGAÇÕES APROVADAS (Anexo VIII IN 28/2018): Vitamina D "contribui para absorção de cálcio". Ferro "contribui para formação de hemoglobina". Magnésio "contribui para função muscular". Zinco "contribui para função imunológica". Vitamina C "contribui contra estresse oxidativo".

PONTOS CRÍTICOS: dose acima do máximo = NÃO CONFORME (risco saúde). Sem notificação = NÃO CONFORME. Alegação não aprovada = NÃO CONFORME. Forma química não especificada = ALERTA.

BASE LEGAL: RDC 243/2018, IN 28/2018.""".strip()
},


# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 3 — 4 NORMAS TRANSVERSAIS CRÍTICAS
# ══════════════════════════════════════════════════════════════════════════════

{
"chave": "rdc_724_microbiologicos",
"titulo": "RDC 724/2022 + IN 161/2022 — Padrões Microbiológicos para Alimentos",
"fonte": "RDC ANVISA 724/2022 + IN ANVISA 161/2022",
"orgao": "ANVISA",
"categoria": "seguranca_alimentos",
"conteudo": """RDC 724/2022 + IN 161/2022 — PADRÕES MICROBIOLÓGICOS. VIGÊNCIA: 02/01/2023.
MICRORGANISMOS: Salmonella spp. (ausência em 25g/mL para alimentos prontos). Listeria monocytogenes (ausência 25g em prontos para consumo). E. coli (limites por categoria). Bacillus cereus, Staphylococcus, Clostrídios sulfito-redutores.
LIMITES POR CATEGORIA: Carnes cruas (bovina/suína/aves): Salmonella ausência/25g. Embutidos crus (linguiça/hambúrguer): Salmonella ausência/25g; Clostrídios máx. 3×10³ UFC/g. Embutidos cozidos (mortadela/salsicha): Salmonella ausência/25g; Listeria ausência/25g; Staphylococcus máx. 10² UFC/g. Laticínios: Listeria ausência/25g (queijos moles/frescos); Salmonella ausência/25g. Pescado: Salmonella ausência/25g; Vibrio parahaemolyticus máx. 10² NMP/g; Histamina máx. 100mg/100g. Sorvetes: Salmonella ausência/25g; Staphylococcus máx. 10² UFC/g.
IMPACTO ROTULAGEM: temperatura de conservação deve ser compatível com os padrões. Validade baseada em estudo de vida de prateleira. Instrução de preparo/aquecimento obrigatória para produtos que exigem cozimento. "Manter refrigerado", "Consumir em X dias após aberto".
PONTOS CRÍTICOS: produto sensível a Listeria/Salmonella sem temperatura de conservação = NÃO CONFORME. Embutido cru sem instrução de preparo = VERIFICAR. Queijo fresco sem refrigeração declarada = NÃO CONFORME.
BASE LEGAL: RDC 724/2022, IN 161/2022.""".strip()
},

{
"chave": "rdc_722_contaminantes",
"titulo": "RDC 722/2022 + IN 160/2022 — Limites de Contaminantes em Alimentos",
"fonte": "RDC ANVISA 722/2022 + IN ANVISA 160/2022",
"orgao": "ANVISA",
"categoria": "seguranca_alimentos",
"conteudo": """RDC 722/2022 + IN 160/2022 — CONTAMINANTES. VIGÊNCIA: 02/01/2023.
METAIS PESADOS: Chumbo (Pb): carnes processadas máx. 0,10mg/kg; pescado máx. 0,30mg/kg; fórmulas infantis máx. 0,020mg/kg. Cádmio (Cd): carnes máx. 0,050mg/kg (fígado/rim 0,50); pescado máx. 0,050mg/kg. Mercúrio (Hg): atum/cação/espadarte máx. 1,0mg/kg; demais pescados máx. 0,50mg/kg — NEUROTÓXICO. Arsênio (As): arroz máx. 0,20mg/kg; pescado máx. 0,50mg/kg.
MICOTOXINAS: Aflatoxinas totais (B1+B2+G1+G2): amendoim máx. 10μg/kg; milho máx. 20μg/kg; castanha-do-brasil máx. 10μg/kg; leite M1 máx. 0,50μg/kg. DON: trigo máx. 750μg/kg; pão máx. 500μg/kg. OTA: café torrado máx. 10μg/kg; cereais máx. 5μg/kg; vinho máx. 10μg/kg. Fumonisinas (B1+B2): milho máx. 4000μg/kg; fubá máx. 2000μg/kg. Patulina: suco de maçã máx. 50μg/kg; purê de maçã infantil máx. 25μg/kg.
IMPACTO ROTULAGEM: atum/cação/tubarão = recomendação limitação para gestantes e crianças (boa prática). Produtos de amendoim/milho = alertar RT sobre programa de controle de aflatoxinas. Validade deve ser compatível com controle de micotoxinas.
PONTOS CRÍTICOS: atum sem recomendação gestantes/crianças = ALERTA. Amendoim sem controle aflatoxinas = ALERTAR RT. Suco de maçã infantil sem controle patulina = ALERTAR RT.
BASE LEGAL: RDC 722/2022, IN 160/2022.""".strip()
},

{
"chave": "rdc_332_gordura_trans",
"titulo": "RDC 332/2019 — Gordura Trans: Limites e Proibição de OPH",
"fonte": "RDC ANVISA 332/2019",
"orgao": "ANVISA",
"categoria": "rotulagem_nutricional",
"conteudo": """RDC 332/2019 — GORDURA TRANS.
PROIBIÇÃO: óleos parcialmente hidrogenados (OPH) proibidos em TODOS alimentos industrializados desde 01/01/2023. "Gordura vegetal parcialmente hidrogenada" na lista de ingredientes após 01/01/2023 = NÃO CONFORME GRAVE.
EXCEÇÕES NATURAIS (permitidas): gordura trans de origem natural em carnes, leite e derivados bovinos/ovinos. NÃO são afetados pela RDC 332/2019.
ÓLEOS COMPLETAMENTE HIDROGENADOS: não formam TFA — PERMITIDOS. Interesterificados: também PERMITIDOS.
DECLARAÇÃO OBRIGATÓRIA na tabela nutricional (RDC 429/2020): por porção e por 100g. Mesmo se zero, declarar "0g". "Zero trans" = <0,1g/porção. ≥0,1g = declarar valor real.
ALIMENTOS DE RISCO PRÉ-2023 (verificar data fabricação): biscoitos recheados, bolachas, margarinas antigas, massas fritas industriais, sorvetes com coberturas.
PONTOS CRÍTICOS: "gordura vegetal parcialmente hidrogenada" na lista pós-2023 = NÃO CONFORME. Gordura trans ausente da tabela nutricional = NÃO CONFORME. "Zero trans" com OPH = NÃO CONFORME.
BASE LEGAL: RDC 332/2019, RDC 429/2020.""".strip()
},

{
"chave": "organicos_rotulagem",
"titulo": "Lei 10831/2003 + IN MAPA 17/2014 — Alimentos Orgânicos: Rotulagem e Certificação",
"fonte": "Lei 10831/2003 + IN MAPA 17/2014 + Decreto 6323/2007",
"orgao": "MAPA/ANVISA",
"categoria": "rotulagem_especial",
"conteudo": """LEI 10831/2003 + IN MAPA 17/2014 — ORGÂNICOS.
CERTIFICAÇÃO: venda em comércio organizado = certificação por organismo credenciado no MAPA (IBD, Ecocert, IMO, etc.) OU OCS para agricultor familiar. Sem certificação = NÃO pode denominar "orgânico".
SELO SisOrg (verde): OBRIGATÓRIO no rótulo de produtos orgânicos embalados no comércio.
ROTULAGEM OBRIGATÓRIA (IN 17/2014): selo SisOrg + nome do organismo certificador + número do certificado + "ORGÂNICO" ou "PRODUTO ORGÂNICO" em destaque.
PERCENTUAIS: ≥95% ingredientes orgânicos = "produto orgânico" + selo SisOrg. 70-95% = "feito com ingredientes orgânicos" (sem selo no painel principal). <70% = listar ingredientes orgânicos individualmente.
PROIBIÇÕES ABSOLUTAS em orgânicos: OGM (transgênicos), agrotóxicos sintéticos, fertilizantes sintéticos, irradiação.
PONTOS CRÍTICOS: "Orgânico" sem selo SisOrg = NÃO CONFORME (propaganda enganosa). Orgânico com OGM na lista ingredientes = NÃO CONFORME. Orgânico irradiado = NÃO CONFORME. Certificador não credenciado no MAPA = ALERTA.
BASE LEGAL: Lei 10831/2003, Decreto 6323/2007, IN MAPA 17/2014.""".strip()
},


# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 4 — 12 GAPS CRÍTICOS NÃO-POA (embalagens, alegações, suplementos aprofundado,
#            bebidas alcoólicas, alimentos infantis complementares)
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 1 — EMBALAGENS E MATERIAIS EM CONTATO COM ALIMENTOS
# ══════════════════════════════════════════════════════════════════════════════
{
"chave": "rdc_91_2001_embalagens_geral",
"titulo": "RDC 91/2001 — Critérios Gerais e Classificação de Embalagens em Contato com Alimentos",
"fonte": "RDC ANVISA 91/2001",
"orgao": "ANVISA",
"categoria": "embalagens_contato",
"conteudo": """RDC 91/2001 — EMBALAGENS E MATERIAIS EM CONTATO COM ALIMENTOS (NORMA-MÃE)

OBJETO: Estabelece critérios gerais e classifica todos os materiais para embalagens e equipamentos em contato com alimentos. É a norma-mãe do sistema de regulação de embalagens alimentares no Brasil.

CLASSIFICAÇÃO DE MATERIAIS (Art. 3°):
1. PLÁSTICOS: polímeros sintéticos ou naturais → regulados pela RDC 56/2012 (polímeros) e RDC 326/2019 (aditivos)
2. CELULÓSICOS: papel, papelão, cartão → regulados pela RDC 88/2016
3. METÁLICOS: alumínio, aço, folha-de-flandres → regulados pela RDC 854/2024
4. ELASTOMÉRICOS: borracha natural e sintética → regulados por norma específica
5. VIDRO: material inerte, menor regulação
6. CELULOSE REGENERADA: celofane → regulado por norma específica

PRINCÍPIO DA LISTA POSITIVA: apenas substâncias expressamente autorizadas pela ANVISA podem ser usadas em embalagens alimentares. Não existe "lista negativa" — o que não está na lista positiva está proibido.

REQUISITOS GERAIS (Art. 4°):
- Embalagem não pode ceder substâncias ao alimento em quantidades que representem risco à saúde
- Não pode alterar as características sensoriais do alimento (sabor, odor, cor, textura)
- Não pode transferir substâncias em quantidade superior ao limite de migração estabelecido
- Deve ser inerte ao alimento nas condições normais de uso (temperatura, pH, tempo)

MIGRAÇÃO (Art. 5°):
- Migração total: máximo 60mg/kg de alimento ou 10mg/dm² de embalagem
- Migração específica: limites individuais por substância conforme normas específicas
- Simulantes de alimento: para testes, usar simulantes conforme pH e natureza do alimento

DECLARAÇÃO NA EMBALAGEM:
- Embalagens que requerem condições especiais de uso: obrigatório declarar temperatura máxima, compatibilidade com micro-ondas, etc.
- Símbolo de "adequado para contato com alimentos": taça + garfo (obrigatório em embalagens plásticas)

IMPACTO NA VALIDAÇÃO DE RÓTULO:
- Campo fabricante/responsável: verificar se fabricante de embalagem tem licença sanitária
- Campo modo de uso: verificar se temperatura declarada é compatível com embalagem
- "Apto para micro-ondas": embalagem plástica deve ser de material aprovado para essa finalidade
- Embalagem colorida: pigmentos e corantes devem ser aprovados para contato alimentar

PONTOS CRÍTICOS:
- Embalagem plástica colorida sem aprovação dos pigmentos = NÃO CONFORME
- Embalagem metálica: RDC 854/2024 exige conformidade com lista positiva de ligas e revestimentos
- "Apto para micro-ondas" em embalagem PVC = NÃO CONFORME (PVC não é aprovado para micro-ondas)
- Embalagem em material não listado na ANVISA = NÃO CONFORME

BASE LEGAL: RDC 91/2001, complementada por RDC 56/2012, RDC 88/2016, RDC 326/2019, RDC 854/2024, RDC 51/2010.""".strip()
},

{
"chave": "rdc_56_2012_embalagens_plasticas",
"titulo": "RDC 56/2012 + RDC 326/2019 — Embalagens Plásticas em Contato com Alimentos",
"fonte": "RDC ANVISA 56/2012 + RDC 326/2019",
"orgao": "ANVISA",
"categoria": "embalagens_contato",
"conteudo": """RDC 56/2012 — LISTA POSITIVA DE POLÍMEROS PARA EMBALAGENS PLÁSTICAS
RDC 326/2019 — LISTA POSITIVA DE ADITIVOS PARA MATERIAIS PLÁSTICOS

OBJETO: Define quais polímeros e aditivos podem ser usados em embalagens plásticas em contato direto com alimentos.

POLÍMEROS AUTORIZADOS (principais — Anexo da RDC 56/2012):
- PET (Polietileno tereftalato): garrafas, bandejas. Não apto para micro-ondas.
- PE (Polietileno): sacos, filmes, tampas. PEAD (alta densidade) e PEBD (baixa densidade).
- PP (Polipropileno): potes, filmes, tampas. ÚNICO plástico aprovado para micro-ondas em geral.
- PS (Poliestireno): bandejas, copos. Não apto para alimentos quentes.
- PVC (Policloreto de vinila): filmes stretch. Restrições para alimentos gordurosos.
- PA (Poliamida/Nylon): embalagens a vácuo, filmes multicamada.
- PC (Policarbonato): substituído por outras resinas (questões de BPA).

ADITIVOS AUTORIZADOS (RDC 326/2019 — revogou RDC 17/2008):
- Antioxidantes, estabilizantes, plastificantes, lubrificantes — apenas os listados.
- Migração total: ≤ 60mg/kg de alimento.
- Pigmentos e corantes: devem cumprir RDC 52/2010.
- Aminas aromáticas primárias: não detectáveis (LD = 0,01mg/kg).

EMBALAGEM RECICLADA (RDC 20/2008):
- PET reciclado grau alimentício (PET-PCR): permitido com registro prévio na ANVISA.
- Fabricante de embalagem PET reciclada deve estar licenciado pela ANVISA.
- Produtor de alimento deve verificar regularidade do fornecedor de embalagem.

MICRO-ONDAS:
- PP: aprovado geralmente ✅
- PET: aprovado para temperaturas moderadas (verificar especificação) ⚠️
- PS, PVC: NÃO aprovados para micro-ondas ❌
- "Apto para micro-ondas" no rótulo exige que a embalagem seja de material compatível.

IMPACTO NA VALIDAÇÃO DE RÓTULO:
- Rótulo afirma "apto para micro-ondas": verificar se a embalagem é PP ou material aprovado
- Embalagem plástica colorida: pigmentos devem ser aprovados pela ANVISA
- Embalagem PET reciclada: fornecedor deve ter registro ANVISA
- Declaração de temperatura: deve ser compatível com o polímero

PONTOS CRÍTICOS:
- "Leve ao micro-ondas" em embalagem PS ou PVC = NÃO CONFORME
- Embalagem colorida com pigmentos não aprovados = NÃO CONFORME
- PET reciclado sem registro ANVISA do fabricante = NÃO CONFORME

BASE LEGAL: RDC 56/2012, RDC 326/2019 (revogou RDC 17/2008), RDC 51/2010 (migração), RDC 91/2001.""".strip()
},

{
"chave": "rdc_88_2016_embalagens_celulosicas",
"titulo": "RDC 88/2016 — Embalagens Celulósicas (Papel, Papelão, Cartão) em Contato com Alimentos",
"fonte": "RDC ANVISA 88/2016",
"orgao": "ANVISA",
"categoria": "embalagens_contato",
"conteudo": """RDC 88/2016 — MATERIAIS CELULÓSICOS EM CONTATO COM ALIMENTOS

OBJETO: Regula papel, papelão, cartão e celulose regenerada usados em embalagens primárias (contato direto) com alimentos.

MATERIAIS ABRANGIDOS:
- Papel kraft, papel sulfite, papel pergaminho
- Papelão ondulado (quando em contato direto)
- Cartão para embalagem (caixinhas de leite, caixas de suco)
- Celulose regenerada (celofane)
- Materiais compostos: papel laminado com plástico ou alumínio

SUBSTÂNCIAS PERMITIDAS (Lista Positiva):
Fibras: celulose virgem e reciclada com limitações. Celulose reciclada de pós-consumo: restrições mais rígidas (contaminantes do ciclo de reciclagem).
Aditivos de processo: colas, adesivos, agentes de colagem, alvejantes ópticos — apenas os listados.
Tintas de impressão: na face externa (não em contato) devem ser de baixo set-off (não migrar para o alimento através da embalagem).

PAPEL RECICLADO:
Papel reciclado de pós-consumo tem risco de contaminantes (tintas, adesivos, substâncias do uso anterior). ANVISA estabelece limites para: minerais de petróleo (MOSH/MOAH), diisopropilnaftaleno (DIPN), metais pesados.
Embalagem primária (contato direto) com papel reciclado de pós-consumo: deve comprovar conformidade com os limites.

EMBALAGEM LONGA VIDA (Tetra Pak e similares):
Multicamada: plástico + alumínio + papel. Cada camada regulada por sua norma específica.
O plástico interno em contato com o alimento: deve cumprir RDC 56/2012.

IMPACTO NA VALIDAÇÃO DE RÓTULO:
- Embalagem de papel para alimentos gordurosos (pizza, salgado): verificar se papel é aprovado para gordura
- "Embalagem sustentável/reciclada": papel reciclado pós-consumo exige comprovação de conformidade
- Tintas na embalagem: migração por set-off deve ser controlada (não é declarado no rótulo mas é responsabilidade do fabricante)

PONTOS CRÍTICOS:
- Papel reciclado de pós-consumo em contato com alimento gorduroso = ALERTA (verificar MOSH/MOAH)
- Tinta de impressão em contato direto com alimento = NÃO CONFORME
- Caixa de papelão reciclado como embalagem primária sem comprovação = ALERTA

BASE LEGAL: RDC 88/2016, RDC 91/2001.""".strip()
},

{
"chave": "rdc_854_2024_embalagens_metalicas",
"titulo": "RDC 854/2024 — Embalagens e Equipamentos Metálicos em Contato com Alimentos",
"fonte": "RDC ANVISA 854/2024 (revogou RDC 20/2007)",
"orgao": "ANVISA",
"categoria": "embalagens_contato",
"conteudo": """RDC 854/2024 — MATERIAIS METÁLICOS EM CONTATO COM ALIMENTOS
VIGÊNCIA: 02/05/2024. Revogou a RDC 20/2007.

OBJETO: Regula embalagens, utensílios e equipamentos metálicos (latas, tampas, bandejas de alumínio, aço inox) em contato com alimentos.

MATERIAIS METÁLICOS PERMITIDOS:
- Aço inox: ligas definidas na norma (série AISI permitidas — verificar lista)
- Alumínio e ligas de alumínio: com especificações de pureza
- Folha-de-flandres (estanho sobre aço): para latas de conserva
- Aço cromado eletrolítico (TFS/TFC): alternativa à folha-de-flandres
- Aço carbono: apenas com revestimento polimérico aprovado (NÃO em contato direto sem revestimento)

REVESTIMENTOS INTERNOS DE LATAS:
- Vernizes epóxi, acrílico, organoassol: os mais comuns em conservas, bebidas, alimentos ácidos
- Revestimento deve ser feito de substâncias das listas positivas de plásticos (RDC 56/2012, RDC 326/2019)
- BPA (Bisfenol A) em vernizes: em revisão pela ANVISA, usar alternativas (BPA-NI = BPA não intencional)

REQUISITOS DE MIGRAÇÃO:
- Alumínio: limite de migração em alimentos ácidos (pH < 4) mais restritivo
- Chumbo e cádmio: limites rígidos para folha-de-flandres e soldas
- Proibido soldas com chumbo e estanho para latas de alimentos (Lei 9832/1999)

ENSAIOS EXIGIDOS (pelo fabricante de embalagem, não declarado no rótulo):
- Migração global
- Migração específica de metais
- Resistência à corrosão para alimentos ácidos

IMPACTO NA VALIDAÇÃO DE RÓTULO:
- Lata de alumínio para bebida ácida (pH < 4): verificar se revestimento interno é compatível
- "Pode conter BPA": declaração voluntária que algumas empresas adotam
- Bandeja de alumínio para forno: verificar especificação de temperatura máxima

PONTOS CRÍTICOS:
- Aço carbono sem revestimento em contato com alimento = NÃO CONFORME
- Soldas com chumbo em latas = NÃO CONFORME (Lei 9832/1999)
- Lata de alumínio para alimento ácido sem revestimento interno aprovado = ALERTA

BASE LEGAL: RDC 854/2024 (revogou RDC 20/2007), Lei 9832/1999, RDC 91/2001.""".strip()
},

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 2 — ALEGAÇÕES FUNCIONAIS E NUTRICIONAIS COMPLETAS
# ══════════════════════════════════════════════════════════════════════════════
{
"chave": "alegacoes_funcionais_lista_completa",
"titulo": "Lista Completa de Alegações Funcionais Aprovadas ANVISA — Res. 18/1999 + Resolução 2/2002",
"fonte": "Resolução ANVISA 18/1999 + Resolução 2/2002 (atualizada) + IN 28/2018",
"orgao": "ANVISA",
"categoria": "alegacoes_saude",
"conteudo": """LISTA COMPLETA DE ALEGAÇÕES FUNCIONAIS E DE SAÚDE APROVADAS PELA ANVISA

BASE LEGAL: Resolução ANVISA 18/1999 (alegações funcionais), Resolução 2/2002 (lista positiva atualizada), IN 28/2018 (suplementos).

TIPOS DE ALEGAÇÃO:
1. PROPRIEDADE NUTRICIONAL: sobre conteúdo de nutriente (ex: "rico em fibras", "fonte de vitamina C", "baixo em sódio")
   Base: RDC 429/2020 — critérios quantitativos para cada alegação.
2. PROPRIEDADE FUNCIONAL: papel fisiológico do nutriente/substância (lista positiva ANVISA obrigatória)
3. PROPRIEDADE DE SAÚDE: relação nutriente-doença (lista positiva ANVISA, mais restrita)

ALEGAÇÕES FUNCIONAIS APROVADAS — LISTA POSITIVA COMPLETA:

FIBRAS ALIMENTARES
- Fibra alimentar: "As fibras alimentares auxiliam o funcionamento do intestino." Quantidade mínima: 2,5g por porção.
- Farelo de aveia: "O farelo de aveia contribui para a redução do colesterol." Mínimo: 3g de beta-glucana/dia.

VITAMINAS
- Vitamina A: "A vitamina A contribui para a manutenção da visão normal, da saúde da pele e das membranas mucosas, do funcionamento do sistema imunológico."
- Vitamina C: "A vitamina C contribui contra o estresse oxidativo." E "A vitamina C contribui para o funcionamento normal do sistema imunológico."
- Vitamina D: "A vitamina D contribui para a absorção e utilização do cálcio e fósforo, para a formação dos ossos e dentes e para o funcionamento do sistema imunológico."
- Vitamina E: "A vitamina E protege as células dos radicais livres (estresse oxidativo)."
- Vitaminas do complexo B:
  B1 (Tiamina): "contribui para o funcionamento do coração e do sistema nervoso."
  B2 (Riboflavina): "contribui para o funcionamento normal do sistema nervoso e para a manutenção da visão normal."
  B3 (Niacina): "contribui para o funcionamento do sistema nervoso e para a manutenção da pele e membranas mucosas."
  B6: "contribui para o funcionamento do sistema imunológico e para a formação normal das células vermelhas do sangue."
  B12: "contribui para a formação normal dos glóbulos vermelhos do sangue e para o funcionamento do sistema nervoso."
  Ácido fólico: "contribui para o crescimento adequado dos tecidos durante a gestação."
  Biotina: "contribui para o metabolismo normal dos macronutrientes."
  Ácido pantotênico: "contribui para o metabolismo e síntese de hormônios esteróides, vitaminas D e neurotransmissores."

MINERAIS
- Cálcio: "O cálcio contribui para a manutenção de ossos e dentes saudáveis."
- Ferro: "O ferro contribui para a formação normal de hemoglobina e glóbulos vermelhos do sangue."
- Magnésio: "O magnésio contribui para a manutenção normal dos ossos e dentes e para o funcionamento do sistema nervoso e muscular."
- Zinco: "O zinco contribui para o funcionamento do sistema imunológico e para a manutenção dos cabelos, unhas e pele."
- Selênio: "O selênio protege as células do estresse oxidativo." Mínimo: 30μg/porção.
- Iodo: "O iodo contribui para a produção normal de hormônios tireoidianos."
- Potássio: "O potássio contribui para o funcionamento normal do sistema muscular."
- Fósforo: "O fósforo contribui para a manutenção de ossos e dentes saudáveis."

OUTROS NUTRIENTES E SUBSTÂNCIAS BIOATIVAS
- Ômega-3 (EPA/DHA): "O ômega-3 contribui para a manutenção de níveis normais de triglicerídeos no sangue." Mínimo: 0,3g EPA+DHA/porção.
- Carotenóides (Licopeno): "Possui ação antioxidante que protege as células contra os danos dos radicais livres." Mínimo: 3mg licopeno/porção.
- Beta-caroteno: "Possui ação antioxidante que protege as células contra os danos dos radicais livres." Mínimo: 3mg/porção.
- Luteína: "Possui ação antioxidante que protege as células contra os danos dos radicais livres." Mínimo: 3mg/porção.
- Probióticos: "Contribui para o equilíbrio da flora intestinal. Seu consumo deve estar associado a uma alimentação equilibrada e hábitos de vida saudáveis." Mínimo: 10^8 a 10^9 UFC/porção (depende da cepa).
- Prebióticos (FOS, inulina): "Contribui para o equilíbrio da flora intestinal." Mínimo: 3g FOS ou 5g inulina/porção.
- Fitoesteróis: "Os fitoesteróis contribuem para a redução do colesterol." Mínimo: 0,8g/porção.
- Proteína de soja: "A proteína de soja contribui para a redução do colesterol." Mínimo: 25g proteína de soja/dia.

ALEGAÇÕES PROIBIDAS (qualquer produto alimentar):
- "Cura", "trata", "previne" qualquer doença → PROIBIDO (confunde alimento com medicamento)
- "O mais saudável", "o melhor para sua saúde" → PROIBIDO (superlativo não comprovado)
- "Emagrece", "queima gordura", "reduz peso" → PROIBIDO sem aprovação específica
- "Aumenta testosterona", "melhora performance sexual" → PROIBIDO
- Qualquer alegação não listada na lista positiva → PROIBIDO

CRITÉRIOS PARA USO DE ALEGAÇÃO FUNCIONAL:
1. Substância deve estar na lista positiva
2. Quantidade mínima declarada deve ser cumprida por porção
3. Quantidade máxima (se existir) não pode ser ultrapassada
4. Substância deve estar presente em quantidade tecnologicamente adequada
5. Alegação deve ser usada no contexto de uma dieta equilibrada

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- Alegação presente sem substância na quantidade mínima por porção = NÃO CONFORME
- Alegação não listada na lista positiva ANVISA = NÃO CONFORME
- Claim terapêutico em alimento = NÃO CONFORME (grave — pode ser crime sanitário)
- "Rico em fibras" sem 5g fibra/porção (ou 2,5g para "fonte de fibras") = NÃO CONFORME""".strip()
},

{
"chave": "alegacoes_nutricionais_criterios",
"titulo": "Critérios para Alegações Nutricionais — RDC 429/2020 Anexo III",
"fonte": "RDC ANVISA 429/2020 Anexo III + RDC 727/2022",
"orgao": "ANVISA",
"categoria": "alegacoes_saude",
"conteudo": """ALEGAÇÕES NUTRICIONAIS — CRITÉRIOS QUANTITATIVOS (RDC 429/2020 ANEXO III)

ALEGAÇÕES DE CONTEÚDO — CRITÉRIOS POR PORÇÃO:

ENERGIA (valor calórico):
- "Baixo valor energético" ou "Light em calorias": ≤ 40kcal/100g (sólido) ou ≤ 20kcal/100mL (líquido)
- "Sem valor energético" ou "Zero calorias": ≤ 4kcal/porção

GORDURAS:
- "Baixo teor de gorduras totais": ≤ 3g/100g ou ≤ 1,5g/100mL
- "Sem gorduras totais": ≤ 0,5g/porção
- "Baixo teor de gorduras saturadas": ≤ 1,5g/100g ou ≤ 0,75g/100mL, E gordura saturada ≤ 10% VE
- "Sem gorduras saturadas": ≤ 0,1g/porção
- "Zero trans" ou "Sem gorduras trans": ≤ 0,1g/porção
- "Baixo em colesterol": ≤ 20mg/100g ou ≤ 10mg/100mL, E baixo em gorduras saturadas

AÇÚCAR:
- "Sem adição de açúcares": não contém açúcares adicionados (sacarose, mel, xaropes, sucos concentrados)
- "Baixo teor de açúcares": ≤ 5g/100g ou ≤ 2,5g/100mL
- "Sem açúcares": ≤ 0,5g/porção
ATENÇÃO: "sem adição de açúcares" ≠ "sem açúcares". Produto pode ter açúcares naturais (frutose da fruta) e ser "sem adição".

SÓDIO:
- "Baixo teor de sódio": ≤ 120mg/100g ou ≤ 120mg/100mL
- "Muito baixo teor de sódio": ≤ 40mg/100g
- "Sem sódio" ou "Sem sal": ≤ 5mg/porção
- "Não salgar": sem sódio adicionado, mas pode ter sódio natural

FIBRAS:
- "Fonte de fibras": ≥ 2,5g/porção
- "Alto teor de fibras" ou "Rico em fibras": ≥ 5g/porção

PROTEÍNAS:
- "Fonte de proteínas": ≥ 10% da IDR por porção (= 5g proteína/porção para adultos)
- "Alto teor de proteínas": ≥ 20% da IDR por porção (= 10g proteína/porção)

VITAMINAS E MINERAIS:
- "Fonte de [vitamina/mineral]": ≥ 15% da IDR por porção
- "Rico em [vitamina/mineral]": ≥ 30% da IDR por porção

ALEGAÇÕES COMPARATIVAS ("LIGHT" / "REDUZIDO"):
- Deve comparar com produto convencional da mesma categoria
- Diferença mínima: 25% menos em calorias ou no nutriente declarado
- Deve declarar: "X% menos [nutriente] que [produto de referência]"
- Não pode usar "light" apenas pelo método de preparo (ex: assado vs frito) sem diferença nutricional significativa

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- "Sem adição de açúcares" em produto com mel: ALERTA (mel é açúcar adicionado — NÃO CONFORME)
- "Light" sem declarar o % de redução e o nutriente = NÃO CONFORME
- "Rico em fibras" com 2g/porção = NÃO CONFORME (precisa ≥ 5g)
- "Sem gordura trans" com gordura parcialmente hidrogenada na lista de ingredientes = NÃO CONFORME
- "Fonte de proteínas" com 3g/porção = NÃO CONFORME (precisa ≥ 5g)""".strip()
},

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 3 — SUPLEMENTOS — APROFUNDAMENTO DOSES MÁXIMAS
# ══════════════════════════════════════════════════════════════════════════════
{
"chave": "suplementos_doses_maximas_in28",
"titulo": "IN 28/2018 — Tabela Completa de Doses Máximas por Nutriente em Suplementos",
"fonte": "IN ANVISA 28/2018 Anexos I-VIII",
"orgao": "ANVISA",
"categoria": "suplementos",
"conteudo": """IN 28/2018 — DOSES MÍNIMAS E MÁXIMAS POR PORÇÃO EM SUPLEMENTOS ALIMENTARES

IMPORTANTE: doses são por PORÇÃO DIÁRIA declarada no rótulo.

ANEXO I — VITAMINAS (mínimo e máximo por porção):
Vitamina A: mín 75μg RE, máx 600μg RE (cuidado: excesso causa hipervitaminose A)
Vitamina D: mín 2,5μg, máx 100μg (4000 UI) — limite crítico, excesso é tóxico
Vitamina E: mín 2,4mg α-TE, máx 268mg α-TE
Vitamina K: mín 17,5μg, máx 1000μg
Vitamina C: mín 13,5mg, máx 1000mg
Vitamina B1 (Tiamina): mín 0,175mg, máx 100mg
Vitamina B2 (Riboflavina): mín 0,21mg, máx 100mg
Vitamina B3 (Niacina): mín 2,4mg, máx 35mg (como ácido nicotínico); 100mg (como nicotinamida)
Vitamina B5 (Ácido pantotênico): mín 0,75mg, máx 200mg
Vitamina B6: mín 0,21mg, máx 10mg (excesso → neuropatia periférica — ADVERTÊNCIA obrigatória se > 10mg/dia)
Vitamina B7 (Biotina): mín 7,5μg, máx 300μg
Vitamina B9 (Ácido fólico): mín 30μg, máx 1000μg (gestantes: atenção especial)
Vitamina B12: mín 0,375μg, máx 1000μg

ADVERTÊNCIA OBRIGATÓRIA: Vitamina B6 > 10mg/dia: "Altas doses de vitamina B6 podem causar neuropatia periférica. Consulte um médico antes de usar."

ANEXO II — MINERAIS:
Cálcio: mín 120mg, máx 1500mg
Fósforo: mín 87,5mg, máx 1250mg
Magnésio: mín 30mg, máx 350mg
Ferro: mín 2,1mg, máx 45mg (ADVERTÊNCIA: "Não consumir se não houver deficiência de ferro diagnosticada por médico." para doses > 45mg)
Zinco: mín 1,35mg, máx 25mg
Cobre: mín 0,225mg, máx 5mg
Manganês: mín 0,3mg, máx 11mg
Cromo: mín 10,5μg, máx 250μg
Molibdênio: mín 6,75μg, máx 600μg
Selênio: mín 8,25μg, máx 300μg
Iodo: mín 22,5μg, máx 600μg
Flúor: mín 0,55mg, máx 10mg
Sódio: sem dose mínima; máx limitado pelas regras gerais
Potássio: mín 470mg, máx 3500mg
Cloro: mín 550mg, máx 2300mg

ANEXO III — PROTEÍNAS E AMINOÁCIDOS:
Proteínas: whey, caseína, albumina, soja, ervilha, colágeno — sem dose máxima definida
Aminoácidos essenciais individuais: BCAA (leucina, isoleucina, valina) — sem dose máxima
Creatina: 3g/porção máx para uso em suplemento sem prescrição
Taurina: máx 2g/porção (acima disso é bebida energética)
Cafeína: máx 400mg/dia total; máx 200mg/porção isolada; se > 150mg/porção: advertência obrigatória

ANEXO IV — FIBRAS:
Inulina/FOS: sem dose máxima definida
Psyllium: sem dose máxima definida
Beta-glucana: mín 1g/porção para alegação funcional

ADVERTÊNCIAS ESPECÍFICAS POR INGREDIENTE:
- Cafeína > 150mg/porção: "Este produto contém X mg de cafeína por porção. Indivíduos sensíveis à cafeína, crianças, gestantes, nutrizes e idosos não devem consumir."
- Ferro: advertência de toxicidade em crianças
- Vitamina D > 25μg (1000 UI)/porção: "Consulte um médico antes de usar."
- Qualquer suplemento: "Este produto não é um medicamento e não deve ser usado como substituto de uma alimentação variada e equilibrada."

NOTIFICAÇÃO ANVISA (RDC 843/2024 + IN 281/2024):
Número obrigatório no rótulo: "Notificado na Anvisa sob o nº [número]"
Prazo encerrado: 01/09/2025. Suplementos sem notificação após essa data = IRREGULARES.

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- Vitamina D > 100μg/porção sem prescrição = NÃO CONFORME
- Ferro > 45mg/porção sem advertência de toxicidade = NÃO CONFORME
- Vitamina B6 > 10mg/dia sem advertência de neuropatia = NÃO CONFORME
- Suplemento sem número de notificação ANVISA após 01/09/2025 = NÃO CONFORME
- Cafeína > 200mg/porção = NÃO CONFORME (limite de suplemento excedido)
- Ingrediente não listado nos Anexos I-VIII = ingrediente não autorizado = NÃO CONFORME""".strip()
},

{
"chave": "suplementos_rotulagem_especifica",
"titulo": "RDC 243/2018 — Rotulagem Completa Específica de Suplementos Alimentares",
"fonte": "RDC ANVISA 243/2018 + RDC 786/2023",
"orgao": "ANVISA",
"categoria": "suplementos",
"conteudo": """RDC 243/2018 — ROTULAGEM ESPECÍFICA PARA SUPLEMENTOS ALIMENTARES
Atualizada pela RDC 786/2023 e RDC 843/2024.

DENOMINAÇÃO OBRIGATÓRIA:
"Suplemento alimentar" deve constar na denominação do produto, associada ao ingrediente principal.
Exemplos corretos: "Suplemento alimentar de whey protein", "Suplemento vitamínico", "Suplemento alimentar de magnésio"
Exemplos incorretos: apenas "Whey Protein" sem "suplemento alimentar", ou "Vitaminas e minerais" sem a denominação

PAINEL PRINCIPAL — INFORMAÇÕES OBRIGATÓRIAS:
1. Denominação completa (Suplemento alimentar de ___)
2. Número de notificação ANVISA (após 01/09/2025): "Notificado na Anvisa sob o nº ___"
3. Marca registrada (se houver)
4. Quantidade líquida (g, mL, cápsulas, sachês, etc.)
5. Indicação de sabor (se aplicável)

PAINEL LATERAL / INFORMAÇÃO TÉCNICA — OBRIGATÓRIOS:
1. Lista de ingredientes (incluindo excipientes, aromatizantes, adoçantes com INS)
2. Tabela nutricional por porção e %VD
3. Modo de preparo/uso (como e quando consumir, com ou sem água, etc.)
4. Advertências específicas por ingrediente (ver IN 28/2018)
5. Público-alvo: "Destinado a adultos saudáveis" ou especificação (ex: "praticantes de atividade física")
6. Advertência geral OBRIGATÓRIA: "Este produto não é um medicamento e não deve ser usado como substituto de uma alimentação variada e equilibrada. Seu consumo deve ser orientado por nutricionista ou médico."
7. Conservação: temperatura, umidade, exposição à luz
8. Prazo de validade após aberto (quando aplicável)
9. Lote e data de fabricação
10. Fabricante/importador com endereço

TABELA NUTRICIONAL PARA SUPLEMENTOS:
- Declarar TODOS os ingredientes com ação nutricional por porção e por 100g/100mL
- %VD baseado na IDR correspondente
- Se o ingrediente não tem IDR definida: declarar a quantidade e "*" com nota "VD não estabelecido"
- Vitaminas e minerais abaixo de 5% da IDR: não precisam ser declarados (mas podem ser)

ALEGAÇÕES PERMITIDAS EM SUPLEMENTOS:
Apenas as listadas no Anexo VIII da IN 28/2018.
Exemplos permitidos:
- Proteínas: "Contribui para a manutenção e o crescimento da massa muscular."
- Creatina: "Contribui para o aumento de desempenho em exercícios de alta intensidade e curta duração."
- Cafeína: "Contribui para aumentar a resistência durante o exercício de resistência prolongado."
- Vitamina C: "Contribui contra o estresse oxidativo."

PROIBIÇÕES ESPECÍFICAS EM SUPLEMENTOS:
- Claims de tratamento ou cura de doença
- Claims de performance além dos aprovados
- Imagens que sugiram resultados corporais não comprovados
- Comparação com medicamentos
- "Melhora a imunidade" sem especificação do mecanismo aprovado

POPULAÇÃO DE RISCO — ADVERTÊNCIAS ADICIONAIS:
Gestantes e lactantes: "Consulte o médico ou nutricionista antes de utilizar este produto durante a gestação ou amamentação."
Crianças: "Não indicado para crianças."
Hipertensos: produtos com sódio acima de 120mg/porção: alertar.

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- Ausência de "Suplemento alimentar" na denominação = NÃO CONFORME
- Ausência do número de notificação após 01/09/2025 = NÃO CONFORME
- Ausência da advertência geral = NÃO CONFORME
- Alegação não aprovada = NÃO CONFORME
- Ausência de público-alvo = NÃO CONFORME
- Ausência de modo de uso = NÃO CONFORME""".strip()
},

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 4 — BEBIDAS ALCOÓLICAS — GAPS
# ══════════════════════════════════════════════════════════════════════════════
{
"chave": "lei_14064_2020_bebidas_alcoolicas",
"titulo": "Lei 14.064/2020 — Advertências Obrigatórias em Bebidas Alcoólicas",
"fonte": "Lei Federal 14.064/2020",
"orgao": "ANVISA/MAPA",
"categoria": "bebidas_alcoolicas",
"conteudo": """LEI 14.064/2020 — ADVERTÊNCIAS EM BEBIDAS ALCOÓLICAS

OBJETO: Atualiza e unifica as advertências obrigatórias em rótulos de bebidas alcoólicas.

ADVERTÊNCIAS OBRIGATÓRIAS NO RÓTULO (Art. 2°):
Qualquer bebida alcoólica (teor ≥ 0,5% v/v) deve conter advertência visível:

Texto obrigatório (uma das opções aprovadas, em rodízio):
1. "VENDA PROIBIDA PARA MENORES DE 18 ANOS"
2. "QUEM BEBE NÃO DIRIGE"
3. "EVITE O CONSUMO DE ÁLCOOL DURANTE A GRAVIDEZ"
4. "O ÁLCOOL PODE SER PREJUDICIAL À SAÚDE"
5. "BEBA COM MODERAÇÃO"

FORMATO DE EXIBIÇÃO:
- Caracteres legíveis, com destaque (tipicamente em caixa preta ou fundo contrastante)
- Tamanho mínimo: proporcional ao painel do rótulo (verificar especificações do Dec. 6871/2009)
- Posição: painel lateral ou posterior, visível ao consumidor
- Proibido camuflar, dificultar a leitura ou colocar em área de difícil acesso

SÍMBOLO DE PROIBIÇÃO PARA MENORES:
Ícone com "18" e símbolo proibido (barra diagonal sobre círculo) = OBRIGATÓRIO
Posicionado no painel frontal ou lateral visível
Tamanho mínimo recomendado: 1cm²

PROIBIÇÕES ADICIONAIS (Art. 3° e 4°):
- Proibido associar bebida alcoólica a esportes, especialmente esportes com automóveis e motos
- Proibido usar imagens de crianças, adolescentes ou situações que sugiram consumo por menores
- Proibido associar consumo de álcool à condução de veículos
- Proibido usar modelos aparentando ser menores de 25 anos em publicidade
- Proibido claims de benefícios à saúde

RELAÇÃO COM OUTRAS NORMAS:
- Dec. 6871/2009: rotulagem geral de bebidas (teor alcoólico, volume, fabricante)
- Port. MAPA 65/2021: especificações cerveja e chope
- Lei 7678/1988 + Dec. 8198/2014: vinho e derivados da uva
- RDC 727/2022: rotulagem geral (aplicável como norma base)

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- Bebida alcoólica sem advertência de menores = NÃO CONFORME
- Símbolo "18" ausente = NÃO CONFORME
- Teor alcoólico não declarado = NÃO CONFORME (Dec. 6871/2009)
- Imagem de menor de idade na embalagem = NÃO CONFORME
- Associação com direção de veículos = NÃO CONFORME""".strip()
},

{
"chave": "in_mapa_14_2018_bebidas_mistas",
"titulo": "IN MAPA 14/2018 — Bebidas Mistas, RTDs e Misturadores Alcoólicos",
"fonte": "IN MAPA 14/2018",
"orgao": "MAPA",
"categoria": "bebidas_alcoolicas",
"conteudo": """IN MAPA 14/2018 — BEBIDAS MISTAS E MISTURAS DE BEBIDAS ALCOÓLICAS

OBJETO: Regulamenta as bebidas mistas (RTD — Ready to Drink) e misturas de bebidas alcoólicas.

DEFINIÇÕES:
"Bebida mista": produto obtido pela mistura de uma ou mais bebidas alcoólicas com uma ou mais bebidas não alcoólicas, podendo conter outros ingredientes autorizados.
"RTD" (Ready to Drink): bebida mista pronta para consumo, geralmente com teor alcoólico de 3-8% v/v.
"Ice": tipo de RTD à base de bebida destilada (vodka ice, smirnoff ice, etc.)
"Cooler": RTD à base de vinho ou cerveja com suco de frutas.

COMPOSIÇÃO E TEOR:
- Teor alcoólico deve ser declarado em % v/v
- Bebidas mistas com base em destilado: reguladas também pelo Decr. 6871/2009
- Bebidas mistas com base em vinho: reguladas também pela Lei 7678/1988

DENOMINAÇÃO:
- "Bebida mista" + indicação da(s) bebida(s) base
- Ex: "Bebida mista à base de vodca e suco de limão"
- "Ice", "Cooler", "RTD" são denominações aceitas como complemento
- Proibido denominar de forma que confunda com a bebida base pura (ex: chamar de "vodca" uma bebida mista)

ROTULAGEM OBRIGATÓRIA:
1. Denominação de venda
2. Teor alcoólico: "X% vol." ou "X°GL"
3. Volume líquido
4. Lista de ingredientes (incluindo TODOS os ingredientes das bebidas que a compõem)
5. Advertências da Lei 14.064/2020 (menores + dirigir)
6. Fabricante com endereço
7. Lote e validade
8. Alérgenos: cereais com glúten (se base de malte), sulfitos (se base de vinho)

ALÉRGENOS COMUNS EM RTDs:
- Base de cerveja/malte: "CONTÉM GLÚTEN"
- Base de vinho: "CONTÉM SULFITOS"
- Base de destilado + corante caramelo: verificar origem do caramelo

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- RTD sem teor alcoólico declarado = NÃO CONFORME
- Bebida mista com base de malte sem "CONTÉM GLÚTEN" = NÃO CONFORME
- Denominação que confunde com bebida pura = NÃO CONFORME
- Ausência de advertência menores em qualquer RTD = NÃO CONFORME
- Lista de ingredientes incompleta (não lista todos os componentes de cada bebida base) = NÃO CONFORME

BASE LEGAL: IN MAPA 14/2018, Dec. 6871/2009, Lei 14.064/2020, RDC 727/2022.""".strip()
},

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 5 — ALIMENTOS INFANTIS COMPLEMENTARES
# ══════════════════════════════════════════════════════════════════════════════
{
"chave": "rdc_222_2002_alimentos_complementares",
"titulo": "RDC 222/2002 — Alimentos Complementares para Lactentes e Crianças (6-36 meses)",
"fonte": "RDC ANVISA 222/2002",
"orgao": "ANVISA",
"categoria": "alimentos_infantis",
"conteudo": """RDC 222/2002 — ALIMENTOS COMPLEMENTARES PARA LACTENTES E CRIANÇAS DE PRIMEIRA INFÂNCIA

OBJETO: Regula alimentos destinados a crianças de 6 meses a 3 anos que complementam a alimentação (em adição ao leite materno ou fórmula).

CATEGORIAS:
1. ALIMENTOS DE TRANSIÇÃO: papinhas de fruta, purês de hortaliças, sopas e mingaus — para 6+ meses
2. ALIMENTOS ENRIQUECIDOS PARA LACTENTES: cereais, biscoitos, bolachas com vitaminas/minerais adicionados
3. ALIMENTOS PARA CRIANÇAS DE PRIMEIRA INFÂNCIA (1-3 anos): versões para crianças pequenas

COMPOSIÇÃO MÍNIMA/MÁXIMA:
- Energia: 60-80 kcal/100g para papinhas; alimentos secos com mais concentração
- Proteínas: mínimo variável por categoria (vegetais, cereais, carne)
- Gorduras: sem gordura trans; trans naturais em limites
- Vitaminas e minerais: conforme tabela da norma (enriquecimento mínimo obrigatório para alimentos secos industrializados)
- Sódio: limite máximo de 200mg/100kcal (muito baixo — crianças pequenas não devem consumir sódio em excesso)
- Açúcar adicionado: não recomendado para < 2 anos; se adicionado: declarar claramente

PROIBIÇÕES ESPECÍFICAS:
- Sacarose e mel para < 12 meses (risco microbiológico do mel + cárie)
- Aditivos alimentares: lista muito restrita (a maioria dos aditivos comuns é proibida)
- Corantes artificiais: proibidos
- Aromatizantes artificiais: proibidos
- Conservantes: maioria proibida (exceto casos específicos)
- Adoçantes artificiais: proibidos

ROTULAGEM OBRIGATÓRIA:
1. Denominação: "Alimento complementar para lactentes" ou "Alimento para crianças de primeira infância"
2. Faixa etária: "Para maiores de 6 meses" ou "De 1 a 3 anos"
3. Modo de preparo: detalhado e seguro (higiene de utensílios, temperatura)
4. Tabela nutricional: por porção para a faixa etária
5. Informação sobre necessidade de aleitamento materno continuado
6. Advertência: "Este produto não substitui o leite materno"
7. Aviso para profissional de saúde: "A introdução de novos alimentos deve ser orientada por médico ou nutricionista"

ALÉRGENOS ESPECIAIS EM INFANTIS:
- Glúten: introdução gradual após 6 meses, declarar
- Amendoim: introdução precoce recomendada para prevenção de alergia — mas deve constar no rótulo
- Ovo: declarar obrigatoriamente

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- Papinha industrializada com mel para < 12 meses = NÃO CONFORME (risco de botulismo)
- Papinha com corante artificial = NÃO CONFORME
- Papinha com sódio > 200mg/100kcal = NÃO CONFORME
- Ausência de faixa etária no rótulo = NÃO CONFORME
- Ausência de modo de preparo detalhado = NÃO CONFORME
- "Substitui o leite materno" em alimento complementar = NÃO CONFORME

BASE LEGAL: RDC 222/2002, Código Internacional de Comercialização de Substitutos do Leite Materno (OMS/UNICEF), Lei 11.265/2006.""".strip()
},

{
"chave": "rdc_269_2005_vrd_criancas",
"titulo": "RDC 269/2005 — Valor de Referência de Nutrientes para Rotulagem de Alimentos Infantis",
"fonte": "RDC ANVISA 269/2005",
"orgao": "ANVISA",
"categoria": "alimentos_infantis",
"conteudo": """RDC 269/2005 — VALORES DE REFERÊNCIA DE NUTRIENTES (VRD) POR FAIXA ETÁRIA

OBJETO: Estabelece os valores de referência diários para vitaminas e minerais a serem declarados nos rótulos de alimentos especiais por faixa etária.

FAIXAS ETÁRIAS E VRD (para %VD na tabela nutricional):

LACTENTES (0-12 meses) — VRD:
Vitamina A: 375μg RE | Vitamina D: 10μg | Vitamina E: 4mg α-TE | Vitamina K: 10μg
Vitamina C: 35mg | Vitamina B1: 0,3mg | B2: 0,4mg | B3: 4mg | B5: 2mg
B6: 0,3mg | Ácido fólico: 65μg | B12: 0,5μg | Biotina: 6μg
Cálcio: 500mg | Ferro: 10mg | Magnésio: 60mg | Zinco: 4mg | Iodo: 90μg

CRIANÇAS DE 1-3 ANOS — VRD:
Vitamina A: 400μg RE | Vitamina D: 15μg | Vitamina E: 6mg α-TE | Vitamina K: 30μg
Vitamina C: 40mg | Vitamina B1: 0,5mg | B2: 0,5mg | B3: 6mg | B5: 2mg
B6: 0,5mg | Ácido fólico: 150μg | B12: 0,9μg | Biotina: 8μg
Cálcio: 700mg | Ferro: 7mg | Magnésio: 65mg | Zinco: 3mg | Iodo: 90μg

CRIANÇAS DE 4-8 ANOS — VRD:
Vitamina A: 450μg RE | Vitamina D: 15μg | Vitamina E: 7mg α-TE | Vitamina K: 55μg
Vitamina C: 45mg | Vitamina B1: 0,6mg | B2: 0,6mg | B3: 8mg | B5: 3mg
B6: 0,6mg | Ácido fólico: 200μg | B12: 1,2μg
Cálcio: 1000mg | Ferro: 10mg | Magnésio: 110mg | Zinco: 5mg | Iodo: 90μg

ADULTOS (referência geral) — VRD:
Vitamina A: 600μg RE | Vitamina D: 15μg | Vitamina E: 10mg α-TE | Vitamina K: 65μg
Vitamina C: 45mg | B1: 1,2mg | B2: 1,3mg | B3: 16mg | B5: 5mg
B6: 1,3mg | Ácido fólico: 400μg | B12: 2,4μg | Biotina: 30μg
Cálcio: 1000mg | Ferro: 14mg | Magnésio: 260mg | Zinco: 7mg | Iodo: 150μg

APLICAÇÃO NA ROTULAGEM:
Para alimentos destinados a crianças (ex: papinhas, cereais infantis, biscoitos infantis), o %VD da tabela nutricional deve usar os VRD da faixa etária correta, NÃO os valores de adulto.
Exemplo: biscoito infantil "para crianças de 1-3 anos" com 3mg de ferro/porção = 43% VD (usando VRD infantil de 7mg), não 21% VD (usando VRD adulto de 14mg).

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- Alimento infantil usando VRD de adulto na tabela nutricional = NÃO CONFORME (subdeclara ou sobredeclara o %VD)
- Alegação "rico em ferro" em alimento infantil deve usar o critério da faixa etária correta
- Faixa etária não declarada no rótulo de alimento com composição específica por faixa = NÃO CONFORME

BASE LEGAL: RDC 269/2005, RDC 222/2002, RDC 241/2018.""".strip()
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

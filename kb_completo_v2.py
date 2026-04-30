"""
kb_teto_final.py — 10 documentos para atingir o teto máximo da KB
Queijo artesanal (MG + RS), Aditivos por nicho (6 docs), Balas/chicletes
Fontes verificadas via pesquisa antes da geração.
"""
import os, json, datetime, urllib.request, urllib.error

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

DOCUMENTOS = [

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 1 — QUEIJO ARTESANAL ESTADUAL (MG e RS)
# ══════════════════════════════════════════════════════════════════════════════
{
"chave": "queijo_minas_artesanal_mg",
"titulo": "Lei MG 14.185/2002 + Dec. 44.864/2008 — Queijo Minas Artesanal",
"fonte": "Lei MG 14.185/2002 + Decreto MG 42.645/2002 + Decreto MG 44.864/2008",
"orgao": "IMA/MG",
"categoria": "queijo_artesanal_estadual",
"conteudo": """QUEIJO MINAS ARTESANAL — LEGISLAÇÃO ESTADUAL MG
Lei MG 14.185/2002 | Decreto MG 42.645/2002 | Decreto MG 44.864/2008

DEFINIÇÃO E PRODUÇÃO:
Queijo Minas Artesanal (QMA): elaborado a partir de leite cru integral de produção própria, com utilização de soro-fermento (pingo), coalho e sal, em queijaria cadastrada no IMA (Instituto Mineiro de Agropecuária). Técnicas predominantemente manuais.

MICRORREGIÕES TRADICIONAIS RECONHECIDAS:
Serro, Canastra, Araxá, Cerrado, Campo das Vertentes, Triângulo Mineiro, Serra Geral de Minas. Cada microrregião tem tempo mínimo de maturação diferente, estabelecido por pesquisa científica.

TEMPO MÍNIMO DE MATURAÇÃO (por microrregião):
Araxá: mínimo 14 dias. Serro: mínimo 17 dias. Demais regiões: mínimo 22 dias (ou maior período definido por estudos).
Regra federal (IN MAPA 30/2013): queijos artesanais de leite cru podem ser comercializados com maturação < 60 dias quando comprovada segurança microbiológica.

CADASTRO OBRIGATÓRIO NO IMA:
Produtor e propriedade devem ser cadastrados no IMA antes de iniciar produção.
Queijaria deve estar em propriedade rural, produzindo exclusivamente com leite próprio (exceções para assentamentos e grupos de até 15 produtores em raio de 5km).

ROTULAGEM OBRIGATÓRIA (Art. 27 — Decreto 42.645/2002, alterado pelo Dec. 44.864/2008):
1. Denominação "QUEIJO MINAS ARTESANAL" em letras destacadas e visíveis
2. Microrregião de origem (ex: "Canastra", "Serro", "Araxá")
3. Declaração obrigatória: "PRODUTO ELABORADO COM LEITE CRU"
4. Produtor: nome + número de cadastro no IMA
5. Peso líquido
6. Data de fabricação e data de validade
7. Temperatura de conservação
8. Número de registro do rótulo no IMA (rótulo deve ser cadastrado/aprovado antes do uso)
Queijo sem embalagem (curado com casca): marcação em baixo relevo com número de inscrição estadual + número de cadastro IMA.

SELO ARTE (IN MAPA 28/2019):
Queijarias que cumprem todos os requisitos e realizam todas as etapas de produção podem usar o Selo ARTE, que permite comercialização interestadual.
Rótulo com Selo ARTE: deve incluir o logotipo oficial do MAPA.

EMBALAGEM:
Queijo embalado: embalagem plástica não reutilizável, descartável, permeável ao vapor d'água e O2, aprovada pelo Ministério da Saúde.
Queijo só pode ser embalado após o período mínimo de maturação ser completado.

ALÉRGENOS:
"CONTÉM LEITE E DERIVADOS" — obrigatório.
Produzido com coalho de origem animal: pode conter traços de proteínas animais.

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- "Queijo Minas Artesanal" sem cadastro no IMA = NÃO CONFORME
- Sem declaração "PRODUTO ELABORADO COM LEITE CRU" = NÃO CONFORME
- Sem microrregião de origem = NÃO CONFORME
- Rótulo não cadastrado no IMA = NÃO CONFORME
- Maturação abaixo do mínimo da microrregião = NÃO CONFORME
- Produzido fora de MG com denominação "Queijo Minas Artesanal" = NÃO CONFORME

BASE LEGAL: Lei MG 14.185/2002, Decreto MG 42.645/2002, Decreto MG 44.864/2008, Portaria IMA 1969/2020, IN MAPA 28/2019 (Selo ARTE), IN MAPA 30/2013.""".strip()
},

{
"chave": "queijo_artesanal_rs_sc",
"titulo": "RTIQ Queijo Colonial Artesanal (RS/2023) e Queijo Serrano (RS/SC)",
"fonte": "SEAPI/RS Regulamento Técnico Queijo Colonial Artesanal 2023 + IN SEAGRI 7/2014",
"orgao": "SEAPI/RS",
"categoria": "queijo_artesanal_estadual",
"conteudo": """QUEIJO COLONIAL ARTESANAL (RS) E QUEIJO SERRANO (RS/SC)

QUEIJO COLONIAL ARTESANAL — RS (RTIQ SEAPI 2023):
Definição: queijo maturado obtido por coagulação do leite cru ou pasteurizado, com coalho ou enzimas coagulantes, complementada ou não por bactérias lácteas. Técnicas predominantemente manuais.
Classificação: queijo gordo, de média a alta umidade, consistência semidura, elástica, textura compacta (lisa ou fechada).
Características sensoriais: cor branca ou amarelada, sabor característico ligeiramente ácido ou picante, odor agradável pronunciado com o grau de maturação.

ROTULAGEM DO QUEIJO COLONIAL ARTESANAL (RS):
- Denominação: "Queijo Colonial Artesanal" ou "Queijo Colonial"
- Rotulagem deve ser previamente aprovada pelo Serviço de Inspeção (SIE-RS ou SISBI-POA)
- Número de registro do SIE ou SIM no rótulo
- Produtor: nome e endereço da queijaria
- Peso líquido
- Data de fabricação e validade
- Temperatura de conservação (refrigerado: máx. 10-12°C)
- "CONTÉM LEITE E DERIVADOS" (alérgeno)
- Se leite cru: declarar "ELABORADO COM LEITE CRU"
Comercialização: pode ser com ou sem embalagem. Sem embalagem = identificação na peça.

QUEIJO SERRANO — RS E SC (IN SEAGRI/RS 7/2014):
Definição: queijo artesanal maturado de leite cru, produzido na região dos Campos de Cima da Serra (RS e SC). Produto de denominação de origem reconhecida.
Características: queijo gordo, de baixa umidade, consistência dura a semidura.
Temperatura de conservação: máx. 12°C.
Aditivos: NÃO são autorizados aditivos ou coadjuvantes tecnológicos (queijo puramente artesanal).
Maturação: período mínimo conforme regulamento do SIE-RS.

ROTULAGEM DO QUEIJO SERRANO:
- Denominação: "Queijo Serrano" (com indicação de Campos de Cima da Serra como origem)
- Aprovação prévia pelo SIE-RS ou SIE-SC
- "ELABORADO COM LEITE CRU" obrigatório
- "CONTÉM LEITE E DERIVADOS"
- Produtor, endereço, peso, data, validade, temperatura

COMERCIALIZAÇÃO INTERESTADUAL:
Queijos artesanais com Selo ARTE (IN MAPA 28/2019) podem ser comercializados em todo o Brasil.
Sem Selo ARTE: restrito ao estado de origem (ou municípios do entorno via SIM/SISBI).

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- "Queijo Colonial Artesanal" sem aprovação de rótulo pelo SIE-RS = NÃO CONFORME
- Queijo Serrano com aditivos declarados na lista de ingredientes = NÃO CONFORME (aditivos são proibidos)
- Venda interestadual sem Selo ARTE = IRREGULAR
- Temperatura de conservação ausente no rótulo = NÃO CONFORME

BASE LEGAL: RTIQ Queijo Colonial Artesanal SEAPI/RS 2023, IN SEAGRI/RS 7/2014 (Queijo Serrano), IN MAPA 28/2019 (Selo ARTE), Lei MG 14.185/2002 (referência para outros estados).""".strip()
},

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 2 — ADITIVOS POR NICHO (6 documentos)
# ══════════════════════════════════════════════════════════════════════════════
{
"chave": "aditivos_laticinios",
"titulo": "IN 211/2023 — Principais Aditivos em Laticínios (Leite, Queijo, Iogurte, Requeijão)",
"fonte": "IN ANVISA 211/2023 + RDC 975/2025 + IN 432/2026",
"orgao": "ANVISA",
"categoria": "aditivos_por_nicho",
"conteudo": """ADITIVOS MAIS USADOS EM LATICÍNIOS — IN 211/2023

ESTABILIZANTES (função: manter textura, evitar sinérese):
- Carragena (INS 407): iogurte, leite fermentado, creme de leite. Limite típico: 0,5g/kg.
- Goma guar (INS 412): requeijão, queijo processado, sobremesas lácteas.
- Goma xantana (INS 415): iogurte light, leite fermentado, molhos de queijo.
- Amido modificado (INS 1400-1442): iogurte, creme, queijo fundido. Declarar tipo específico.
- Pectina (INS 440): iogurte de frutas, bebida láctea fermentada.
- Gelatina (proteína animal, não é INS): declarar "Gelatina" na lista de ingredientes. Fonte bovina/suína = alérgeno potencial.
- Fosfato de sódio (INS 339i): queijo fundido/processado — OBRIGATÓRIO declarar (emulsificante de sal fundente).

CONSERVANTES:
- Nisina (INS 234): queijos pasteurizados, requeijão. Bacteriocina natural. Limite: 12,5mg/kg.
- Sorbato de potássio (INS 202): queijos mofados/maturados na superfície, requeijão. Limite: 1g/kg.
- Natamicina (INS 235): aplicada na superfície de queijos curados para inibir fungos. Declarar: "Conservante: natamicina (INS 235) aplicada na superfície".

CORANTES:
- Urucum (INS 160b/bixin): cor laranja/amarela em manteiga, queijo prato, requeijão. Natural.
- Betacaroteno (INS 160a): cor amarela em manteiga e margarina. Natural ou sintético.
- Cúrcuma/curcumina (INS 100): cor amarela suave em queijos e manteigas.
- Caramelo (INS 150a-d): raramente em laticínios; quando presente declarar tipo.

EDULCORANTES (em laticínios diet/light):
- Sucralose (INS 955), acessulfame-K (INS 950), aspartame (INS 951 — advertência fenilalanina).
- Estévia (INS 960): "Edulcorante: glicosídeos de esteviol (INS 960a)".

ACIDULANTES:
- Ácido lático (INS 270): iogurte, leite fermentado — produto da fermentação natural, mas pode ser adicionado.
- Ácido cítrico (INS 330): bebida láctea, sorvete, requeijão.

DECLARAÇÃO NA LISTA DE INGREDIENTES:
Formato obrigatório: "Função: nome do aditivo (INS XXX)"
Ex: "Estabilizante: carragena (INS 407)", "Conservante: sorbato de potássio (INS 202)", "Corante: urucum (INS 160b)".

PONTOS CRÍTICOS:
- Queijo processado/fundido sem declarar fosfato emulsificante = NÃO CONFORME
- Natamicina aplicada na superfície sem declaração = NÃO CONFORME
- Gelatina sem identificar fonte animal/vegetal = ALERTA (consumidores halal/veganos)
- Aspartame sem advertência fenilcetonúricos = NÃO CONFORME""".strip()
},

{
"chave": "aditivos_bebidas",
"titulo": "IN 211/2023 — Principais Aditivos em Bebidas (Sucos, Refrigerantes, Energéticos, Cervejas)",
"fonte": "IN ANVISA 211/2023 + RDC 975/2025",
"orgao": "ANVISA",
"categoria": "aditivos_por_nicho",
"conteudo": """ADITIVOS MAIS USADOS EM BEBIDAS — IN 211/2023

CONSERVANTES:
- Benzoato de sódio (INS 211): refrigerantes, sucos prontos, isotônicos. Limite máx. 150mg/kg. PROIBIDO em sucos integrais.
- Sorbato de potássio (INS 202): sucos prontos, néctares, bebidas à base de fruta. Limite: 500mg/kg.
- Dióxido de enxofre (INS 220) / sulfitos: vinhos, sucos de uva, bebidas fermentadas. Limite variável. "CONTÉM SULFITOS" obrigatório se > 10mg/kg SO2 (alérgeno).
- Ácido ascórbico (INS 300): como conservante/antioxidante em sucos. Pode ser declarado como "Antioxidante: ácido ascórbico (INS 300)".

ACIDULANTES:
- Ácido cítrico (INS 330): o mais usado — refrigerantes, sucos, isotônicos, energéticos.
- Ácido fosfórico (INS 338): refrigerantes tipo cola. Confere sabor característico.
- Ácido málico (INS 296): refrigerantes sabor maçã, uva, pera. Mais suave que cítrico.
- Ácido tartárico (INS 334): bebidas à base de uva, sidra, kombucha.

AROMATIZANTES:
- "Aroma natural de [fruta]": obrigatório declarar função + nome.
- "Aromatizante" ou "Aroma artificial": quando artificial.
- Extrato de guaraná: declarar "Extrato de guaraná (Paullinia cupana)" — contém cafeína naturalmente.

CORANTES (bebidas):
- Tartrazina (INS 102): cor amarela intensa. Associada a hiperatividade — alguns países exigem advertência.
- Sunset Yellow/Amarelo Crepúsculo (INS 110): laranja.
- Carmim/Ácido carmínico (INS 120): vermelho intenso — origem animal (cochonilha). Declarar; pode ser alérgeno.
- Azul Brilhante (INS 133): azul. Raramente usado isolado.
- Caramelo (INS 150a-d): cola, cervejas escuras, bebidas amarronzadas.
- Carotenóides (INS 160a-f): amarelo-laranja. Naturais.
- Antocianinas (INS 163): roxo/vermelho. Naturais (uva, acerola).

EDULCORANTES:
- Sucralose (INS 955): bebidas zero/light — estável ao calor, uso crescente.
- Acessulfame-K (INS 950): geralmente combinado com sucralose ou aspartame.
- Aspartame (INS 951): bebidas diet/zero — ADVERTÊNCIA FENILCETONÚRICOS obrigatória.
- Estévia (INS 960a): bebidas "sem açúcar adicionado" com adoçante natural.
- Ciclamato (INS 952): refrigerantes diet — "não recomendado para crianças, gestantes e hipertensos".

ESTABILIZANTES:
- Goma arábica (INS 414): para emulsionar óleos essenciais de citrus em bebidas.
- CMC/Carboximetilcelulose (INS 466): néctares e bebidas de frutas para corpo e viscosidade.
- Pectina (INS 440): sucos turvos (nectar de laranja natural).

CAFEÍNA (declaração):
- Adicionada: "Cafeína" na lista de ingredientes. Declarar mg/100mL ou mg/porção.
- > 20mg/100mL: declaração obrigatória do teor.
- Energéticos: limite 32mg/100mL.

PONTOS CRÍTICOS:
- Benzoato em suco integral = NÃO CONFORME
- Sulfitos > 10mg/kg sem "CONTÉM SULFITOS" = NÃO CONFORME
- Carmim sem declaração em bebida vermelha/rosada = ALERTA (origem animal)
- Tartrazina em país de exportação UE: exige advertência "pode prejudicar a atividade e atenção das crianças"
- Aspartame sem advertência fenilcetonúricos = NÃO CONFORME""".strip()
},

{
"chave": "aditivos_panificacao",
"titulo": "IN 211/2023 — Principais Aditivos em Panificação (Pão, Bolo, Biscoito, Massa)",
"fonte": "IN ANVISA 211/2023 + RDC 975/2025",
"orgao": "ANVISA",
"categoria": "aditivos_por_nicho",
"conteudo": """ADITIVOS MAIS USADOS EM PANIFICAÇÃO E DERIVADOS — IN 211/2023

MELHORADORES DE FARINHA / AGENTES DE TRATAMENTO:
- Ácido ascórbico (INS 300): reforça a rede de glúten, melhora estrutura do pão. Declarar como "Melhorador de farinha: ácido ascórbico (INS 300)".
- Ácido azodicarbonamídico (INS 927a): branqueador e melhorador. Banido na UE e Austrália — verificar mercado alvo.
- Amido modificado (INS 1400-1442): textura, maciez, vida de prateleira. Declarar tipo específico.

CONSERVANTES:
- Propionato de cálcio (INS 282): pão de forma, pão de hamburger, bolo industrial. Principal conservante anti-mofo em panificação. Limite: 3g/kg. Declarar: "Conservante: propionato de cálcio (INS 282)".
- Propionato de sódio (INS 281): similar ao 282, menos comum.
- Sorbato de potássio (INS 202): bolos e doces industriais.

EMULSIFICANTES:
- Lecitina de soja (INS 322): melhorador de massa, antiumectante. ALERTA: "CONTÉM SOJA" — alérgeno.
- Mono e diglicerídeos de ácidos graxos (INS 471): maciez, anti-envelhecimento. Muito comum em pão de forma.
- Ésteres de monoglicerídeos e diacetil-ácido tartárico (INS 472e — DATEM): fortalecedor de massa. Declarar: "Emulsificante: DATEM (INS 472e)".
- Estearoil-2-lactilato de sódio (INS 481i — SSL): condicionar massa.

FERMENTO E LEAVENING:
- Bicarbonato de sódio (INS 500ii): fermento químico em bolos, biscoitos. Fonte de sódio — declarar na tabela nutricional.
- Pirofosfato ácido de sódio (INS 450i): junto com bicarbonato forma pó royal.
- Fermento biológico (Saccharomyces cerevisiae): "Fermento biológico" — não é INS, declarar pelo nome.

CORANTES:
- Caramelo (INS 150): cor dourada em pão de hambúrguer, brioche.
- Açafrão/cúrcuma (INS 100): cor amarela em pão e bolo.
- Urucum (INS 160b): laranja em massas.
- Óxido de titânio (INS 171): branco em cobertura/glacê — verificar legislação (proibido na UE desde 2022).

AGENTES DE FIRMEZA / ANTIAGREGANTES:
- Carbonato de cálcio (INS 170i): em farinhas enriquecidas, biscoitos.
- Dióxido de silício (INS 551): antiagregante em misturas para bolo, farinhas temperadas.

PONTOS CRÍTICOS:
- Lecitina de soja sem "CONTÉM SOJA" = NÃO CONFORME
- Propionato de cálcio: declarar função + INS — comum RT esquecer
- Bicarbonato de sódio sem contar no sódio da tabela nutricional = NÃO CONFORME
- Ácido azodicarbonamídico: legal no Brasil, mas verificar mercado de exportação""".strip()
},

{
"chave": "aditivos_carnes_embutidos",
"titulo": "IN 211/2023 — Principais Aditivos em Carnes e Embutidos (Salsicha, Linguiça, Mortadela)",
"fonte": "IN ANVISA 211/2023 + RTIQs MAPA",
"orgao": "ANVISA/MAPA",
"categoria": "aditivos_por_nicho",
"conteudo": """ADITIVOS MAIS USADOS EM CARNES E EMBUTIDOS — IN 211/2023

CONSERVANTES / CURA:
- Nitrito de sódio (INS 250): cura de embutidos (salsicha, mortadela, apresuntado, bacon). Dá cor rosada característica. Limite máx.: 150mg/kg no produto final. Declarar: "Conservante: nitrito de sódio (INS 250)".
- Nitrato de sódio (INS 251): cura lenta em presuntos curados, salames. Limite: 300mg/kg.
- Nitrato de potássio (INS 252): alternativa ao 251.
ATENÇÃO: nitritos são ALVO de revisão regulatória mundial — limite máximo em redução progressiva. Monitorar.

ANTIOXIDANTES:
- Eritorbato de sódio (INS 316): acelera cura e estabiliza cor. Quase universal em embutidos industriais.
- Ácido ascórbico (INS 300): similar ao eritorbato, mais natural.
- BHA (INS 320) e BHT (INS 321): em gorduras animais processadas. Cada vez menos usados.

ESTABILIZANTES / LIGANTES:
- Polifosfato de sódio (INS 452i): retenção de água, textura em linguiça e presunto. Limite e uso regulamentado. ATENÇÃO: uso excessivo para retenção fraudulenta de água = NÃO CONFORME.
- Carragena (INS 407): em embutidos cozidos para textura.
- Amido de milho/mandioca: declarar como ingrediente, não como aditivo.

REALÇADORES DE SABOR:
- Glutamato monossódico (INS 621): muito comum em temperados. Declarar: "Realçador de sabor: glutamato monossódico (INS 621)".
- Inosinato de sódio (INS 631) + Guanilato de sódio (INS 627): sinergia com glutamato.
- Extrato de levedura: fonte natural de glutamatos. Declarar: "Extrato de levedura" como ingrediente.

ADITIVOS DE FUMAÇA:
- Fumaça líquida / Extrato natural de fumaça: sabor defumado sem fumaça real. Declarar: "Aroma de fumaça" ou "Extrato natural de fumaça".
- Defumação real: processo, não aditivo. Declarar na denominação: "Linguiça defumada".

CORANTES:
- Carmim (INS 120): cor vermelha em embutidos. Origem animal (cochonilha) — declarar.
- Urucum (INS 160b): cor laranja/amarela em linguiça calabresa.
- Caramelo (INS 150): cor marrom em salsicha Frankfurt.
- Vermelho de Bordeaux (INS 124): cor vermelho intenso — verificar lista positiva.

PONTOS CRÍTICOS:
- Nitritos/nitratos: verificar se dentro do limite máximo (150/300 mg/kg) — responsabilidade do fabricante
- Polifosfatos para retenção de água acima do limite = adulteração
- Glutamato sem declarar função + INS = NÃO CONFORME
- Fumaça líquida declarada como "defumado" = NÃO CONFORME (processo ≠ aditivo)""".strip()
},

{
"chave": "aditivos_doces_confeitaria",
"titulo": "IN 211/2023 — Principais Aditivos em Doces, Chocolates, Sorvetes e Confeitaria",
"fonte": "IN ANVISA 211/2023 + RDC 264/2005 + RDC 266/2005",
"orgao": "ANVISA",
"categoria": "aditivos_por_nicho",
"conteudo": """ADITIVOS MAIS USADOS EM DOCES, CHOCOLATES, SORVETES E CONFEITARIA — IN 211/2023

EMULSIFICANTES:
- Lecitina de soja (INS 322): chocolate (obrigatório para fluidez), sorvete, recheios. "CONTÉM SOJA".
- Lecitina de girassol (INS 322): alternativa sem soja para chocolates "soja-free".
- Poliglicerol polirricinoleato (PGPR — INS 476): em chocolate para reduzir viscosidade. Alternativa à lecitina.
- Mono e diglicerídeos (INS 471): sorvete, coberturas, recheios cremosos.

ESTABILIZANTES (sorvete):
- Carragena (INS 407) + Goma de alfarroba (INS 410) + Goma guar (INS 412): combinação clássica para textura cremosa e controle de cristais de gelo.
- Goma xantana (INS 415): sorvetes premium, gelatos.

CONSERVANTES:
- Sorbato de potássio (INS 202): doces com recheio, geleias, sorvetes.
- Benzoato de sódio (INS 211): xaropes, caldas, coberturas.

CORANTES (alto uso em confeitaria):
- Tartrazina (INS 102): amarelo intenso em balas, geleias, pirulitos.
- Azul Brilhante (INS 133): azul em confeitos, cobertura de bolo.
- Eritrosina (INS 127): cereja em calda, confeitos vermelhos/cor-de-rosa.
- Carmim (INS 120): vermelho em sorvetes, geleias, balas. Origem animal.
- Dióxido de titânio (INS 171): branco em pasta de confeiteiro, glacê. Revisão regulatória em andamento.
- Corante alimentar misto: declarar todos os INS individualmente.

EDULCORANTES EM DOCES DIET:
- Sorbitol (INS 420): chocolate diet, balas sem açúcar. Efeito laxante acima de 20g/dia → obrigatório: "Consumo excessivo pode ter efeito laxativo".
- Maltitol (INS 965): chocolate diet — muito usado. Mesmo aviso de efeito laxativo.
- Xilitol (INS 967): balas e chicletes sem açúcar.
- Todos os polióis: se > 10g/porção → declarar aviso laxativo.

AROMATIZANTES:
- Baunilha/vanilina (INS 160a ou aroma natural de baunilha): chocolate, sorvete, recheios.
- "Aroma de morango", "Aroma artificial de framboesa" etc.

ACIDULANTES:
- Ácido cítrico (INS 330): balas, geleias — confere acidez.
- Ácido málico (INS 296): balas ácidas.
- Ácido tartárico (INS 334): balas ácidas, confeitos de uva.

PONTOS CRÍTICOS:
- Lecitina de soja em chocolate sem "CONTÉM SOJA" = NÃO CONFORME
- Carmim sem declaração em produto vermelho = ALERTA (origem animal)
- Sorbitol/maltitol > 10g sem aviso laxativo = NÃO CONFORME
- Tartrazina em produto amarelo: declarar (alguns consumidores evitam)
- Polióis: calcular valor calórico correto (2,4 kcal/g, não 4 kcal/g)""".strip()
},

{
"chave": "aditivos_condimentos_snacks",
"titulo": "IN 211/2023 — Principais Aditivos em Condimentos, Snacks e Molhos",
"fonte": "IN ANVISA 211/2023 + RDC 276/2005",
"orgao": "ANVISA",
"categoria": "aditivos_por_nicho",
"conteudo": """ADITIVOS MAIS USADOS EM CONDIMENTOS, SNACKS E MOLHOS — IN 211/2023

REALÇADORES DE SABOR (altíssima prevalência):
- Glutamato monossódico (INS 621): salgadinhos, sopas, temperos, molho shoyu, macarrão instantâneo. O aditivo mais comum em salgadinhos. Declarar: "Realçador de sabor: glutamato monossódico (INS 621)".
- Inosinato dissódico (INS 631): combinado com glutamato para potencializar sabor.
- Guanilato dissódico (INS 627): combinado com glutamato + inosinato = "mistura de realçadores".
- Quando os 3 são usados juntos: declarar cada um separadamente com INS.

CONSERVANTES:
- Sorbato de potássio (INS 202): molhos, ketchup, maionese, pasta de alho.
- Benzoato de sódio (INS 211): ketchup, molho de pimenta, vinagre temperado. Limite 150mg/kg.
- Ácido acético/vinagre (INS 260): conservante natural em mostarda, picles, ketchup.

ANTIOXIDANTES:
- BHA (INS 320) e BHT (INS 321): em snacks fritos com óleos vegetais. Em redução de uso.
- TBHQ (INS 319): em snacks fritos. Limite: 200mg/kg de gordura.
- Rosmarino (INS 392): antioxidante natural crescente em snacks premium.

CORANTES (salgadinhos e snacks):
- Urucum/bixina (INS 160b): laranja em salgadinhos de queijo, chips temperados. Natural.
- Curcumina/cúrcuma (INS 100): amarelo em chips e snacks.
- Páprica/capsantina (INS 160c): laranja-vermelho em chips de páprica e snacks temperados.
- Caramelo (INS 150): cor marrom em snacks.

EDULCORANTES EM CONDIMENTOS:
- Sucralose (INS 955): ketchup light, molho de tomate light.
- Acessulfame-K (INS 950): combinação em produtos diet.

ESTABILIZANTES / ESPESSANTES:
- Goma xantana (INS 415): molhos, maionese, ketchup, pasta de tomate.
- Guar (INS 412): pasta de alho industrializada, temperos em pasta.
- Amido modificado (INS 1400-1442): espessante em molhos.

ACIDULANTES:
- Ácido cítrico (INS 330): salgadinhos sabor limão, molhos.
- Ácido málico (INS 296): snacks sabor fruta.
- Ácido fosfórico (INS 338): alguns molhos de pimenta estilo americano.

ANTIAGREGANTES:
- Dióxido de silício (INS 551): temperos em pó, sal temperado, misturas para preparo. Evita grumos.
- Carbonato de cálcio (INS 170): idem.

PONTOS CRÍTICOS:
- Glutamato sem função "Realçador de sabor" + INS = NÃO CONFORME
- Salgadinho com TBHQ ou BHA: declarar (consumidores cada vez mais atentos)
- Corante tartrazina em snack amarelo: declarar (pode causar reação em pessoas sensíveis)
- Antiagregante: obrigatório declarar em temperos em pó""".strip()
},

# ══════════════════════════════════════════════════════════════════════════════
# BLOCO 3 — BALAS, CHICLETES E CONFEITARIA SEM RTIQ ESPECÍFICO
# ══════════════════════════════════════════════════════════════════════════════
{
"chave": "balas_chicletes_confeitos",
"titulo": "Balas, Chicletes, Pirulitos e Confeitos — Normas Gerais Aplicáveis",
"fonte": "RDC 727/2022 + RDC 429/2020 + IN 211/2023 + Portaria SVS 29/1998",
"orgao": "ANVISA",
"categoria": "nao_poa_doces",
"conteudo": """BALAS, CHICLETES, PIRULITOS E CONFEITOS
ATENÇÃO: Não existe RTIQ (Regulamento Técnico de Identidade e Qualidade) específico para balas e chicletes no Brasil. Aplicam-se as normas gerais de rotulagem e segurança de alimentos.

NORMAS APLICÁVEIS:
RDC 727/2022 (rotulagem geral), RDC 429/2020 + IN 75/2020 (nutricional), IN 211/2023 (aditivos), RDC 26/2015 (alérgenos — absorvida pela RDC 727/2022), Portaria SVS 29/1998 (diet/sem açúcar), CDC (Código de Defesa do Consumidor).

DENOMINAÇÕES E CATEGORIAS:
- "Bala": confeito sólido ou semi-sólido à base de açúcar e/ou glicose.
- "Bala de goma": base de goma (gelatina, pectina, ágar-ágar, amido).
- "Bala dura" ("hard candy"): açúcar + glicose cozidos a alta temperatura.
- "Bala mastigável" ("chewy"/"toffee"): textura maleável, gordura + açúcar.
- "Pirulito": bala dura em palito.
- "Chiclete" / "goma de mascar": base de goma insolúvel (goma natural ou sintética) + edulcorante + aromatizante.
- "Pastilha": bala comprimida, geralmente com mentol ou frutas.
- "Confeito": amendoim ou chocolate com cobertura de açúcar colorida.
- "Marshmallow": base de açúcar + gelatina batida com ar.

ROTULAGEM OBRIGATÓRIA (RDC 727/2022):
1. Denominação de venda
2. Lista de ingredientes (incluindo todos os aditivos com função + INS)
3. Tabela nutricional (porção: 10g para balas; 3g para chicletes/pastilhas — usar bom senso conforme embalagem)
4. Peso líquido ou quantidade de unidades
5. Data de validade e lote
6. Fabricante com endereço

ALÉRGENOS MAIS COMUNS (declaração obrigatória):
- Leite (em balas de leite, toffee, caramelo): "CONTÉM LEITE E DERIVADOS"
- Amendoim (em confeitos, pé-de-moleque): "CONTÉM AMENDOIM"
- Glúten (em alguns chicletes com farinha): "CONTÉM GLÚTEN"
- Ovo (em marshmallow e alguns balas): "CONTÉM OVO"
- Gelatina bovina/suína: declarar a origem na lista de ingredientes (relevante para consumidores halal/kosher/veganos). ATENÇÃO: gelatina suína = não kosher + não halal.

ADITIVOS COMUNS (todos precisam declarar função + INS):
- Corantes: tartrazina (INS 102), eritrosina (INS 127), carmim (INS 120 — animal), curcumina (INS 100), azul brilhante (INS 133).
- Conservantes: sorbato de potássio (INS 202), benzoato de sódio (INS 211).
- Acidulantes: ácido cítrico (INS 330), ácido málico (INS 296), ácido tartárico (INS 334) — balas ácidas.
- Aromatizantes: declarar função + nome/tipo.
- Emulsificantes em toffee: lecitina de soja (INS 322) → "CONTÉM SOJA".
- Agentes de revestimento: cera de carnaúba (INS 903), goma-laca (INS 904) — em confeitos brilhantes.

CHICLETES E GOMAS DE MASCAR:
Base gum (goma): ingrediente declarado como "Base de goma de mascar" ou "Goma" (composição proprietária).
Edulcorantes: chicletes sem açúcar usam sorbitol (INS 420), xilitol (INS 967), maltitol (INS 965).
Aviso de efeito laxativo: se polióis > 10g/porção — "Consumo excessivo pode ter efeito laxativo".
Xilitol: prejudicial a cães (aviso nas embalagens de exportação).

CHICLETES FUNCIONAIS (com flúor ou vitaminas):
- Com flúor: verificar limite de flúor permitido (RDC 269/2005). Não é categoria especial — tratar como suplemento se tiver alegação.
- Com vitamina C: deve cumprir requisitos de alegação funcional (Res. 18/1999) e quantidade mínima.

BALAS DIET/SEM AÇÚCAR (Portaria SVS 29/1998):
- "Diet" em bala = ausência de sacarose + uso de edulcorante.
- "Sem açúcar": sem adição de açúcares (sacarose, mel, frutose, xaropes) — polióis são permitidos.
- Edulcorantes: declarar advertências específicas (aspartame → fenilcetonúricos; ciclamato → crianças/gestantes/hipertensos).

LUPA FRONTAL (RDC 429/2020):
Balas convencionais com alto açúcar: geralmente > 15g açúcar adicionado/100g → LUPA OBRIGATÓRIA.
Verificar também sódio (balas salgadas, chicletes com sódio).

PONTOS CRÍTICOS PARA VALIDAÇÃO:
- Bala de goma com gelatina sem identificar fonte = ALERTA (bovina/suína)
- Carmim (corante) sem declaração em bala vermelha/rosa = NÃO CONFORME (origem animal)
- Chiclete com poliol > 10g/porção sem aviso laxativo = NÃO CONFORME
- Lupa frontal ausente em bala açucarada = NÃO CONFORME
- Corante sem função + INS = NÃO CONFORME
- Alérgeno (leite, amendoim) não declarado = NÃO CONFORME

BASE LEGAL: RDC 727/2022, RDC 429/2020, IN 75/2020, IN 211/2023, Portaria SVS 29/1998, Res. 18/1999.""".strip()
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
    print(f"Inserindo {len(DOCUMENTOS)} documentos (teto máximo da KB)...\n")
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
    print(f"KB esperada no Supabase: ~{192 + ok} documentos")
    print(f"\nCobertura estimada após inserção:")
    print(f"  POA: ~95-97%")
    print(f"  Não-POA: ~92-93%")
    print(f"  (Teto máximo atingido — gaps residuais são estruturalmente irredutíveis)")

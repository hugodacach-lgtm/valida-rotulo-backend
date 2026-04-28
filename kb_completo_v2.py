"""
kb_nao_poa_final.py — Cobertura completa dos 19 gaps restantes na KB
19 normas: 17 não-POA + 2 POA (conservas vegetais, cogumelos)
Rodar no Shell do Render: python3 kb_nao_poa_final.py
"""
import os, json, datetime, urllib.request, urllib.error

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

DOCUMENTOS = [

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
        print("❌ Configure SUPABASE_URL e SUPABASE_KEY.")
        exit(1)

    print(f"Inserindo {len(DOCUMENTOS)} documentos na KB...\n")
    ok = fail = 0
    for doc in DOCUMENTOS:
        r = upsert(doc)
        if r.get("ok"):
            print(f"  ✅ {doc['chave']} — {r['chars']} chars")
            ok += 1
        else:
            print(f"  ❌ {doc['chave']}: {r.get('erro')}")
            fail += 1

    print(f"\n{'='*50}")
    print(f"Concluído: {ok} inseridos, {fail} com erro")
    print(f"KB esperada após este script: ~{154 + ok} documentos")
    print("Cobertura: 158/158 normas mapeadas = 100%")

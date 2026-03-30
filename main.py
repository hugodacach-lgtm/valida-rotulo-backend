import os, base64, json, io, asyncio, re
try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
import httpx
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ValidaRótulo IA v6 — KB Expandida POA")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE — URLs dos PDFs oficiais MAPA/ANVISA/INMETRO
# 50 categorias cobrindo toda a cadeia POA
# ═══════════════════════════════════════════════════════════════════════════════
MAPA_URLS = {
    # ── CARNES E EMBUTIDOS ────────────────────────────────────────────────
    "embutidos":          ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN042000salsichamortadelalinguia.pdf"],
    "salame":             ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN222000RTsalamesalaminhocopaprescrupresparmalingcolpepperoni.pdf"],
    "presunto":           ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7652023RTIQpresunto.pdf"],
    "hamburguer":         ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7242022RThamburguer1.pdf"],
    "bacon":              ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/copy_of_Port7482023RTbacon.pdf"],
    "carne_moida":        ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port6642022RTIQcarnemoda1.pdf"],
    "charque":            ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN922020RTCharqueCarneSalgadaMidoSalgado.pdf"],
    "fiambre":            ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7062022RTIQfiambre.pdf"],
    "carne_maturada":     ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7232022RTcarnematuradabovino.pdf"],
    "carnes_temperadas":  ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN172018RTcrneostemperados.pdf"],
    "almondega_kibe":     ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN202000RTcrneosalmondegakibe.pdf"],
    "gelatina_colageno":  ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port3842021Gelatinagelatinahidrolisadaecolgeno.pdf"],
    "corned_beef":        ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN832003RTcornedbeefbovinoconserva.pdf"],
    "paleta_salgada":     ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN62001RTcarneospaletasalgadosempanadospresserranopratopronto.pdf"],

    # ── LATICÍNIOS ────────────────────────────────────────────────────────
    "laticinios_geral":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port1461996RTqueijomanteigacremedeleitegorduralctealeitefluido.pdf"],
    "queijo_coalho_manteiga": ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN302001RTmanteigatemaoumanteigadegarrafaqueijodecoalhoequeijodemanteiga.pdf"],
    "mussarela":              ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port3661997RTMassaqueijomussarela.pdf"],
    "requeijao":              ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port3591997RTrequeijaoouqueijofundido.pdf"],
    "leite_uht":              ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port3701997RTleiteUHTUAT.pdf"],
    "leite_pasteurizado":     ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN762018RTleitecrurefrleitepasteuhomogleitefluido.pdf"],
    "leite_fermentado":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN462007RTleitesfermentados.pdf"],
    "doce_de_leite":          ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port3541997RTdocedeleite.pdf"],
    "soro_de_leite":          ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN942020RTSorodeleite.pdf"],
    "queijo_prato":           ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port3581997RTQueijoprato.pdf"],
    "queijo_processado":      ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port3561997RTQueijoprocessado.pdf"],

    # ── PESCADO ───────────────────────────────────────────────────────────
    "pescado_fresco":         ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port1851997RTpeixefresco.pdf"],
    "pescado_congelado":      ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN212017RTpeixecongelado.pdf"],
    "pescado_salgado":        ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN012019RTpeixesalgadopeixesalgadoseco.pdf"],
    "camarao":                ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN232019RTcamaraofrescoresfcongeladodescongelado.pdf"],
    "lagosta":                ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN242019RTlagostafrescacongelada.pdf"],
    "moluscos_cefalopodes":   ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port10222024RTmoluscocefal%C3%B3pode.pdf"],
    "conserva_sardinha":      ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN222011RTconservassardinhas.pdf"],
    "conserva_atum":          ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN462011RTconservasatuns.pdf"],
    "conserva_peixe":         ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN452011RTconservaspeixe.pdf"],

    # ── MEL E APÍCOLA ─────────────────────────────────────────────────────
    "mel":                    ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7952023RTIQmel.pdf"],

    # ── OVOS ──────────────────────────────────────────────────────────────
    "ovos":                   ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port012020RTovosdemesadeovosparasementeovoscaipiras.pdf"],
    "ovos_derivados":         ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7282022RTovointegralpasteurizadodesidratado.pdf"],

    # ── LATICÍNIOS EXTRAS ────────────────────────────────────────────────
    "leite_em_po":            ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN532018RTleiteempoMercosul.pdf"],
    "leite_condensado":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN472018RTleitecondensado.pdf"],
    "nata":                   ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN232012RTnata.pdf"],
    "queijo_provolone":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN732020RTqueijoprovolone.pdf"],
    "queijo_parmesao":        ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port3531997RTqueijoparmesao.pdf"],

    # ── NORMAS ANVISA NA KB ──────────────────────────────────────────────
    "alergenos_rdc727":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/rdc727_rotulagem%20geral.pdf"],
    "nutricional_in75":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/INSTRU%C3%87%C3%83O%20NORMATIVA-IN%20N%C2%BA%2075%2C%20DE%208%20DE%20OUTUBRO%20DE%202020%20-%20INSTRU%C3%87%C3%83O%20NORMATIVA-IN%20N%C2%BA%2075%2C%20DE%208%20DE%20OUTUBRO%20DE%202020%20-%20DOU%20-%20Imprensa%20Nacional.pdf"],
    "aditivos_rdc778":        ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/RDC%20778%20-%20Aditivos%20alimentares%20%28geral%29.pdf"],

    # ── NORMAS GERAIS ─────────────────────────────────────────────────────
    "rotulagem_geral":        [
        "https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN222005Regulamentortuloregistroproduto.pdf",
        "https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port2402021AlteraIN222005rotulagem.pdf",
        "https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port4492022AlteraIN222005rotulagem.pdf",
    ],
    "nomenclatura":           ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port14852025PadrocategoriaenomeclaturaPOA.pdf"],

    # ── CÁRNEOS ADICIONAIS ─────────────────────────────────────────────────
    "apresuntado":            ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7012022RTIQapresuntado.pdf"],
    "paleta_empanados":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN62001RTcarneospaletasalgadosempanadospresserranopratopronto.pdf"],
    "corned_beef":            ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN832003RTcornedbeefbovinoconserva.pdf"],

    # ── PESCADO ADICIONAIS ──────────────────────────────────────────────────
    "camarao":                ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN232019RTcamaraofrescoresfriradocongelado.pdf"],
    "conserva_sardinhas":     ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN222011RTconservasardinhas.pdf"],
    "conserva_peixes":        ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN452011RTconservadepeixe.pdf"],
    "conserva_atuns":         ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN462011RTconservadeatuns.pdf"],
    "lagosta":                ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN242019RTlagostafrescocongelado.pdf"],

    # ── LATICÍNIOS ADICIONAIS ───────────────────────────────────────────────
    "leite_em_po":            ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN532018RTleiteempoMercosul.pdf"],
    "leite_condensado":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN472018RTleitecondensado.pdf"],
    "bebida_lactea":          ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN162005RTbebidalactea.pdf"],
    "soro_leite":             ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN942020RTsoroleite.pdf"],

    # ── MEL E APÍCOLA ADICIONAIS ────────────────────────────────────────────
    "mel_qualidade":          ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN112000RTmeldequal.pdf"],
    "apicola_derivados":      ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN032001RTapitoxinacerageleiarealpropolis.pdf"],

    # ── OVOS ADICIONAIS ─────────────────────────────────────────────────────
    "ovos_pasteurizados":     ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port7282022RTovointegralpasteurizadodesidratado.pdf"],

    # ── MAPA — RIISPOA ATUALIZADO ────────────────────────────────────────────
    "riispoa_atualizado":     ["https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/decreto/d10468.htm"],

    # ── INMETRO — CONTEÚDO LÍQUIDO COMPLETO ──────────────────────────────────
    "inmetro_conteudo_liq":   [
        "https://www.inmetro.gov.br/legislacao/rtac/pdf/RTAC002775.pdf",
        "https://www.inmetro.gov.br/legislacao/rtac/pdf/RTAC002776.pdf",
    ],
    "inmetro_carnes_queijos": ["https://www.inmetro.gov.br/legislacao/rtac/pdf/RTAC003070.pdf"],

    # ── ANVISA — NOVA FÓRMULA (2024) ──────────────────────────────────────────
    "nova_formula_rdc902":    ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-902-de-6-de-setembro-de-2024-583517765"],

    # ── ANVISA — REGULARIZAÇÃO SNVS (2024) ───────────────────────────────────
    "regularizacao_rdc843":   ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-843-de-22-de-fevereiro-de-2024-543791616"],

    # ── ANVISA — ALÉRGENOS (obrigatório para TODOS os produtos) ─────────────
    "alergenos_rdc727":       ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-727-de-1-de-julho-de-2022-413249279"],

    # ── LATICÍNIOS — ÚLTIMAS 3 ────────────────────────────────────────────
    "leite_aromatizado":      ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN262007RTleitearomatizado.pdf"],
    "composto_lacteo":        ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN282007RTcompostolacteo.pdf"],
    "nata":                   ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN232012RTnata.pdf"],

    # ── OVOS — NOMENCLATURA ATUALIZADA ───────────────────────────────────
    "ovos_nomenclatura":      ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port11792024nomenclaturaovos.pdf"],

    # ── ANVISA — ROTULAGEM GERAL ──────────────────────────────────────────
    "rotulagem_anvisa_rdc715": ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-715-de-1-de-julho-de-2022-413249117"],

    # ── ANVISA — AROMATIZANTES ────────────────────────────────────────────
    # RDC 725/2022 — PDF scanned, sem texto extraível
    # Conteúdo embutido diretamente como texto (resumo da norma)
    "aromatizantes_rdc725":   ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-725-de-1-de-julho-de-2022-413249198"],

    # ── ANVISA — ADITIVOS IT 70/2016 (alegações aditivos em embutidos/laticínios)
    "aditivos_it70":          ["https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa/2016/arquivos/2016_informe_tecnico_70.pdf"],

    # ════════════════════════════════════════════════════════════════════════
    # NORMAS GERAIS — APLICÁVEIS A TODOS OS ALIMENTOS (POA e não-POA)
    # ════════════════════════════════════════════════════════════════════════

    # ── INMETRO — CONTEÚDO LÍQUIDO COMPLEMENTARES ─────────────────────────
    "inmetro_251_requisitos": ["https://www.inmetro.gov.br/legislacao/rtac/pdf/RTAC002776.pdf"],
    "inmetro_265_medidas":    ["https://www.inmetro.gov.br/legislacao/rtac/pdf/RTAC003057.pdf"],
    "inmetro_248_verificacao":["https://www.inmetro.gov.br/legislacao/rtac/pdf/RTAC001781.pdf"],

    # ── ANVISA — IRRADIAÇÃO ────────────────────────────────────────────────
    "irradiacao_rdc21":       ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-21-de-26-de-janeiro-de-2001-396649938"],

    # ── ANVISA — REGULARIZAÇÃO CATEGORIAS (IN 281/2024) ───────────────────
    "regularizacao_in281":    ["https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-281-de-22-de-fevereiro-de-2024-547762772"],

    # ── ANVISA — SUPLEMENTOS ALIMENTARES ──────────────────────────────────
    "suplementos_rdc243":     ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-243-de-26-de-julho-de-2018-41232201"],
    "suplementos_in28":       ["https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-28-de-26-de-julho-de-2018-41232253"],

    # ── ANVISA — CEREAIS, FARINHAS, MASSAS ────────────────────────────────
    "cereais_rdc711":         ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-711-de-1-de-julho-de-2022-413249064"],
    "cereais_integrais_rdc712":["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-712-de-1-de-julho-de-2022-413249083"],

    # ── LEGISLAÇÕES FEDERAIS GERAIS ────────────────────────────────────────
    "dec_lei_986_1969":       ["https://www.planalto.gov.br/ccivil_03/decreto-lei/del0986.htm"],
    "lei_8078_cdc":           ["https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm"],
    "lei_6437_infracoes":     ["https://www.planalto.gov.br/ccivil_03/leis/l6437.htm"],
    "lei_12849_latex":        ["https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/lei/l12849.htm"],
    "port_392_2021_alteracao":["https://www.in.gov.br/en/web/dou/-/portaria-n-392-de-29-de-setembro-de-2021-350099068"],

    # ── MAPA — TRANSGÊNICOS COMPLEMENTARES ────────────────────────────────
    "transgenicos_ini1_2004": ["https://www.planalto.gov.br/ccivil_03/_Ato2004-2006/2004/Instrucao_normativa/INI-1-2004.htm"],
    "transgenicos_port2658":  ["https://www.planalto.gov.br/ccivil_03/portaria/P_2658.htm"],

    # ── MAPA — BEBIDAS ─────────────────────────────────────────────────────
    "bebidas_dec6871":        ["https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2009/decreto/d6871.htm"],
}
_kb_cache: dict = {}

# ═══════════════════════════════════════════════════════════════════════════════
# DETECÇÃO DE CATEGORIA — palavras-chave por produto
# ═══════════════════════════════════════════════════════════════════════════════
CATEGORIA_KEYWORDS = {
    # Embutidos
    "embutidos":        ["salsicha", "linguiça", "linguica", "mortadela", "apresuntado"],
    "salame":           ["salame", "salaminho", "copa", "coppa", "pepperoni", "presunto parma", "presunto serrano"],
    "presunto":         ["presunto", "presunto cozido", "presunto defumado"],
    "hamburguer":       ["hambúrguer", "hamburguer", "burger"],
    "bacon":            ["bacon", "panceta", "pancetta"],
    "carne_moida":      ["carne moída", "carne moida"],
    "charque":          ["charque", "carne salgada", "miúdo salgado", "jabá", "jaba"],
    "fiambre":          ["fiambre"],
    "carne_maturada":   ["carne maturada", "dry aged"],
    "carnes_temperadas":["carne temperada", "frango temperado", "carne marinada"],
    "almondega_kibe":   ["almôndega", "almondega", "kibe", "quibe"],
    "gelatina_colageno":["gelatina", "colágeno", "colageno"],

    # Laticínios
    "laticinios_geral": ["queijo", "queijinho", "cheese"],
    "queijo_coalho_manteiga": ["queijo coalho", "queijo de manteiga", "manteiga de garrafa", "manteiga da terra"],
    "mussarela":        ["mussarela", "mozzarela", "mozzarella", "muçarela"],
    "leite_uht":        ["leite uht", "leite longa vida", "leite uat"],
    "leite_pasteurizado":["leite pasteurizado", "leite integral", "leite desnatado", "leite semidesnatado"],
    "doce_de_leite":    ["doce de leite"],
    "leite_fermentado": ["iogurte", "yogurte", "leite fermentado", "kefir", "bebida láctea", "bebida lactea"],
    "requeijao":        ["requeijão", "requeijao", "queijo fundido", "cream cheese"],

    # Pescado
    "pescado_fresco":   ["peixe", "pescado", "tilápia", "tilapia", "salmão", "salmao", "atum", "sardinha", "merluza", "badejo"],
    "pescado_congelado":["peixe congelado", "pescado congelado", "filé congelado", "file congelado"],
    "pescado_salgado":  ["bacalhau", "peixe salgado", "pescado salgado"],
    "camarao":          ["camarão", "camarao", "lagosta", "lula", "polvo"],

    # Mel e apícola
    "mel":              ["mel", "própolis", "propolis", "geleia real", "pólen", "pollen", "apicola", "apícola"],

    # Ovos
    "ovos":             ["ovo", "ovos", "ovo caipira", "ovo codorna"],

    # Aves
    "aves_geral":       ["frango", "frango inteiro", "peito de frango", "coxa", "sobrecoxa", "pato", "peru", "aves"],
    # Carnes adicionais
    "apresuntado":      ["apresuntado"],
    "paleta_empanados": ["paleta cozida", "empanado", "presunto serrano", "presunto parma", "prato pronto"],
    "corned_beef":      ["corned beef", "carne em conserva", "carne enlatada", "carne bovina em conserva"],
    # Pescado adicional
    "camarao":          ["camarão", "camarao", "camaroes"],
    "conserva_sardinhas":["sardinha", "conserva de sardinha", "sardinha em óleo", "sardinha em molho"],
    "conserva_peixes":  ["peixe em conserva", "peixe enlatado", "atum em lata", "conserva de peixe"],
    "conserva_atuns":   ["atum", "bonito", "conserva de atum", "atum em óleo", "atum ao natural"],
    "lagosta":          ["lagosta", "caranguejo"],
    # Laticínios adicionais
    "leite_em_po":      ["leite em pó", "leite em po", "leite desidratado", "leite integral em pó"],
    "leite_condensado": ["leite condensado", "leite condensado adoçado"],
    "bebida_lactea":    ["bebida láctea", "bebida lactea"],
    "soro_leite":       ["soro de leite", "soro lácteo", "whey"],
    # Mel adicionais
    "mel_qualidade":    ["mel", "mel puro", "mel orgânico", "mel silvestre", "mel florada"],
    "apicola_derivados":["própolis", "propolis", "geleia real", "pólen apícola", "pollen", "cera de abelha", "apitoxina", "extrato de própolis"],
    # Ovos adicionais
    "ovos_pasteurizados":["ovo pasteurizado", "ovo desidratado", "ovo em pó", "ovo integral"],
    "ovos_nomenclatura": ["ovos caipira", "ovos de granja", "ovo orgânico", "ovo cage free"],
    # Laticínios finais
    "leite_aromatizado": ["leite aromatizado", "leite com chocolate", "leite com morango", "leite sabor"],
    "composto_lacteo":   ["composto lácteo", "composto lacteo", "alimento lácteo composto"],
    "nata":              ["nata", "creme nata"],
    # ANVISA geral e MAPA geral
    "rotulagem_anvisa_rdc715": ["rotulagem", "rótulo alimento embalado"],
    "aromatizantes_rdc725":    ["aromatizante", "aroma natural", "flavorizante"],
    "aditivos_it70":           ["aditivo alimentar", "conservante", "corante", "estabilizante", "espessante"],
    "riispoa_atualizado":      ["inspeção industrial", "produto de origem animal", "registro produto"],
    "inmetro_carnes_queijos":  ["produto cárneo", "queijo", "requeijão", "conteúdo líquido"],
    "nova_formula_rdc902":     ["nova fórmula", "alteração composição"],
    "regularizacao_rdc843":    ["regularização", "notificação produto"],
    # INMETRO complementares
    "inmetro_251_requisitos":  ["conteúdo líquido", "volume nominal", "embalagem"],
    "inmetro_265_medidas":     ["conteúdo líquido", "indicação quantitativa", "massa volume"],
    "inmetro_248_verificacao": ["verificação conteúdo", "produto pré-medido"],
    # ANVISA gerais
    "irradiacao_rdc21":        ["irradiado", "irradiação", "tratamento radiação"],
    "regularizacao_in281":     ["notificação", "isenção registro", "categoria alimento"],
    "suplementos_rdc243":      ["suplemento alimentar", "suplemento nutricional", "whey protein", "proteína em pó"],
    "suplementos_in28":        ["suplemento alimentar", "BCAA", "creatina", "termogênico"],
    "cereais_rdc711":          ["cereal", "farinha", "amido", "massa alimentícia", "biscoito", "pão", "farelo"],
    "cereais_integrais_rdc712":["integral", "cereal integral", "grão integral", "farinha integral"],
    # Legislações federais
    "dec_lei_986_1969":        ["alimento", "denominação", "fraude alimentar"],
    "lei_8078_cdc":            ["consumidor", "direito do consumidor", "código defesa"],
    "lei_6437_infracoes":      ["infração sanitária", "autuação", "penalidade"],
    "lei_12849_latex":         ["látex", "latex natural", "alergia látex"],
    "port_392_2021_alteracao": ["redução de conteúdo", "downsizing", "embalagem menor"],
    # Transgênicos
    "transgenicos_ini1_2004":  ["transgênico", "ogm", "organismo geneticamente modificado"],
    "transgenicos_port2658":   ["símbolo transgênico", "símbolo T", "símbolo ogm"],
    # Bebidas
    "bebidas_dec6871":         ["bebida", "suco", "néctar", "refrigerante", "cerveja", "vinho", "cachaça"],
    # Pescado — categorias novas
    "camarao":          ["camarão", "camarao", "camarões", "camaroes"],
    "lagosta":          ["lagosta"],
    "moluscos_cefalopodes": ["lula", "polvo", "pota", "cefalópode", "cefalopode"],
    "conserva_peixe_sardinha": ["sardinha", "conserva de sardinha", "sardinha em lata"],
    "conserva_atum":    ["atum", "atum em conserva", "atum enlatado", "bonito", "conserva de atum"],

    # Laticínios extras
    "leite_em_po":      ["leite em pó", "leite em po", "leite desidratado"],
    "leite_condensado": ["leite condensado", "leite condençado"],
    "nata_creme":       ["nata", "creme de leite"],
    "queijo_prato":     ["queijo prato"],
    "queijo_parmesao":  ["queijo parmesão", "queijo parmesao", "parmesano", "reggiano"],
    "queijo_provolone": ["queijo provolone", "provolone"],
    "queijo_fundido":   ["queijo fundido", "queijo processado", "queijo cremoso"],

    # Carnes extras
    "pate_bacon_copa":  ["patê", "pate", "copa"],
    "paleta_empanados_presunto_serrano": ["paleta cozida", "empanado", "nugget", "presunto serrano"],
    "corned_beef_conserva": ["corned beef", "carne enlatada", "carne em conserva"],

    # Ovos derivados
    "ovos_pasteurizados": ["ovo pasteurizado", "ovo desidratado", "ovo integral pasteurizado"],

    # ANVISA
    "alergenos_rdc727":   ["alérgenos", "alergenos", "alergênico", "alergenico"],
    "nutricional_in75":   ["tabela nutricional", "informação nutricional"],
    "aditivos_rdc778":    ["aditivo", "conservante", "corante", "estabilizante"],

    # Pescado extras
    "conserva_sardinha":  ["sardinha", "sardinha em lata", "conserva de sardinha"],
    "conserva_atum":      ["atum", "atum em conserva", "atum enlatado", "bonito"],
    "conserva_peixe":     ["conserva de peixe", "peixe em lata", "peixe enlatado"],

    # Laticínios extras
    "leite_em_po":        ["leite em pó", "leite em po", "leite desidratado", "leite pó"],
    "leite_condensado":   ["leite condensado"],
    "nata":               ["nata", "creme de leite"],
    "queijo_provolone":   ["provolone", "queijo provolone"],
    "queijo_parmesao":    ["parmesão", "parmesao", "parmesano", "queijo parmesão"],

    # Ovos derivados
    "ovos_derivados":     ["ovo pasteurizado", "ovo desidratado", "ovo integral pasteurizado", "ovoproduto"],

    # Carnes extras
    "pate_bacon_copa":    ["patê", "pate"],
    "paleta_salgada":     ["paleta cozida", "empanado", "nugget", "presunto serrano", "prato pronto"],
    "corned_beef":        ["corned beef", "carne enlatada", "carne em conserva"],
}

def detect_categories(obs: str) -> list[str]:
    """Detecta múltiplas categorias relevantes para o produto."""
    o = obs.lower()
    detected = []
    for categoria, keywords in CATEGORIA_KEYWORDS.items():
        if any(kw in o for kw in keywords):
            # Mapeia aves_geral para nomenclatura (sem RTIQ próprio ainda)
            if categoria == "aves_geral":
                detected.append("nomenclatura")
            elif categoria in MAPA_URLS:
                detected.append(categoria)
    # Sempre inclui laticínios_geral para qualquer queijo
    if "queijo" in o and "laticinios_geral" not in detected:
        detected.append("laticinios_geral")
    # Atum pode ser cárneo ou conserva - cobre os dois
    if "atum" in o:
        if "conserva_atuns" not in detected: detected.append("conserva_atuns")
        if "conserva_peixes" not in detected: detected.append("conserva_peixes")
    return list(dict.fromkeys(detected))  # remove duplicatas mantendo ordem

# ── FALLBACK TEXTUAL — RDC 725/2022 (PDF scanned, sem texto extraível) ───────
RDC_725_FALLBACK = """RESOLUÇÃO RDC Nº 725, DE 1º DE JULHO DE 2022 — ANVISA
Dispõe sobre os aditivos alimentares aromatizantes. Vigência: 1/9/2022.

DEFINIÇÕES: Aromatizante = substância com propriedades odoríferas/sápidas. Natural = obtido de matérias-primas vegetais/animais/microbianas por processos físicos, microbiológicos ou enzimáticos. Artificial = sintetizado quimicamente. De reação = processo Maillard. De fumaça = extrato de madeiras não tratadas.

ROTULAGEM NA LISTA DE INGREDIENTES (Art. 10 + RDC 727/2022 Art. 12 §3º):
- Declarar pela FUNÇÃO TECNOLÓGICA: "Aromatizante"
- Pode acrescentar classificação: "natural", "artificial" ou "de fumaça"
- Exemplos válidos: "Aromatizante natural" / "Aromatizante artificial" / "Aromatizante de fumaça"
- PROIBIDO: mencionar propriedades medicamentosas ou terapêuticas das ervas

RESTRIÇÕES (Art. 7º):
- Proibidos: óleos essenciais de fava-tonca, sassafrás e sabina
- Aromatizante de fumaça: máx 0,03 μg de 3,4-benzopireno/kg de alimento

PARA POA (embutidos defumados, bacon, linguiça, charque):
- Fumaça líquida = aromatizante de fumaça → declarar como "Aromatizante de fumaça"
- Aroma de defumação artificial → declarar como "Aromatizante artificial"
- Extrato de fumaça, fumaça condensada: idem, declarar função + classificação"""

async def fetch_pdf_text(url: str, max_chars: int = 4500) -> str:
    """Baixa PDF/HTML do MAPA e extrai texto. Usa fallback para PDFs scanned."""
    if "725" in url and "2022" in url:
        return RDC_725_FALLBACK
    try:
        from pypdf import PdfReader
        async with httpx.AsyncClient(timeout=25.0) as client:
            r = await client.get(url, follow_redirects=True)
            if r.status_code != 200:
                return ""
            content_type = r.headers.get("content-type", "")
            if "html" in content_type:
                import re as _re
                clean = _re.sub(r'<[^>]+>', ' ', r.text)
                clean = _re.sub(r'\s+', ' ', clean).strip()
                return clean[:max_chars]
            reader = PdfReader(io.BytesIO(r.content))
            text = "".join(p.extract_text() or "" for p in reader.pages)
            return text.strip()[:max_chars]
    except Exception:
        return ""


async def pdf_to_images_b64(pdf_bytes: bytes) -> list[dict]:
    """
    Converte PDF para imagens PNG em alta resolução (300 DPI).
    Trata PDFs CMYK (artes gráficas) convertendo para RGB.
    Estratégias em ordem de preferência:
    1. PyMuPDF (fitz) — melhor qualidade, suporte CMYK nativo
    2. pdftoppm (Poppler) — 300 DPI, boa qualidade
    3. PDF nativo via Anthropic — fallback final
    """
    import subprocess, tempfile, os as _os, glob as _glob

    # ── Método 1: PyMuPDF (fitz) ─────────────────────────────────────────
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # 300 DPI = zoom 4.17 (72 DPI padrão × 4.17 = 300)
            mat = fitz.Matrix(4.17, 4.17)
            # Renderiza em RGB (converte CMYK automaticamente)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB, alpha=False)
            img_bytes = pix.tobytes("png")
            pages.append({
                "b64": base64.b64encode(img_bytes).decode(),
                "mime": "image/png",
                "page": page_num + 1
            })
        doc.close()
        if pages:
            return pages
    except ImportError:
        pass  # PyMuPDF não instalado, tenta próximo método
    except Exception:
        pass

    # ── Método 2: pdftoppm (Poppler) a 300 DPI ───────────────────────────
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        out_prefix = tmp_path.replace(".pdf", "_page")
        result = subprocess.run(
            ["pdftoppm", "-png", "-r", "300", tmp_path, out_prefix],
            capture_output=True, timeout=60
        )
        _os.unlink(tmp_path)

        if result.returncode == 0:
            page_files = sorted(_glob.glob(out_prefix + "*.png"))
            pages = []
            for i, pf in enumerate(page_files):
                with open(pf, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                pages.append({"b64": img_b64, "mime": "image/png", "page": i + 1})
                _os.unlink(pf)
            if pages:
                return pages
    except Exception:
        pass

    # ── Método 3: PDF nativo (fallback) ──────────────────────────────────
    pdf_b64 = base64.b64encode(pdf_bytes).decode()
    return [{"b64": pdf_b64, "mime": "application/pdf", "page": 0, "is_pdf": True}]


async def get_kb_for_categories(categories: list[str]) -> str:
    """Carrega e combina KB para múltiplas categorias detectadas."""
    if not categories:
        return ""

    async def load_one(cat: str) -> str:
        if cat in _kb_cache:
            return _kb_cache[cat]
        urls = MAPA_URLS.get(cat, [])
        if not urls:
            return ""
        texts = await asyncio.gather(*[fetch_pdf_text(u) for u in urls])
        result = "\n\n".join(t for t in texts if t)
        _kb_cache[cat] = result
        return result

    # Carrega em paralelo, max 2 categorias para não estourar o contexto
    cats_to_load = categories[:2]
    texts = await asyncio.gather(*[load_one(c) for c in cats_to_load])

    sections = []
    for cat, text in zip(cats_to_load, texts):
        if text:
            # Limita cada RTIQ a 2000 chars para não exceder contexto
            sections.append(f"### RTIQ: {cat.upper().replace('_',' ')}\n{text[:2000]}")

    return "\n\n---\n\n".join(sections)


# ═══════════════════════════════════════════════════════════════════════════════
# CAMPOS NOME
# ═══════════════════════════════════════════════════════════════════════════════
CAMPOS_NOME = {
    1: "Denominação de venda",
    2: "Lista de ingredientes",
    3: "Conteúdo líquido",
    4: "Identificação do fabricante",
    5: "Lote",
    6: "Prazo de validade",
    7: "Instruções de conservação",
    8: "Carimbo SIF/SIE/SIM",
    9: "Tabela nutricional",
    10: "Rotulagem nutricional frontal (lupa)",
    11: "Declaração de alérgenos",
    12: "Declaração de transgênicos",
}


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════
SP_VALIDACAO = """Você é ValidaRótulo IA — o sistema mais preciso de validação de rótulos de produtos de origem animal do Brasil, especialista em SIM, SIE e SIF.

REGRAS ABSOLUTAS:
1. Analise CADA detalhe visível na imagem — texto, símbolos, formatação, cores, posicionamento
2. Se um elemento não está visível na arte do rótulo: registre como AUSENTE
3. Lote e validade NÃO fazem parte da arte do rótulo — são impressos na linha de produção. NÃO avalie e NÃO cobre esses campos.
4. Cite sempre a norma específica (número e ano) para cada avaliação
5. Nunca pule nenhum dos 12 campos obrigatórios

{kb_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASSO 1 — IDENTIFICAÇÃO DO PRODUTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Identifique da imagem:
• Nome completo do produto conforme aparece no rótulo
• Espécie animal (bovino/suíno/frango/pescado/ovino/caprino/bubalino/abelha/galinha/misto)
• Categoria: in natura / embutido cozido / embutido frescal / curado / defumado / laticínio / mel / ovo / conserva
• Órgão de inspeção detectado pelo carimbo: SIF / SIE / SIM
• Sigla exata do carimbo (ex: SIF 1234 / SISP 567 / SIM 89)
• RTIQ aplicável (ex: IN 04/2000 para linguiça)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASSO 2 — LEGISLAÇÕES APLICÁVEIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Normas obrigatórias para todos os POA:
• IN 22/2005 + Port. 240/2021 + Port. 449/2022 (MAPA) — rotulagem geral POA
• RDC 727/2022 (ANVISA) — rotulagem geral alimentos
• RDC 429/2020 + IN 75/2020 (ANVISA) — rotulagem nutricional
• INMETRO Port. 249/2021 + 262/2024 — conteúdo líquido
• Port. SDA 1485/2025 — nomenclatura POA
• Decreto 4.680/2003 — transgênicos
• Lei 10.674/2003 — glúten
• RDC 715/2022 — lactose

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASSO 3 — VALIDAÇÃO DOS 12 CAMPOS OBRIGATÓRIOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use EXATAMENTE estes ícones:
✅ CONFORME — [o que está correto] (norma)
❌ NÃO CONFORME — [o que está errado] → [como deve ser] (norma)
⚠️ AUSENTE — [campo não encontrado na arte] → [o que deve constar] (norma)
🔍 NÃO VERIFICÁVEL — [motivo] → [recomendação]

─────────────────────────────────────────────
CAMPO 1 — DENOMINAÇÃO DE VENDA
─────────────────────────────────────────────
a) Nome específico conforme RTIQ e Port. 1485/2025 — não pode ser genérico
   • Embutidos: espécie + tipo (ex: "Linguiça Toscana Suína", não "Linguiça")
   • Queijos: variedade completa (ex: "Queijo Minas Frescal")
   • Laticínios: classificação obrigatória (integral/semidesnatado/desnatado)
   • Ovos: tipo e categoria (ex: "Ovos de Galinha Tipo Extra")
b) Posicionada no PAINEL PRINCIPAL com fonte em destaque
c) Sem termos proibidos sem certificação ("caseiro", "artesanal", "natural")

─────────────────────────────────────────────
CAMPO 2 — LISTA DE INGREDIENTES
─────────────────────────────────────────────
a) Precedida de "Ingredientes:" (ou "Ingrediente:" se único)
b) ORDEM DECRESCENTE de quantidade — verificar se água e ingredientes principais estão na posição correta
c) Aditivos: função tecnológica + nome ou INS obrigatórios
   • CORRETO: "Conservantes: Nitrito de Sódio (INS 250), Nitrato de Sódio (INS 251)"
   • ERRADO: apenas "Conservante" sem identificar qual
   • Corante tartrazina (INS 102): nome OBRIGATÓRIO
   • Aromatizantes: "Aromatizante natural/artificial/de fumaça" (RDC 725/2022)
d) Ingredientes compostos: composição entre parênteses
e) Fonte mínima: 1mm (área >80cm²) ou 0,75mm (área ≤80cm²)
f) ⚠️ PROTEÍNA DE SOJA — ALERTA OBRIGATÓRIO PARA EMBUTIDOS:
   Quando "Proteína de Soja" ou "Proteína Texturizada de Soja" aparecer na lista de ingredientes
   de qualquer embutido (linguiça, salsicha, mortadela, hambúrguer, etc.), o PERCENTUAL deve
   estar declarado entre parênteses — ex: "Proteína de Soja (2%)" ou "Proteína Texturizada de
   Soja (4,5%)". MOTIVO: os RTIQs fixam limites máximos por categoria (IN 4/2000):
   • Linguiça tipo toscana/calabresa/portuguesa: PROIBIDA adição de proteína vegetal
   • Salsicha: máx. 4,5% | Mortadela: máx. 4% | Hambúrguer: máx. 4%
   • Apresuntado: máx. 4% | Salame: proibido
   Sem o % declarado, é impossível verificar conformidade com o RTIQ.
   Se proteína de soja aparecer SEM percentual → alertar como ❌ NÃO CONFORME

─────────────────────────────────────────────
CAMPO 3 — CONTEÚDO LÍQUIDO
─────────────────────────────────────────────
a) Em g/kg (sólidos) ou mL/L (líquidos) no PAINEL PRINCIPAL
b) Tamanho mínimo da fonte (INMETRO Port. 249/2021):
   • ≤50g: 2mm | 50-200g: 3mm | 200g-1kg: 4mm | >1kg: 6mm
c) "Peso líquido" ou "Conteúdo líquido" — não peso bruto

─────────────────────────────────────────────
CAMPO 4 — IDENTIFICAÇÃO DO FABRICANTE
─────────────────────────────────────────────
a) RAZÃO SOCIAL completa (não apenas nome fantasia)
b) CNPJ no formato correto: XX.XXX.XXX/XXXX-XX
c) ENDEREÇO COMPLETO: logradouro + número + bairro + cidade + UF + CEP
d) Para importados: nome e endereço do importador no Brasil

─────────────────────────────────────────────
CAMPO 5 — DECLARAÇÃO DE GLÚTEN (Lei 10.674/2003)
─────────────────────────────────────────────
a) Obrigatório para TODOS os alimentos embalados
b) Deve constar: "CONTÉM GLÚTEN" ou "NÃO CONTÉM GLÚTEN"
c) Verificar ingredientes: trigo, centeio, cevada, aveia → CONTÉM GLÚTEN
d) Posição: próxima à lista de ingredientes ou área de alérgenos
e) Em destaque suficiente para leitura

─────────────────────────────────────────────
CAMPO 6 — DECLARAÇÃO DE LACTOSE (RDC 715/2022)
─────────────────────────────────────────────
a) Obrigatória quando produto contém lactose
b) Para laticínios: sempre declarar presença de lactose
c) Formato aceito: "CONTÉM LACTOSE" — declaração separada dos alérgenos
d) Produtos "zero lactose" ou "sem lactose": verificar se atende teor máximo (<100mg/100g)
e) Declaração de lactose é SEPARADA da declaração de leite como alérgeno

─────────────────────────────────────────────
CAMPO 7 — INSTRUÇÕES DE CONSERVAÇÃO
─────────────────────────────────────────────
a) Temperatura específica obrigatória para produtos perecíveis:
   • Refrigerados: "Manter refrigerado entre X°C e Y°C"
   • Congelados: "Manter congelado a -18°C ou menos"
b) Instrução pós-abertura: "Após aberto, consumir em até X dias, mantendo refrigerado"
c) Condições específicas do RTIQ devem ser respeitadas

─────────────────────────────────────────────
CAMPO 8 — CARIMBO DE INSPEÇÃO (exclusivo POA)
─────────────────────────────────────────────
a) FORMATO OVAL obrigatório (não redondo, não retangular)
b) Conteúdo por órgão:
   • SIF: "SIF" + número do estabelecimento
   • SIE: sigla estadual (SISP, SIE-MG, CISPOA, etc.) + número
   • SIM: "SIM" + número municipal
c) Número e sigla legíveis
d) Posicionado em destaque no rótulo

─────────────────────────────────────────────
CAMPO 9 — TABELA NUTRICIONAL (RDC 429/2020 + IN 75/2020)
─────────────────────────────────────────────
PORÇÃO PADRÃO por categoria:
• Queijos/Requeijão: 30g | Manteiga/creme de leite: 10g
• Embutidos fatiados (presunto, salame): 30g
• Embutidos para cozinhar (linguiça, salsicha): 50g
• Carnes in natura: 100g | Hambúrguer cru: 80g
• Leite fluido: 200mL | Leite em pó: 26g | Iogurte: 100g
• Mel: 25g | Pescado: 100g | Ovos: 30g

NUTRIENTES OBRIGATÓRIOS (verificar se todos presentes):
☐ Valor energético: kcal E kJ (obrigatório os dois)
☐ Carboidratos totais: g
☐ Açúcares totais: g
☐ Açúcares adicionados: g (separado dos totais)
☐ Proteínas: g
☐ Gorduras totais: g
☐ Gorduras saturadas: g
☐ Gorduras trans: g — OBRIGATÓRIO declarar "0g" mesmo se ausente
☐ Fibra alimentar: g
☐ Sódio: mg

Valores por porção E por 100g/mL obrigatórios.

─────────────────────────────────────────────
CAMPO 10 — ROTULAGEM NUTRICIONAL FRONTAL (LUPA)
─────────────────────────────────────────────
Lupa OBRIGATÓRIA se (por 100g):
• Açúcares adicionados ≥ 15g → "ALTO EM AÇÚCARES ADICIONADOS"
• Gorduras saturadas ≥ 6g → "ALTO EM GORDURAS SATURADAS"
• Sódio ≥ 600mg → "ALTO EM SÓDIO"

Verificar:
a) Lupa preta com texto em branco no PAINEL PRINCIPAL
b) Texto exato: "ALTO EM [NUTRIENTE]"
c) Se valores não visíveis claramente: registrar como 🔍 NÃO VERIFICÁVEL

─────────────────────────────────────────────
CAMPO 11 — DECLARAÇÃO DE ALÉRGENOS (RDC 727/2022, Art. 13-15)
─────────────────────────────────────────────
FORMATO OBRIGATÓRIO (Art. 15 RDC 727/2022):
a) CAIXA ALTA obrigatório
b) NEGRITO obrigatório
c) Cor CONTRASTANTE com o fundo do rótulo (a norma não exige cor específica)
d) Altura mínima de 2mm (ou 1mm se área do painel ≤100cm²)
e) Posicionada IMEDIATAMENTE após ou abaixo da lista de ingredientes
⚠️ IMPORTANTE: Fundo amarelo NÃO é exigência legal — a cor pode ser qualquer uma desde que contraste. Não penalize por ausência de amarelo.

TEXTO OBRIGATÓRIO:
• "ALÉRGICOS: CONTÉM [nome do alimento]" → para ingredientes INTENCIONAIS (presentes na fórmula)
• "ALÉRGICOS: PODE CONTER [nome do alimento]" → SOMENTE para contaminação cruzada (não intencional)
⚠️ ERRO COMUM: usar "PODE CONTER" para ingrediente declarado na lista → isso é NÃO CONFORME pois
   induz o consumidor a acreditar que o alérgeno pode ou não estar presente quando está sempre presente.

DECLARAÇÃO INCLUI DERIVADOS — exemplos corretos:
• Soja como ingrediente → "ALÉRGICOS: CONTÉM SOJA E DERIVADOS DE SOJA"
• Leite como ingrediente → "ALÉRGICOS: CONTÉM LEITE E DERIVADOS DE LEITE"  
• Trigo como ingrediente → "ALÉRGICOS: CONTÉM TRIGO E DERIVADOS DE TRIGO"
• Múltiplos alérgenos → "ALÉRGICOS: CONTÉM SOJA E DERIVADOS DE SOJA, LEITE E DERIVADOS DE LEITE"

PRINCIPAIS ALÉRGENOS — verificar os presentes nos ingredientes:
Trigo/centeio/cevada/aveia e derivados | Crustáceos e derivados | Ovos e derivados
Peixes e derivados | Amendoim e derivados | Soja e derivados | Leite e derivados
Oleaginosas (amêndoa, castanha, nozes, etc.) e derivados | Aipo | Mostarda
Gergelim | Sulfitos (>10mg/kg) | Tremoço | Moluscos

Regras especiais:
• "CONTÉM LEITE E DERIVADOS" obrigatório mesmo em laticínios
• "CONTÉM PEIXE E DERIVADOS" obrigatório mesmo em produtos de peixe
• CMS de aves: declarar "CONTÉM CMS DE AVES" separadamente (não é alérgeno mas exigência MAPA)
• Contaminação cruzada: "PODE CONTER" apenas se houver risco real documentado no PCA

─────────────────────────────────────────────
CAMPO 12 — DECLARAÇÃO DE TRANSGÊNICOS (Decreto 4.680/2003)
─────────────────────────────────────────────
a) Se ingrediente OGM >1%: símbolo triângulo amarelo "T" obrigatório (mín. 4mm)
b) Texto: "[ingrediente] transgênico" ou "Contém X% de [ingrediente] transgênico"
c) Atenção: soja, milho frequentemente transgênicos em embutidos
d) Se nenhum OGM >1%: omissão ou "Não contém transgênicos" (ambos corretos)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASSO 4 — RELATÓRIO FINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### PRODUTO: [nome + espécie + categoria]
### ÓRGÃO: [SIF/SIE/SIM] | CARIMBO: [número] | RTIQ: [norma]

### SCORE: [X]/12 campos conformes ([Y]%)

### VEREDICTO:
✅ APROVADO — 11-12 conformes, sem não conformidade crítica
⚠️ APROVADO COM RESSALVAS — 7-10 conformes, não conformidades corrigíveis
❌ REPROVADO — ≤6 conformes OU qualquer não conformidade crítica:
   (sem carimbo oval | denominação incorreta | alérgenos ausentes | sem tabela nutricional)

### CORREÇÕES PRIORITÁRIAS:
[1ª — impede comercialização imediata]
[2ª — não conformidades técnicas]
[3ª — melhorias recomendadas]

### PONTOS CONFORMES:
[campos aprovados]"""


SP_REVISAO = """Você é um auditor sênior de rotulagem com 20 anos de MAPA/DIPOA.

Revise criticamente o relatório. Foque APENAS em erros reais — não repita o correto.

Verifique:
1. Todos os 12 campos foram avaliados? (1-Denominação, 2-Ingredientes, 3-Conteúdo líquido, 4-Fabricante, 5-Glúten, 6-Lactose, 7-Conservação, 8-Carimbo, 9-Tabela nutricional, 10-Lupa, 11-Alérgenos, 12-Transgênicos)
2. Lote e validade foram corretamente IGNORADOS? (são impressos na produção, não na arte)
3. Denominação: conferiu contra Port. 1485/2025 e RTIQ?
4. Ingredientes: ordem decrescente verificada? Aditivos com INS e função tecnológica?
5. Glúten: declaração "CONTÉM/NÃO CONTÉM GLÚTEN" verificada? (Lei 10.674/2003)
6. Lactose: verificada para laticínios? Separada da declaração de alérgenos?
7. Carimbo: formato OVAL verificado? (não redondo, não retangular)
8. Tabela nutricional: porção correta para a categoria? Gorduras trans declaradas mesmo se 0g?
9. Alérgenos: fundo amarelo com contorno preto? Todos 14 grupos checados?

RELATÓRIO:
{relatorio}

Se correto: "✅ REVISÃO CONCLUÍDA — Nenhuma inconsistência encontrada."
Se erros: "⚠️ Campo X: [problema] → [correção]" — máximo 200 palavras total."""


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
async def call_claude_simple(system: str, user: str, max_tokens: int = 350) -> str:
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "temperature": 0,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        if r.status_code != 200:
            return ""
        return r.json().get("content", [{}])[0].get("text", "")

def extrair_score(texto: str):
    m = re.search(r"SCORE[:\s]+(\d+)\s*/\s*12", texto, re.IGNORECASE)
    return int(m.group(1)) if m else None

def extrair_veredicto(texto: str) -> str:
    m = re.search(r"VEREDICTO[:\s]+(APROVADO COM RESSALVAS|APROVADO|REPROVADO)", texto, re.IGNORECASE)
    return m.group(1).upper() if m else "NÃO IDENTIFICADO"

def detectar_status_campo(texto: str, campo: int) -> str:
    nome = CAMPOS_NOME.get(campo, "")
    linhas = texto.split("\n")
    for i, linha in enumerate(linhas):
        if f"CAMPO {campo}" in linha.upper() or (nome and nome.upper() in linha.upper()):
            trecho = " ".join(linhas[i:i+5]).upper()
            if "NÃO CONFORME" in trecho or "NAO CONFORME" in trecho:
                return "NAO_CONFORME"
            elif "AUSENTE" in trecho:
                return "AUSENTE"
            elif "CONFORME" in trecho:
                return "CONFORME"
    return "NAO_DETECTADO"


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: VALIDAR
# ═══════════════════════════════════════════════════════════════════════════════
SP_DETECT = """Você é um sistema de identificação de rótulos POA. Analise a imagem e retorne APENAS um JSON válido, sem texto antes ou depois.

Retorne:
{
  "produto": "nome exato conforme aparece no rótulo",
  "categoria_kb": "categoria_da_lista",
  "especie": "bovino|suino|frango|peru|pato|pescado|ovino|caprino|bubalino|abelha|galinha|misto",
  "orgao": "SIF|SIE|SIM|nao_identificado",
  "numero_registro": "número do carimbo ou vazio",
  "sigla_sie": "sigla estadual se SIE (ex: SISP, SIE-MG) ou vazio",
  "confianca": "alta|media|baixa"
}

Lista de categorias_kb válidas:
embutidos, salame, presunto, hamburguer, bacon, carne_moida, charque, fiambre,
carne_maturada, carnes_temperadas, almondega_kibe, gelatina_colageno,
apresuntado, paleta_empanados, corned_beef,
laticinios_geral, queijo_coalho_manteiga, mussarela, leite_uht, leite_pasteurizado,
doce_de_leite, leite_fermentado, requeijao, leite_em_po, leite_condensado,
bebida_lactea, soro_leite, leite_aromatizado, composto_lacteo, nata,
pescado_fresco, pescado_congelado, pescado_salgado, camarao,
conserva_sardinhas, conserva_peixes, conserva_atuns, lagosta,
mel, mel_qualidade, apicola_derivados,
ovos, ovos_pasteurizados,
aves_geral, outro
"""

async def detect_product_phase1(image_b64: str, mime_type: str, obs: str) -> dict:
    """Fase 1: identifica produto, categoria e órgão automaticamente da imagem."""
    user_content = [
        {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": image_b64}},
        {"type": "text", "text": f"Identifique este rótulo.{' Dica: ' + obs if obs else ''} Retorne APENAS o JSON."}
    ]
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 300,
        "temperature": 0,
        "system": SP_DETECT,
        "messages": [{"role": "user", "content": user_content}],
    }
    headers_api = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers_api)
            if r.status_code != 200:
                return {}
            text = r.json().get("content", [{}])[0].get("text", "")
            # Extrai JSON do texto
            import re as _re
            m = _re.search(r'\{[\s\S]*\}', text)
            if m:
                return json.loads(m.group(0))
    except Exception:
        pass
    return {}

async def stream_validation(image_b64: str, mime_type: str, obs: str, orgao: str = ""):
    # ── DETECÇÃO + KB em paralelo com obs do usuário ─────────────────────
    # Usa obs para enriquecer keywords sem chamar Phase 1 separado (mais rápido)
    produto_detectado = ""
    categoria_detectada = ""
    orgao_final = orgao or ""
    sigla_sie = ""
    num_registro = ""
    especie = ""
    detected = {}

    # Carrega KB baseado em obs (Phase 1 agora está dentro do prompt principal)
    categories = detect_categories(obs) if obs else []
    kb_text = await get_kb_for_categories(categories) if categories else ""

    if kb_text:
        cats_str = ", ".join(categories[:3]).upper().replace("_", " ")
        kb_section = f"""## LEGISLAÇÃO ESPECÍFICA CARREGADA — {cats_str}
Os textos abaixo são extraídos diretamente dos PDFs oficiais do MAPA para este produto.
Use como referência primária na validação:

{kb_text}

---"""
    else:
        kb_section = ""

    # Contexto do órgão — usa detecção automática + input do usuário
    orgao_map = {
        "SIM": "ATENÇÃO: Produto registrado no SIM (Serviço de Inspeção Municipal). Verificar carimbo oval com sigla 'SIM' e número do município. Exigências municipais somam-se às federais.",
        "SIE": f"ATENÇÃO: Produto registrado no SIE (Serviço de Inspeção Estadual{' — ' + sigla_sie if sigla_sie else ''}). Verificar carimbo com sigla estadual{' ' + sigla_sie if sigla_sie else ''}. Exigências estaduais somam-se às federais.",
        "SIF": "ATENÇÃO: Produto registrado no SIF (Serviço de Inspeção Federal — DIPOA/MAPA). Máximo rigor. Verificar carimbo oval com 'SIF' e número do estabelecimento. Produto pode ser comercializado em todo território nacional.",
    }
    orgao_context = orgao_map.get(orgao_final.upper(), "")

    # Contexto da detecção automática
    detection_context = ""
    if detected:
        detection_context = f"""## DETECÇÃO AUTOMÁTICA DA FASE 1
Produto identificado: {produto_detectado}
Espécie animal: {especie}
Órgão de inspeção detectado: {orgao_final}
{f'Sigla SIE: {sigla_sie}' if sigla_sie else ''}
{f'Número do registro: {num_registro}' if num_registro else ''}
Confiança da detecção: {detected.get('confianca', 'media')}

Use essas informações como ponto de partida — confirme ou corrija com base no que você vê na imagem.
---"""

    system_prompt = SP_VALIDACAO.format(kb_section=kb_section)
    if orgao_context:
        system_prompt += f"\n\n{orgao_context}"
    if detection_context:
        system_prompt += f"\n\n{detection_context}"

    user_text = "Analise este rótulo com máxima precisão. Execute TODOS os passos. Não pule nenhum campo."
    if obs:
        user_text += f"\nObservação adicional: {obs}"
    if produto_detectado:
        user_text += f"\nProduto identificado automaticamente: {produto_detectado}"

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2500,
        "temperature": 0,
        "stream": True,
        "system": system_prompt,
        "messages": [{"role": "user", "content": (
            [{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": image_b64}},
             {"type": "text", "text": user_text}]
            if mime_type == "application/pdf" else
            [{"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": image_b64}},
             {"type": "text", "text": user_text}]
        )}],
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    relatorio = ""

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST", "https://api.anthropic.com/v1/messages",
            json=payload, headers=headers
        ) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                yield f"data: {json.dumps({'error': error_body.decode()})}\n\n"
                return
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                raw = line[6:].strip()
                if raw == "[DONE]":
                    break
                try:
                    ev = json.loads(raw)
                    if ev.get("type") == "content_block_delta":
                        delta = ev.get("delta", {})
                        if delta.get("type") == "text_delta":
                            chunk = delta.get("text", "")
                            relatorio += chunk
                            yield f"data: {json.dumps({'text': chunk})}\n\n"
                except Exception:
                    continue

    # Segunda leitura crítica
    yield f"data: {json.dumps({'text': '\n\n---\n\n## REVISÃO CRÍTICA\n'})}\n\n"
    revisao = await call_claude_simple(
        SP_REVISAO.format(relatorio=relatorio),
        "Revise com rigor técnico.",
        350
    )
    if revisao:
        yield f"data: {json.dumps({'text': revisao})}\n\n"

    yield "data: [DONE]\n\n"



def preprocess_image(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """
    Zoom máximo na imagem — simula o que um humano faz ao dar zoom para ler letra pequena.
    Estratégia:
    - Sempre amplia para 4500px no maior lado (zoom máximo)
    - Aplica UnsharpMask após interpolação para recuperar bordas de letras
    - Aumenta contraste levemente para melhorar leitura de texto
    - Imagens já grandes (>4500px): mantém tamanho, aplica só sharpening
    """
    try:
        from PIL import Image as PILImage, ImageFilter, ImageEnhance

        img = PILImage.open(io.BytesIO(image_bytes))

        # Normaliza modo de cor
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        elif img.mode == "L":
            img = img.convert("RGB")

        w, h = img.size
        maior = max(w, h)
        TARGET = 4500  # zoom máximo — equivalente a dar zoom total na imagem

        if maior < TARGET:
            # Upscale: amplia proporcionalmente até TARGET px
            scale = TARGET / maior
            img = img.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
            # UnsharpMask agressivo: recupera nitidez das letras após interpolação
            # radius=2 → afeta bordas finas de texto; percent=200 → sharpening forte
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=200, threshold=1))
        elif maior > TARGET:
            # Imagens já grandes: só downscale leve para não explodir payload
            scale = TARGET / maior
            img = img.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)

        # Contraste +20%: melhora legibilidade de texto cinza em fundo claro
        img = ImageEnhance.Contrast(img).enhance(1.2)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue(), "image/jpeg"

    except Exception:
        return image_bytes, mime_type

@app.post("/validar")
async def validar_rotulo(
    imagem: UploadFile = File(...),
    obs: str = Form(default=""),
    orgao: str = Form(default=""),
):
    if not ANTHROPIC_API_KEY:
        return JSONResponse({"error": "ANTHROPIC_API_KEY não configurada"},
                            headers={"Access-Control-Allow-Origin": "*"})

    contents = await imagem.read()
    content_type = (imagem.content_type or "").lower()
    filename = (imagem.filename or "").lower()

    # ── Detectar se é PDF ────────────────────────────────────────────────
    is_pdf = (
        content_type == "application/pdf" or
        filename.endswith(".pdf")
    )

    if is_pdf:
        pages = await pdf_to_images_b64(contents)
        if not pages:
            return JSONResponse({"error": "Não foi possível processar o PDF."},
                                headers={"Access-Control-Allow-Origin": "*"})

        first = pages[0]
        if first.get("is_pdf"):
            # PDF nativo — envia direto para API Anthropic como documento
            image_b64 = first["b64"]
            mime_type = "application/pdf"
        else:
            # PDF convertido em imagens — mescla todas as páginas numa única imagem vertical
            # Isso garante que o agente veja frente E verso do rótulo
            from PIL import Image as _PIL
            page_imgs = []
            for pg in pages:
                raw_bytes = base64.b64decode(pg["b64"])
                proc_bytes, _ = preprocess_image(raw_bytes, pg["mime"])
                page_imgs.append(_PIL.open(io.BytesIO(proc_bytes)))

            if len(page_imgs) == 1:
                # Página única — usa direto
                buf = io.BytesIO()
                page_imgs[0].save(buf, "JPEG", quality=95)
                processed_bytes = buf.getvalue()
            else:
                # Múltiplas páginas — empilha verticalmente com separador
                total_w = max(img.width for img in page_imgs)
                sep = 20  # pixels de separação entre páginas
                total_h = sum(img.height for img in page_imgs) + sep * (len(page_imgs) - 1)
                merged = _PIL.new("RGB", (total_w, total_h), (200, 200, 200))
                y_offset = 0
                for img in page_imgs:
                    # Centraliza horizontalmente se larguras diferentes
                    x_offset = (total_w - img.width) // 2
                    merged.paste(img, (x_offset, y_offset))
                    y_offset += img.height + sep
                buf = io.BytesIO()
                merged.save(buf, "JPEG", quality=95)
                processed_bytes = buf.getvalue()

            mime_type = "image/jpeg"
            image_b64 = base64.b64encode(processed_bytes).decode("utf-8")
            if len(pages) > 1:
                obs = (obs + " " if obs else "") + f"[PDF com {len(pages)} páginas — frente e verso incluídos na análise]"
    else:
        mime_map = {
            "image/jpeg": "image/jpeg",
            "image/jpg": "image/jpeg",
            "image/png": "image/png",
            "image/webp": "image/webp",
            "image/gif": "image/gif",
            "image/bmp": "image/jpeg",
        }
        raw_mime = mime_map.get(content_type, "image/jpeg")
        # Pré-processa: garante resolução mínima 1500px para leitura de texto
        processed_bytes, mime_type = preprocess_image(contents, raw_mime)
        image_b64 = base64.b64encode(processed_bytes).decode("utf-8")

    return StreamingResponse(
        stream_validation(image_b64, mime_type, obs, orgao),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: EVAL
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/eval")
async def avaliar_rotulo(
    imagem: UploadFile = File(...),
    gabarito: str = Form(...),
):
    if not ANTHROPIC_API_KEY:
        return JSONResponse({"error": "ANTHROPIC_API_KEY não configurada"},
                            headers={"Access-Control-Allow-Origin": "*"})
    try:
        gab = json.loads(gabarito)
    except Exception:
        return JSONResponse({"error": "Gabarito inválido"},
                            headers={"Access-Control-Allow-Origin": "*"})

    contents = await imagem.read()
    mime_map = {"image/jpeg": "image/jpeg", "image/jpg": "image/jpeg",
                "image/png": "image/png", "image/webp": "image/webp"}
    raw_mime = mime_map.get(imagem.content_type, "image/jpeg")
    processed_bytes, mime_type = preprocess_image(contents, raw_mime)
    image_b64 = base64.b64encode(processed_bytes).decode("utf-8")

    obs = f"{gab.get('produto', '')} {gab.get('categoria', '')}".strip()
    orgao = gab.get("orgao", "")
    categories = detect_categories(obs)
    kb_text = await get_kb_for_categories(categories) if categories else ""
    kb_section = f"## LEGISLAÇÃO ESPECÍFICA\n{kb_text}\n---" if kb_text else ""
    system_prompt = SP_VALIDACAO.format(kb_section=kb_section)

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2500,
        "temperature": 0,
        "stream": True,
        "system": system_prompt,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": image_b64}},
            {"type": "text", "text": f"Valide este rótulo. Produto: {obs}"},
        ]}],
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    relatorio = ""

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", "https://api.anthropic.com/v1/messages",
                                  json=payload, headers=headers) as response:
            if response.status_code != 200:
                return JSONResponse({"error": "Erro na API Claude"},
                                    headers={"Access-Control-Allow-Origin": "*"})
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                raw = line[6:].strip()
                if raw == "[DONE]":
                    break
                try:
                    ev = json.loads(raw)
                    if ev.get("type") == "content_block_delta" and \
                       ev.get("delta", {}).get("type") == "text_delta":
                        relatorio += ev["delta"]["text"]
                except Exception:
                    continue

    erros_conhecidos = gab.get("erros_conhecidos", [])
    detalhes = []
    for erro in erros_conhecidos:
        campo = erro["campo"]
        esperado = erro["status"]
        detectado = detectar_status_campo(relatorio, campo)
        detalhes.append({
            "campo": campo,
            "nome": CAMPOS_NOME.get(campo, ""),
            "esperado": esperado,
            "detectado": detectado,
            "acertou": detectado == esperado,
            "descricao_gabarito": erro.get("descricao", ""),
            "norma": erro.get("norma", ""),
        })

    total = len(detalhes)
    acertos = sum(1 for d in detalhes if d["acertou"])

    return JSONResponse({
        "produto": gab.get("produto", ""),
        "relatorio_completo": relatorio,
        "score_agente": extrair_score(relatorio),
        "score_esperado": gab.get("score_esperado"),
        "veredicto_agente": extrair_veredicto(relatorio),
        "veredicto_esperado": gab.get("veredicto_esperado", "").upper(),
        "precisao_pct": round(acertos / total * 100) if total > 0 else 100,
        "erros_avaliados": total,
        "erros_acertados": acertos,
        "detalhes": detalhes,
    }, headers={"Access-Control-Allow-Origin": "*"})


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH + KB PRELOAD
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "ValidaRótulo IA v6",
        "kb_categories": len(MAPA_URLS),
        "kb_cached": list(_kb_cache.keys()),
        "endpoints": ["/validar", "/eval", "/kb/preload", "/kb/status"],
    }


@app.get("/kb/preload")
async def preload_kb():
    """Pré-carrega todas as legislações em cache."""
    results = {}
    for category in MAPA_URLS:
        text = await get_kb_for_categories([category])
        results[category] = f"{len(text)} chars" if text else "erro/vazio"
    return {"status": "ok", "total": len(MAPA_URLS), "loaded": results}


@app.get("/kb/status")
def kb_status():
    """Mostra status atual do cache da KB."""
    return {
        "total_categories": len(MAPA_URLS),
        "cached": len(_kb_cache),
        "cached_categories": list(_kb_cache.keys()),
        "pending": [k for k in MAPA_URLS if k not in _kb_cache],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EXCEPTION HANDLER (garante CORS mesmo em crashes)
# ═══════════════════════════════════════════════════════════════════════════════
from fastapi import Request as _Request

@app.exception_handler(Exception)
async def global_exception_handler(request: _Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"},
    )

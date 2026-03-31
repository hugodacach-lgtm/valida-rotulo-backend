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

app = FastAPI(title="ValidaRótulo IA v7 — Cobertura Universal: POA + Vegetais + Bebidas + Suplementos")
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

    # ── CÁRNEOS — GAPS FECHADOS ───────────────────────────────────────────
    "pate":                   ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN202000RTcrneosalmondegakibe.pdf"],
    "prato_pronto_poa":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN62001RTcarneospaletasalgadosempanadospresserranopratopronto.pdf"],
    "funcional_poa":          [
        "https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-267-de-22-de-setembro-de-2005-13651025",
        "https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN762018RTleitecrurefrleitepasteuhomogleitefluido.pdf",
    ],
    "jerked_beef":            ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN222000RTjerkedbeef.pdf"],
    "carne_sol":              ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN922020RTCharqueCarneSalgadaMidoSalgado.pdf"],
    "frango_inteiro":         ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port14852025PadrocategoriaenomeclaturaPOA.pdf"],

    # ── LATICÍNIOS — GAPS FECHADOS ────────────────────────────────────────
    "queijo_suico_gruyere":   ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port1461996RTqueijomanteigacremedeleitegorduralctealeitefluido.pdf"],
    "queijo_gouda_edam":      ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port1461996RTqueijomanteigacremedeleitegorduralctealeitefluido.pdf"],
    "creme_azedo":            ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN232012RTnata.pdf"],
    "miudos_visceras":        ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port14852025PadrocategoriaenomeclaturaPOA.pdf"],
    "peru_pato":              ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port14852025PadrocategoriaenomeclaturaPOA.pdf"],
    "leite_cabra":            ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port1461996RTqueijomanteigacremedeleitegorduralctealeitefluido.pdf"],
    "ovo_codorna":            ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port012020RTovosdemesadeovosparasementeovoscaipiras.pdf"],
    "queijo_provolone":       ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN732020RTqueijoprovolone.pdf"],
    "queijo_brie_camembert":  ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/Port1461996RTqueijomanteigacremedeleitegorduralctealeitefluido.pdf"],
    "bebida_lactea":          ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN162005RTbebidalactea.pdf"],
    "composto_lacteo":        ["https://www.gov.br/agricultura/pt-br/assuntos/inspecao/produtos-animal/legislacao/IN282007RTcompostolacteo.pdf"],

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

    # ════════════════════════════════════════════════════════════════════════
    # CATEGORIAS NÃO-POA — ANVISA + MAPA (FASE 2)
    # ════════════════════════════════════════════════════════════════════════

    # ── CEREAIS, PÃES, MASSAS, BISCOITOS ─────────────────────────────────
    "cereais_pao_massa":      ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-711-de-1-de-julho-de-2022-413249064"],
    "alimentos_integrais":    ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-712-de-1-de-julho-de-2022-413249083"],
    "farinhas_amidos":        ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-711-de-1-de-julho-de-2022-413249064"],
    "biscoito_bolacha":       ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-711-de-1-de-julho-de-2022-413249064"],
    "macarrao_massa":         ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-711-de-1-de-julho-de-2022-413249064"],

    # ── ÓLEOS E GORDURAS ─────────────────────────────────────────────────
    "oleos_gorduras":         ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+270+de+22+de+setembro+de+2005.pdf"],
    "azeite_oliva":           ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+270+de+22+de+setembro+de+2005.pdf"],
    "margarina":              ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+270+de+22+de+setembro+de+2005.pdf"],

    # ── AÇÚCAR, MEL VEGETAL E PRODUTOS AÇUCARADOS ───────────────────────
    "acucar_derivados":       ["https://www.planalto.gov.br/ccivil_03/decreto-lei/del0986.htm"],
    "chocolate_cacau":        ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+264_2005.pdf"],
    "doces_geleias":          ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+272_2005.pdf"],
    "sorvete_gelado":         ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+266_2005.pdf"],

    # ── FRUTAS, HORTALIÇAS E CONSERVAS ───────────────────────────────────
    "conservas_vegetais":     ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+272_2005.pdf"],
    "frutas_processadas":     ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+272_2005.pdf"],
    "cogumelos":              ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+272_2005.pdf"],

    # ── CONDIMENTOS, MOLHOS E TEMPEROS ───────────────────────────────────
    "condimentos_temperos":   ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+276_2005.pdf"],
    "molhos_ketchup":         ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+276_2005.pdf"],
    "vinagre":                ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+278_2005.pdf"],
    "cafe_cevada_cha":        ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+277_2005.pdf"],

    # ── LEGUMINOSAS E GRÃOS ──────────────────────────────────────────────
    "leguminosas_graos":      ["https://www.planalto.gov.br/ccivil_03/decreto-lei/del0986.htm"],
    "feijao_ervilha_graos":   ["https://www.planalto.gov.br/ccivil_03/decreto-lei/del0986.htm"],

    # ── BEBIDAS (expansão) ────────────────────────────────────────────────
    "suco_néctar":            ["https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2009/decreto/d6871.htm"],
    "refrigerante":           ["https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2009/decreto/d6871.htm"],
    "agua_mineral":           ["https://www.planalto.gov.br/ccivil_03/leis/l9433.htm"],
    "cerveja":                ["https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2009/decreto/d6871.htm"],
    "vinho":                  ["https://www.planalto.gov.br/ccivil_03/leis/l7678.htm"],
    "cachaça_destilados":     ["https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2009/decreto/d6871.htm"],
    "bebida_energetica":      ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-727-de-1-de-julho-de-2022-413249279"],
    "isotonica":              ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-727-de-1-de-julho-de-2022-413249279"],

    # ── SUPLEMENTOS ALIMENTARES ──────────────────────────────────────────
    "suplementos_rdc243_v2":  ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-243-de-26-de-julho-de-2018-41232201"],
    "suplementos_in28_v2":    ["https://www.in.gov.br/en/web/dou/-/instrucao-normativa-n-28-de-26-de-julho-de-2018-41232253"],
    "proteina_po":            ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-243-de-26-de-julho-de-2018-41232201"],
    "vitaminas_minerais":     ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-243-de-26-de-julho-de-2018-41232201"],

    # ── ALIMENTOS PARA FINS ESPECIAIS ────────────────────────────────────
    "dieta_diabetico":        ["https://antigo.anvisa.gov.br/documents/33916/392655/resolucao+29-98.pdf"],
    "formula_infantil":       ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-241-de-26-de-julho-de-2018-41232198"],
    "alimento_celíaco":       ["https://www.planalto.gov.br/ccivil_03/leis/2003/l10.674.htm"],

    # ── SNACKS, SALGADINHOS E INDUSTRIALIZADOS MISTOS ───────────────────
    "salgadinhos_snacks":     ["https://www.in.gov.br/en/web/dou/-/resolucao-rdc-n-711-de-1-de-julho-de-2022-413249064"],
    "barrinha_cereal":        ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+263_2005.pdf"],
    "amendoim_castanhas":     ["https://antigo.anvisa.gov.br/documents/33916/392655/RDC+276_2005.pdf"],
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

    # ════════════════════════════════════════════════════════════════════
    # CATEGORIAS NÃO-POA (Fase 2)
    # ════════════════════════════════════════════════════════════════════

    # ── CEREAIS, PÃES, MASSAS, BISCOITOS ─────────────────────────────────
    "cereais_pao_massa":   ["pão", "pao", "bisnaguinha", "baguete", "macarrão", "macarrao",
                            "massa", "espaguete", "lasanha", "arroz", "aveia", "granola",
                            "muesli", "cereal matinal", "biscoito", "bolacha", "wafer",
                            "crackers", "torrada"],
    "farinhas_amidos":     ["farinha de trigo", "farinha de milho", "farinha de arroz",
                            "amido de milho", "maisena", "fécula", "polvilho", "tapioca",
                            "fubá", "farelo", "flocos"],
    "biscoito_bolacha":    ["biscoito", "bolacha", "wafer", "cookie", "crackers"],
    "macarrao_massa":      ["macarrão", "macarrao", "massa", "espaguete", "penne",
                            "fusilli", "lasanha", "talharim", "nhoque"],
    "alimentos_integrais": ["integral", "grão inteiro", "cereal integral", "pão integral",
                            "farinha integral", "macarrão integral"],

    # ── ÓLEOS, GORDURAS E MARGARINAS ─────────────────────────────────────
    "oleos_gorduras":      ["óleo", "oleo", "gordura vegetal", "óleo de soja",
                            "óleo de girassol", "óleo de canola", "óleo de milho",
                            "óleo de palma", "óleo de coco"],
    "azeite_oliva":        ["azeite", "azeite de oliva", "olive oil", "azeite extra virgem"],
    "margarina":           ["margarina", "creme vegetal", "gordura vegetal culinária"],

    # ── AÇÚCAR E PRODUTOS AÇUCARADOS ─────────────────────────────────────
    "acucar_derivados":    ["açúcar", "acucar", "açúcar refinado", "açúcar cristal",
                            "açúcar mascavo", "açúcar demerara", "rapadura", "melado"],
    "chocolate_cacau":     ["chocolate", "cacau", "achocolatado", "creme de avelã",
                            "trufas", "bombom"],
    "doces_geleias":       ["geleia", "compota", "doce de frutas", "marmelada",
                            "goiabada", "pasta de amendoim"],
    "sorvete_gelado":      ["sorvete", "picolé", "picole", "gelato", "frozen", "sorbet"],

    # ── FRUTAS, HORTALIÇAS E CONSERVAS ───────────────────────────────────
    "conservas_vegetais":  ["conserva", "picles", "ervilha enlatada", "milho enlatado",
                            "tomate pelado", "extrato de tomate", "polpa de tomate",
                            "palmito", "azeitona"],
    "frutas_processadas":  ["polpa de fruta", "purê de fruta", "fruta desidratada",
                            "fruta seca", "uva passa", "banana passa"],
    "cogumelos":           ["cogumelo", "shitake", "champignon", "funghi"],

    # ── CONDIMENTOS, MOLHOS E TEMPEROS ───────────────────────────────────
    "condimentos_temperos":["tempero", "condimento", "pimenta", "colorau", "urucum",
                            "alho em pó", "cebola em pó", "curry", "curcuma", "canela",
                            "cominho", "páprica", "sal temperado", "caldo em cubo",
                            "caldo em pó", "sazon"],
    "molhos_ketchup":      ["molho", "ketchup", "maionese", "mostarda", "shoyu",
                            "molho de soja", "molho inglês", "molho barbecue", "pesto"],
    "vinagre":             ["vinagre", "aceto", "vinagre de maçã", "vinagre balsâmico"],
    "cafe_cevada_cha":     ["café", "cafe", "nescafé", "espresso", "cevada",
                            "chá", "cha", "erva mate", "mate", "camomila"],

    # ── LEGUMINOSAS E GRÃOS ──────────────────────────────────────────────
    "leguminosas_graos":   ["feijão", "feijao", "lentilha", "grão de bico", "ervilha",
                            "fava", "quinoa", "trigo em grão"],
    "feijao_ervilha_graos":["feijão carioca", "feijão preto", "feijão branco",
                            "grão de bico", "lentilha vermelha"],

    # ── BEBIDAS ──────────────────────────────────────────────────────────
    "suco_néctar":         ["suco", "néctar", "nectar", "suco de laranja", "suco de uva",
                            "suco integral", "néctar de fruta", "refresco", "polpa de açaí"],
    "refrigerante":        ["refrigerante", "coca-cola", "pepsi", "guaraná", "fanta",
                            "sprite", "água tônica", "cola"],
    "agua_mineral":        ["água mineral", "agua mineral", "água com gás",
                            "água saborizada", "água aromatizada"],
    "cerveja":             ["cerveja", "chope", "lager", "ale", "pilsen", "ipa", "stout",
                            "weiss", "cerveja sem álcool", "cerveja zero"],
    "vinho":               ["vinho", "espumante", "champagne", "prosecco",
                            "vinho tinto", "vinho branco", "vinho rosé"],
    "cachaça_destilados":  ["cachaça", "cachaca", "pinga", "aguardente", "vodka",
                            "rum", "whisky", "gin", "tequila", "conhaque", "licor"],
    "bebida_energetica":   ["energético", "energetico", "red bull", "monster",
                            "energy drink", "bebida energizante"],
    "isotonica":           ["isotônico", "isotonico", "gatorade", "powerade",
                            "bebida esportiva", "bebida hidratante"],

    # ── SUPLEMENTOS ALIMENTARES ──────────────────────────────────────────
    "proteina_po":         ["whey", "proteína em pó", "proteina em po", "proteína isolada",
                            "proteína concentrada", "caseína", "albumina",
                            "proteína vegetal", "proteína de ervilha"],
    "vitaminas_minerais":  ["vitamina c", "vitamina d", "vitamina b12", "complexo b",
                            "multivitamínico", "zinco", "magnésio", "ômega 3",
                            "fish oil", "colágeno hidrolisado"],
    "suplementos_rdc243_v2":["suplemento", "bcaa", "creatina", "glutamina",
                              "termogênico", "pre-treino", "hipercalórico"],
    "dieta_diabetico":     ["diet", "zero açúcar", "sem açúcar adicionado", "diabético"],
    "formula_infantil":    ["fórmula infantil", "formula infantil", "leite maternizado"],

    # ── SNACKS E INDUSTRIALIZADOS MISTOS ────────────────────────────────
    "salgadinhos_snacks":  ["salgadinho", "snack", "chips", "doritos", "cheetos",
                            "batata frita", "amendoim crocante"],
    "barrinha_cereal":     ["barra de cereal", "barrinha", "granola bar",
                            "barra de proteína"],
    "amendoim_castanhas":  ["amendoim", "castanha", "nozes", "amêndoa", "amendoa",
                            "macadâmia", "avelã", "pistache", "mix de nuts"],

    # Carnes extras (mantido)
    "pate_bacon_copa":     ["patê", "pate", "copa"],
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

    # ── CARNES — GAPS FECHADOS ─────────────────────────────────────────────
    "pate":               ["patê", "pate", "patê de frango", "patê de fígado", "patê de presunto"],
    "prato_pronto_poa":   ["empanado", "nugget", "steak de frango", "bife empanado", "lasanha",
                           "lasanha com carne", "croquete", "prato pronto", "semiprontos",
                           "produto cárneo elaborado", "hambúrguer recheado", "cordon bleu"],
    "funcional_poa":      ["leite com cálcio", "leite enriquecido", "leite com vitaminas",
                           "leite com ômega", "ovo enriquecido", "ovo com ômega", "probiótico",
                           "prebiótico", "lactobacillus", "bifidobacterium", "leite funcional",
                           "iogurte funcional", "alimento funcional", "reduzido em gordura"],
    "jerked_beef":        ["jerked beef", "jerk beef", "carne bovina salgada", "carne curada"],
    "carne_sol":          ["carne de sol", "carne do sol", "carne sol"],
    "frango_inteiro":     ["frango inteiro", "frango resfriado", "frango congelado", "galeto", "frango caipira"],
    "miudos_visceras":    ["fígado", "figado", "coração bovino", "coracao bovino", "rim bovino", "língua bovina",
                           "lingua bovina", "bucho", "mocotó", "mocoto", "tutano", "rabo bovino",
                           "moela", "coração de frango", "fígado de frango", "figado de frango", "miúdo", "miudo"],
    "peru_pato":          ["peru", "peito de peru", "coxa de peru", "pato", "carne de pato", "pato inteiro"],
    "leite_cabra":        ["leite de cabra", "queijo de cabra", "iogurte de cabra"],
    "ovo_codorna":        ["ovo de codorna", "ovos de codorna"],
    "queijo_brie_camembert": ["brie", "camembert", "queijo brie", "queijo camembert"],
    "queijo_provolone":   ["provolone", "queijo provolone"],
    "paleta_salgada":     ["paleta cozida", "empanado", "nugget", "presunto serrano", "prato pronto"],
    "corned_beef":        ["corned beef", "carne enlatada", "carne em conserva"],

    # ── LATICÍNIOS — GAPS FECHADOS ─────────────────────────────────────────
    "queijo_suico_gruyere":["queijo suíço", "queijo suico", "gruyère", "gruyere", "emmental", "emental"],
    "queijo_gouda_edam":   ["gouda", "edam", "queijo holandês", "queijo holandes"],
    "creme_azedo":         ["creme azedo", "sour cream", "crème fraîche"],
    "bebida_lactea":       ["bebida láctea", "bebida lactea", "iogurte bebível", "iogurte para beber"],
    "composto_lacteo":     ["composto lácteo", "composto lacteo", "alimento lácteo composto"],

    # ── PESCADO — REGIONAIS E GAPS ─────────────────────────────────────────
    "pescado_fresco":      ["peixe", "pescado", "tilápia", "tilapia", "salmão", "salmao", "atum",
                            "sardinha", "merluza", "badejo", "pintado", "dourado", "robalo", "tainha",
                            "corvina", "pacu", "tambaqui", "pirarucu", "surubim", "garoupa",
                            "linguado", "pescada", "cação", "cacao", "tubarão"],

    # ════════════════════════════════════════════════════════════════════════
    # NÃO-POA — PRODUTOS VEGETAIS, INDUSTRIALIZADOS, BEBIDAS, SUPLEMENTOS
    # ════════════════════════════════════════════════════════════════════════
    "cereais_rdc711":          ["arroz branco", "milho", "fubá", "fuba", "amido de milho",
                                "farinha de trigo", "farinha de milho", "farinha de arroz",
                                "flocos de aveia", "flocos de milho", "aveia em flocos",
                                "canjica", "quirera", "pipoca", "polenta"],
    "cereais_integrais_rdc712":["integral", "grão inteiro", "grain", "farelo de trigo",
                                "farelo de aveia", "farinha integral", "cereal integral"],
    "frutas_hortalicas_rdc714":["conserva de legume", "palmito", "milho em conserva",
                                "ervilha em conserva", "tomate pelado", "extrato de tomate",
                                "purê de tomate", "passata", "molho de tomate",
                                "picles", "azeitona", "alcaparra"],
    "acucares_rdc713":         ["açúcar cristal", "açúcar refinado", "açúcar demerara",
                                "açúcar mascavo", "açúcar orgânico", "açúcar impalpável",
                                "rapadura", "melado", "melaço"],
    "oleos_gorduras_rdc270":   ["óleo de soja", "oleo de soja", "óleo de girassol",
                                "óleo de canola", "óleo de milho", "azeite de oliva",
                                "azeite extra virgem", "óleo de côco", "gordura vegetal",
                                "banha", "gordura de palma", "margarina", "creme vegetal"],
    "sucos_nectares_in49":     ["suco de", "néctar de", "nectar de", "refresco de",
                                "bebida de fruta", "suco integral", "suco concentrado",
                                "polpa de fruta", "smoothie"],
    "cerveja_in14":            ["cerveja", "chope", "chopp", "ale", "lager", "pilsen",
                                "weiss", "weizen", "ipa", "stout", "porter", "bock",
                                "cerveja artesanal", "craft beer"],
    "vinho_lei7678":           ["vinho tinto", "vinho branco", "vinho rosé", "vinho rose",
                                "espumante", "champagne", "prosecco", "cava",
                                "vinho frisante", "vinho licoroso", "vinho do porto"],
    "suplementos_rdc243":      ["suplemento alimentar", "whey protein", "whey concentrado",
                                "whey isolado", "creatina", "bcaa", "aminoácido essencial",
                                "colágeno hidrolisado", "multivitamínico", "termogênico",
                                "pré-treino", "pre-treino", "hipercalórico", "mass gainer",
                                "albumina", "caseína", "caseina", "proteína vegetal em pó"],
    "suplementos_proteinas":   ["proteína em pó", "proteina em po", "proteína concentrada",
                                "proteína isolada", "blend proteico"],
    "regularizacao_rdc843":    ["biscoito", "bolacha", "cookie", "wafer",
                                "chocolate", "barra de chocolate", "bombom", "trufa",
                                "sorvete", "gelado", "picolé", "bolo", "torta",
                                "macarrão instantâneo", "lamen", "lámen", "ramen",
                                "salgadinho", "chips", "snack", "barra de cereal",
                                "ketchup", "mostarda industrial", "maionese",
                                "molho shoyu", "shoyu", "molho inglês",
                                "fermento", "levedura", "extrato de levedura"],
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


# ══════════════════════════════════════════════════════════════════════════════
# NORMAS ESTADUAIS SIE — DIFERENÇAS EM RELAÇÃO AO FEDERAL
# Base: manuais CISPOA-RS, SISP-SP, IMA-MG, CIDASC-SC, ADAPAR-PR
# Conteúdo de rótulo federal (MAPA + ANVISA) aplica-se integralmente a todos.
# O que está aqui são adições/especificidades estaduais.
# ══════════════════════════════════════════════════════════════════════════════

CISPOA_RS_FALLBACK = """NORMAS COMPLEMENTARES CISPOA-RS (Coordenadoria de Inspeção de Produtos de Origem Animal - RS)

BASE LEGAL: Decreto Estadual RS nº 37.106/1996 + Portarias CISPOA vigentes.

DIFERENÇAS DO FEDERAL:
1. DENOMINAÇÃO DE VENDA:
   • O RS exige que a denominação inclua OBRIGATORIAMENTE a espécie animal por extenso (ex: "Linguiça Suína Frescal", não apenas "Linguiça Frescal")
   • Queijos artesanais: deve constar "Artesanal" na denominação se produzido artesanalmente

2. IDENTIFICAÇÃO DO FABRICANTE:
   • Além do federal, deve constar o número de registro no CISPOA no formato: "CISPOA/RS Nº XXXX" 
   • Estabelecimentos de agricultura familiar: aceita CPF ao invés de CNPJ + menção "Agricultura Familiar"

3. CAMPO SIE (específico RS):
   • Carimbo oval com: "SIE/RS" + número ou "CISPOA" + número
   • Sigla aceita: "SIE RS", "CISPOA RS", "INPOA RS"
   • Alguns selos mais antigos usam apenas número — aceitar se oval e legível

4. LATICÍNIOS ARTESANAIS RS:
   • Queijos artesanais com maturação: prazo de validade diferenciado (Lei Estadual RS 15.136/2018)
   • "Queijo Artesanal" deve mencionar município/região de origem se for indicação geográfica
   • Não exige tabela nutricional para queijos artesanais com superfície ≤100cm² (mesma isenção federal)

5. PRODUTOS DE PESCADO RS:
   • Pescado de piscicultura gaúcha: pode incluir menção opcional "Piscicultura Gaúcha"
   • Mesmas exigências federais para tabela nutricional e alérgenos

OBSERVAÇÃO: Para rotulagem federal (SIF), o CISPOA não adiciona requisitos de conteúdo. 
As adições acima são exclusivas para produtos com registro CISPOA."""

SISP_SP_FALLBACK = """NORMAS COMPLEMENTARES SISP-SP (Serviço de Inspeção do Estado de São Paulo)

BASE LEGAL: Decreto Estadual SP nº 24.528/1986 + Portaria SAA-SP nº 06/2011 e atualizações.

DIFERENÇAS DO FEDERAL:
1. IDENTIFICAÇÃO DO FABRICANTE:
   • Deve constar número de registro SISP no formato: "SISP Nº XXXX" ou "SIE SP XXXX"
   • Resolução SAA-SP exige declaração do município de fabricação por extenso (não apenas endereço)

2. CAMPO SIE (específico SP):
   • Carimbo oval: "SISP" + número ou "SIE SP" + número
   • Cor do carimbo: preferencialmente preto ou azul escuro sobre fundo branco
   • Não aceita carimbos apenas com número sem sigla SISP ou SIE SP

3. LATICÍNIOS SP:
   • Queijo Minas Artesanal produzido em SP: pode usar denominação regional se certificado pelo IEA/SP
   • Manteiga de garrafa: denominação "Manteiga da Terra" aceita em SP conforme Port. SAA

4. PRODUTOS CÁRNEOS SP:
   • Linguiça "tipo toscana" produzida em SP: deve especificar se suína pura (sem proteína vegetal)
   • Referências ao "Padrão Paulista" ou regionais são permitidas se tecnicamente corretas

OBSERVAÇÃO: SP tem volume alto de registros SISP em laticínios artesanais e embutidos de pequenos produtores. A maioria dos requisitos espelha o federal."""

IMA_MG_FALLBACK = """NORMAS COMPLEMENTARES IMA-MG (Instituto Mineiro de Agropecuária)

BASE LEGAL: Decreto Estadual MG nº 44.864/2008 + Portarias IMA vigentes.

DIFERENÇAS DO FEDERAL:
1. IDENTIFICAÇÃO DO FABRICANTE:
   • Deve constar número de registro IMA-MG: "IMA/MG Nº XXXX" ou "SIE MG XXXX"
   • Para agroindústria familiar: pode constar DAP (Declaração de Aptidão ao PRONAF) ao invés de CNPJ

2. CAMPO SIE (específico MG):
   • Carimbo oval: "IMA MG" ou "SIE MG" + número
   • Queijos artesanais de Minas: carimbo específico "QUEIJO ARTESANAL DE MINAS" + microrregião

3. QUEIJOS ARTESANAIS MINEIROS (Lei Estadual MG 23.157/2018):
   • Denominação obrigatória: "Queijo Minas Artesanal" + microrregião certificada
     (Canastra, Serro, Serra da Canastra, Araxá, Cerrado, Campo das Vertentes, etc.)
   • NÃO precisa de tabela nutricional se embalagem ≤100cm² (mesma isenção federal)
   • DEVE constar: "Produto artesanal feito de leite cru" se for o caso
   • Prazo de validade diferenciado conforme maturação (Decreto MG 44.864/2008)
   • Identificação do produtor rural: pode ser CPF + nome do produtor

4. EMBUTIDOS ARTESANAIS MG:
   • Linguiça artesanal: pode usar denominação regional ("Linguiça Mineira") se tradicional
   • Origem animal: espécie obrigatória por extenso

OBSERVAÇÃO: MG tem o maior volume de produtos SIE com queijos artesanais certificados. 
As normas de queijo artesanal mineiro são as mais específicas do país."""

CIDASC_SC_FALLBACK = """NORMAS COMPLEMENTARES CIDASC-SC (Companhia Integrada de Desenvolvimento Agrícola de SC)

BASE LEGAL: Lei Estadual SC 12.117/2002 + Manual CIDASC de Rotulagem (versão 5.0/2023).

DIFERENÇAS DO FEDERAL:
1. IDENTIFICAÇÃO DO FABRICANTE:
   • Deve constar: "SIE/SC Nº XXXX" ou "CIDASC Nº XXXX"
   • Agroindústria familiar rural: deve constar "Estabelecimento de Agroindústria Rural Familiar"

2. CAMPO SIE (específico SC):
   • Carimbo oval: "SIE SC" + número ou "CIDASC" + número
   • SC aceita "SISC" (antigo) para estabelecimentos registrados antes de 2010

3. MEL E APÍCOLA SC:
   • Mel catarinense com indicação de flora: deve constar "Mel Monofloral" ou "Mel Silvestre/Multifloral"
   • Não exige tabela nutricional para embalagens ≤100cm²

4. EMBUTIDOS E DEFUMADOS SC:
   • Linguiça colonial catarinense: pode usar denominação "Colonial" se atender padrão SC
   • Salame colonial: idem, "Salame Colonial Catarinense" é denominação regional aceita

OBSERVAÇÃO: SC tem manual de rotulagem publicado e atualizado (2023) que é o mais completo 
do país para nível estadual. Disponível em cidasc.sc.gov.br."""

ADAPAR_PR_FALLBACK = """NORMAS COMPLEMENTARES ADAPAR-PR (Agência de Defesa Agropecuária do Paraná)

BASE LEGAL: Lei Estadual PR 14.978/2006 + Resolução ADAPAR vigente.

DIFERENÇAS DO FEDERAL:
1. IDENTIFICAÇÃO DO FABRICANTE:
   • Deve constar: "SIE/PR Nº XXXX" ou "ADAPAR Nº XXXX"

2. CAMPO SIE (específico PR):
   • Carimbo oval: "SIE PR" + número ou "ADAPAR" + número

3. ESPECIFICIDADES PR:
   • O PR praticamente espelha o federal — menor diferenciação entre os estados com SIE ativo
   • Queijos artesanais: mesmas regras federais, sem denominação regional específica certificada
   • Embutidos: sem adições ao federal

OBSERVAÇÃO: O PR tem exigências mais próximas ao federal. 
Foco principal em procedimentos de registro, não em conteúdo de rótulo."""

# Mapa de Estado → Fallback

# ──────────────────────────────────────────────────────────────────────────────
# PRATOS PRONTOS POA — RTIQ (IN 6/2001 + Port. 1485/2025)
# ──────────────────────────────────────────────────────────────────────────────
PRATO_PRONTO_POA_FALLBACK = """PRODUTOS CÁRNEOS ELABORADOS / PRATOS PRONTOS POA (IN 6/2001 + Port. 1485/2025)

CATEGORIAS COBERTAS: Empanados (nugget, steak, bife empanado), Lasanha com carne,
Quibe industrializado, Croquete de carne/frango, Hambúrguer recheado, Produto cárneo
semiprontos para consumo, Frango temperado inteiro/em partes.

DENOMINAÇÃO DE VENDA (Campo 1):
• Empanados: "Empanado de [espécie]" — ex: "Empanado de Frango", "Empanado Bovino"
• NÃO pode usar "filé" sem ser músculo inteiro: "Filé de Frango Empanado" exige músculo
• Nuggets: "Produto Cárneo Reestruturado Empanado de [espécie]" ou denominação consagrada
• Lasanha: "Lasanha com Carne Bovina" — deve identificar espécie
• Quibe: "Quibe Industrializado" ou "Kibe" — ambos aceitos pela Port. 1485/2025
• Croquete: "Croquete de [ingrediente principal]"

LISTA DE INGREDIENTES (Campo 2):
• Em empanados: declarar "Farinha de trigo" — implica CONTÉM GLÚTEN obrigatório
• CMS de aves em empanados: declarar "Carne Mecanicamente Separada de Aves (X%)"
• Proteína de soja em empanados: declarar % entre parênteses — limite máx. 4% (IN 6/2001)
• Ingredientes compostos (massa, molho): listar subingredientes entre parênteses
• Corante caramelo: declarar "Corante Caramelo (INS 150)" com classe e INS

TABELA NUTRICIONAL — PORÇÕES PADRÃO (IN 75/2020):
• Empanados (nugget, steak): porção = 100g (4 unidades médias)
• Hambúrguer recheado: porção = 80g
• Lasanha congelada: porção = 300g (1 porção individual)
• Quibe: porção = 100g (2 unidades)
• Croquete: porção = 80g (2 unidades)

FAIXAS TACO — PLAUSIBILIDADE NUTRICIONAL POR 100g:
EMPANADO DE FRANGO (industrializado):
• kcal: TACO 230-280 | Proteínas: mín 10g (IN 6/2001), típico 14-18g
• Gorduras totais: típico 12-18g | Carboidratos: típico 14-22g (farinha de trigo)
• Sódio: típico 500-900mg | Fibra: típico 0,5-2g (farinha)

EMPANADO BOVINO:
• kcal: TACO 220-270 | Proteínas: mín 10g, típico 13-17g
• Gorduras totais: típico 12-17g | Carboidratos: típico 12-20g
• Sódio: típico 500-900mg

NUGGET DE FRANGO:
• kcal: TACO 240-300 | Proteínas: mín 10g, típico 13-17g
• Gorduras totais: típico 14-20g | Carboidratos: típico 12-20g
• Sódio: típico 500-1000mg

LASANHA COM CARNE BOVINA (congelada):
• kcal: TACO 100-160 | Proteínas: típico 6-10g
• Gorduras totais: típico 4-9g | Carboidratos: típico 12-20g
• Sódio: típico 400-700mg

QUIBE / KIBE INDUSTRIALIZADO:
• kcal: TACO 180-250 | Proteínas: mín 12g, típico 12-17g
• Gorduras totais: típico 10-18g | Carboidratos: típico 8-14g (trigo integral)
• Sódio: típico 350-700mg

ALERTA ESPECIAL: carboidratos altos (>8g/100g) em produtos cárneos elaborados
são normais e esperados — indicam adição de farinha, amido ou proteína vegetal."""

# ──────────────────────────────────────────────────────────────────────────────
# PRODUTO DUAL MAPA + ANVISA — ALIMENTOS FUNCIONAIS DE ORIGEM ANIMAL
# ──────────────────────────────────────────────────────────────────────────────
DUAL_MAPA_ANVISA_FALLBACK = """ALIMENTOS FUNCIONAIS / ENRIQUECIDOS DE ORIGEM ANIMAL
BASE LEGAL: RDC 267/2003 (alegações funcionais) + RDC 18/1999 (bioativos) + IN MAPA específica

PRODUTOS TÍPICOS COM REGISTRO DUAL:
• Leite enriquecido com cálcio, ferro, vitaminas A/D, ômega-3 (UHT ou pasteurizado)
• Ovo enriquecido com ômega-3, vitamina E ou selênio
• Iogurte com probióticos (Lactobacillus, Bifidobacterium)
• Queijo com reduzido teor de gordura + fibras adicionadas
• Leite fermentado funcional (tipo Yakult/Activia)

CAMPO 1 — DENOMINAÇÃO:
• Produto MAPA: "Leite UHT Integral" / "Iogurte Natural" (denominação técnica obrigatória)
• Claim funcional ANVISA: pode adicionar na embalagem mas NÃO na denominação técnica
  ✅ CORRETO: "Leite UHT Integral — Fonte de Cálcio" (claim separado da denominação)
  ❌ ERRADO: "Leite Cálcio Integral" (modifica a denominação técnica)
• Probióticos: "Iogurte com [microrganismo]" aceito se souche declarado e viable count comprovado

CAMPO 2 — LISTA DE INGREDIENTES:
• Nutrientes adicionados: declarar em ordem decrescente normalmente
• Vitaminas/minerais adicionados: declarar nome completo + função
  Ex: "Vitamina D (colecalciferol) — antioxidante" ou apenas nome
• Probióticos: declarar o nome completo do microrganismo
  Ex: "Fermentos lácteos (Lactobacillus acidophilus, Bifidobacterium lactis)"
• Ômega-3: declarar fonte — "Óleo de peixe (fonte de ômega-3)"

CAMPO 9 — TABELA NUTRICIONAL:
• Nutrientes objeto de alegação DEVEM ser declarados (obrigatório — RDC 267/2003)
• Vitaminas e minerais: declarar em mg ou µg + % VD
• Probióticos UFC: podem ser declarados em nota separada (não na tabela principal)
• Ômega-3: declarar EPA + DHA separadamente se for o claim

CAMPO 10 — LUPA FRONTAL:
• Atenção: produto enriquecido com sódio pode acionar lupa "ALTO EM SÓDIO" mesmo sendo
  produto "saudável" — verificar se sódio ≥600mg/100g mesmo com claims positivos

ALEGAÇÕES PROIBIDAS (RDC 267/2003 Art. 3):
• "Cura", "trata", "previne" doenças específicas — PROIBIDO
• "Fortalece o sistema imune" sem substantiação científica — PROIBIDO
• "Reduz o risco de doenças cardíacas" só se ômega-3 EPA+DHA ≥600mg/porção
• Probióticos: só "contribui para o equilíbrio da flora intestinal" (alegação aprovada pela ANVISA)
• Cálcio: "contribui para manutenção de ossos e dentes" (aprovada)"""

# ──────────────────────────────────────────────────────────────────────────────
# NORMAS SIE — 21 ESTADOS RESTANTES
# ──────────────────────────────────────────────────────────────────────────────
SIE_OUTROS_ESTADOS_FALLBACK = """NORMAS SIE — ESTADOS SEM ADIÇÕES RELEVANTES AO FEDERAL
(AC, AL, AM, AP, CE, DF, ES, GO, MA, MS, MT, PA, PB, PE, PI, RJ, RN, RO, RR, SE, TO)

REGRA GERAL: Todos esses estados adotam as normas federais (MAPA + ANVISA) integralmente
para conteúdo de rótulo. As diferenças são exclusivamente procedimentais (registro, formulários).

SIGLAS E ÓRGÃOS SIE POR ESTADO:
• AC (Acre): IDAF-AC — "SIE AC Nº XXXX"
• AL (Alagoas): ADEAL — "SIE AL Nº XXXX"
• AM (Amazonas): ADAF-AM — "SIE AM Nº XXXX"
• AP (Amapá): RURAP-AP — "SIE AP Nº XXXX"
• BA (Bahia): ADAB — "SIE BA Nº XXXX" | Ativo em pescado e mel
• CE (Ceará): ADAGRI-CE — "SIE CE Nº XXXX" | Ativo em pescado
• DF (Distrito Federal): SEAGRI-DF — "SIE DF Nº XXXX"
• ES (Espírito Santo): IDAF-ES — "SIE ES Nº XXXX"
• GO (Goiás): AGRODEFESA — "SIE GO Nº XXXX" | Ativo em bovinos
• MA (Maranhão): AGED-MA — "SIE MA Nº XXXX"
• MS (Mato Grosso do Sul): IAGRO-MS — "SIE MS Nº XXXX" | Ativo em bovinos
• MT (Mato Grosso): INDEA-MT — "SIE MT Nº XXXX" | Ativo em bovinos
• PA (Pará): ADEPARÁ — "SIE PA Nº XXXX" | Ativo em pescado
• PB (Paraíba): AESA-PB — "SIE PB Nº XXXX"
• PE (Pernambuco): ADAGRO-PE — "SIE PE Nº XXXX"
• PI (Piauí): ADAPI-PI — "SIE PI Nº XXXX"
• RJ (Rio de Janeiro): PESAGRO-RJ / SEAPEC — "SIE RJ Nº XXXX" | Ativo em laticínios e pescado
• RN (Rio Grande do Norte): IDEMA-RN / EMPARN — "SIE RN Nº XXXX"
• RO (Rondônia): IDARON — "SIE RO Nº XXXX"
• RR (Roraima): ADERR — "SIE RR Nº XXXX"
• SE (Sergipe): EMDAGRO — "SIE SE Nº XXXX"
• TO (Tocantins): ADAPEC-TO — "SIE TO Nº XXXX"

NOTAS ESPECÍFICAS:
• BA, PA, CE: produtos de pescado podem ter exigência de declarar "pescado artesanal" ou
  "pesca artesanal" se oriundo de colônias de pesca registradas — verificar se aplicável
• GO, MS, MT: bovinos — sem adições ao federal para conteúdo de rótulo
• RJ: laticínios artesanais fluminenses — mesmas regras de queijo artesanal (leite cru declarado)

CAMPO 8 — CARIMBO SIE:
• Formato oval obrigatório — IGUAL ao federal
• Deve conter: sigla do estado + "SIE" + número OR sigla do órgão estadual + número
  Ex válidos: "SIE RJ 1234", "IAGRO MS 456", "ADAB BA 789"
• Produtos fabricados nesses estados que circulam APENAS no estado de origem"""


SIE_ESTADO_MAP = {
    # Estados com normas específicas relevantes
    "RS": CISPOA_RS_FALLBACK, "CISPOA": CISPOA_RS_FALLBACK,
    "SP": SISP_SP_FALLBACK,   "SISP": SISP_SP_FALLBACK,
    "MG": IMA_MG_FALLBACK,    "IMA": IMA_MG_FALLBACK,
    "SC": CIDASC_SC_FALLBACK, "CIDASC": CIDASC_SC_FALLBACK,
    "PR": ADAPAR_PR_FALLBACK, "ADAPAR": ADAPAR_PR_FALLBACK,
    # 21 estados restantes — normas gerais SIE
    "AC": SIE_OUTROS_ESTADOS_FALLBACK, "IDAF": SIE_OUTROS_ESTADOS_FALLBACK,
    "AL": SIE_OUTROS_ESTADOS_FALLBACK, "ADEAL": SIE_OUTROS_ESTADOS_FALLBACK,
    "AM": SIE_OUTROS_ESTADOS_FALLBACK, "ADAF": SIE_OUTROS_ESTADOS_FALLBACK,
    "AP": SIE_OUTROS_ESTADOS_FALLBACK, "RURAP": SIE_OUTROS_ESTADOS_FALLBACK,
    "BA": SIE_OUTROS_ESTADOS_FALLBACK, "ADAB": SIE_OUTROS_ESTADOS_FALLBACK,
    "CE": SIE_OUTROS_ESTADOS_FALLBACK, "ADAGRI": SIE_OUTROS_ESTADOS_FALLBACK,
    "DF": SIE_OUTROS_ESTADOS_FALLBACK, "SEAGRI": SIE_OUTROS_ESTADOS_FALLBACK,
    "ES": SIE_OUTROS_ESTADOS_FALLBACK,
    "GO": SIE_OUTROS_ESTADOS_FALLBACK, "AGRODEFESA": SIE_OUTROS_ESTADOS_FALLBACK,
    "MA": SIE_OUTROS_ESTADOS_FALLBACK, "AGED": SIE_OUTROS_ESTADOS_FALLBACK,
    "MS": SIE_OUTROS_ESTADOS_FALLBACK, "IAGRO": SIE_OUTROS_ESTADOS_FALLBACK,
    "MT": SIE_OUTROS_ESTADOS_FALLBACK, "INDEA": SIE_OUTROS_ESTADOS_FALLBACK,
    "PA": SIE_OUTROS_ESTADOS_FALLBACK, "ADEPAR": SIE_OUTROS_ESTADOS_FALLBACK,
    "PB": SIE_OUTROS_ESTADOS_FALLBACK,
    "PE": SIE_OUTROS_ESTADOS_FALLBACK, "ADAGRO": SIE_OUTROS_ESTADOS_FALLBACK,
    "PI": SIE_OUTROS_ESTADOS_FALLBACK, "ADAPI": SIE_OUTROS_ESTADOS_FALLBACK,
    "RJ": SIE_OUTROS_ESTADOS_FALLBACK, "PESAGRO": SIE_OUTROS_ESTADOS_FALLBACK,
    "RN": SIE_OUTROS_ESTADOS_FALLBACK,
    "RO": SIE_OUTROS_ESTADOS_FALLBACK, "IDARON": SIE_OUTROS_ESTADOS_FALLBACK,
    "RR": SIE_OUTROS_ESTADOS_FALLBACK, "ADERR": SIE_OUTROS_ESTADOS_FALLBACK,
    "SE": SIE_OUTROS_ESTADOS_FALLBACK, "EMDAGRO": SIE_OUTROS_ESTADOS_FALLBACK,
    "TO": SIE_OUTROS_ESTADOS_FALLBACK, "ADAPEC": SIE_OUTROS_ESTADOS_FALLBACK,
}

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
        if doc.needs_pass:
            return [{"error": "PDF protegido por senha. Exporte o arquivo sem senha antes de enviar.", "is_error": True}]
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
SP_VALIDACAO = """Você é ValidaRótulo IA — o sistema mais completo de validação de rótulos de alimentos embalados do Brasil.
Cobre: POA (carnes, laticínios, ovos, pescados, mel), produtos vegetais, industrializados, bebidas e suplementos.

REGRAS ABSOLUTAS:
1. Analise CADA detalhe visível na imagem — texto, símbolos, formatação, cores, posicionamento
2. Se um elemento não está visível na arte do rótulo: registre como AUSENTE
3. Lote e validade NÃO fazem parte da arte do rótulo — são impressos na linha de produção. NÃO avalie esses campos.
4. Cite sempre a norma específica (número e ano) para cada avaliação
5. Nunca pule nenhum dos 12 campos obrigatórios
6. TEXTO EM CURVA/ARCO: leia ativamente textos curvos, arqueados ou em arco — comum em carimbos e denominações. Gire mentalmente a perspectiva. Não marque como NÃO VERIFICÁVEL apenas por estar em curva.
7. FONTE ESTILIZADA: se não for possível ler com certeza, descreva o que é visível e indique a incerteza — nunca ignore o campo.
8. CORTES COM OSSO: valores por 100g de produtos com osso (costela, bisteca, asa de frango) são naturalmente menores que TACO para carne pura — considere antes de alertar plausibilidade.
9. MIÚDOS/VÍSCERAS: não existe RTIQ de identidade e qualidade para miúdos. Use RIISPOA Art. 227+ e Port. 1485/2025. Não penalize ausência de RTIQ específico.
6. DETECTE O TIPO DE PRODUTO primeiro (POA / vegetal / industrializado / bebida / suplemento) para aplicar as regras corretas no Campo 8

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
NORMAS BASE — obrigatórias para TODOS os alimentos embalados:
• RDC 727/2022 (ANVISA) — rotulagem geral (denominação, ingredientes, fabricante, etc.)
• RDC 429/2020 + IN 75/2020 (ANVISA) — rotulagem nutricional obrigatória
• INMETRO Port. 249/2021 — conteúdo líquido e peso líquido
• Decreto 4.680/2003 + Port. 2658/2003 — transgênicos (símbolo T)
• Lei 10.674/2003 — glúten (CONTÉM / NÃO CONTÉM)
• RDC 715/2022 — lactose (CONTÉM LACTOSE)
• CDC Lei 8.078/1990 — código de defesa do consumidor
• Decreto-Lei 986/1969 — normas básicas de alimentos

NORMAS ESPECÍFICAS POR TIPO (aplicar conforme produto detectado):

POA — Produtos de Origem Animal:
• IN 22/2005 + Port. 240/2021 + Port. 449/2022 (MAPA) — rotulagem geral POA
• Port. SDA 1485/2025 — nomenclatura POA
• RTIQ específico por categoria (IN 4/2000, IN 20/2000, IN 22/2000, Port. 146/1996, etc.)

PRODUTOS VEGETAIS E INDUSTRIALIZADOS:
• RDC 711/2022 — cereais e derivados (arroz, trigo, milho, aveia, etc.)
• RDC 712/2022 — cereais integrais e produtos integrais
• RDC 714/2022 — frutas, hortaliças, cogumelos e similares
• RDC 713/2022 — açúcares e similares
• RDC 843/2024 + IN 281/2024 — regularização e isenção de registro ANVISA
• Decreto 6.871/2009 — bebidas em geral
• IN MAPA 14/2018 — cerveja
• IN MAPA 49/2018 — sucos de frutas e néctares

SUPLEMENTOS ALIMENTARES:
• RDC 243/2018 — suplementos alimentares (definição, categorias, rotulagem)
• IN 28/2018 — categorias de suplementos
• IN 76/2020 — proteínas para suplementos

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
CAMPO 8 — REGISTRO / INSPEÇÃO / NOTIFICAÇÃO
─────────────────────────────────────────────
Este campo se adapta conforme o tipo de produto detectado:

▶ PRODUTO DE ORIGEM ANIMAL — POA (carnes, embutidos, laticínios, ovos, pescados, mel):
   a) CARIMBO DE INSPEÇÃO OVAL obrigatório (não redondo, não retangular)
   b) Conteúdo por órgão:
      • SIF (federal): "SIF" + número do estabelecimento
      • SIE (estadual): sigla estadual (SISP, SIE-MG, CISPOA, etc.) + número
      • SIM (municipal): "SIM" + número municipal
   c) Número e sigla legíveis, posicionado em destaque

▶ BEBIDAS ALCOÓLICAS (vinho, cerveja, cachaça, destilados):
   a) Registro obrigatório no MAPA — Decreto 6.871/2009
   b) Número de registro MAPA deve constar no rótulo
   c) Para cerveja: "Registro no MAPA nº XXXXX" ou número de lote com rastreabilidade

▶ SUPLEMENTOS ALIMENTARES:
   a) Notificação ANVISA obrigatória — RDC 243/2018
   b) Deve constar: "Notificado ANVISA" + número ou "Dispensado de Registro" conforme RDC 843/2024
   c) Para produtos com alegações de saúde: registro ANVISA obrigatório

▶ ALIMENTOS INDUSTRIALIZADOS GERAIS (biscoito, macarrão, pão, chocolate, conservas, etc.):
   a) MAIORIA é isenta de registro ANVISA — RDC 843/2024 e IN 281/2024
   b) Verificar se há número de registro ANVISA (formato: XX.XXXX.XXXXX.XXX-X) ou
      informação de isenção — ambos são aceitos
   c) Produtos que EXIGEM registro: alegações funcionais/saúde, enriquecidos, para fins especiais,
      suplementos, fórmulas infantis
   d) Se não há menção de registro e produto é isento: ✅ CONFORME (maioria dos alimentos)

▶ PRODUTOS VEGETAIS IN NATURA (frutas, hortaliças, grãos, cereais não processados):
   a) Isentos de registro ANVISA — campos de registro/notificação não aplicáveis
   b) Verificar se há código de rastreabilidade ou identificação do produtor/embalador
   c) Registrar como ✅ N/A — Produto isento de registro

─────────────────────────────────────────────
CAMPO 9 — TABELA NUTRICIONAL (RDC 429/2020 + IN 75/2020)
─────────────────────────────────────────────

NÍVEL 1 — ESTRUTURA OBRIGATÓRIA
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
Valores por porção E por 100g/mL obrigatórios. Fundo BRANCO, letras PRETAS.

NÍVEL 2 — COERÊNCIA MATEMÁTICA
Calcule o valor energético esperado usando os valores por 100g declarados:
  kcal esperado = (Proteínas × 4) + (Carboidratos × 4) + (Gorduras totais × 9)
Compare com o kcal declarado. Tolerância: ±20% (permitido pela RDC 429/2020).
• Dentro de ±20% → ✅ CONFORME — valores coerentes
• Fora de ±20%   → ❌ NÃO CONFORME — valor energético não bate com os macros declarados
Se os valores por 100g não estiverem visíveis, calcule pela porção.

NÍVEL 3 — PLAUSIBILIDADE POR CATEGORIA (TACO 4ª ed. UNICAMP + RTIQ/MAPA)
Compare os valores declarados POR 100g com as faixas abaixo.
• Faixa TACO = valores analíticos reais (mín–máx esperado)
• Limite RTIQ = exigência legal (mínimo ou máximo)
• ✅ dentro da faixa | ⚠️ fora da faixa típica mas dentro do RTIQ | ❌ viola limite RTIQ
• 🔍 NÃO VERIFICÁVEL se os valores por 100g não estiverem legíveis

━━━ EMBUTIDOS CÁRNEOS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LINGUIÇA SUÍNA / PORCO (IN 4/2000):
• kcal: TACO 220-290 | Proteínas: mín 12g RTIQ, típico TACO 14-20g
• Gorduras totais: máx 30g RTIQ, típico TACO 17-25g | Gord.sat: típico TACO 6-9g
• Carboidratos: típico TACO 0-3g (>8g é incomum) | Sódio: típico TACO 700-1200mg

LINGUIÇA DE FRANGO (IN 4/2000):
• kcal: TACO 215-250 | Proteínas: mín 12g RTIQ, típico TACO 13-19g
• Gorduras totais: máx 30g RTIQ, típico TACO 15-22g
• Carboidratos: típico TACO 0-4g | Sódio: típico TACO 600-1100mg

LINGUIÇA BOVINA (IN 4/2000):
• kcal: TACO 200-270 | Proteínas: mín 12g RTIQ, típico TACO 14-20g
• Gorduras totais: máx 30g RTIQ, típico TACO 14-22g | Sódio: típico TACO 600-1000mg

SALSICHA (IN 4/2000):
• kcal: TACO 220-280 | Proteínas: mín 12g RTIQ, típico TACO 12-15g
• Gorduras totais: máx 30g RTIQ, típico TACO 18-26g | Gord.sat: típico TACO 6-9g
• Sódio: típico TACO 600-1100mg | Carboidratos: típico TACO 2-6g

MORTADELA (IN 4/2000):
• kcal: TACO 250-310 | Proteínas: mín 12g RTIQ, típico TACO 12-16g
• Gorduras totais: máx 30g RTIQ, típico TACO 20-28g | Gord.sat: típico TACO 8-11g
• Sódio: típico TACO 700-1200mg | Carboidratos: típico TACO 2-5g

HAMBÚRGUER BOVINO (IN 20/2000):
• kcal: TACO 200-260 | Proteínas: mín 15g RTIQ, típico TACO 13-20g
• Gorduras totais: máx 23g RTIQ, típico TACO 12-21g | Sódio: típico TACO 300-700mg
• Carboidratos: típico TACO 0-3g

HAMBÚRGUER DE FRANGO (IN 20/2000):
• kcal: TACO 170-230 | Proteínas: mín 15g RTIQ, típico TACO 14-20g
• Gorduras totais: máx 23g RTIQ, típico TACO 8-18g | Sódio: típico TACO 300-650mg

PRESUNTO COZIDO (IN 20/2000):
• kcal: TACO 120-160 | Proteínas: mín 14g RTIQ, típico TACO 17-21g
• Gorduras totais: máx 4g RTIQ presunto cozido, típico TACO 2-5g
• Sódio: típico TACO 900-1300mg | Carboidratos: típico TACO 0-2g

APRESUNTADO (IN 20/2000):
• kcal: TACO 150-200 | Proteínas: mín 14g RTIQ, típico TACO 15-19g
• Gorduras totais: máx 30g RTIQ apresuntado, típico TACO 6-15g | Sódio: típico TACO 900-1400mg

SALAME (IN 22/2000):
• kcal: TACO 340-420 | Proteínas: mín 20g RTIQ, típico TACO 22-28g
• Gorduras totais: máx 42g RTIQ, típico TACO 28-40g | Gord.sat: típico TACO 12-18g
• Sódio: típico TACO 1500-2400mg | Carboidratos: típico TACO 0-3g

COPA / COPPA (IN 22/2000):
• kcal: TACO 300-400 | Proteínas: mín 20g RTIQ, típico TACO 20-26g
• Gorduras totais: típico TACO 24-36g | Sódio: típico TACO 1400-2200mg

BACON / BARRIGA CURADA (IN 89/2003):
• kcal: TACO 380-520 | Proteínas: típico TACO 10-15g
• Gorduras totais: típico TACO 38-52g | Gord.sat: típico TACO 14-20g
• Sódio: típico TACO 1000-1600mg | Carboidratos: típico TACO 0-2g

CHARQUE / CARNE SECA (RIISPOA):
• kcal: TACO 250-330 | Proteínas: típico TACO 30-40g (concentrada pela desidratação)
• Gorduras totais: típico TACO 10-20g | Sódio: típico TACO 1500-3000mg (produto salgado)
• Carboidratos: típico TACO 0-1g

CMS — CARNE MECANICAMENTE SEPARADA DE AVES (IN 4/2000):
• kcal: TACO 200-260 | Proteínas: mín 12g RTIQ, típico TACO 12-16g
• Gorduras totais: máx 30g RTIQ, típico TACO 15-25g | Sódio: típico TACO 60-120mg (in natura)

━━━ LATICÍNIOS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEITE PASTEURIZADO INTEGRAL (Port. 146/1996):
• kcal: TACO 59-63 | Proteínas: mín 2,9g RTIQ, típico TACO 2,9-3,2g
• Gorduras totais: mín 3g RTIQ integral, típico TACO 3,0-3,5g | Gord.sat: típico TACO 1,9-2,2g
• Carboidratos: típico TACO 4,6-5,0g | Sódio: típico TACO 40-55mg

LEITE PASTEURIZADO SEMIDESNATADO (Port. 146/1996):
• kcal: TACO 42-50 | Proteínas: mín 2,9g RTIQ, típico TACO 3,0-3,3g
• Gorduras totais: 0,6-2,9g RTIQ, típico TACO 1,0-2,0g | Sódio: típico TACO 40-55mg

LEITE PASTEURIZADO DESNATADO (Port. 146/1996):
• kcal: TACO 33-40 | Proteínas: mín 2,9g RTIQ, típico TACO 3,0-3,4g
• Gorduras totais: máx 0,5g RTIQ, típico TACO 0,1-0,4g | Sódio: típico TACO 40-55mg

LEITE EM PÓ INTEGRAL (Port. 146/1996):
• kcal: TACO 490-510 | Proteínas: mín 24g RTIQ, típico TACO 25-28g
• Gorduras totais: mín 26g RTIQ, típico TACO 26-30g | Carboidratos: típico TACO 37-42g
• Sódio: típico TACO 340-400mg

QUEIJO MINAS FRESCAL (Port. 146/1996 + IN 68/2019):
• kcal: TACO 255-275 | Proteínas: mín 17g RTIQ, típico TACO 17-20g
• Gorduras totais: máx 20g RTIQ (integral), típico TACO 17-22g | Gord.sat: típico TACO 10-14g
• Sódio: típico TACO 290-550mg | Carboidratos: típico TACO 2-4g

QUEIJO MUSSARELA (Port. 146/1996):
• kcal: TACO 295-320 | Proteínas: mín 18g RTIQ, típico TACO 20-25g
• Gorduras totais: típico TACO 20-26g | Gord.sat: típico TACO 12-17g
• Sódio: típico TACO 500-800mg | Carboidratos: típico TACO 1-4g

QUEIJO PRATO (Port. 146/1996):
• kcal: TACO 345-375 | Proteínas: típico TACO 24-28g
• Gorduras totais: típico TACO 26-32g | Gord.sat: típico TACO 16-20g
• Sódio: típico TACO 500-750mg | Carboidratos: típico TACO 1-3g

QUEIJO COALHO (Port. 146/1996):
• kcal: TACO 265-300 | Proteínas: típico TACO 20-24g
• Gorduras totais: típico TACO 18-24g | Sódio: típico TACO 700-1100mg

QUEIJO PARMESÃO (Port. 146/1996):
• kcal: TACO 440-470 | Proteínas: mín 32g RTIQ, típico TACO 33-38g
• Gorduras totais: típico TACO 30-37g | Sódio: típico TACO 1300-1800mg

RICOTA (Port. 146/1996):
• kcal: TACO 128-145 | Proteínas: típico TACO 11-15g
• Gorduras totais: típico TACO 7-10g | Sódio: típico TACO 150-300mg | Carboidratos: típico TACO 2-4g

REQUEIJÃO CREMOSO (Port. 146/1996):
• kcal: TACO 245-265 | Proteínas: típico TACO 10-13g
• Gorduras totais: típico TACO 20-24g | Sódio: típico TACO 400-700mg | Carboidratos: típico TACO 3-5g

IOGURTE NATURAL INTEGRAL (Port. 146/1996):
• kcal: TACO 58-66 | Proteínas: mín 2,9g RTIQ, típico TACO 3,0-4,0g
• Gorduras totais: típico TACO 2,5-3,5g | Sódio: típico TACO 40-60mg
• Carboidratos: típico TACO 4,5-6g (da lactose)

MANTEIGA (Port. 146/1996):
• kcal: TACO 720-750 | Proteínas: típico TACO 0,5-1,0g
• Gorduras totais: mín 80g RTIQ, típico TACO 80-85g | Gord.sat: típico TACO 50-60g
• Sódio: típico TACO 580-700mg (com sal) / 10-30mg (sem sal)

CREME DE LEITE (Port. 146/1996):
• kcal: TACO 260-300 | Proteínas: típico TACO 2,0-2,8g
• Gorduras totais: mín 20g RTIQ, típico TACO 25-35g | Sódio: típico TACO 30-60mg
• Carboidratos: típico TACO 3-5g

━━━ PESCADOS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TILÁPIA / PEIXE MAGRO (Port. 185/1997):
• kcal: TACO 82-100 | Proteínas: típico TACO 18-22g
• Gorduras totais: típico TACO 1-3g | Sódio: típico TACO 50-120mg | Carboidratos: típico 0g

SALMÃO / PEIXE GORDO (Port. 185/1997):
• kcal: TACO 170-200 | Proteínas: típico TACO 18-22g
• Gorduras totais: típico TACO 8-14g | Gord.sat: típico TACO 2-4g
• Sódio: típico TACO 50-120mg | Carboidratos: típico 0g

ATUM EM CONSERVA — ÁGUA (Port. 185/1997):
• kcal: TACO 100-130 | Proteínas: típico TACO 22-28g
• Gorduras totais: típico TACO 1-4g | Sódio: típico TACO 300-500mg

ATUM EM CONSERVA — ÓLEO:
• kcal: TACO 180-220 | Proteínas: típico TACO 22-28g
• Gorduras totais: típico TACO 8-14g | Sódio: típico TACO 300-500mg

SARDINHA EM CONSERVA (Port. 185/1997):
• kcal: TACO 180-220 | Proteínas: típico TACO 20-26g
• Gorduras totais: típico TACO 8-14g | Sódio: típico TACO 350-600mg

CAMARÃO CRU (Port. 185/1997):
• kcal: TACO 85-100 | Proteínas: típico TACO 18-22g
• Gorduras totais: típico TACO 0,5-2g | Sódio: típico TACO 130-250mg

BACALHAU SECO SALGADO:
• kcal: TACO 340-380 | Proteínas: típico TACO 70-80g (concentrada)
• Gorduras totais: típico TACO 2-5g | Sódio: típico TACO 4000-8000mg (produto salgado)

━━━ CARNES IN NATURA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CARNE BOVINA MAGRA (patinho, coxão mole) crua (RIISPOA):
• kcal: TACO 125-160 | Proteínas: típico TACO 19-22g
• Gorduras totais: típico TACO 4-9g | Sódio: típico TACO 55-75mg | Carboidratos: típico 0g

CARNE BOVINA GORDA (costela, acém) crua:
• kcal: TACO 220-330 | Proteínas: típico TACO 14-18g
• Gorduras totais: típico TACO 18-30g | Sódio: típico TACO 55-75mg

FRANGO PEITO SEM PELE cru (RIISPOA):
• kcal: TACO 115-125 | Proteínas: típico TACO 20-23g
• Gorduras totais: típico TACO 2-4g | Sódio: típico TACO 50-70mg | Carboidratos: típico 0g

FRANGO COXA/SOBRECOXA SEM PELE cru:
• kcal: TACO 155-175 | Proteínas: típico TACO 16-19g
• Gorduras totais: típico TACO 8-13g | Sódio: típico TACO 65-90mg

CARNE SUÍNA PERNIL / LOMBO cru (RIISPOA):
• kcal: TACO 130-170 | Proteínas: típico TACO 17-21g
• Gorduras totais: típico TACO 6-14g | Sódio: típico TACO 50-75mg

━━━ OVOS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVO DE GALINHA inteiro cru (IN 29/2008):
• kcal: TACO 138-148 | Proteínas: típico TACO 12-14g
• Gorduras totais: típico TACO 8-11g | Gord.sat: típico TACO 2,5-3,5g
• Sódio: típico TACO 120-160mg | Carboidratos: típico TACO 0,5-1,5g

━━━ MEL E APÍCOLAS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEL (IN 11/2000):
• kcal: TACO 295-320 | Carboidratos: mín 65g RTIQ, típico TACO 78-82g
• Proteínas: típico TACO 0,2-0,8g | Gorduras totais: típico TACO 0g
• Sódio: típico TACO 2-15mg — sódio alto em mel é sinal de adulteração
• Umidade: máx 20% RTIQ (importante para detectar mel adulterado diluído = kcal < 295)

━━━ PRODUTOS VEGETAIS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARROZ BRANCO COZIDO (TACO / RDC 711/2022):
• kcal: TACO 128-135 | Carboidratos: típico TACO 28-30g
• Proteínas: típico TACO 2,5-3,0g | Gorduras totais: típico TACO 0-0,3g
• Fibras: típico TACO 1,5-2,5g | Sódio: típico TACO 0-5mg (sem sal)

ARROZ INTEGRAL COZIDO:
• kcal: TACO 124-132 | Carboidratos: típico TACO 25-28g
• Proteínas: típico TACO 2,5-3,0g | Fibras: típico TACO 1,8-3,0g

FEIJÃO COZIDO (TACO):
• kcal: TACO 76-86 | Carboidratos: típico TACO 13-16g
• Proteínas: típico TACO 4,5-5,5g | Fibras: típico TACO 8-11g
• Sódio: típico TACO 2-5mg (sem sal)

FARINHA DE TRIGO (TACO / RDC 711/2022):
• kcal: TACO 355-365 | Carboidratos: típico TACO 75-78g
• Proteínas: típico TACO 9-11g | Gorduras totais: típico TACO 1-2g
• Fibras: típico TACO 2-4g | Sódio: típico TACO 0-5mg

ÓLEO VEGETAL (soja, girassol, canola — RDC 714/2022):
• kcal: TACO 880-900 | Gorduras totais: típico TACO 99-100g
• Proteínas: típico TACO 0g | Carboidratos: típico TACO 0g
• Sódio: típico TACO 0mg — sódio em óleo = adulteração

AZEITE DE OLIVA:
• kcal: TACO 880-900 | Gorduras totais: típico TACO 99-100g
• Gord.sat: típico TACO 14-16g | Gord.mono: típico TACO 70-76g
• Sódio: típico TACO 0mg

AÇÚCAR CRISTAL/REFINADO (TACO / RDC 713/2022):
• kcal: TACO 387-400 | Carboidratos: típico TACO 99-100g
• Proteínas: típico TACO 0g | Gorduras totais: típico TACO 0g
• Sódio: típico TACO 0-2mg

SAL (cloreto de sódio puro):
• Sódio: ~39.000mg/100g (puro) — porção típica 1g → 390mg sódio
• Isento de tabela nutricional conforme ANVISA

━━━ INDUSTRIALIZADOS MISTOS ━━━━━━━━━━━━━━━━━━━━━━━━━━━
BISCOITO SALGADO / CRACKER (TACO):
• kcal: TACO 420-460 | Carboidratos: típico TACO 65-72g
• Proteínas: típico TACO 8-12g | Gorduras totais: típico TACO 12-20g
• Fibras: típico TACO 2-4g | Sódio: típico TACO 700-1200mg

BISCOITO DOCE / RECHEADO (TACO):
• kcal: TACO 450-490 | Carboidratos: típico TACO 68-75g
• Proteínas: típico TACO 5-8g | Gorduras totais: típico TACO 15-22g
• Açúcares totais: típico TACO 25-40g | Sódio: típico TACO 300-600mg

PÃO DE FORMA / FATIADO (TACO):
• kcal: TACO 255-275 | Carboidratos: típico TACO 45-52g
• Proteínas: típico TACO 7-10g | Gorduras totais: típico TACO 3-6g
• Fibras: típico TACO 2-4g | Sódio: típico TACO 450-700mg

MACARRÃO (MASSA SECA, CRU):
• kcal: TACO 368-376 | Carboidratos: típico TACO 73-77g
• Proteínas: típico TACO 10-12g | Gorduras totais: típico TACO 1-2g
• Fibras: típico TACO 2-4g | Sódio: típico TACO 0-10mg (sem sal)

CHOCOLATE AO LEITE (TACO):
• kcal: TACO 540-570 | Carboidratos: típico TACO 57-62g
• Proteínas: típico TACO 7-9g | Gorduras totais: típico TACO 30-36g
• Gord.sat: típico TACO 16-22g | Açúcares totais: típico TACO 48-56g
• Sódio: típico TACO 80-150mg

CHOCOLATE MEIO AMARGO / AMARGO (TACO):
• kcal: TACO 530-565 | Carboidratos: típico TACO 45-55g
• Proteínas: típico TACO 4-6g | Gorduras totais: típico TACO 35-42g
• Açúcares totais: típico TACO 28-42g | Sódio: típico TACO 5-30mg

MOLHO DE TOMATE INDUSTRIALIZADO (TACO):
• kcal: TACO 35-55 | Carboidratos: típico TACO 6-10g
• Proteínas: típico TACO 1-2g | Gorduras totais: típico TACO 0,5-2g
• Sódio: típico TACO 400-700mg — acima de 800mg é alto

MAIONESE TRADICIONAL (TACO):
• kcal: TACO 295-320 | Gorduras totais: típico TACO 30-33g
• Proteínas: típico TACO 1-2g | Carboidratos: típico TACO 2-4g
• Sódio: típico TACO 500-800mg

MARGARINA (TACO):
• kcal: TACO 720-750 | Gorduras totais: mín 80g típico TACO 80-85g
• Gord.sat: típico TACO 18-28g | Gord.trans: verificar (deve ser declarado)
• Sódio: típico TACO 400-700mg (com sal)

LEITE EM PÓ / ACHOCOLATADO EM PÓ (TACO):
• kcal: TACO 380-420 | Carboidratos: típico TACO 72-78g (achocolatado)
• Proteínas: típico TACO 5-8g | Gorduras totais: típico TACO 4-7g
• Sódio: típico TACO 180-300mg

GRANOLA / CEREAL MATINAL (TACO):
• kcal: TACO 390-430 | Carboidratos: típico TACO 65-72g
• Proteínas: típico TACO 8-12g | Gorduras totais: típico TACO 8-14g
• Fibras: típico TACO 5-9g | Sódio: típico TACO 100-300mg

━━━ BEBIDAS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUCO DE LARANJA 100% (TACO / IN MAPA 49/2018):
• kcal: TACO 43-50 | Carboidratos: típico TACO 9-12g
• Proteínas: típico TACO 0,5-1g | Gorduras totais: típico TACO 0g
• Sódio: típico TACO 0-5mg — sódio alto = adulteração

SUCO DE UVA 100%:
• kcal: TACO 60-72 | Carboidratos: típico TACO 14-18g
• Açúcares totais: típico TACO 14-17g | Sódio: típico TACO 0-5mg

NÉCTAR (frutas, mín 30-50% suco dependendo da fruta):
• kcal: TACO 40-65 | Carboidratos: típico TACO 9-16g (pode ter açúcar adicionado)
• Proteínas: típico TACO 0-0,5g | Sódio: típico TACO 0-30mg

REFRIGERANTE (cola, guaraná, laranja):
• kcal: TACO 38-45 (normal) / 0-2 (zero/light)
• Carboidratos: típico TACO 9-11g (normal) / 0-0,5g (zero)
• Sódio: típico TACO 10-30mg

ÁGUA MINERAL (Decreto 7841/2012):
• kcal: TACO 0 | Carboidratos: TACO 0g | Sódio: variável por fonte
• Água com sódio >200mg/L deve declarar "ALTO TEOR DE SÓDIO"

CERVEJA (IN MAPA 14/2018):
• kcal: TACO 43-48 (lata/garrafa) | Carboidratos: típico TACO 3-4g
• Proteínas: típico TACO 0,3-0,5g | Álcool: 4-5% v/v (regular)
• Sódio: típico TACO 10-20mg | Fibras: 0g

VINHO TINTO SECO (Lei 7678/1988):
• kcal: TACO 70-85 | Carboidratos: típico TACO 2-4g (seco)
• Álcool: 11-14% v/v | Sódio: típico TACO 5-10mg

━━━ SUPLEMENTOS ALIMENTARES (RDC 243/2018) ━━━━━━━━━━━
PROTEÍNA WHEY (concentrado/isolado):
• Proteínas: min 10g/porção RTIQ, típico 20-30g/30-40g porção
• Carboidratos: concentrado típico 3-8g | isolado típico 0-3g
• Gorduras totais: concentrado típico 2-6g | isolado típico 0-2g
• Sódio: típico 50-200mg/porção

PROTEÍNA VEGETAL (soja, ervilha):
• Proteínas: típico 18-25g/porção | Carboidratos: típico 3-8g
• Gorduras totais: típico 1-4g | Sódio: típico 100-300mg/porção

CREATINA MONOIDRATADA:
• Porção: 3-5g | Proteínas: 0g | Carboidratos: 0g | Gorduras: 0g
• Sódio: 0mg — qualquer nutriente acima de 0 é incomum em creatina pura

VITAMINAS/MINERAIS (complexo multivitamínico):
• Porção muito variável | Verificar se % VD está declarado
• Vitaminas lipossolúveis (A, D, E, K): podem ser perigosas em excesso — verificar se % VD < 300%

━━━ PRODUTOS VEGETAIS E INDUSTRIALIZADOS — GAPS POA ━━━━━
━━━ PRATOS PRONTOS E ELABORADOS POA ━━━━━━━━━━━━━━━━━━
⚠️ ATENÇÃO: Em produtos cárneos elaborados (empanados, lasanha, pratos prontos),
carboidratos altos (>8g/100g) são NORMAIS e esperados — indicam farinha e amido adicionados.
Não alertar como inconsistência. Verificar % VD na tabela.

EMPANADO DE FRANGO (nugget, steak, filé):
• kcal: TACO 230-290 | Proteínas: mín 10g RTIQ (IN 6/2001), típico TACO 13-18g
• Gorduras totais: típico TACO 12-18g | Carboidratos: típico TACO 14-22g (normal — farinha)
• Sódio: típico TACO 500-950mg

EMPANADO BOVINO:
• kcal: TACO 220-270 | Proteínas: mín 10g RTIQ, típico TACO 12-17g
• Gorduras totais: típico TACO 11-17g | Carboidratos: típico TACO 12-20g
• Sódio: típico TACO 500-900mg

NUGGET DE FRANGO (reestruturado):
• kcal: TACO 240-300 | Proteínas: mín 10g RTIQ, típico TACO 12-16g
• Gorduras totais: típico TACO 14-20g | Carboidratos: típico TACO 12-20g
• Sódio: típico TACO 500-1000mg

LASANHA COM CARNE BOVINA/FRANGO (congelada):
• kcal: TACO 100-160 | Proteínas: típico TACO 6-10g
• Gorduras totais: típico TACO 4-9g | Carboidratos: típico TACO 12-20g
• Sódio: típico TACO 400-700mg

QUIBE / KIBE INDUSTRIALIZADO:
• kcal: TACO 180-250 | Proteínas: mín 12g, típico TACO 12-17g
• Gorduras totais: típico TACO 10-18g | Carboidratos: típico TACO 8-14g
• Sódio: típico TACO 350-700mg

CROQUETE DE CARNE:
• kcal: TACO 200-280 | Proteínas: típico TACO 8-13g
• Gorduras totais: típico TACO 10-18g | Carboidratos: típico TACO 15-25g
• Sódio: típico TACO 400-800mg

━━━ ALIMENTOS FUNCIONAIS DE ORIGEM ANIMAL ━━━━━━━━━━━━
LEITE ENRIQUECIDO (cálcio, vitaminas, ômega-3):
• kcal: TACO 55-70 (similar ao leite base) | Proteínas: típico TACO 3,0-3,5g
• Verificar se nutrientes objeto de alegação estão DECLARADOS NA TABELA (obrigatório RDC 267/2003)
• Vitaminas A/D: em µg ou UI | Cálcio: em mg com % VD

OVO ENRIQUECIDO (ômega-3, vitamina E):
• kcal/composição: similar ao ovo padrão (TACO 138-148 kcal)
• Verificar se EPA+DHA ou vitamina E declarados na tabela se forem objeto de claim

IOGURTE COM PROBIÓTICOS:
• kcal/composição: similar ao iogurte padrão (TACO 58-70 kcal)
• Verificar: alegação "contribui para equilíbrio da flora intestinal" é aprovada pela ANVISA
• NÃO aceito: "fortalece imunidade", "previne infecções" — proibidos pela RDC 267/2003

LEITE FERMENTADO FUNCIONAL:
• kcal: TACO 55-80 | Proteínas: típico TACO 3,0-4,0g
• Verificar UFC/porção se declarado — mín. 10⁸ UFC/porção para alegação probiótica (ANVISA)

━━━ PRODUTOS CÁRNEOS — GAPS POA ━━━━━━━━━━━━━━━━━━━━━━━
PATÊ (IN 20/2000 + Almôndega/Kibe):
• kcal: TACO 180-280 | Proteínas: mín 8g típico TACO 10-18g
• Gorduras totais: típico TACO 14-25g | Sódio: típico TACO 600-1100mg
• Carboidratos: típico TACO 2-8g (pode ter amido/farinha)

ALMÔNDEGA / QUIBE / KIBE (IN 20/2000):
• kcal: TACO 170-250 | Proteínas: típico TACO 12-18g
• Gorduras totais: típico TACO 10-20g | Sódio: típico TACO 400-800mg
• Carboidratos: típico TACO 4-12g (quibe tem trigo)

FIAMBRE (Port. 706/2022):
• kcal: TACO 130-180 | Proteínas: mín 14g RTIQ, típico TACO 14-18g
• Gorduras totais: típico TACO 5-12g | Sódio: típico TACO 900-1300mg

JERKED BEEF / CARNE CURADA (IN 22/2000):
• kcal: TACO 220-290 | Proteínas: típico TACO 25-35g
• Gorduras totais: típico TACO 8-16g | Sódio: típico TACO 1000-2000mg
• Diferença do charque: menor teor de sal (processo de cura vs salga)

CARNE DE SOL (RIISPOA):
• kcal: TACO 200-260 | Proteínas: típico TACO 22-30g
• Gorduras totais: típico TACO 8-15g | Sódio: típico TACO 800-1800mg

FRANGO TEMPERADO / MARINADO (IN 17/2018):
• kcal: TACO 130-200 | Proteínas: típico TACO 16-21g
• Gorduras totais: típico TACO 5-15g | Sódio: típico TACO 400-900mg (sal + tempero)

CORNED BEEF (IN 83/2003):
• kcal: TACO 220-280 | Proteínas: típico TACO 18-24g
• Gorduras totais: típico TACO 12-20g | Sódio: típico TACO 900-1400mg

━━━ LATICÍNIOS — GAPS POA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUEIJO SUÍÇO / GRUYÈRE / EMMENTAL (Port. 146/1996):
• kcal: TACO 370-410 | Proteínas: típico TACO 26-30g
• Gorduras totais: típico TACO 28-34g | Gord.sat: típico TACO 18-22g
• Sódio: típico TACO 200-400mg (menor que queijos brasileiros)

QUEIJO GOUDA / EDAM (Port. 146/1996):
• kcal: TACO 340-380 | Proteínas: típico TACO 24-28g
• Gorduras totais: típico TACO 27-32g | Sódio: típico TACO 600-900mg

DOCE DE LEITE (Port. 354/1997):
• kcal: TACO 295-330 | Carboidratos: típico TACO 54-60g
• Proteínas: típico TACO 6-8g | Gorduras totais: típico TACO 6-10g
• Sódio: típico TACO 80-160mg

LEITE CONDENSADO (IN 47/2018):
• kcal: TACO 320-350 | Carboidratos: típico TACO 54-58g
• Proteínas: mín 6,5g RTIQ, típico TACO 7-9g
• Gorduras totais: mín 8g RTIQ, típico TACO 8-12g | Sódio: típico TACO 100-160mg

BEBIDA LÁCTEA (IN 16/2005):
• kcal: TACO 55-80 | Proteínas: mín 1,2g RTIQ, típico TACO 1,5-3g
• Gorduras totais: típico TACO 1,5-3,5g | Sódio: típico TACO 40-80mg
• Carboidratos: típico TACO 8-14g (pode ter açúcar adicionado)

COMPOSTO LÁCTEO (IN 28/2007):
• kcal: TACO 400-450 | Proteínas: mín 10g RTIQ, típico TACO 12-18g
• Gorduras totais: típico TACO 10-18g | Carboidratos: típico TACO 55-65g
• Sódio: típico TACO 200-400mg

CREME AZEDO / SOUR CREAM (IN 23/2012):
• kcal: TACO 195-230 | Proteínas: típico TACO 3-4g
• Gorduras totais: mín 17g RTIQ, típico TACO 18-24g
• Sódio: típico TACO 30-80mg | Carboidratos: típico TACO 3-5g

━━━ CORTES BOVINOS ESPECÍFICOS ━━━━━━━━━━━━━━━━━━━━━━━━
ALCATRA / CONTRA-FILÉ / FILÉ MIGNON (cortes nobres) crus:
• kcal: TACO 120-160 | Proteínas: típico TACO 20-23g
• Gorduras totais: típico TACO 3-8g | Sódio: típico TACO 50-65mg | Carboidratos: típico 0g

PICANHA crua:
• kcal: TACO 155-200 | Proteínas: típico TACO 18-21g
• Gorduras totais: típico TACO 9-15g (capa de gordura) | Sódio: típico TACO 55-70mg

MÚSCULO / ACÉM / PALETA BOVINA crus (cortes de segunda):
• kcal: TACO 110-145 | Proteínas: típico TACO 20-23g
• Gorduras totais: típico TACO 2-6g | Sódio: típico TACO 55-75mg

COSTELA BOVINA crua:
• kcal: TACO 240-320 | Proteínas: típico TACO 14-18g
• Gorduras totais: típico TACO 18-28g | Sódio: típico TACO 60-80mg

COXÃO DURO / COXÃO MOLE / PATINHO / FRALDINHA / MAMINHA / LAGARTO / CUPIM crus:
• kcal: TACO 115-160 | Proteínas: típico TACO 19-23g
• Gorduras totais: típico TACO 3-9g | Sódio: típico TACO 50-70mg

━━━ CORTES SUÍNOS ESPECÍFICOS ━━━━━━━━━━━━━━━━━━━━━━━
BISTECA SUÍNA / COSTELINHA crua:
• kcal: TACO 155-220 | Proteínas: típico TACO 16-20g
• Gorduras totais: típico TACO 9-16g | Sódio: típico TACO 55-75mg

LOMBO SUÍNO cru:
• kcal: TACO 130-160 | Proteínas: típico TACO 19-22g
• Gorduras totais: típico TACO 5-10g | Sódio: típico TACO 50-70mg

PALETA SUÍNA crua:
• kcal: TACO 135-170 | Proteínas: típico TACO 17-21g
• Gorduras totais: típico TACO 7-13g | Sódio: típico TACO 55-75mg

TOUCINHO cru:
• kcal: TACO 560-650 | Proteínas: típico TACO 4-8g
• Gorduras totais: típico TACO 60-72g | Gord.sat: típico TACO 22-28g | Sódio: típico TACO 40-60mg

━━━ AVES — CORTES E MIÚDOS ━━━━━━━━━━━━━━━━━━━━━━━━━
FRANGO ASA crua:
• kcal: TACO 175-220 | Proteínas: típico TACO 17-20g
• Gorduras totais: típico TACO 10-15g | Sódio: típico TACO 65-90mg

FRANGO SOBRECOXA COM PELE crua:
• kcal: TACO 250-275 | Proteínas: típico TACO 15-18g
• Gorduras totais: típico TACO 18-23g | Sódio: típico TACO 65-90mg

FRANGO FÍGADO cru:
• kcal: TACO 95-115 | Proteínas: típico TACO 17-20g
• Gorduras totais: típico TACO 3-5g | Carboidratos: típico TACO 1-3g (glicogênio)
• Sódio: típico TACO 65-90mg | Rico em vitamina A e ferro

FRANGO CORAÇÃO cru:
• kcal: TACO 145-175 | Proteínas: típico TACO 16-20g
• Gorduras totais: típico TACO 7-12g | Sódio: típico TACO 65-90mg

FRANGO MOELA crua:
• kcal: TACO 85-110 | Proteínas: típico TACO 17-21g
• Gorduras totais: típico TACO 1-4g | Sódio: típico TACO 60-85mg

PERU PEITO cru:
• kcal: TACO 100-120 | Proteínas: típico TACO 22-25g
• Gorduras totais: típico TACO 1-3g | Sódio: típico TACO 55-75mg

PATO cru:
• kcal: TACO 190-240 | Proteínas: típico TACO 16-20g
• Gorduras totais: típico TACO 13-20g | Sódio: típico TACO 65-85mg

━━━ MIÚDOS / VÍSCERAS BOVINAS ━━━━━━━━━━━━━━━━━━━━━━━
FÍGADO BOVINO cru:
• kcal: TACO 130-145 | Proteínas: típico TACO 19-22g
• Gorduras totais: típico TACO 3-5g | Carboidratos: típico TACO 2-4g (glicogênio)
• Sódio: típico TACO 65-85mg | ⚠️ Carboidratos > 0g é normal em fígado (glicogênio)

CORAÇÃO BOVINO cru:
• kcal: TACO 110-135 | Proteínas: típico TACO 17-21g
• Gorduras totais: típico TACO 4-7g | Sódio: típico TACO 80-110mg

RIM BOVINO cru:
• kcal: TACO 95-115 | Proteínas: típico TACO 16-20g
• Gorduras totais: típico TACO 3-6g | Sódio: típico TACO 180-250mg (naturalmente alto)

LÍNGUA BOVINA crua:
• kcal: TACO 195-230 | Proteínas: típico TACO 14-18g
• Gorduras totais: típico TACO 13-19g | Sódio: típico TACO 65-85mg

━━━ PESCADOS REGIONAIS BRASILEIROS ━━━━━━━━━━━━━━━━━━
PEIXE MAGRO REGIONAL — Corvina / Pescada / Linguado / Badejo:
• kcal: TACO 75-100 | Proteínas: típico TACO 17-21g
• Gorduras totais: típico TACO 0,5-2g | Sódio: típico TACO 50-120mg

PEIXE MÉDIO REGIONAL — Dourado / Robalo / Tainha / Surubim / Pintado:
• kcal: TACO 90-130 | Proteínas: típico TACO 17-21g
• Gorduras totais: típico TACO 2-6g | Sódio: típico TACO 50-120mg

PEIXE REGIONAL AMAZÔNICO — Tambaqui / Pirarucu / Pacu / Tucunaré / Traíra:
• kcal: TACO 90-140 | Proteínas: típico TACO 17-22g
• Gorduras totais: típico TACO 2-8g | Sódio: típico TACO 50-120mg
• ⚠️ Pirarucu tem proteína alta (22-26g) — produto muito magro

CAÇÃO / TUBARÃO:
• kcal: TACO 80-100 | Proteínas: típico TACO 18-22g
• Gorduras totais: típico TACO 0,5-2g | Sódio: típico TACO 60-130mg

GAROUPA / BADEJO (peixes nobres):
• kcal: TACO 80-100 | Proteínas: típico TACO 18-22g
• Gorduras totais: típico TACO 0,5-2g | Sódio: típico TACO 50-100mg

MERLUZA:
• kcal: TACO 70-90 | Proteínas: típico TACO 16-20g
• Gorduras totais: típico TACO 0,5-1,5g | Sódio: típico TACO 50-110mg

━━━ MOLUSCOS E CRUSTÁCEOS ━━━━━━━━━━━━━━━━━━━━━━━━━
MEXILHÃO cru (Port. 1022/2024):
• kcal: TACO 70-90 | Proteínas: típico TACO 11-14g
• Gorduras totais: típico TACO 1,5-3g | Carboidratos: típico TACO 2-4g
• Sódio: típico TACO 280-400mg | ⚠️ Carboidratos > 0g é normal em moluscos

OSTRA crua (Port. 1022/2024):
• kcal: TACO 65-85 | Proteínas: típico TACO 8-12g
• Gorduras totais: típico TACO 1-3g | Carboidratos: típico TACO 3-5g
• Sódio: típico TACO 400-600mg

LULA crua (Port. 1022/2024):
• kcal: TACO 75-95 | Proteínas: típico TACO 15-18g
• Gorduras totais: típico TACO 1-2g | Sódio: típico TACO 200-350mg

POLVO cru (Port. 1022/2024):
• kcal: TACO 75-95 | Proteínas: típico TACO 14-18g
• Gorduras totais: típico TACO 0,5-2g | Sódio: típico TACO 230-380mg

━━━ OVOS ESPECÍFICOS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVO DE CODORNA cru (Port. 01/2020):
• kcal: TACO 155-170 | Proteínas: típico TACO 13-15g
• Gorduras totais: típico TACO 11-13g | Gord.sat: típico TACO 3-4g
• Sódio: típico TACO 130-180mg | Carboidratos: típico TACO 0,5-1g

CLARA DE OVO crua:
• kcal: TACO 45-55 | Proteínas: típico TACO 10-12g
• Gorduras totais: típico TACO 0g | Sódio: típico TACO 160-200mg
• Carboidratos: típico TACO 0,5-1g

GEMA DE OVO crua:
• kcal: TACO 320-360 | Proteínas: típico TACO 15-17g
• Gorduras totais: típico TACO 28-32g | Gord.sat: típico TACO 9-11g
• Sódio: típico TACO 45-65mg

━━━ LATICÍNIOS ESPECÍFICOS ━━━━━━━━━━━━━━━━━━━━━━━━━
QUEIJO PROVOLONE (IN 73/2020):
• kcal: TACO 355-385 | Proteínas: mín 20g RTIQ, típico TACO 25-30g
• Gorduras totais: típico TACO 28-35g | Gord.sat: típico TACO 18-22g
• Sódio: típico TACO 800-1100mg | Carboidratos: típico TACO 0-2g

QUEIJO BRIE / CAMEMBERT (Port. 146/1996):
• kcal: TACO 295-335 | Proteínas: típico TACO 17-22g
• Gorduras totais: típico TACO 23-28g | Gord.sat: típico TACO 14-18g
• Sódio: típico TACO 400-600mg

KEFIR (IN 46/2007):
• kcal: TACO 50-70 | Proteínas: típico TACO 3-4g
• Gorduras totais: típico TACO 1-4g | Sódio: típico TACO 40-60mg
• Carboidratos: típico TACO 4-6g (menor que iogurte — fermentação consome lactose)

IOGURTE GREGO / GREGO ESTILO (Port. 146/1996):
• kcal: TACO 90-140 | Proteínas: típico TACO 6-10g (concentrado, mais proteína)
• Gorduras totais: típico TACO 5-10g | Sódio: típico TACO 40-70mg
• Carboidratos: típico TACO 3-7g

LEITE DE CABRA (Port. 146/1996):
• kcal: TACO 65-75 | Proteínas: mín 2,8g RTIQ, típico TACO 3,0-3,5g
• Gorduras totais: típico TACO 3,5-4,5g | Sódio: típico TACO 40-55mg
• Carboidratos: típico TACO 4,4-4,8g

QUEIJO PARMESÃO RALADO:
• kcal: TACO 450-480 | Proteínas: típico TACO 35-42g
• Gorduras totais: típico TACO 28-35g | Sódio: típico TACO 1400-1900mg
• ⚠️ Mais concentrado que bloco por conta da desidratação

━━━ PRODUTOS APÍCOLAS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRÓPOLIS EXTRATO LÍQUIDO / TINTURA (IN 03/2001):
• kcal: tipicamente 150-300 (varia com concentração de álcool/propóleos)
• Proteínas: traços | Gorduras: traços | Carboidratos: 0-5g por 100mL
• ⚠️ Produto com alto teor alcoólico — verificar se declara "contém álcool"
• Sódio: típico <10mg

GELEIA REAL (IN 03/2001):
• kcal: TACO 130-170 | Proteínas: típico TACO 12-16g
• Gorduras totais: típico TACO 5-8g | Carboidratos: típico TACO 8-14g
• Sódio: típico TACO 50-100mg

PÓLEN APÍCOLA (IN 03/2001):
• kcal: TACO 340-400 | Proteínas: típico TACO 20-28g
• Carboidratos: típico TACO 40-55g | Gorduras totais: típico TACO 4-8g
• Sódio: típico TACO 30-80mg

━━━ CONSIDERAÇÕES PARA PRODUTOS TEMPERADOS/PROCESSADOS ━━
Para produtos temperados (IN 17/2018) os valores de sódio podem ser 10-40% maiores que
o corte in natura pelo sal e condimentos adicionados. Considere isso na avaliação.
Carboidratos acima de 10g/100g em embutidos puros (sem amido declarado) = incomum.
Fibra alimentar acima de 0g/100g em carnes puras in natura = incomum (indica erro ou vegetal).
⚠️ EXCEÇÕES onde Carboidratos > 0g são NORMAIS: fígado (glicogênio), moluscos, ovos (traços).
⚠️ Rim bovino tem sódio naturalmente alto (~200mg) — não confundir com sal adicionado.

━━━ PRODUTOS VEGETAIS — CEREAIS E DERIVADOS ━━━━━━━━━━━━
ARROZ BRANCO cru (TACO):
• kcal: 358-368 | Carboidratos: típico 79-82g | Proteínas: típico 7-9g
• Gorduras totais: típico 0,5-1g | Sódio: típico 1-5mg | Fibra: típico 1,5-2,5g

ARROZ INTEGRAL cru:
• kcal: 355-368 | Carboidratos: típico 75-78g | Proteínas: típico 7-9g
• Gorduras totais: típico 1,5-3g | Fibra: típico 4-6g

FARINHA DE TRIGO:
• kcal: 355-365 | Carboidratos: típico 75-80g | Proteínas: típico 9-12g
• Gorduras totais: típico 1-2g | Fibra: típico 2-3g | Sódio: típico 1-5mg

PÃO FRANCÊS / DE FORMA:
• kcal: 245-285 | Carboidratos: típico 50-58g | Proteínas: típico 7-10g
• Gorduras totais: típico 2-5g | Sódio: típico 400-700mg | Fibra: típico 2-4g

MACARRÃO (massa seca):
• kcal: 365-380 | Carboidratos: típico 75-80g | Proteínas: típico 10-13g
• Gorduras totais: típico 1-2g | Sódio: típico 5-15mg (sem sal) / 300-600mg (com sal)

BISCOITO SALGADO / CRACKER:
• kcal: 380-430 | Carboidratos: típico 60-70g | Proteínas: típico 8-12g
• Gorduras totais: típico 12-20g | Sódio: típico 500-900mg

BISCOITO DOCE / COOKIE:
• kcal: 430-480 | Carboidratos: típico 65-72g | Proteínas: típico 5-8g
• Gorduras totais: típico 18-26g | Açúcares: típico 25-40g | Sódio: típico 200-500mg

GRANOLA / CEREAL MATINAL:
• kcal: 380-430 | Carboidratos: típico 60-70g | Proteínas: típico 8-12g
• Gorduras totais: típico 10-18g | Fibra: típico 5-9g | Açúcares: típico 15-30g

━━━ ÓLEOS, GORDURAS E MARGARINAS ━━━━━━━━━━━━━━━━━━━━━
ÓLEO VEGETAL (soja, girassol, canola, milho):
• kcal: 882-900 | Gorduras totais: 100g | Proteínas: 0g | Carboidratos: 0g
• Gord.sat: soja 15g | girassol 10g | canola 7g | milho 13g | Sódio: 0mg
• ⚠️ Óleo com proteínas ou carboidratos declarados = erro ou adulteração

AZEITE DE OLIVA:
• kcal: 884-900 | Gorduras totais: 100g | Gord.sat: típico 14g | Gord.mono: típico 73g
• Proteínas: 0g | Carboidratos: 0g | Sódio: 0mg

MARGARINA:
• kcal: 540-720 | Gorduras totais: 60-80g | Gord.sat: típico 20-35g
• Trans: máx 2g/dia recomendado ANVISA | Sódio: típico 350-600mg

━━━ AÇÚCAR E PRODUTOS AÇUCARADOS ━━━━━━━━━━━━━━━━━━━━
AÇÚCAR REFINADO / CRISTAL:
• kcal: 385-390 | Carboidratos: 99-100g (quase tudo sacarose)
• Proteínas: 0g | Gorduras: 0g | Sódio: 0-2mg

CHOCOLATE AO LEITE:
• kcal: 520-560 | Carboidratos: típico 57-62g | Açúcares: típico 50-55g
• Gorduras totais: típico 28-33g | Gord.sat: típico 16-20g
• Proteínas: típico 7-9g | Sódio: típico 80-120mg

CHOCOLATE AMARGO (>70% cacau):
• kcal: 550-600 | Carboidratos: típico 32-45g | Açúcares: típico 20-35g
• Gorduras totais: típico 38-45g | Proteínas: típico 8-12g | Sódio: típico 10-30mg

SORVETE (base leite):
• kcal: 180-250 | Carboidratos: típico 25-35g | Açúcares: típico 20-28g
• Gorduras totais: típico 8-14g | Proteínas: típico 3-5g | Sódio: típico 60-100mg

━━━ CONDIMENTOS, MOLHOS E TEMPEROS ━━━━━━━━━━━━━━━━━━
KETCHUP:
• kcal: 90-115 | Carboidratos: típico 20-27g | Açúcares: típico 15-22g
• Gorduras totais: típico 0g | Sódio: típico 900-1300mg

MAIONESE:
• kcal: 280-320 | Gorduras totais: típico 30-35g | Proteínas: típico 1-2g
• Carboidratos: típico 2-5g | Sódio: típico 500-800mg

SHOYU / MOLHO DE SOJA:
• kcal: 50-70 | Proteínas: típico 5-8g | Carboidratos: típico 6-10g
• Gorduras: típico 0g | Sódio: típico 4000-7000mg ⚠️ MUITO ALTO em sódio — normal

━━━ BEBIDAS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUCO DE LARANJA (100% integral):
• kcal: 40-48 | Carboidratos: típico 9-11g | Açúcares: típico 8-10g
• Proteínas: típico 0,5-1g | Gorduras: 0g | Sódio: típico 0-5mg
• ⚠️ Suco com sódio >20mg/100mL indica adição irregular

SUCO DE UVA INTEGRAL:
• kcal: 65-75 | Carboidratos: típico 15-18g | Açúcares: típico 14-17g
• Proteínas: típico 0,5g | Gorduras: 0g | Sódio: típico 3-10mg

NÉCTAR DE FRUTA (>30% polpa):
• kcal: 40-65 | Carboidratos: típico 10-16g (com açúcar adicionado)
• Proteínas: típico 0-0,5g | Sódio: típico 5-30mg

REFRIGERANTE REGULAR:
• kcal: 36-45/100mL | Carboidratos: típico 9-12g | Açúcares: típico 9-12g
• Gorduras: 0g | Proteínas: 0g | Sódio: típico 5-20mg

REFRIGERANTE DIET/ZERO:
• kcal: 0-5/100mL | Carboidratos: típico 0g | Adoçantes: verificar declaração

CERVEJA:
• kcal: 40-50/100mL | Carboidratos: típico 3-5g | Proteínas: típico 0,3-0,5g
• Gorduras: 0g | Sódio: típico 3-12mg | Teor alcoólico: declarar em %vol

VINHO TINTO/BRANCO:
• kcal: 68-85/100mL | Carboidratos: típico 2-4g (seco) / 5-10g (suave)
• Gorduras: 0g | Sódio: típico 5-15mg | Teor alcoólico: declarar em %vol

━━━ SUPLEMENTOS ALIMENTARES (RDC 243/2018) ━━━━━━━━━
WHEY PROTEIN CONCENTRADO (70-80% prot):
• kcal: 350-400/100g | Proteínas: típico 70-80g | Carboidratos: típico 8-15g
• Gorduras totais: típico 5-8g | Sódio: típico 200-500mg

WHEY PROTEIN ISOLADO (>90% prot):
• kcal: 350-380/100g | Proteínas: típico 88-95g | Carboidratos: típico 2-5g
• Gorduras totais: típico 0,5-2g | Sódio: típico 150-400mg

CREATINA MONOHIDRATADA:
• kcal: 0 | Proteínas: 0g | Carboidratos: 0g | Gorduras: 0g
• ⚠️ Creatina com calorias declaradas = erro ou produto adulterado

━━━ LEGUMINOSAS E GRÃOS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEIJÃO CARIOCA / PRETO cru:
• kcal: 340-355 | Carboidratos: típico 60-65g | Proteínas: típico 20-23g
• Gorduras totais: típico 1-2g | Fibra: típico 15-20g | Sódio: típico 5-10mg

GRÃO DE BICO cru:
• kcal: 360-380 | Carboidratos: típico 60-65g | Proteínas: típico 18-22g
• Gorduras totais: típico 5-7g | Fibra: típico 15-18g

Formato de saída para o Campo 9 (USE SEMPRE AS 3 LINHAS):
✅/❌/⚠️/🔍 Nível 1 — Estrutura: [resultado detalhado]
✅/❌/⚠️/🔍 Nível 2 — Coerência matemática: (Prot×4) + (Carb×4) + (Gord×9) = Xkcal esperado | declarado: Ykcal | variação: Z% | [resultado]
✅/❌/⚠️/🔍 Nível 3 — Plausibilidade [categoria detectada]: [nutriente]: valor declarado | faixa típica TACO: min-max | limite RTIQ/ANVISA: X | [resultado]

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
    # Gap A: se obs vazia, usa Phase 1 para detectar categoria automaticamente
    if not obs and mime_type != "application/pdf":
        try:
            detected_auto = await detect_product_phase1(image_b64, mime_type, "")
            if detected_auto.get("categoria_kb") and detected_auto["categoria_kb"] != "outro":
                obs = detected_auto.get("produto", "")
                categories = [detected_auto["categoria_kb"]]
                if detected_auto.get("orgao") and not orgao_final:
                    orgao_final = detected_auto["orgao"]
            else:
                categories = []
        except Exception:
            categories = []
    else:
        categories = detect_categories(obs) if obs else []
    try:
        kb_text = await get_kb_for_categories(categories) if categories else ""
    except Exception:
        kb_text = ""

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

    # Injetar contexto de alimento funcional dual MAPA+ANVISA quando detectado
    funcional_context = ""
    if any(kw in obs.lower() for kw in ["funcional", "probiótico", "probiotico", "enriquecido",
                                          "ômega", "omega", "lactobacillus", "bifidobacterium",
                                          "vitamina d", "vitamina a", "reduzido em", "light", "zero"]):
        funcional_context = f"\n\n## ALIMENTO FUNCIONAL / DUAL MAPA+ANVISA\n{DUAL_MAPA_ANVISA_FALLBACK}"

    # Injetar contexto de prato pronto POA quando detectado
    prato_pronto_context = ""
    if any(kw in obs.lower() for kw in ["empanado", "nugget", "lasanha", "croquete",
                                          "prato pronto", "semiprontos", "cordon bleu",
                                          "steak", "hamburguer recheado"]):
        prato_pronto_context = f"\n\n## PRATO PRONTO / PRODUTO CÁRNEO ELABORADO\n{PRATO_PRONTO_POA_FALLBACK}"

    # Injetar norma estadual SIE quando estado detectado
    sie_context = ""
    if orgao_final.upper() == "SIE" and sigla_sie:
        # Detectar estado pelo carimbo/sigla
        for estado_key, fallback_text in SIE_ESTADO_MAP.items():
            if estado_key.upper() in sigla_sie.upper():
                sie_context = f"\n\n## NORMAS COMPLEMENTARES SIE — {sigla_sie.upper()}\n{fallback_text}"
                break
    # Também detectar pelo obs do usuário (ex: "CISPOA", "SISP")
    if not sie_context and obs:
        for estado_key, fallback_text in SIE_ESTADO_MAP.items():
            if estado_key.upper() in obs.upper():
                sie_context = f"\n\n## NORMAS COMPLEMENTARES SIE — {estado_key}\n{fallback_text}"
                break

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

    # Injeta exemplos few-shot de validações anteriores (Sistema 2)
    fewshot = ""
    if categories:
        fewshot = get_fewshot_examples(categories[0])

    system_prompt = SP_VALIDACAO.replace("{kb_section}", kb_section)
    if orgao_context:
        system_prompt += f"\n\n{orgao_context}"
    if sie_context:
        system_prompt += sie_context
    if funcional_context:
        system_prompt += funcional_context
    if prato_pronto_context:
        system_prompt += prato_pronto_context
    if fewshot:
        system_prompt += fewshot
    if detection_context:
        system_prompt += f"\n\n{detection_context}"

    user_text = "Analise este rótulo com máxima precisão. Execute TODOS os passos. Não pule nenhum campo."
    if obs:
        user_text += f"\nObservação adicional: {obs}"
    if produto_detectado:
        user_text += f"\nProduto identificado automaticamente: {produto_detectado}"

    # Gera case_id para este rótulo (usado pelo feedback endpoint)
    case_id = _case_id(image_b64)

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
        SP_REVISAO.replace("{relatorio}", relatorio),
        "Revise com rigor técnico.",
        350
    )
    if revisao:
        yield f"data: {json.dumps({'text': revisao})}\n\n"

    # ── Auto-aprendizado: armazena resultado sem precisar de feedback RT ───────
    try:
        import re as _re2
        score_match  = _re2.search(r"SCORE[:\s]+(\d+)\s*/\s*12", relatorio, _re2.IGNORECASE)
        score_auto   = int(score_match.group(1)) if score_match else None
        prod_match   = _re2.search(r"PRODUTO[:\s]+([^\n|]+)", relatorio, _re2.IGNORECASE)
        prod_auto    = prod_match.group(1).strip()[:80] if prod_match else ""
        erros_auto_list = _re2.findall(
            r"CAMPO (\d+)[^\n]*(?:NÃO CONFORME|AUSENTE)[^\n]*\n([^\n]{0,120})",
            relatorio, _re2.IGNORECASE
        )
        erros_auto = "; ".join(f"C{num}: {desc[:60]}" for num, desc in erros_auto_list[:5])
        auto_case = {
            "case_id":      case_id,
            "produto":      prod_auto or (obs[:50] if obs else ""),
            "categoria":    categories[0] if categories else "",
            "feedback":     None,
            "erros_auto":   erros_auto,
            "erros_encontrados": erros_auto,
            "score_agente": score_auto,
            "timestamp":    __import__("datetime").datetime.now().isoformat(),
            "auto_stored":  True,
        }
        existing = next((x for x in _cases_db if x["case_id"] == case_id), None)
        if not existing:
            _cases_db.append(auto_case)
            if len(_cases_db) > _MAX_CASES:
                _cases_db.pop(0)
            import datetime as _dt
            supabase_case = {**auto_case, "created_at": _dt.datetime.now().isoformat()}
            asyncio.ensure_future(_sb_upsert("validacoes", supabase_case))
    except Exception:
        pass  # auto-store nunca deve quebrar o relatório
    # ────────────────────────────────────────────────────────────────────────────

    # Emite case_id para o frontend usar no feedback
    yield f"data: {json.dumps({'case_id': case_id, 'fewshot_used': bool(fewshot), 'produto': prod_auto})}\n\n"
    yield "data: [DONE]\n\n"



def check_image_readability(image_bytes: bytes) -> dict:
    """
    Verifica se a imagem tem resolução e contraste suficientes para leitura de texto.
    Retorna {"ok": bool, "warning": str, "dim": tuple}
    """
    try:
        from PIL import Image as PILImage, ImageFilter
        import statistics
        img = PILImage.open(__import__("io").BytesIO(image_bytes))
        w, h = img.size
        maior = max(w, h)
        # Resolução mínima para rótulo legível antes do zoom
        if maior < 300:
            return {"ok": False,
                    "warning": f"⚠️ Imagem muito pequena ({w}×{h}px). Envie uma foto com pelo menos 800px no maior lado para garantir leitura do texto.",
                    "dim": (w, h)}
        # Verifica se imagem não é completamente branca/preta (PDF em branco, etc.)
        gray = img.convert("L")
        pixels = list(gray.getdata())
        try:
            stdev = statistics.stdev(pixels[:10000])  # amostra
        except Exception:
            stdev = 50
        if stdev < 8:
            return {"ok": False,
                    "warning": "⚠️ Imagem sem contraste detectável. Verifique se o arquivo está correto e tente novamente.",
                    "dim": (w, h)}
        return {"ok": True, "warning": "", "dim": (w, h)}
    except Exception:
        return {"ok": True, "warning": "", "dim": (0, 0)}


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
        return JSONResponse({"error": "ANTHROPIC_API_KEY não configurada"}, status_code=400,
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
            return JSONResponse({"error": "Não foi possível processar o PDF."}, status_code=400,
                                headers={"Access-Control-Allow-Origin": "*"})

        # Gap H: verificar se houve erro de senha
        if pages and pages[0].get("is_error"):
            return JSONResponse(
                {"error": pages[0]["error"]}, status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )
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
        # Gap B: verifica legibilidade antes de processar
        quality = check_image_readability(contents)
        if not quality["ok"]:
            return JSONResponse(
                {"error": quality["warning"]}, status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )
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
        return JSONResponse({"error": "ANTHROPIC_API_KEY não configurada"}, status_code=400,
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
    try:
        kb_text = await get_kb_for_categories(categories) if categories else ""
    except Exception:
        kb_text = ""
    kb_section = f"## LEGISLAÇÃO ESPECÍFICA\n{kb_text}\n---" if kb_text else ""
    system_prompt = SP_VALIDACAO.replace("{kb_section}", kb_section)

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

# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA 1 — MONITORAMENTO LEGISLATIVO CONTÍNUO
# Verifica o DOU diariamente por novas normas relevantes a POA
# ══════════════════════════════════════════════════════════════════════════════

_monitor_lock = asyncio.Lock()

MONITOR_KEYWORDS = [
    "rotulagem", "RTIQ", "produto de origem animal", "embutido", "laticínio",
    "pescado", "mel", "ovos", "inspeção industrial", "DIPOA", "SIGSIF",
    "alergênicos", "aditivos alimentares", "informação nutricional",
    "denominação de venda", "transgênico", "glúten", "lactose",
]
MONITOR_ORGANS = ["MAPA", "ANVISA", "INMETRO", "DIPOA", "SDA", "SNVS"]
MONITOR_DOC_TYPES = ["instrução normativa", "portaria", "resolução", "decreto",
                     "instrução de serviço", "circular"]

async def fetch_dou_recent(query: str, days_back: int = 2) -> list[dict]:
    """Busca publicações recentes no DOU via API pública."""
    from datetime import datetime, timedelta
    end_date   = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    url = (
        "https://www.in.gov.br/consulta/-/buscar/dou"
        f"?q={query.replace(' ', '+')}"
        f"&s=todos"
        f"&exactDate=&startDate={start_date.strftime('%d-%m-%Y')}"
        f"&endDate={end_date.strftime('%d-%m-%Y')}"
        f"&sortType=0"
    )
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, headers={"User-Agent": "ValidaRotuloMonitor/1.0"})
            if r.status_code != 200:
                return []
            import re as _re
            # Extrai títulos e links dos resultados
            titles = _re.findall(r'class="title-marker[^"]*"[^>]*>([^<]+)<', r.text)
            links  = _re.findall(r'href="(/web/dou/-/[^"]+)"', r.text)
            results = []
            for i, title in enumerate(titles[:10]):
                link = f"https://www.in.gov.br{links[i]}" if i < len(links) else ""
                results.append({"title": title.strip(), "link": link})
            return results
    except Exception:
        return []

def is_relevant_publication(title: str) -> bool:
    """Verifica se uma publicação do DOU é relevante para POA."""
    t = title.lower()
    has_keyword = any(kw.lower() in t for kw in MONITOR_KEYWORDS)
    has_doctype = any(dt.lower() in t for dt in MONITOR_DOC_TYPES)
    return has_keyword and has_doctype

async def send_monitor_alert(findings: list[dict], webhook_url: str = "") -> bool:
    """Envia alerta por webhook quando norma relevante é detectada."""
    if not findings:
        return False
    payload = {
        "text": f"🚨 *ValidaRótulo — Nova norma POA detectada*\n"
                + "\n".join(f"• {f['title']}\n  {f['link']}" for f in findings),
        "findings": findings,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }
    # Webhook (Slack, Discord, n8n, Zapier — qualquer URL)
    if webhook_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(webhook_url, json=payload)
        except Exception:
            pass
    # Também armazena localmente para o endpoint /monitor/status
    _monitor_history.append(payload)
    if len(_monitor_history) > 100:
        _monitor_history.pop(0)
    import datetime as _dt3
    asyncio.ensure_future(_sb_insert("monitor_alertas", {
        **payload, "created_at": _dt3.datetime.now().isoformat()
    }))
    return True

_monitor_history: list[dict] = []

@app.post("/monitor/check")
async def monitor_check(request: Request):
    """
    Endpoint chamado diariamente pelo cron job.
    Busca novas publicações relevantes no DOU e envia alertas.
    Configurar cron em: https://cron-job.org (grátis)
    URL: POST https://valida-rotulo-backend.onrender.com/monitor/check
    Frequência: diária às 09:00 BRT
    """
    async with _monitor_lock:
        all_findings = []
        for kw in ["rotulagem produto origem animal", "RTIQ MAPA", "ANVISA rotulagem"]:
            results = await fetch_dou_recent(kw, days_back=2)
            for r in results:
                if is_relevant_publication(r["title"]) and r not in all_findings:
                    all_findings.append(r)

        webhook_url = os.environ.get("MONITOR_WEBHOOK_URL", "")
        alerted = await send_monitor_alert(all_findings, webhook_url)

        return JSONResponse({
            "status": "ok",
            "checked_at": __import__("datetime").datetime.now().isoformat(),
            "findings": len(all_findings),
            "alerted": alerted,
            "publications": all_findings,
        }, headers={"Access-Control-Allow-Origin": "*"})

@app.get("/monitor/status")
async def monitor_status():
    """Mostra histórico de alertas enviados."""
    return JSONResponse({
        "total_alerts": len(_monitor_history),
        "recent": _monitor_history[-5:] if _monitor_history else [],
        "webhook_configured": bool(os.environ.get("MONITOR_WEBHOOK_URL")),
        "setup_instructions": {
            "cron": "https://cron-job.org → POST /monitor/check diariamente às 09:00",
            "webhook": "Render dashboard → Environment → MONITOR_WEBHOOK_URL=<sua URL>",
            "slack_example": "https://hooks.slack.com/services/XXX/YYY/ZZZ",
        }
    }, headers={"Access-Control-Allow-Origin": "*"})

@app.post("/kb/update")
async def kb_update(request: Request):
    """
    Recebe texto de nova norma e atualiza o cache da KB.
    Usar quando uma norma nova for detectada e revisada.
    Body: { "categoria": "embutidos", "texto": "...", "fonte": "IN XX/AAAA" }
    """
    try:
        body = await request.json()
        categoria = body.get("categoria", "manual")
        texto     = body.get("texto", "")
        fonte     = body.get("fonte", "")
        if not texto:
            return JSONResponse({"error": "texto obrigatório"},
                                headers={"Access-Control-Allow-Origin": "*"})
        _kb_cache[categoria] = f"[Atualizado manualmente — {fonte}]\n{texto}"
        return JSONResponse({
            "status": "ok",
            "categoria": categoria,
            "chars": len(texto),
            "fonte": fonte,
        }, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return JSONResponse({"error": str(e)},
                            headers={"Access-Control-Allow-Origin": "*"})


# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA 2 — APRENDIZADO POR USO (FEW-SHOT LOOP)
# Armazena validações + feedback do RT → melhora próximas validações
# ══════════════════════════════════════════════════════════════════════════════

import hashlib as _hashlib

# Banco de casos em memória (persiste durante o processo, reset no redeploy)
# Para produção: substituir por Supabase/PlanetScale (gratuitos)

# ══════════════════════════════════════════════════════════════════════════════
# SUPABASE — PERSISTÊNCIA DE DADOS
# Configurar no Render: SUPABASE_URL e SUPABASE_KEY (anon key)
# Se variáveis não existirem, cai em fallback in-memory (desenvolvimento)
# ══════════════════════════════════════════════════════════════════════════════

_SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
_SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
_SUPABASE_ON  = bool(_SUPABASE_URL and _SUPABASE_KEY)

async def _sb_get(table: str, filters: dict = None, limit: int = 500) -> list[dict]:
    """Lê registros do Supabase. Retorna [] se Supabase não configurado."""
    if not _SUPABASE_ON:
        return []
    url = f"{_SUPABASE_URL}/rest/v1/{table}?limit={limit}&order=created_at.desc"
    if filters:
        for k, v in filters.items():
            url += f"&{k}=eq.{v}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, headers={
                "apikey": _SUPABASE_KEY,
                "Authorization": f"Bearer {_SUPABASE_KEY}",
            })
            return r.json() if r.status_code == 200 else []
    except Exception:
        return []

async def _sb_upsert(table: str, data: dict) -> bool:
    """Insere ou atualiza registro no Supabase. Retorna True se OK."""
    if not _SUPABASE_ON:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.post(
                f"{_SUPABASE_URL}/rest/v1/{table}",
                headers={
                    "apikey": _SUPABASE_KEY,
                    "Authorization": f"Bearer {_SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates",
                },
                json=data,
            )
            return r.status_code in (200, 201)
    except Exception:
        return False

async def _sb_insert(table: str, data: dict) -> bool:
    """Insere registro no Supabase."""
    if not _SUPABASE_ON:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.post(
                f"{_SUPABASE_URL}/rest/v1/{table}",
                headers={
                    "apikey": _SUPABASE_KEY,
                    "Authorization": f"Bearer {_SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json=data,
            )
            return r.status_code in (200, 201)
    except Exception:
        return False

async def load_cases_from_supabase() -> list[dict]:
    """Carrega casos do Supabase para memória no startup."""
    rows = await _sb_get("validacoes", limit=500)
    return rows

async def load_monitor_from_supabase() -> list[dict]:
    """Carrega histórico de alertas do Supabase."""
    rows = await _sb_get("monitor_alertas", limit=100)
    return rows

_cases_db: list[dict] = []
_MAX_CASES = 500  # máximo de casos em memória

def _case_id(image_b64: str) -> str:
    """Gera ID único para uma imagem."""
    return _hashlib.md5(image_b64[:500].encode()).hexdigest()[:12]

def get_fewshot_examples(categoria: str, max_examples: int = 3) -> str:
    """
    Recupera exemplos para few-shot injection.
    Usa TODOS os casos armazenados — com ou sem feedback do RT.
    Prioridade:
      1. Mesma categoria + feedback RT positivo (mais confiável)
      2. Mesma categoria + auto-validado com score alto (≥10/12)
      3. Qualquer categoria + alta confiança
    Extrai padrões de erros recorrentes para alertar proativamente.
    """
    if not _cases_db:
        return ""

    # Tier 1: feedback RT explícito + mesma categoria
    tier1 = [c for c in _cases_db
             if c.get("categoria") == categoria
             and c.get("feedback") in ("correto", "parcialmente_correto")]

    # Tier 2: auto-validado com score ≥10 + mesma categoria (confiança alta)
    tier2 = [c for c in _cases_db
             if c.get("categoria") == categoria
             and c.get("feedback") is None
             and (c.get("score_agente") or 0) >= 10
             and c.get("erros_auto")]

    # Tier 3: qualquer categoria com score alto
    tier3 = [c for c in _cases_db
             if c.get("feedback") is None
             and (c.get("score_agente") or 0) >= 10]

    pool = (tier1 + tier2 + tier3)[:max_examples * 4]
    if not pool:
        return ""

    # Detecta erros RECORRENTES na categoria (aparece em >30% dos casos)
    from collections import Counter
    cat_cases = [c for c in _cases_db if c.get("categoria") == categoria]
    erros_recorrentes = ""
    if len(cat_cases) >= 3:
        all_erros = " ".join(
            (c.get("erros_auto") or "") + " " + (c.get("erros_encontrados") or "")
            for c in cat_cases
        ).lower()
        palavras = Counter(w for w in all_erros.split()
                           if len(w) > 5 and w not in {"campo","nenhum","conforme","verificar"})
        top = [w for w, n in palavras.most_common(5) if n >= max(2, len(cat_cases) * 0.3)]
        if top:
            erros_recorrentes = (
                f"\nPADRÕES DE ERRO RECORRENTES nesta categoria "
                f"(detectados em {len(cat_cases)} validações anteriores):\n"
                f"Fique especialmente atento a: {', '.join(top)}\n"
            )

    # Exemplos concretos
    examples = pool[:max_examples]
    parts = []
    for ex in examples:
        origem = "RT" if ex.get("feedback") else "auto-validado"
        score  = ex.get("score_agente")
        erros  = ex.get("erros_auto") or ex.get("erros_encontrados") or "nenhum registrado"
        parts.append(
            f"[{ex.get('produto','produto')} — {ex.get('categoria','?')} | origem: {origem}"
            + (f" | score: {score}/12" if score else "") + "]\n"
            f"Não-conformidades encontradas: {erros[:200]}"
        )

    header = f"\n## BASE DE CONHECIMENTO PRÁTICO ({len(_cases_db)} validações reais)"
    if erros_recorrentes:
        header += erros_recorrentes
    if parts:
        header += "\nEXEMPLOS RECENTES:\n" + "\n---\n".join(parts)
    return header

@app.post("/feedback")
async def store_feedback(request: Request):
    """
    Armazena feedback do RT após uma validação.
    Body: {
      "case_id": "abc123",
      "produto": "Linguiça Suína Frescal",
      "categoria": "embutidos",
      "feedback": "correto" | "incorreto" | "parcialmente_correto",
      "erros_encontrados": "campo 11 errado, campo 9 ok",
      "rt_comment": "O agente não percebeu que...",
      "score_agente": 10,
      "score_real": 9
    }
    """
    try:
        body = await request.json()
        case = {
            "case_id":          body.get("case_id", ""),
            "produto":          body.get("produto", ""),
            "categoria":        body.get("categoria", ""),
            "feedback":         body.get("feedback", ""),
            "erros_encontrados":body.get("erros_encontrados", ""),
            "rt_comment":       body.get("rt_comment", ""),
            "score_agente":     body.get("score_agente"),
            "score_real":       body.get("score_real"),
            "timestamp":        __import__("datetime").datetime.now().isoformat(),
        }
        # Atualiza caso existente ou adiciona novo
        existing = next((c for c in _cases_db if c["case_id"] == case["case_id"]), None)
        if existing:
            existing.update(case)
        else:
            _cases_db.append(case)
            if len(_cases_db) > _MAX_CASES:
                _cases_db.pop(0)

        # Persiste feedback no Supabase
        import datetime as _dt2
        asyncio.ensure_future(_sb_upsert("validacoes", {
            **case, "created_at": _dt2.datetime.now().isoformat()
        }))
        return JSONResponse({
            "status": "ok",
            "total_cases": len(_cases_db),
            "case_id": case["case_id"],
            "persistido": _SUPABASE_ON,
        }, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return JSONResponse({"error": str(e)},
                            headers={"Access-Control-Allow-Origin": "*"})

@app.get("/admin/stats")
async def admin_stats():
    """Painel de aprendizado: métricas de qualidade por categoria."""
    if not _cases_db:
        return JSONResponse({
            "total_cases": 0,
            "message": "Nenhuma validação com feedback ainda."
        }, headers={"Access-Control-Allow-Origin": "*"})

    from collections import Counter, defaultdict
    categorias = Counter(c["categoria"] for c in _cases_db if c.get("categoria"))
    feedbacks  = Counter(c["feedback"]  for c in _cases_db if c.get("feedback"))

    # Precisão por categoria
    precisao = {}
    by_cat = defaultdict(list)
    for c in _cases_db:
        if c.get("categoria") and c.get("feedback"):
            by_cat[c["categoria"]].append(c["feedback"])
    for cat, fbs in by_cat.items():
        corretos = sum(1 for f in fbs if f in ("correto", "parcialmente_correto"))
        precisao[cat] = round(corretos / len(fbs) * 100) if fbs else 0

    # Erros mais comuns
    erros_text = " ".join(c.get("erros_encontrados", "") for c in _cases_db)
    erros_comuns = Counter(w for w in erros_text.lower().split()
                           if len(w) > 4 and w not in {"campo","nenhum","ok","sim","não","para"})

    auto_stored   = sum(1 for x in _cases_db if x.get("auto_stored"))
    com_feedback  = sum(1 for x in _cases_db if x.get("feedback"))
    score_medio   = None
    scores = [x["score_agente"] for x in _cases_db if x.get("score_agente") is not None]
    if scores:
        score_medio = round(sum(scores) / len(scores), 1)

    return JSONResponse({
        "total_cases":        len(_cases_db),
        "auto_armazenados":   auto_stored,
        "com_feedback_rt":    com_feedback,
        "score_medio_agente": score_medio,
        "feedbacks":          dict(feedbacks),
        "precisao_pct":       precisao,
        "top_categorias":     dict(categorias.most_common(8)),
        "erros_mais_comuns":  dict(erros_comuns.most_common(10)),
        "fewshot_por_categoria": {
            cat: {
                "total": sum(1 for x in _cases_db if x.get("categoria") == cat),
                "com_feedback": sum(1 for x in _cases_db if x.get("categoria") == cat and x.get("feedback")),
                "auto_alta_confianca": sum(1 for x in _cases_db
                                           if x.get("categoria") == cat
                                           and (x.get("score_agente") or 0) >= 10),
            }
            for cat in set(x.get("categoria","") for x in _cases_db) if cat
        },
        "como_melhorar": {
            "proxima_melhoria": "Adicione feedback RT em 10+ casos para ativar exemplos mais precisos",
            "status_fewshot": (
                "Ativo — injetando exemplos" if len(_cases_db) >= 5
                else f"Aguardando {5 - len(_cases_db)} validações para ativar"
            ),
        }
    }, headers={"Access-Control-Allow-Origin": "*"})



# ══════════════════════════════════════════════════════════════════════════════
# CRIADOR DE RÓTULOS — Gera conteúdo + PDF/PNG profissional
# ══════════════════════════════════════════════════════════════════════════════

SP_CRIAR_ROTULO = """Você é um especialista em rotulagem de alimentos brasileira.
Sua tarefa é gerar TODOS os campos obrigatórios de um rótulo de alimento conforme a legislação vigente.

RETORNE SOMENTE JSON válido, sem markdown, sem texto fora do JSON.

Estrutura obrigatória:
{
  "denominacao": "Denominação de venda exata conforme RTIQ",
  "ingredientes": "Lista completa em ordem decrescente com INS e funções tecnológicas",
  "conteudo_liquido": "Conteúdo líquido formatado com símbolo INMETRO (ex: 200 g ℮)",
  "fabricante": "Razão Social\nCNPJ: XX.XXX.XXX/XXXX-XX\nEndereço completo\nCidade - UF CEP",
  "carimbo": "SIF/SIE/SIM + número (ex: SIF 3456)",
  "conservacao": "Instrução de conservação com temperatura específica",
  "lote": "Veja fundo da embalagem",
  "validade": "Veja fundo da embalagem",
  "alergenos": "CONTÉM: X, Y E DERIVADOS. / PODE CONTER: Z.",
  "transgenicos": "(Não contém transgênicos)" ou texto conforme aplicável,
  "lupa_necessaria": true/false,
  "lupa_motivo": "ALTO EM SÓDIO" / "ALTO EM GORDURAS SATURADAS" / "ALTO EM AÇÚCAR" ou null,
  "porcao": "100g (porção padrão conforme IN 75/2020)",
  "tabela_nutricional": {
    "porcao": "100g",
    "energia_kcal": "XXX kcal",
    "energia_kj": "XXX kJ",
    "carboidratos": "Xg",
    "acucares_totais": "Xg",
    "acucares_adicionados": "Xg",
    "proteinas": "Xg",
    "gorduras_totais": "Xg",
    "gorduras_saturadas": "Xg",
    "gorduras_trans": "0g",
    "fibra": "Xg",
    "sodio": "XXmg"
  },
  "gluten": "CONTÉM GLÚTEN" ou "NÃO CONTÉM GLÚTEN",
  "lactose": "CONTÉM LACTOSE" ou "NÃO CONTÉM LACTOSE" ou null,
  "observacoes_rt": "Orientações específicas ao RT sobre este produto",
  "legislacoes": ["IN 4/2000", "RDC 727/2022"]
}

REGRAS OBRIGATÓRIAS:
1. Denominação: use exatamente o nome técnico do RTIQ aplicável + espécie animal
2. Ingredientes: ordem decrescente, aditivos com INS e função tecnológica
3. Tabela nutricional: use valores TACO para a categoria se não informado
4. Alérgenos: 14 grupos da RDC 727/2022, CONTÉM para intencionais, PODE CONTER para cruzada
5. Lupa: obrigatória se sódio >= 600mg, gordura saturada >= 6g, ou açúcar adicionado >= 15g por 100g
6. Lote e validade: sempre "Veja fundo/tampa da embalagem" pois são impressos na linha
7. Conteúdo líquido: incluir símbolo ℮ (INMETRO) e unidade correta
"""

import tempfile as _tempfile, uuid as _uuid

def _gerar_pdf_label(campos: dict, formato: str, tema: str) -> tuple[bytes, bytes]:
    """
    Gera PDF profissional do rótulo e converte para PNG.
    Retorna (pdf_bytes, png_bytes).
    Formatos: retangular (210x100mm), quadrado (100x100mm), circular (90x90mm)
    Temas: moderno, classico, premium
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import io as _io

    # ── Dimensões por formato ──────────────────────────────────────────────────
    dims = {
        "retangular": (210*mm, 100*mm),
        "quadrado":   (100*mm, 100*mm),
        "circular":   (90*mm,  90*mm),
    }
    W, H = dims.get(formato, dims["retangular"])

    # ── Paletas de tema ────────────────────────────────────────────────────────
    temas = {
        "moderno":  {"bg": colors.HexColor("#111827"), "acc": colors.HexColor("#16a34a"),
                     "txt": colors.white, "light": colors.HexColor("#f9fafb"),
                     "dark": colors.HexColor("#1f2937"), "border": colors.HexColor("#374151")},
        "classico": {"bg": colors.HexColor("#1e3a5f"), "acc": colors.HexColor("#c9922a"),
                     "txt": colors.white, "light": colors.HexColor("#f8f5f0"),
                     "dark": colors.HexColor("#1e3a5f"), "border": colors.HexColor("#2d5a8e")},
        "premium":  {"bg": colors.HexColor("#1a0a2e"), "acc": colors.HexColor("#c9a227"),
                     "txt": colors.white, "light": colors.HexColor("#fdf9f0"),
                     "dark": colors.HexColor("#2d1457"), "border": colors.HexColor("#4a1a7a")},
    }
    T = temas.get(tema, temas["moderno"])

    buf = _io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(W, H))

    # ── Fundo ──────────────────────────────────────────────────────────────────
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── Funções auxiliares ─────────────────────────────────────────────────────
    def rect_fill(x, y, w, h, color):
        c.setFillColor(color); c.rect(x, y, w, h, fill=1, stroke=0)

    def text(txt, x, y, size=7, bold=False, color=None, align="left", max_w=None):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.setFillColor(color or colors.HexColor("#111827"))
        if align == "center":
            c.drawCentredString(x, y, str(txt)[:80])
        elif align == "right":
            c.drawRightString(x, y, str(txt)[:80])
        else:
            txt_str = str(txt)
            if max_w:
                # Truncate to fit
                while len(txt_str) > 3 and c.stringWidth(txt_str, "Helvetica-Bold" if bold else "Helvetica", size) > max_w:
                    txt_str = txt_str[:-4] + "..."
            c.drawString(x, y, txt_str)

    def wrap_text(txt, x, y, max_w, size=6.5, line_h=8, color=None, max_lines=6):
        """Simple word wrap."""
        c.setFont("Helvetica", size)
        c.setFillColor(color or colors.HexColor("#374151"))
        words = str(txt).split()
        lines, line = [], ""
        for w in words:
            test = (line + " " + w).strip()
            if c.stringWidth(test, "Helvetica", size) <= max_w:
                line = test
            else:
                if line: lines.append(line)
                line = w
        if line: lines.append(line)
        for i, ln in enumerate(lines[:max_lines]):
            c.drawString(x, y - i*line_h, ln)
        return len(lines[:max_lines]) * line_h

    # ══════════════════════════════════════════════════════════════════════════
    # LAYOUT RETANGULAR (210 x 100mm)
    # ══════════════════════════════════════════════════════════════════════════
    if formato == "retangular":
        margin = 3*mm
        # Cabeçalho escuro
        rect_fill(0, H - 22*mm, W, 22*mm, T["bg"])
        # Nome produto grande
        prod = (campos.get("denominacao") or "Produto")[:45]
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(T["txt"])
        c.drawString(margin, H - 14*mm, prod)
        # Carimbo no canto direito
        carimbo = campos.get("carimbo", "SIF 000")
        rect_fill(W - 28*mm, H - 19*mm, 25*mm, 16*mm, colors.white)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(T["bg"])
        c.drawCentredString(W - 15.5*mm, H - 12*mm, carimbo)
        c.setFont("Helvetica", 5.5)
        c.drawCentredString(W - 15.5*mm, H - 16*mm, "INSPECIONADO")
        # Linha accent
        rect_fill(0, H - 24*mm, W, 2*mm, T["acc"])

        # ── Coluna esquerda (ingredientes + fabricante + conservação) ──────────
        col_w = W * 0.52
        y = H - 27*mm
        text("INGREDIENTES", margin, y, size=6, bold=True, color=T["dark"])
        y -= 2*mm
        wrap_text(campos.get("ingredientes", ""), margin, y, col_w - 2*margin, size=6, line_h=7.5, max_lines=5)
        y -= 42

        text("FABRICANTE", margin, y, size=6, bold=True, color=T["dark"])
        y -= 2*mm
        wrap_text(campos.get("fabricante", ""), margin, y, col_w - 2*margin, size=6, line_h=7.5, max_lines=3)
        y -= 26

        text("CONSERVAR: " + (campos.get("conservacao","") or "")[:60],
             margin, y, size=5.5, color=colors.HexColor("#6b7280"), max_w=col_w-2*margin)
        y -= 7
        text(campos.get("gluten","") + " · " + (campos.get("lactose","") or ""),
             margin, y, size=5.5, bold=True, color=colors.HexColor("#dc2626"), max_w=col_w-2*margin)
        y -= 7
        alergs = campos.get("alergenos","")[:100]
        text(alergs, margin, y, size=5.5, color=colors.HexColor("#374151"), max_w=col_w-2*margin)

        # Lote / validade / conteúdo
        y = 4*mm
        text(campos.get("conteudo_liquido",""), margin, y, size=7, bold=True, color=T["dark"])
        text("LOTE: Veja embalagem   VALIDADE: Veja embalagem",
             margin + 30*mm, y, size=5.5, color=colors.HexColor("#9ca3af"))

        # ── Divisória vertical ─────────────────────────────────────────────────
        c.setStrokeColor(colors.HexColor("#e5e7eb"))
        c.setLineWidth(0.5)
        c.line(col_w, H - 25*mm, col_w, 2*mm)

        # ── Tabela nutricional (coluna direita) ────────────────────────────────
        tx = col_w + 2*mm
        tw = W - col_w - margin
        tn = campos.get("tabela_nutricional", {})

        ty = H - 27*mm
        # Header tabela
        rect_fill(tx, ty - 5*mm, tw, 5*mm, T["dark"])
        c.setFont("Helvetica-Bold", 7); c.setFillColor(T["txt"])
        c.drawCentredString(tx + tw/2, ty - 3.5*mm, "Informação Nutricional")
        ty -= 5*mm
        rect_fill(tx, ty - 4*mm, tw, 4*mm, colors.HexColor("#f3f4f6"))
        c.setFont("Helvetica", 5.5); c.setFillColor(colors.HexColor("#374151"))
        c.drawString(tx + 1*mm, ty - 3*mm, f"Porção: {tn.get('porcao', '100g')} (1 porção)")
        ty -= 4*mm

        rows_nut = [
            ("Valor energético", f"{tn.get('energia_kcal','?')} = {tn.get('energia_kj','?')} kJ"),
            ("Carboidratos", tn.get("carboidratos","?")),
            ("   Acucares totais", tn.get("acucares_totais","?")),
            ("   Acucares adicionados", tn.get("acucares_adicionados","?")),
            ("Proteinas", tn.get("proteinas","?")),
            ("Gorduras totais", tn.get("gorduras_totais","?")),
            ("   Gord. saturadas", tn.get("gorduras_saturadas","?")),
            ("   Gord. trans", tn.get("gorduras_trans","0g")),
            ("Fibra alimentar", tn.get("fibra","?")),
            ("Sodio", tn.get("sodio","?")),
        ]
        for i, (nm, vl) in enumerate(rows_nut):
            row_bg = colors.HexColor("#ffffff") if i%2==0 else colors.HexColor("#f9fafb")
            rect_fill(tx, ty - 5*mm, tw, 5*mm, row_bg)
            c.setStrokeColor(colors.HexColor("#e5e7eb")); c.setLineWidth(0.3)
            c.line(tx, ty - 5*mm, tx + tw, ty - 5*mm)
            c.setFont("Helvetica", 5.5); c.setFillColor(colors.HexColor("#374151"))
            c.drawString(tx + 1*mm, ty - 3.5*mm, nm[:28])
            c.setFont("Helvetica-Bold", 5.5); c.setFillColor(colors.HexColor("#111827"))
            c.drawRightString(tx + tw - 1*mm, ty - 3.5*mm, str(vl)[:12])
            ty -= 5*mm

        # Lupa se necessário
        if campos.get("lupa_necessaria") and campos.get("lupa_motivo"):
            rect_fill(tx, ty - 6*mm, tw, 6*mm, colors.HexColor("#111827"))
            c.setFont("Helvetica-Bold", 7); c.setFillColor(colors.white)
            c.drawCentredString(tx + tw/2, ty - 4*mm, campos["lupa_motivo"][:25])
            ty -= 6*mm

        # Borda do rótulo inteiro
        c.setStrokeColor(colors.HexColor("#374151")); c.setLineWidth(1)
        c.rect(0.5, 0.5, W - 1, H - 1, fill=0, stroke=1)

    # ══════════════════════════════════════════════════════════════════════════
    # LAYOUT QUADRADO (100 x 100mm)
    # ══════════════════════════════════════════════════════════════════════════
    elif formato == "quadrado":
        m = 3*mm
        rect_fill(0, H - 20*mm, W, 20*mm, T["bg"])
        prod = (campos.get("denominacao") or "Produto")[:30]
        c.setFont("Helvetica-Bold", 11); c.setFillColor(T["txt"])
        c.drawCentredString(W/2, H - 13*mm, prod)
        c.setFont("Helvetica", 7); c.setFillColor(colors.HexColor("#9ca3af"))
        c.drawCentredString(W/2, H - 17*mm, campos.get("carimbo","SIF 000"))
        rect_fill(0, H - 22*mm, W, 2*mm, T["acc"])

        # Conteúdo líquido proeminente
        c.setFont("Helvetica-Bold", 14); c.setFillColor(T["dark"])
        c.drawCentredString(W/2, H - 28*mm, campos.get("conteudo_liquido",""))

        # Ingredientes
        y = H - 34*mm
        text("INGREDIENTES", m, y, size=5.5, bold=True, color=T["dark"])
        y -= 2*mm
        wrap_text(campos.get("ingredientes",""), m, y, W - 2*m, size=5.5, line_h=7, max_lines=4)
        y -= 34

        # Fabricante em uma linha
        fab = (campos.get("fabricante","") or "").split("\n")[0][:40]
        text("Fab: " + fab, m, y, size=5.5, color=colors.HexColor("#6b7280"), max_w=W-2*m)
        y -= 7

        # Alérgenos
        text(campos.get("gluten","") + " · " + (campos.get("lactose","") or ""),
             m, y, size=5.5, bold=True, color=colors.HexColor("#dc2626"), max_w=W-2*m)
        y -= 7
        text((campos.get("alergenos",""))[:80], m, y, size=5, color=colors.HexColor("#374151"), max_w=W-2*m)

        # Tabela nutricional compacta no rodapé
        tn = campos.get("tabela_nutricional", {})
        ty = 22*mm
        rect_fill(m, ty, W - 2*m, 4*mm, T["dark"])
        c.setFont("Helvetica-Bold", 6); c.setFillColor(T["txt"])
        c.drawCentredString(W/2, ty + 2.5*mm, f"Informacao Nutricional | Porcao: {tn.get('porcao','100g')}")
        ty += 4*mm
        cols_nut = [
            ("Energia", f"{tn.get('energia_kcal','?')}"),
            ("Prot.", tn.get("proteinas","?")),
            ("Carb.", tn.get("carboidratos","?")),
            ("Gord.", tn.get("gorduras_totais","?")),
            ("Sodio", tn.get("sodio","?")),
        ]
        cw = (W - 2*m) / len(cols_nut)
        for i, (nm, vl) in enumerate(cols_nut):
            cx = m + i*cw
            bg = colors.HexColor("#f9fafb") if i%2==0 else colors.white
            rect_fill(cx, m, cw, ty - m, bg)
            c.setFont("Helvetica", 5); c.setFillColor(colors.HexColor("#6b7280"))
            c.drawCentredString(cx + cw/2, ty - 4*mm, nm)
            c.setFont("Helvetica-Bold", 6); c.setFillColor(colors.HexColor("#111827"))
            c.drawCentredString(cx + cw/2, ty - 9*mm, str(vl)[:8])

        c.setStrokeColor(colors.HexColor("#374151")); c.setLineWidth(1)
        c.rect(0.5, 0.5, W-1, H-1, fill=0, stroke=1)

    # ══════════════════════════════════════════════════════════════════════════
    # LAYOUT CIRCULAR (90 x 90mm — renderizado em quadrado, circular via borda)
    # ══════════════════════════════════════════════════════════════════════════
    else:
        cx, cy, r = W/2, H/2, W/2 - 1*mm
        # Círculo de fundo
        c.setFillColor(T["bg"]); c.circle(cx, cy, r, fill=1, stroke=0)
        # Círculo accent externo
        c.setStrokeColor(T["acc"]); c.setLineWidth(3)
        c.circle(cx, cy, r - 1, fill=0, stroke=1)
        # Arco interno branco para conteúdo
        c.setFillColor(colors.white); c.circle(cx, cy, r - 8*mm, fill=1, stroke=0)

        # Produto no topo do círculo
        prod = (campos.get("denominacao") or "Produto")[:22]
        c.setFont("Helvetica-Bold", 9); c.setFillColor(T["txt"])
        c.drawCentredString(cx, H - 14*mm, prod)
        c.setFont("Helvetica", 6); c.setFillColor(T["acc"])
        c.drawCentredString(cx, H - 18*mm, campos.get("carimbo","SIF 000"))

        # Conteúdo líquido central
        c.setFont("Helvetica-Bold", 18); c.setFillColor(T["dark"])
        c.drawCentredString(cx, cy + 6*mm, campos.get("conteudo_liquido",""))

        # Fabricante
        fab = (campos.get("fabricante","") or "").split("\n")[0][:28]
        c.setFont("Helvetica", 6); c.setFillColor(colors.HexColor("#6b7280"))
        c.drawCentredString(cx, cy - 2*mm, fab)

        # Glúten/lactose
        c.setFont("Helvetica-Bold", 6); c.setFillColor(colors.HexColor("#dc2626"))
        c.drawCentredString(cx, cy - 8*mm, campos.get("gluten",""))

        # Conservação
        conserv = (campos.get("conservacao","") or "")[:35]
        c.setFont("Helvetica", 5.5); c.setFillColor(colors.HexColor("#374151"))
        c.drawCentredString(cx, 14*mm, conserv)
        c.setFont("Helvetica", 5); c.setFillColor(colors.HexColor("#9ca3af"))
        c.drawCentredString(cx, 10*mm, "LOTE e VALIDADE: veja embalagem")

    c.save()
    pdf_bytes = buf.getvalue()

    # ── Converte para PNG usando PyMuPDF ──────────────────────────────────────
    png_bytes = b""
    try:
        import fitz as _fitz
        doc = _fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        mat = _fitz.Matrix(4, 4)  # 4x zoom = alta resolução
        pix = page.get_pixmap(matrix=mat, alpha=False)
        png_bytes = pix.tobytes("png")
    except Exception:
        pass

    return pdf_bytes, png_bytes


@app.post("/criar")
async def criar_rotulo(request: Request):
    """
    Gera rótulo completo: conteúdo via Claude + validação automática.
    Retorna SSE stream com campos JSON e depois validação streaming.
    """
    form = await request.form()
    produto     = form.get("produto", "")
    categoria   = form.get("categoria", "")
    especie     = form.get("especie", "")
    orgao       = form.get("orgao", "SIF")
    num_reg     = form.get("num_registro", "")
    peso        = form.get("peso", "")
    fabricante  = form.get("fabricante", "")
    endereco    = form.get("endereco", "")
    cnpj        = form.get("cnpj", "")
    ingredientes= form.get("ingredientes", "")
    nutricional = form.get("nutricional", "")
    obs         = form.get("obs", "")
    formato     = form.get("formato", "retangular")
    tema        = form.get("tema", "moderno")

    if not produto or not categoria:
        return JSONResponse({"error": "Produto e categoria são obrigatórios"},
                            headers={"Access-Control-Allow-Origin": "*"})

    user_msg = f"""Gere o rótulo para:
PRODUTO: {produto}
CATEGORIA: {categoria}
ESPÉCIE: {especie or "não informado"}
ÓRGÃO DE INSPEÇÃO: {orgao} {num_reg}
PESO/VOLUME: {peso}
FABRICANTE: {fabricante}
ENDEREÇO: {endereco}
CNPJ: {cnpj}
INGREDIENTES FORNECIDOS: {ingredientes or "gerar com base na categoria"}
INFO NUTRICIONAL: {nutricional or "calcular pela tabela TACO"}
OBSERVAÇÕES: {obs}

Retorne SOMENTE o JSON conforme especificado."""

    async def stream_criar():
        headers_cors = {"Access-Control-Allow-Origin": "*",
                        "Content-Type": "text/event-stream",
                        "Cache-Control": "no-cache"}
        try:
            # ── Fase 1: Gerar campos via Claude ──────────────────────────────
            resp = httpx.AsyncClient(timeout=60.0)
            async with resp as client:
                r = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": os.environ.get("ANTHROPIC_API_KEY",""),
                             "anthropic-version": "2023-06-01",
                             "content-type": "application/json"},
                    json={"model": "claude-sonnet-4-20250514",
                          "max_tokens": 2000,
                          "system": SP_CRIAR_ROTULO,
                          "messages": [{"role": "user", "content": user_msg}]}
                )
                data = r.json()
                raw_json = data["content"][0]["text"]

            # Limpa markdown se veio
            raw_json = raw_json.strip()
            if raw_json.startswith("```"):
                raw_json = raw_json.split("```")[1]
                if raw_json.startswith("json"):
                    raw_json = raw_json[4:]
            raw_json = raw_json.strip().rstrip("```")

            campos = json.loads(raw_json)

            # Emite campos para o frontend renderizar preview
            yield f"data: {json.dumps({'tipo': 'campos', 'dados': json.dumps(campos)})}\n\n"

            # ── Fase 2: Gerar PDF + PNG ───────────────────────────────────────
            try:
                pdf_bytes, png_bytes = _gerar_pdf_label(campos, formato, tema)
                pdf_b64 = base64.b64encode(pdf_bytes).decode()
                png_b64 = base64.b64encode(png_bytes).decode() if png_bytes else ""
                yield f"data: {json.dumps({'tipo': 'arquivos', 'pdf': pdf_b64, 'png': png_b64, 'produto': produto})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'tipo': 'aviso', 'msg': 'Preview gerado; PDF indisponível: ' + str(e)[:60]})}\n\n"

            # ── Fase 3: Validação automática do rótulo gerado ─────────────────
            yield f"data: {json.dumps({'tipo': 'validacao_inicio'})}\n\n"

            kb_text = await get_kb_for_categories(detect_categories(categoria + " " + produto))
            kb_section = f"\n\nCONTEXTO LEGISLATIVO:\n{kb_text}" if kb_text else ""

            val_system = SP_VALIDACAO.replace("{kb_section}", kb_section)
            val_msg = f"""Valide este rótulo que acabou de ser GERADO automaticamente.
Produto: {campos.get('denominacao', produto)}
Campos gerados: {json.dumps(campos, ensure_ascii=False)[:3000]}"""

            async with httpx.AsyncClient(timeout=120.0) as client2:
                async with client2.stream("POST",
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": os.environ.get("ANTHROPIC_API_KEY",""),
                             "anthropic-version": "2023-06-01",
                             "content-type": "application/json"},
                    json={"model": "claude-sonnet-4-20250514",
                          "max_tokens": 3000, "stream": True,
                          "system": val_system,
                          "messages": [{"role": "user", "content": val_msg}]}
                ) as resp2:
                    async for line in resp2.aiter_lines():
                        if line.startswith("data:"):
                            ev = json.loads(line[5:].strip())
                            if ev.get("type") == "content_block_delta":
                                chunk = ev.get("delta",{}).get("text","")
                                if chunk:
                                    yield f"data: {json.dumps({'tipo': 'validacao_texto', 'text': chunk})}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'tipo': 'erro', 'msg': str(e)[:200]})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(stream_criar(),
        media_type="text/event-stream",
        headers={"Access-Control-Allow-Origin": "*",
                 "Cache-Control": "no-cache",
                 "X-Accel-Buffering": "no"})


@app.on_event("startup")
async def startup_load():
    """No startup, carrega dados persistidos do Supabase para memória."""
    global _cases_db, _monitor_history
    if _SUPABASE_ON:
        rows = await load_cases_from_supabase()
        if rows:
            _cases_db = rows
        alerts = await load_monitor_from_supabase()
        if alerts:
            _monitor_history = alerts

@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "ValidaRótulo IA v6",
        "supabase": "conectado" if _SUPABASE_ON else "não configurado (in-memory)",
        "cases_em_memoria": len(_cases_db),
        "kb_categories": len(MAPA_URLS),
        "kb_cached": list(_kb_cache.keys()),
        "endpoints": ["/validar", "/eval", "/feedback", "/admin/stats", "/monitor/check"],
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

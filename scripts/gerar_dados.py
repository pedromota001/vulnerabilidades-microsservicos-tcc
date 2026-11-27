#!/usr/bin/env python3
"""Converte a planilha de análise do TCC em site/data/dados.json.

A planilha é a única fonte de dados do site. Rode de novo sempre que ela mudar:

    python3 scripts/gerar_dados.py

Usa só a biblioteca padrão (o .xlsx é um zip de XML). Lê os valores
calculados que o Excel/LibreOffice salvou no arquivo, por isso a planilha
deve ser salva por um deles depois de cada edição.
"""
import json
import shutil
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PLANILHA = RAIZ / "dados" / "planilha-analise-tcc2.xlsx"
PDF = RAIZ / "dados" / "tcc.pdf"
SAIDA = RAIZ / "site" / "data" / "dados.json"

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
DIMENSOES = ["Desempenho", "Complexidade", "Custo operacional"]
# Ordem de força das ligações, definida no Leia-me.
ORDEM_LIGACAO = ["Explícita", "Inferida", "Explícita (genérica)", "Nenhuma"]


# ---------------------------------------------------------------- leitura
def _indice_coluna(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n


def ler_planilha(caminho):
    """Devolve {aba: {linha: {coluna: valor}}} e as cores de fundo por estilo."""
    z = zipfile.ZipFile(caminho)
    strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            strings.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    abas, estilos = {}, {}
    for s in wb.find("m:sheets", NS):
        alvo = rels[s.get(f"{{{NS['r']}}}id")].lstrip("/")
        alvo = alvo if alvo.startswith("xl/") else "xl/" + alvo
        linhas, est = {}, {}
        for c in ET.fromstring(z.read(alvo)).iter(f"{{{NS['m']}}}c"):
            ref = c.get("r")
            lin, col = int(re.search(r"\d+", ref).group()), _indice_coluna(ref)
            v, tipo = c.find("m:v", NS), c.get("t")
            if tipo == "s" and v is not None:
                val = strings[int(v.text)]
            elif tipo == "inlineStr":
                val = "".join(x.text or "" for x in c.iter(f"{{{NS['m']}}}t"))
            elif v is not None:
                val = v.text
                if tipo not in ("str", "e"):
                    try:
                        f = float(val)
                        val = int(f) if f.is_integer() else f
                    except ValueError:
                        pass
            else:
                continue
            if isinstance(val, str):
                val = val.strip()
            linhas.setdefault(lin, {})[col] = val
            est[(lin, col)] = int(c.get("s", 0))
        abas[s.get("name")] = linhas
        estilos[s.get("name")] = est
    return abas, estilos, _cores_por_estilo(z)


def _cores_por_estilo(z):
    st = ET.fromstring(z.read("xl/styles.xml"))
    fills = []
    for f in st.find("m:fills", NS):
        fg = f.find(".//m:fgColor", NS)
        rgb = fg.get("rgb") if fg is not None else None
        fills.append("#" + rgb[2:] if rgb else None)
    return [fills[int(x.get("fillId", 0))] for x in st.find("m:cellXfs", NS)]


def tabela(abas, nome, colunas, padrao_id=None, linha_cab=1):
    """Lê uma aba como lista de dicts. Só as colunas listadas (na ordem A, B, C...).
    Com padrao_id, ignora linhas cuja 1ª coluna não casa (legendas, notas)."""
    linhas = abas[nome]
    out = []
    for n in sorted(linhas):
        if n <= linha_cab:
            continue
        lin = linhas[n]
        if padrao_id and not re.fullmatch(padrao_id, str(lin.get(1, ""))):
            continue
        if not any(lin.get(i + 1) not in (None, "") for i in range(len(colunas))):
            continue
        out.append({k: lin.get(i + 1, "") for i, k in enumerate(colunas)})
    return out


def lista_codigos(texto):
    return [c for c in re.split(r"[,;\s]+", str(texto)) if re.fullmatch(r"[A-Z]{3}", c)]


def valor_por_rotulo(abas, nome, rotulo, coluna=3):
    for lin in abas[nome].values():
        if str(lin.get(1, "")).strip() == rotulo:
            return lin.get(coluna)
    raise KeyError(f"Rótulo '{rotulo}' não encontrado na aba {nome}")


# ---------------------------------------------------------------- licença
# Nome em português e link de cada código SPDX que o campo `license` do CITATION.cff pode ter.
LICENCAS = {
    "CC-BY-4.0": ("Creative Commons Atribuição 4.0 Internacional (CC BY 4.0)",
                  "https://creativecommons.org/licenses/by/4.0/deed.pt-br"),
}


def codigo_licenca_cff(caminho):
    """Código do campo `license` do CITATION.cff, ou "" se o arquivo ou o campo não existirem."""
    if not caminho.exists():
        return ""
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        m = re.match(r"license:\s*[\"']?([^\"'#\s]+)", linha)
        if m:
            return m.group(1)
    return ""


def ler_licenca():
    """(nome, link). Usa o CITATION.cff; sem o campo (ou com código desconhecido),
    volta ao comportamento anterior: primeira linha do LICENSE, sem link."""
    codigo = codigo_licenca_cff(RAIZ / "CITATION.cff")
    if codigo in LICENCAS:
        return LICENCAS[codigo]
    lic = RAIZ / "LICENSE"
    if lic.exists():
        return next((l.strip() for l in lic.read_text(encoding="utf-8").splitlines() if l.strip()), ""), ""
    return "", ""


# ---------------------------------------------------------------- montagem
def montar(abas, estilos, cores):
    estudos = tabela(abas, "Corpus", ["codigo", "autores", "ano", "veiculo", "tipo", "nivel", "titulo", "doi"],
                     r"[A-Z]{3}")
    vulns = tabela(abas, "Vuln_Consolidadas",
                   ["id", "frente", "categoria", "nome", "descricao", "ocorrencias", "n_estudos", "estudos",
                    "n_mitigacoes", "observacao", "n_mitigacoes_especificas"], r"F\d-\d\d[a-z]?")
    oc_vuln = tabela(abas, "Ocorrencias_Vuln", ["id", "estudo", "item", "pagina", "origem", "destino"], r"OV\d+")
    mits = tabela(abas, "Mitigacoes", ["id", "nome", "descricao", "ocorrencias", "n_estudos", "n_vulns"], r"M\d\d")
    oc_mit = tabela(abas, "Ocorrencias_Mit", ["id", "estudo", "trecho", "pagina", "mitigacao"], r"OM\d+")
    mapa = tabela(abas, "Mapeamento", ["vuln", "categoria", "mitigacao", "tipo", "base"], r"F\d-\d\d[a-z]?")
    # Colunas N a P (auxiliares) ficam de fora de propósito.
    trechos = tabela(abas, "Q4_Trechos",
                     ["id", "estudo", "pagina", "mitigacao", "dimensao", "texto", "evidencia", "mapeamento",
                      "justificativa", "produto", "caracteristica", "destino", "observacao"], r"TQ\d+")

    # Cores e nomes dos níveis vindos da própria Q4_Matriz (cor de fundo da célula de nível).
    niveis = {}
    matriz = []
    for n in sorted(abas["Q4_Matriz"]):
        lin = abas["Q4_Matriz"][n]
        if not re.fullmatch(r"M\d\d", str(lin.get(1, ""))):
            continue
        celulas = []
        for i, dim in enumerate(DIMENSOES):
            c0 = 3 + 4 * i
            nivel = lin.get(c0, "")
            cor = cores[estilos["Q4_Matriz"].get((n, c0), 0)]
            if nivel and nivel != "Sem evidência" and cor:
                niveis.setdefault(nivel, cor)
            celulas.append({"dimensao": dim, "nivel": nivel, "base": lin.get(c0 + 1, ""),
                            "n_estudos": lin.get(c0 + 2, ""), "observacao": lin.get(c0 + 3, "")})
        matriz.append({"mitigacao": lin[1], "nome": lin.get(2, ""), "celulas": celulas})
    legenda_matriz = next((str(l[1]) for l in abas["Q4_Matriz"].values()
                           if str(l.get(1, "")).startswith("Legenda")), "")

    # Ligações: tipo mais forte por vulnerabilidade.
    for v in vulns:
        ligs = [m for m in mapa if m["vuln"] == v["id"]]
        tipos = [l["tipo"] for l in ligs] or ["Nenhuma"]
        v["ligacao_mais_forte"] = min(tipos, key=ORDEM_LIGACAO.index)
        v["ligacoes"] = [{"mitigacao": l["mitigacao"], "tipo": l["tipo"], "base": l["base"]} for l in ligs]
        v["lista_estudos"] = lista_codigos(v["estudos"])
        v["origens"] = [o["id"] for o in oc_vuln if o["destino"] == v["id"]]
    for m in mits:
        m["lista_estudos"] = sorted({o["estudo"] for o in oc_mit if o["mitigacao"] == m["id"]})
        m["ligacoes"] = [{"vuln": l["vuln"], "tipo": l["tipo"], "base": l["base"]} for l in mapa
                         if l["mitigacao"] == m["id"]]

    frentes = []
    for v in vulns:
        f = next((x for x in frentes if x["nome"] == v["frente"]), None)
        if not f:
            f = {"nome": v["frente"], "categorias": []}
            frentes.append(f)
        c = next((x for x in f["categorias"] if x["nome"] == v["categoria"]), None)
        if not c:
            c = {"nome": v["categoria"], "vulns": []}
            f["categorias"].append(c)
        c["vulns"].append(v["id"])

    # Leia-me: textos institucionais e descrições das frentes / tipos de ligação.
    leia = [str(abas["Leia-me"][n].get(1, "")) for n in sorted(abas["Leia-me"])]
    def achar(prefixo):
        return next((l for l in leia if l.startswith(prefixo)), "")
    descr_frentes = {}
    for l in leia:
        m = re.match(r"(Frente \d) — ([^:]+): (.*)", l)
        if m:
            descr_frentes[m.group(1)] = {"titulo": m.group(2), "descricao": m.group(3)}
    for f in frentes:
        f.update(descr_frentes.get(f["nome"], {"titulo": "", "descricao": ""}))
    tipos_ligacao = {}
    for l in leia:
        m = re.match(r"• (Explícita \(genérica\)|Explícita|Inferida): (.*)", l)
        if m:
            tipos_ligacao[m.group(1)] = m.group(2)
    trabalho = re.search(r'"([^"]+)"', achar("Trabalho:"))
    autor = re.search(r"Autor: ([^.]+)\. Orientador: (.+?)\.?$", achar("Autor:"))
    repo = re.search(r"https?://\S+", achar("Versão final"))
    sobre = {
        "titulo": trabalho.group(1) if trabalho else "",
        "instituicao": achar("Trabalho:"),
        "autor": autor.group(1) if autor else "",
        "orientador": autor.group(2) if autor else "",
        "versao": achar("Versão final"),
        "repositorio": repo.group(0).rstrip(".") if repo else "",
        "rastreabilidade": achar("Toda a análise"),
        "escopo": achar("• \"Escopo B\""),
        "estrutura": achar("Três níveis"),
        "regras_contagem": [l for l in leia if re.match(r"\d\. ", l)],
        "paginas": achar("• Páginas:"),
        "status": achar("Versão final (nov"),
    }
    sobre["licenca"], sobre["licenca_url"] = ler_licenca()

    # Indicadores (recalculados das abas de base).
    exp = [v for v in vulns if v["ligacao_mais_forte"] == "Explícita"]
    sem_concreta = [v for v in vulns if v["ligacao_mais_forte"] in ("Explícita (genérica)", "Nenhuma")]
    celulas = [c for m in matriz for c in m["celulas"]]
    principal = [c for c in celulas if c["base"] in ("Medido", "Declarado")]
    linhas_vuln = [o for o in oc_vuln if re.fullmatch(r"F\d-\d\d[a-z]?", o["destino"])]
    nao_contadas = [o for o in oc_vuln if not re.fullmatch(r"F\d-\d\d[a-z]?", o["destino"])]
    desdobramentos = valor_por_rotulo(abas, "Contagens",
                                      "Desdobramentos (um item que trata de mais de um problema vira mais de uma linha)")
    indicadores = {
        "estudos": len(estudos),
        "vulnerabilidades": len(vulns),
        "frentes": len(frentes),
        "categorias": sum(len(f["categorias"]) for f in frentes),
        "mitigacoes": len(mits),
        "mitigacoes_ligadas": len({l["mitigacao"] for l in mapa}),
        "vulns_explicitas": len(exp),
        "vulns_sem_concreta": len(sem_concreta),
        "matriz_mitigacoes": len(matriz),
        "matriz_celulas": len(celulas),
        "matriz_sem_evidencia": sum(c["nivel"] == "Sem evidência" for c in celulas),
        "matriz_principal": len(principal),
        "itens_extraidos": len(oc_vuln) - desdobramentos,
        "itens_nao_contados": len(nao_contadas),
        "itens_contados": len(linhas_vuln) - desdobramentos,
        "desdobramentos": desdobramentos,
        "linhas_codificacao": len(linhas_vuln),
    }
    # Valores como registrados na aba Contagens (para o teste comparar com os recalculados).
    indicadores_planilha = {
        "itens_extraidos": valor_por_rotulo(abas, "Contagens", "Itens registrados nos documentos de extração"),
        "itens_nao_contados": valor_por_rotulo(abas, "Contagens",
                                               "... que NÃO viraram vulnerabilidade (contexto, fora do escopo etc.)"),
        "itens_contados": valor_por_rotulo(abas, "Contagens", "... que sustentam vulnerabilidades"),
        "linhas_codificacao": valor_por_rotulo(abas, "Contagens", "Linhas de codificação ligadas a vulnerabilidades"),
        "mitigacoes_ligadas": valor_por_rotulo(abas, "Contagens", "Mitigações distintas ligadas a alguma vulnerabilidade"),
        "mitigacoes": valor_por_rotulo(abas, "Contagens", "Mitigações no catálogo"),
        "vulnerabilidades": valor_por_rotulo(abas, "Contagens", "Vulnerabilidades consolidadas"),
    }

    return {
        "sobre": sobre,
        "indicadores": indicadores,
        "indicadores_planilha": indicadores_planilha,
        "tipos_ligacao": tipos_ligacao,
        "ordem_ligacao": ORDEM_LIGACAO,
        "niveis": niveis,
        "legenda_matriz": legenda_matriz,
        "dimensoes": DIMENSOES,
        "frentes": frentes,
        "estudos": estudos,
        "vulnerabilidades": vulns,
        "ocorrencias_vuln": [o for o in oc_vuln if o in linhas_vuln],
        "mitigacoes": mits,
        "ocorrencias_mit": oc_mit,
        "matriz": matriz,
        "trechos": trechos,
        "arquivos": {"planilha": "dados/" + PLANILHA.name, "pdf": "dados/" + PDF.name if PDF.exists() else None},
    }


def main():
    abas, estilos, cores = ler_planilha(PLANILHA)
    dados = montar(abas, estilos, cores)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    # Copia a planilha (e o PDF, se existir) para o site poder oferecer o download.
    destino = RAIZ / "site" / "dados"
    destino.mkdir(parents=True, exist_ok=True)
    for arq in (PLANILHA, PDF):
        if arq.exists():
            shutil.copy2(arq, destino / arq.name)
    print(f"Gerado {SAIDA.relative_to(RAIZ)}")
    for k, v in dados["indicadores"].items():
        print(f"  {k}: {v}")
    return dados


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

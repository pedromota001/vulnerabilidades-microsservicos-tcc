"""Confere, célula por célula, se o que o site mostra é igual à planilha,
e recalcula as contagens que a planilha guarda como fórmulas.

Rodar:  python3 -m unittest discover -s tests -v
"""
import re
import sys
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import gerar_dados as g  # noqa: E402

ID_VULN = r"F\d-\d\d[a-z]?"


def linhas_brutas(abas, aba, padrao, ncols):
    """Linhas da aba cuja coluna A casa o padrão, como listas de valores brutos."""
    out = []
    for n in sorted(abas[aba]):
        lin = abas[aba][n]
        if re.fullmatch(padrao, str(lin.get(1, ""))):
            out.append([lin.get(c, "") for c in range(1, ncols + 1)])
    return out


class FidelidadeAPlanilha(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.abas, est, cores = g.ler_planilha(g.PLANILHA)
        cls.d = g.montar(cls.abas, est, cores)

    def comparar(self, aba, padrao, lista, campos):
        brutas = linhas_brutas(self.abas, aba, padrao, len(campos))
        self.assertEqual(len(lista), len(brutas), f"{aba}: nº de linhas")
        for bruta, item in zip(brutas, lista):
            for campo, valor in zip(campos, bruta):
                with self.subTest(aba=aba, id=bruta[0], campo=campo):
                    self.assertEqual(item[campo], valor)

    # ---- 1. Cada célula exibida é idêntica à da planilha
    def test_corpus(self):
        self.comparar("Corpus", r"[A-Z]{3}", self.d["estudos"],
                      ["codigo", "autores", "ano", "veiculo", "tipo", "nivel", "titulo", "doi"])

    def test_vulnerabilidades(self):
        self.comparar("Vuln_Consolidadas", ID_VULN, self.d["vulnerabilidades"],
                      ["id", "frente", "categoria", "nome", "descricao", "ocorrencias", "n_estudos", "estudos",
                       "n_mitigacoes", "observacao", "n_mitigacoes_especificas"])

    def test_mitigacoes(self):
        self.comparar("Mitigacoes", r"M\d\d", self.d["mitigacoes"],
                      ["id", "nome", "descricao", "ocorrencias", "n_estudos", "n_vulns"])

    def test_ocorrencias_mit(self):
        self.comparar("Ocorrencias_Mit", r"OM\d+", self.d["ocorrencias_mit"],
                      ["id", "estudo", "trecho", "pagina", "mitigacao"])

    def test_ocorrencias_vuln(self):
        brutas = [b for b in linhas_brutas(self.abas, "Ocorrencias_Vuln", r"OV\d+", 6) if re.fullmatch(ID_VULN, b[5])]
        campos = ["id", "estudo", "item", "pagina", "origem", "destino"]
        self.assertEqual(len(self.d["ocorrencias_vuln"]), len(brutas))
        for b, o in zip(brutas, self.d["ocorrencias_vuln"]):
            self.assertEqual([o[c] for c in campos], b)

    def test_mapeamento(self):
        brutas = linhas_brutas(self.abas, "Mapeamento", ID_VULN, 5)
        site = sorted((v["id"], l["mitigacao"], l["tipo"], l["base"])
                      for v in self.d["vulnerabilidades"] for l in v["ligacoes"])
        self.assertEqual(site, sorted((b[0], b[2], b[3], b[4]) for b in brutas))

    def test_trechos_q4(self):
        self.comparar("Q4_Trechos", r"TQ\d+", self.d["trechos"],
                      ["id", "estudo", "pagina", "mitigacao", "dimensao", "texto", "evidencia", "mapeamento",
                       "justificativa", "produto", "caracteristica", "destino", "observacao"])

    def test_matriz(self):
        brutas = linhas_brutas(self.abas, "Q4_Matriz", r"M\d\d", 14)
        self.assertEqual(len(self.d["matriz"]), len(brutas))
        for b, m in zip(brutas, self.d["matriz"]):
            self.assertEqual((m["mitigacao"], m["nome"]), (b[0], b[1]))
            for i, c in enumerate(m["celulas"]):
                with self.subTest(m=b[0], dim=c["dimensao"]):
                    self.assertEqual([c["nivel"], c["base"], c["n_estudos"], c["observacao"]], b[2 + 4 * i: 6 + 4 * i])

    def test_ordem_das_dimensoes(self):
        cab = self.abas["Q4_Matriz"][1]
        self.assertEqual([cab[3], cab[7], cab[11]],
                         [f"{dim} — Nível" for dim in self.d["dimensoes"]])
        self.assertEqual(self.d["dimensoes"], ["Desempenho", "Complexidade", "Custo operacional"])

    # ---- 2. Contagens da planilha (fórmulas) = recalculadas a partir das abas de base
    def test_contagens_por_vulnerabilidade(self):
        for v in self.d["vulnerabilidades"]:
            with self.subTest(v=v["id"]):
                self.assertEqual(v["n_mitigacoes"], len(v["ligacoes"]))
                self.assertEqual(v["n_estudos"], len(v["lista_estudos"]))
                self.assertEqual(v["ocorrencias"], len(v["origens"]))
                self.assertEqual(sorted(v["lista_estudos"]),
                                 sorted({o["estudo"] for o in self.d["ocorrencias_vuln"] if o["destino"] == v["id"]}))

    def test_contagens_por_mitigacao(self):
        for m in self.d["mitigacoes"]:
            with self.subTest(m=m["id"]):
                self.assertEqual(m["n_vulns"], len(m["ligacoes"]))
                self.assertEqual(m["n_estudos"], len(m["lista_estudos"]))
                self.assertEqual(m["ocorrencias"], sum(o["mitigacao"] == m["id"] for o in self.d["ocorrencias_mit"]))

    def test_n_estudos_da_matriz(self):
        estudos = defaultdict(set)
        for t in self.d["trechos"]:
            if t["destino"] == "MATRIZ":
                estudos[(t["mitigacao"], t["dimensao"])].add(t["estudo"])
        for m in self.d["matriz"]:
            for c in m["celulas"]:
                with self.subTest(m=m["mitigacao"], dim=c["dimensao"]):
                    self.assertEqual(c["n_estudos"], len(estudos[(m["mitigacao"], c["dimensao"])]))
                    self.assertEqual(c["nivel"] == "Sem evidência", c["n_estudos"] == 0)

    def test_aba_contagens_por_categoria(self):
        linhas = [l for l in self.abas["Contagens"].values() if str(l.get(1, "")).startswith("Frente ")]
        self.assertEqual(len(linhas), 12)
        for l in linhas:
            cat = l[2]
            vs = [v for v in self.d["vulnerabilidades"] if v["categoria"] == cat]
            ligs = [x for v in vs for x in v["ligacoes"]]
            with self.subTest(categoria=cat):
                self.assertEqual(l[3], sum(len(v["origens"]) for v in vs), "linhas de codificação")
                self.assertEqual(l[4], len(vs), "vulnerabilidades")
                self.assertEqual(l[5], sum(v["ligacao_mais_forte"] == "Nenhuma" for v in vs), "sem mitigação")
                self.assertEqual(l[6], sum(v["ligacao_mais_forte"] == "Explícita (genérica)" for v in vs), "só genérica")
                self.assertEqual(l[7], sum(x["tipo"].startswith("Explícita") for x in ligs), "ligações explícitas")
                self.assertEqual(l[8], sum(x["tipo"] == "Inferida" for x in ligs), "ligações inferidas")

    def test_aba_q4_contagens(self):
        q = {str(l.get(1, "")).strip(): l for l in self.abas["Q4_Contagens"].values()}
        cel = [(i, c) for m in self.d["matriz"] for i, c in enumerate(m["celulas"])]
        for rotulo, cond in [("Medido", lambda c: c["base"] == "Medido"),
                             ("Declarado", lambda c: c["base"] == "Declarado"),
                             ("Declarado (mapeamento inferido)", lambda c: c["base"] == "Declarado (mapeamento inferido)"),
                             ("Inferido", lambda c: c["base"] == "Inferido"),
                             ("Alto", lambda c: c["nivel"] == "Alto"), ("Médio", lambda c: c["nivel"] == "Médio"),
                             ("Baixo", lambda c: c["nivel"] == "Baixo"),
                             ("Relatado, sem magnitude", lambda c: c["nivel"] == "Relatado, sem magnitude")]:
            for i in range(3):
                with self.subTest(indicador=rotulo, dim=i):
                    self.assertEqual(q[rotulo][2 + i], sum(cond(c) for j, c in cel if j == i))
        tr = self.d["trechos"]
        mz = [t for t in tr if t["destino"] == "MATRIZ"]
        esperado = {
            "Registros com destino MATRIZ": len(mz),
            "… medidos": sum(t["evidencia"] == "Medido" for t in mz),
            "… inferidos": sum(t["evidencia"] == "Inferido" for t in mz),
            "… declarados com mapeamento inferido": sum(t["evidencia"] == "Declarado" and t["mapeamento"] == "Inferido" for t in mz),
            "Citações secundárias visíveis, fora da matriz (SEC)": sum(t["destino"] == "SEC" for t in tr),
            "Excluídos por dimensão indefinida (EXCL)": sum(t["destino"] == "EXCL" for t in tr),
            "Fora do escopo ou do catálogo (FORA)": sum(t["destino"] == "FORA" for t in tr),
            "Estudos com ao menos um trecho na matriz": len({t["estudo"] for t in mz}),
            "Estudos com trecho medido na matriz": len({t["estudo"] for t in mz if t["evidencia"] == "Medido"}),
            "Mitigações analisadas": len(self.d["matriz"]),
            "Sem nenhuma evidência nas 3 dimensões": sum(all(c["nivel"] == "Sem evidência" for c in m["celulas"]) for m in self.d["matriz"]),
            "Com evidência dos autores (medida ou declarada, mapeamento explícito) nas 3 dimensões":
                sum(all(c["base"] in ("Medido", "Declarado") for c in m["celulas"]) for m in self.d["matriz"]),
        }
        for rotulo, valor in esperado.items():
            with self.subTest(indicador=rotulo):
                self.assertEqual(q[rotulo][5], valor)

    # ---- 3. Textos do Leia-me usados no site existem na planilha
    def test_textos_do_leia_me(self):
        leia = " ".join(str(l.get(1, "")) for l in self.abas["Leia-me"].values())
        s = self.d["sobre"]
        for campo in ["titulo", "autor", "orientador", "repositorio", "estrutura", "escopo"]:
            with self.subTest(campo=campo):
                self.assertTrue(s[campo] and s[campo] in leia)
        self.assertEqual(len(self.d["tipos_ligacao"]), 3)
        self.assertTrue(all(f["titulo"] for f in self.d["frentes"]))


if __name__ == "__main__":
    unittest.main()

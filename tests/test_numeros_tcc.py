"""Confere se os números gerados a partir da planilha batem com os do TCC.

Rodar:  python3 -m unittest discover -s tests -v
Se algum número não bater, o teste falha e o site não é publicado.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import gerar_dados  # noqa: E402

# Valores publicados no texto do TCC.
TCC = {
    "estudos": 17,
    "vulnerabilidades": 43,
    "frentes": 3,
    "categorias": 12,
    "mitigacoes": 27,
    "mitigacoes_ligadas": 26,
    "vulns_explicitas": 24,
    "vulns_sem_concreta": 9,
    "matriz_mitigacoes": 25,
    "matriz_celulas": 75,
    "matriz_sem_evidencia": 34,
    "matriz_principal": 27,
    "itens_extraidos": 110,
    "itens_nao_contados": 25,
    "itens_contados": 85,
    "linhas_codificacao": 90,
}
PERCENTUAIS = {  # (numerador, denominador, valor no TCC com 1 casa)
    "vulns_explicitas": ("vulnerabilidades", "55,8"),
    "vulns_sem_concreta": ("vulnerabilidades", "20,9"),
    "matriz_principal": ("matriz_celulas", "36,0"),
}


class NumerosDoTCC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        abas, estilos, cores = gerar_dados.ler_planilha(gerar_dados.PLANILHA)
        cls.dados = gerar_dados.montar(abas, estilos, cores)
        cls.ind = cls.dados["indicadores"]

    def test_valores_do_tcc(self):
        for chave, esperado in TCC.items():
            with self.subTest(indicador=chave):
                self.assertEqual(self.ind[chave], esperado,
                                 f"{chave}: site = {self.ind[chave]}, TCC = {esperado}")

    def test_percentuais(self):
        for num, (den, esperado) in PERCENTUAIS.items():
            with self.subTest(indicador=num):
                pct = f"{100 * self.ind[num] / self.ind[den]:.1f}".replace(".", ",")
                self.assertEqual(pct, esperado)

    def test_recalculo_bate_com_aba_contagens(self):
        for chave, valor in self.dados["indicadores_planilha"].items():
            with self.subTest(indicador=chave):
                self.assertEqual(self.ind[chave], valor,
                                 f"{chave}: recalculado = {self.ind[chave]}, aba Contagens = {valor}")

    def test_reconciliacao_fecha(self):
        i = self.ind
        self.assertEqual(i["itens_nao_contados"] + i["itens_contados"], i["itens_extraidos"])
        self.assertEqual(i["itens_contados"] + i["desdobramentos"], i["linhas_codificacao"])

    def test_colunas_auxiliares_fora(self):
        for t in self.dados["trechos"]:
            self.assertFalse({"chave", "auxiliar"} & {k.lower() for k in t})
        self.assertEqual(len(self.dados["trechos"][0]), 13)

    def test_referencias_validas(self):
        estudos = {e["codigo"] for e in self.dados["estudos"]}
        mits = {m["id"] for m in self.dados["mitigacoes"]}
        for v in self.dados["vulnerabilidades"]:
            self.assertTrue(set(v["lista_estudos"]) <= estudos, v["id"])
            for l in v["ligacoes"]:
                self.assertIn(l["mitigacao"], mits, v["id"])
        for t in self.dados["trechos"]:
            self.assertIn(t["estudo"], estudos, t["id"])

    def test_cores_dos_niveis(self):
        self.assertEqual(set(self.dados["niveis"]), {"Alto", "Médio", "Baixo", "Relatado, sem magnitude"})


if __name__ == "__main__":
    unittest.main()

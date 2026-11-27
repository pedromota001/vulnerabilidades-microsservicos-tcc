# Vulnerabilidades de Segurança em Arquiteturas de Microsserviços: Taxonomia, Mitigações e Trade-offs

Dados de pesquisa do Trabalho de Conclusão de Curso (TCC) em Ciência da Computação
da Universidade Católica de Pernambuco (UNICAP), 2026.

- **Autor:** Pedro Mota Santos Lindoso de Carvalho
- **Orientador:** Prof. Pedro Rafael Ximenes do Carmo

## Sobre o trabalho

O trabalho é uma revisão estruturada da literatura sobre vulnerabilidades de segurança
em arquiteturas de microsserviços. A partir de 17 estudos selecionados, foram produzidos:

- uma **taxonomia de 43 vulnerabilidades**, organizada em 3 frentes e 12 categorias;
- um **catálogo de 27 mitigações**, ligado às vulnerabilidades;
- uma **matriz de trade-offs**, que avalia 25 das 27 mitigações em três dimensões:
  desempenho, complexidade de implementação e custo operacional.

As três frentes da taxonomia são:

1. **Comunicação e Rede:** o caminho por onde as requisições trafegam, de fora para
   dentro (cliente → API Gateway → serviço) e entre serviços.
2. **Autenticação/Autorização em APIs:** falhas em quem pode acessar o quê.
3. **Service Mesh/mTLS:** vulnerabilidades próprias da camada de mesh.

Toda a análise é rastreável: cada vulnerabilidade, mitigação e célula da matriz de
trade-offs pode ser seguida até o trecho e a página do estudo de origem, e cada decisão
tomada está registrada na aba `Registro_Decisoes`.

## Site

Os dados da planilha também podem ser explorados no site
https://pedromota001.github.io/vulnerabilidades-microsservicos-tcc/,
que apresenta a taxonomia, as vulnerabilidades, as mitigações, a matriz de trade-offs
e os estudos selecionados de forma navegável. O site é gerado automaticamente a partir
da planilha, que é a sua única fonte de dados.

## Conteúdo do repositório

| Caminho | Descrição |
|---|---|
| `dados/planilha-analise-tcc2.xlsx` | Planilha de análise completa, citada no Apêndice A do trabalho |
| `scripts/` | Script que lê a planilha e gera os dados usados pelo site |
| `site/` | Código do site (HTML, CSS e JavaScript); os dados são gerados a partir da planilha, sem nada escrito à mão |
| `tests/` | Testes que conferem se os dados do site são idênticos aos da planilha e se os números batem com os do trabalho |
| `.github/workflows/` | Rotina que, a cada atualização na branch `master`, gera os dados, roda os testes e publica o site no GitHub Pages |
| `CITATION.cff` | Dados para citação do repositório |
| `LICENSE` | Texto da licença CC BY 4.0 |

A primeira aba da planilha, **Leia-me**, explica a estrutura, as convenções e as regras
de contagem. Recomenda-se lê-la antes das demais.

## Abas da planilha

| Aba | Conteúdo |
|---|---|
| `Leia-me` | Guia da planilha, convenções e regras de contagem |
| `Padroes_Sintese` | Os 10 padrões de síntese que sustentam a Discussão, com a evidência de cada um |
| `Corpus` | Os 17 estudos selecionados: código, autores, ano, veículo, tipo de estudo, nível, título e DOI |
| `Selecao_Busca` | Reexecução das buscas (01/11/2026), os 31 candidatos avaliados com a decisão de cada um e o caminho de identificação dos 17 estudos |
| `Ocorrencias_Vuln` | Cada item extraído dos estudos sobre vulnerabilidades, com página e destino (vulnerabilidade consolidada ou motivo de não contar) |
| `Vuln_Consolidadas` | As 43 vulnerabilidades da taxonomia, com frente, categoria, número de estudos e mitigações ligadas |
| `Ocorrencias_Mit` | Cada menção a uma mitigação nos estudos, com página e a mitigação correspondente do catálogo |
| `Mitigacoes` | O catálogo das 27 mitigações, com número de estudos e de vulnerabilidades ligadas |
| `Mapeamento` | As ligações entre vulnerabilidades e mitigações, com o tipo de cada ligação e sua base |
| `Q4_Trechos` | Os trechos dos estudos sobre o custo das mitigações (desempenho, complexidade de implementação e custo operacional), com tipo de evidência e destino |
| `Q4_Matriz` | A matriz de trade-offs: 25 mitigações × 3 dimensões, com nível, base, número de estudos e observação de cada célula |
| `Q4_Contagens` | Os indicadores da análise de trade-offs |
| `Contagens` | Os indicadores da taxonomia e da cobertura por mitigações, por frente e categoria, e a reconciliação entre itens extraídos e vulnerabilidades |
| `Contexto_Lacunas` | Achados de contexto e lacunas apontadas pelos próprios autores, usados na Discussão |
| `Regras_Metodologicas` | As regras R1 a R19 aplicadas na análise |
| `Registro_Decisoes` | Todas as decisões da análise (D01 a D69), com justificativa, itens afetados e quem decidiu |
| `Pendencias_Orientador` | As questões levadas ao orientador e como cada uma foi resolvida |
| `Fora_Escopo` | Os itens extraídos que não entraram na análise, com o motivo |

As contagens nas abas `Vuln_Consolidadas`, `Mitigacoes`, `Contagens`, `Q4_Matriz` e
`Q4_Contagens` são fórmulas, calculadas a partir das abas de ocorrências e de trechos.
As colunas N a P da `Q4_Trechos` estão ocultas porque apenas sustentam essas fórmulas.

## Como citar

CARVALHO, Pedro Mota Santos Lindoso de. **Vulnerabilidades de Segurança em Arquiteturas
de Microsserviços: Taxonomia, Mitigações e Trade-offs**: planilha de análise. Recife:
Universidade Católica de Pernambuco, 2026. Conjunto de dados. Disponível em:
https://github.com/pedromota001/vulnerabilidades-microsservicos-tcc.

Também é possível usar o botão **"Cite this repository"**, na lateral desta página.

## Licença

A planilha de análise deste repositório está disponível sob a licença
[Creative Commons Atribuição 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.pt-br).
Você pode copiar, redistribuir e adaptar o material para qualquer finalidade, desde que
cite a autoria.

Os trechos curtos dos estudos analisados, reproduzidos na planilha entre aspas e com
indicação de página, continuam pertencendo aos seus autores e não estão cobertos por
esta licença.

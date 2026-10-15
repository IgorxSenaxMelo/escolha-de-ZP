# Relatório de validação preliminar

- Cadastro: 20 alternativas lidas do script MATLAB; IDs não são renumerados (inclui ausência de ZP11 e ZP13 na lista fornecida).
- Algoritmo: merge sort interativo, julgamento direto/invertido, transitividade, classes de empate e ranking com posições iguais documentados.
- Ordem inicial: o MATLAB usa `rng(2026)` + `randperm`; a implementação atual usa a ordem fixa do cadastro. Portanto, equivalência exata da sequência de comparações não está demonstrada.
- Dados de fainas: preservadas séries disponíveis no código anterior; fonte e valores não foram validados independentemente com a imagem/registro oficial. As linhas ZP10-H e ZP12-H permanecem separadas.
- Indicadores socioeconômicos/geográficos: não preenchidos por falta de uma correspondência validada entre cada ZP, os municípios abrangidos e o ano de cada indicador.
- Testes automatizados: cobrem relação direta/inversa, transitividade, empate, comparação desconhecida e merge ordenado.
- Teste de interface/browser: não executado neste ambiente; é necessário validar localmente com `streamlit run app.py`.

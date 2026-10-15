# Relatório de validação

## Executado e aprovado
- `python -m unittest discover -s tests -v`: **24 testes OK** (relação direta/inversa, transitividade, empates,
  limite de 69 comparações, ordem final independente da ordem inicial em 45 execuções, usuário inconsistente
  termina, prior correto reduz nº de perguntas, registro sem dados pessoais, gravação em CSV/Sheets simulado,
  fallback quando o Sheets falha, cálculo de métricas de fainas, haversine).
- `python validacao.py`: 20 ZPs, séries 2017–2025 completas, fontes referenciadas existem. Avisos: IDHM ausente
  em ZP06/ZP20; 9 zeros de fainas não confirmados; séries ZP10-H/ZP12-H separadas.
- `python tests/smoke_app_stub.py`: `app.py` executa o fluxo (comparar → concluir → registrar uma única vez →
  desfazer → recomeçar) com Streamlit **simulado**.

## NÃO validado (limitações reais)
1. **Equivalência com o MATLAB:** o script `.m` não foi recebido nesta sessão (só o ZIP do projeto anterior).
   O algoritmo vem do `ranking.py` anterior, que já declarava reproduzir o MATLAB; não foi comparado com saídas reais do MATLAB.
2. **Interface real no navegador:** Streamlit/Plotly não puderam ser instalados aqui. Rode `streamlit run app.py` e teste.
3. **Google Sheets real:** testado só com planilha simulada (sem rede/credenciais). Faça um ranking de teste após configurar.
4. **Dados:** ver `DADOS_NAO_OBTIDOS.md`. Fainas e lotação não foram revalidadas com fonte oficial.

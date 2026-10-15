# Comparador de Zonas de Praticagem (ZP)

## O que foi aplicado do script MATLAB
- As 20 alternativas e seus IDs reais.
- Merge sort adaptativo: a aplicação só pergunta quando não conhece a relação.
- Reutilização dos julgamentos diretos.
- Inferência por transitividade entre classes de empate.
- Opção de empate.
- Salvamento automático do histórico em `sessao_zp.json`.
- Retomada da sessão ao abrir novamente a aplicação no mesmo diretório.
- Exportação de ranking e julgamentos em CSV.
- Ação para desfazer o último julgamento e reiniciar o ranking.

## Executar
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Observações
A lotação foi transcrita da tabela fornecida. As fainas foram transcritas visualmente
do gráfico de 2017 a 2025; confirme com a planilha original antes de usar para decisão.
IDHM, custo de vida e dados de aeroportos ainda não foram preenchidos com valores,
para evitar apresentar dados não verificados como fatos.
O estado é salvo em arquivo local `sessao_zp.json`. Em hospedagens efêmeras, esse arquivo
pode não persistir após reinicializações; para uso multiusuário ou persistência em nuvem,
será necessário configurar armazenamento adequado.

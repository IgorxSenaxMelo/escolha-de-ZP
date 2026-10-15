# Comparador de Zonas de Praticagem (ZP)

## Executar localmente
1. Instale Python 3.10 ou superior.
2. Descompacte o ZIP.
3. No terminal, dentro da pasta do projeto:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Conteúdo
- `app.py`: aplicação Streamlit.
- `indicadores_cidades.csv`: modelo para completar IDHM, custo de vida e aeroportos.
- `requirements.txt`: dependências.

## Importante
Os dados de lotação foram transcritos da imagem enviada pelo usuário e os valores anuais
de fainas foram transcritos visualmente da imagem histórica. Revise com a fonte original.
As séries de Sergipe e Ilhéus estão separadas para preservar a forma como aparecem no
gráfico histórico; não devem ser somadas automaticamente a outras séries sem validar
a abrangência por ano.
IDHM, custo de vida e aeroportos estão em branco intencionalmente até serem preenchidos
com fontes verificáveis.

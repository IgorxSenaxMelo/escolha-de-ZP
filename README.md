# Comparador de Zonas de Praticagem (ZP)

Cada pessoa compara ZPs duas a duas (ZP A, ZP B ou empate) e obtém o **seu ranking de preferência**.
Ao concluir, o ranking é gravado **de forma anônima, com data/hora**, numa planilha privada do criador.
A tela mostra, em cada par, IDHM (com ano e município), distância ao aeroporto, população, lotação
de práticos e dados de fainas 2017–2025.

## Executar
```bash
pip install -r requirements.txt
streamlit run app.py
```
Sem configurar o Google Sheets, o app funciona e grava em `respostas_local.csv` (só para testes locais).

## Gravar os rankings numa planilha só sua (Google Sheets)
1. Em <https://console.cloud.google.com> crie um projeto, ative as APIs **Google Sheets** e **Google Drive**.
2. Crie uma **conta de serviço** e baixe a chave JSON.
3. Crie uma planilha no seu Google Drive (**privada**). Compartilhe-a **somente** com o e-mail da conta
   de serviço (`client_email` do JSON), como *Editor*. Copie o ID da planilha (trecho entre `/d/` e `/edit`).
4. Preencha os segredos conforme `.streamlit/secrets.toml.example`:
   - local: arquivo `.streamlit/secrets.toml`;
   - Streamlit Community Cloud: *App settings → Secrets*.
5. Rode o app, conclua um ranking de teste e confira a aba `respostas`. A barra lateral mostra
   "Registro: Google Sheets ativo" quando as credenciais foram lidas.

Quem responde nunca vê a planilha. Cada linha: data/hora (Brasília e UTC), id aleatório de sessão,
nº de comparações/empates, duração, ranking (`ZP15 > ZP16 = ZP14 > …`), posição de cada ZP (`pos_ZPxx`)
e o histórico completo das respostas. **Não** são coletados nome, e-mail, IP nem identificadores de aparelho.
O aviso de registro anônimo aparece no topo da tela (boa prática de transparência/LGPD).

Se o Sheets falhar no momento de salvar, o app tenta o arquivo local e, se tudo falhar, oferece
"Tentar registrar novamente" à pessoa. Em hospedagem com disco efêmero o CSV local pode se perder:
confirme que o Sheets está ativo.

## Algoritmo (o que foi preservado)
Merge sort interativo: só pergunta quando a relação não pode ser inferida; reaproveita julgamentos
(direto e invertido); transitividade entre classes de empate; empate como resposta; posições iguais para
empatados; no máximo 69 comparações para 20 ZPs. **Desfazer**, **salvar/retomar (JSON)** e
exportação (CSV/Excel) estão disponíveis.

Diferenças em relação ao projeto anterior (explícitas, não silenciosas):
- **Ordem inicial** (`config_zp.json → ordem_inicial`): `prior` (padrão) coloca primeiro as ZPs de
  preferência histórica alta (14, 15, 16, 5, 17), depois as demais e por fim as baixas (6, 7, 8), embaralhando
  dentro de cada grupo. Isso só muda **quais pares são perguntados e quantos**; o ranking final vem apenas
  das respostas (teste automatizado confirma). Alternativas: `aleatoria` (análogo ao `randperm` do MATLAB) e
  `cadastro` (ordem fixa do projeto anterior). Não é possível reproduzir o gerador do MATLAB (`rng(2026)`) em Python.
- **Posição na tela (A/B) sorteada por par e sessão** para diluir viés de posição; não altera o resultado.
- **Rótulos de preferência histórica não aparecem durante a comparação** (evita efeito de "o que os outros
  preferem"); aparecem na aba *Perfil*, separados dos dados objetivos. Mude `mostrar_rotulos_na_comparacao` para `true` se quiser.
- **Correção importante:** a versão anterior salvava a sessão em um único `sessao_zp.json` no servidor, o que
  misturaria respostas de pessoas diferentes. Agora cada visitante tem sessão própria.

## Dados
| Arquivo | Conteúdo |
|---|---|
| `dados_zp.csv` | 20 ZPs, UF, lotação de práticos (tabela fornecida pelo criador) |
| `indicadores.csv` | indicadores com valor, unidade, município, ano, fonte, URL, data de consulta, qualidade |
| `referencias_geograficas.csv` | município/aeroporto de referência e coordenadas aproximadas (distância calculada) |
| `fainas_historicas.csv` | fainas 2017–2025 (transcrição fornecida; não revalidada) |
| `fontes.csv` | fontes usadas e fontes oficiais recomendadas ainda não consultadas |
| `config_zp.json` | grupos/preferências históricas e ordem inicial (editável sem mexer no algoritmo) |

Para atualizar um dado, edite o CSV e rode `python validacao.py`. O app só lê arquivos locais (funciona offline).
Veja **DADOS_NAO_OBTIDOS.md** para o que ainda falta.

## Testes
```bash
python -m unittest discover -s tests -v      # 24 testes (algoritmo, dados, gravação)
python tests/smoke_app_stub.py               # fluxo do app com Streamlit simulado
python validacao.py                          # consistência dos dados
```

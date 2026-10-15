# Comparador de Zonas de Praticagem (ZP)

## Executar localmente
1. Instale Python 3.10 ou superior.
2. No terminal, entre na pasta do projeto.
3. Execute `pip install -r requirements.txt`.
4. Execute `streamlit run app.py`.

## Algoritmo preservado
A aplicação implementa merge sort interativo, reutilização de julgamentos diretos, inversão de julgamento quando o par é consultado na ordem contrária, inferência por transitividade entre classes de empate, empate como resposta, salvamento de sessão e ranking com posições iguais para alternativas empatadas. O fluxo de comparações é adaptativo e só solicita um julgamento quando a relação não pode ser inferida.

**Diferença a observar:** o MATLAB define `rng(2026)` e gera `randperm(nAlt)`. A ordem pseudoaleatória do MATLAB não é reproduzida exatamente por Python sem reproduzir o gerador/algoritmo específico do MATLAB. Esta versão usa a ordem de cadastro como ordem inicial fixa, de forma determinística. O método de merge e as regras de julgamento são preservados, mas comparações específicas e ordem em cenários de inconsistência/empate podem diferir.

## Dados e limitações
- `dados_zp.csv`: cadastro de 20 alternativas e lotação transcrita da base anterior. Campos sem valor são indisponíveis/não pesquisados, não zero.
- `fainas_historicas.csv`: séries 2017–2025 transcritas visualmente da imagem/código previamente fornecido. Os zeros, a associação de séries e a fonte oficial precisam ser validados com a imagem original/planilha. Séries como Sergipe e Ilhéus são mantidas como linhas separadas (ZP10-H/ZP12-H), não somadas automaticamente às zonas atuais.
- `fontes.csv`: fontes institucionais de referência e status do levantamento. Os indicadores de IDHM, renda, PIB, segurança, saúde, aeroportos, distâncias e conectividade **não foram preenchidos**, pois exigem pesquisa e atribuição cuidadosa por município/região e ano.
- Os perfis de preferência (ZP14, ZP15, ZP16, ZP05 e ZP17; grupo de interesse militar ZP01–03; e percepção desfavorável ZP06–08) são apresentados como contexto preliminar do usuário, não como dados objetivos ou pontuação.

## Persistência
A sessão é salva automaticamente em `sessao_zp.json` no diretório local. A aba de comparação permite exportar/importar esse arquivo para mover a sessão entre dispositivos. Em hospedagem com disco efêmero ou múltiplos usuários, configure armazenamento persistente e isolamento por usuário antes de uso real.

## Testes
Execute `python -m unittest discover -s tests -v`. Os testes validam relações diretas, inversão, transitividade, empates e integridade das alternativas.

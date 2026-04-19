# Changelog

Este arquivo registra as mudancas notaveis da biblioteca `lpa2v`.

O formato foi inspirado em Keep a Changelog, mas adaptado para o contexto atual do projeto.

## [Unreleased]

- Nenhuma mudanca registrada no momento.

## [0.4.0] - 2026-04-19

### Adicionado

- algoritmo `Capet`/`CPAet` com suporte a analise temporal e filtro de melhores evidencias
- modelos publicos `CapetInput` e `CapetResult`
- suporte de linha de comando para `lpa2v capet`
- suporte a inicializacao temporal por `window_size` e `bootstrap_value`
- suite dedicada `tests/test_cpaet.py`
- exportacao publica de `Capet` no pacote principal e no modulo `lpa2v.algorithms`
- arquivo `LICENSE` sob a licenca MIT

### Alterado

- README ampliado com documentacao do `CAPet`, exemplos adicionais e fluxo de uso legado
- CLI passou a listar e executar o algoritmo `capet`
- `ParaAnalyzer` ganhou o metodo estatico `classify_values(...)` para classificacao direta a partir de `gc` e `gct`
- validacoes e testes do `para-analisador` foram reforcados
- a lista de algoritmos disponiveis passou a incluir `capet`
- metadata do pacote em `pyproject.toml` foi alinhado para MIT

### Observacoes

- a versao `0.4.0` foi escolhida por representar uma expansao funcional relevante sobre a base do ZIP, incluindo novo algoritmo e nova superficie de CLI/API

## [0.3.0] - 2026-04-13

### Adicionado

- estrutura inicial do pacote Python com layout `src/`
- modelos centrais de evidencia em `models.py`
- arquitetura base com `LPA2vAlgorithm`, `EvidencePairAlgorithm` e `AlgorithmRegistry`
- implementacoes dos algoritmos `para-analisador`, `NAP` e `CAP`
- fabrica de algoritmos com `create_algorithm(...)`
- interface de linha de comando para `algorithms`, `para-analisador`, `nap` e `cap`
- suite inicial de testes para `para-analisador`, `NAP` e `CAP`
- README com instalacao, uso em Python, uso por CLI e compatibilidade legada

### Observacoes

- esta entrada representa a base funcional encontrada no arquivo `lib-lpa2v-python-main.zip`
- a data `2026-04-19` foi registrada a partir do `LastWriteTime` do arquivo `lib-lpa2v-python-main.zip`

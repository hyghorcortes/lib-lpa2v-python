# LPA2v

Biblioteca Python orientada a objetos para algoritmos baseados em LPA2v.

Esta primeira versao foi criada para servir como base de crescimento da biblioteca e ja inclui os algoritmos `para-analisador`, `NAP`, `CAP` e `CAPet`, modelados de forma extensivel para facilitar a entrada de novos algoritmos no futuro. O `CAPet` desta biblioteca segue a formulacao da `CPAet` descrita por Hyghor Miranda Cortes et al., baseada em `mu`, `lambda` e na media movel `m_e` das melhores evidencias.

## Objetivos desta primeira versao

- consolidar uma base Python reutilizavel para algoritmos fundamentados em LPA2v
- disponibilizar implementacoes orientadas a objetos de `para-analisador`, `NAP`, `CAP` e `CAPet` com interfaces consistentes
- preservar a logica essencial dos algoritmos e as convencoes legadas necessarias para compatibilidade com referencias anteriores
- facilitar uso, teste e extensao da biblioteca tanto via codigo Python quanto por linha de comando

## Estrutura do projeto

```text
src/lpa2v/
  algorithms/
    base.py
    cap.py
    cpaet.py
    nap.py
    para_analyzer.py
    registry.py
  cli.py
  models.py
```

## Instalacao

```bash
pip install -e .
```

## Uso rapido em Python

```python
from lpa2v import Cap, Capet, EvidencePair, Nap, ParaAnalyzer

para_algorithm = ParaAnalyzer()
para_result = para_algorithm.run(EvidencePair(favorable=0.80, contrary=0.55))

print(para_result.state.value)   # QT-V
print(para_result.region_id)     # 8
print(para_result.gc)            # 0.25
print(para_result.gct)           # 0.35

nap_algorithm = Nap()
nap_result = nap_algorithm.analyze(0.70, 0.20)

print(nap_result.mi_er)          # 0.745049...
print(nap_result.phi_e)          # -0.9
print(nap_result.as_legacy_vector())

cap_algorithm = Cap()
cap_result = cap_algorithm.analyze(0.60, 0.70, 0.20)

print(cap_result.resultant_evidence_degree)  # 0.745049...
print(cap_result.signed_interval)            # -0.9
print(cap_result.control_mode.value)         # internal_analysis

capet_algorithm = Capet()
capet_result = capet_algorithm.analyze(1.00, 0.00, moving_average_in=(0.50, 0.60, 0.90))

print(capet_result.accepted_sample)          # True
print(capet_result.me)                       # 0.833333...
print(capet_result.me_adj)                   # 0.683333...
print(capet_result.state.value)              # V
print(capet_result.resultant_evidence_degree)  # 1.0

capet_bootstrap_result = capet_algorithm.analyze(1.00, 0.00, window_size=3)

print(capet_bootstrap_result.input.moving_average_in)  # (0.5, 0.5, 0.5)
print(capet_bootstrap_result.me_out)                   # (0.5, 0.5, 1.0)
```

## Uso com fabrica/registro de algoritmos

```python
from lpa2v import create_algorithm

algorithm = create_algorithm("para-analisador")
result = algorithm.run((0.60, 0.30))
print(result.to_dict())

nap = create_algorithm("nap")
print(nap.run((0.70, 0.20)).to_dict())

cap = create_algorithm("cap")
print(cap.run({"external_interval": 0.60, "mu": 0.70, "lambda": 0.20}).to_dict())

capet = create_algorithm("cpaet")
print(capet.run({"mu": 1.00, "lambda": 0.00, "moving_average_in": [0.50, 0.60, 0.90]}).to_dict())
print(capet.run({"mu": 1.00, "lambda": 0.00, "window_size": 3, "bootstrap_value": 0.50}).to_dict())
```

## Uso de entrada legada

Nas implementacoes antigas em MATLAB, em alguns pontos o segundo valor era usado como complemento de `lambda`.

Para esse caso, os algoritmos baseados em par de evidencias oferecem o atalho `analyze_legacy(...)`:

```python
from lpa2v import Cap, Capet, Nap, ParaAnalyzer

para_result = ParaAnalyzer().analyze_legacy(favorable=0.7, contrary_complement=0.8)
nap_result = Nap().analyze_legacy(favorable=0.7, contrary_complement=0.8)
cap_result = Cap().analyze_legacy(0.60, favorable=0.7, contrary_complement=0.8)
capet_result = Capet().analyze_legacy(favorable=0.7, contrary_complement=0.8, moving_average_in=(0.5, 0.5, 0.5))
```

O `CAPet` tambem permite inicializacao bootstrap de `me_in` usando apenas o tamanho da janela:

```python
from lpa2v import Capet

result = Capet().analyze(1.0, 0.0, window_size=3, bootstrap_value=0.5)
```

## Linha de comando

Listar algoritmos:

```bash
lpa2v algorithms
```

Executar o `para-analisador`:

```bash
lpa2v para-analisador --mu 0.80 --lambda 0.55
```

Com limiares personalizados no `para-analisador`:

```bash
lpa2v para-analisador --mu 0.80 --lambda 0.55 --certainty-limit 0.60 --contradiction-limit 0.40
```

Executar o `NAP`:

```bash
lpa2v nap --mu 0.70 --lambda 0.20
```

Executar o `CAP`:

```bash
lpa2v cap --external-interval 0.60 --mu 0.70 --lambda 0.20
```

Executar o `CAPet` informando explicitamente o vetor temporal `me_in`:

```bash
lpa2v capet --mu 1.00 --lambda 0.00 --me-in 0.50 0.60 0.90
```

Executar o `CAPet` com inicializacao bootstrap de `me_in`:

```bash
lpa2v capet --mu 1.00 --lambda 0.00 --window-size 3 --bootstrap-value 0.50
```

Saida tipica:

```json
{
  "algorithm": "para-analisador",
  "evidence": {
    "favorable": 0.8,
    "contrary": 0.55
  },
  "state": "QT-V",
  "region_id": 8,
  "gc": 0.25,
  "gct": 0.35,
  "thresholds": {
    "c1": 0.5,
    "c2": -0.5,
    "c3": 0.5,
    "c4": -0.5,
    "comparison_factor": 1.0
  }
}
```

## Algoritmos disponiveis

- `para-analisador`: classifica o par de evidencias nas 12 regioes da LPA2v
- `nap`: executa o No de Analise Paraconsistente com saida completa
- `cap`: executa o Cubo Analisador Paraconsistente com intervalo externo de evidencia
- `capet`: executa a CPAet (Cubic Paraconsistent Analyser with Evidence Filter and Temporal Analysis)

Entradas alternativas aceitas:

- `para-analisador` e `nap`: aceitam `EvidencePair`, tupla `(favorable, contrary)` e dicionarios com `favorable`/`contrary`, `mu`/`lambda` ou `mu`/`contrary_complement`.
- `cap`: aceita `CapInput`, tupla `(external_interval, favorable, contrary)` e dicionarios com `external_interval`, `phi_ext`, `external_signed_interval` ou `phi_e`.
- `capet`: aceita `CapetInput`, tupla `(favorable, contrary, moving_average_in)` e dicionarios com `moving_average_in` ou `me_in`, combinados com `favorable`/`contrary`, `mu`/`lambda` ou `mu`/`contrary_complement`. Alternativamente, aceita `window_size` com `bootstrap_value` para inicializar `me_in`.

## Principios de design

- `LPA2vAlgorithm` define o contrato base para algoritmos da biblioteca.
- `EvidencePairAlgorithm` concentra o tratamento padrao de entrada para algoritmos baseados em `mu` e `lambda`.
- `AlgorithmRegistry` centraliza descoberta e instanciacao por nome.
- `EvidencePair` padroniza a entrada de evidencias.
- `ParaAnalyzer` encapsula a classificacao nas 12 regioes.
- `Nap` encapsula o processamento completo do No de Analise Paraconsistente.
- `Cap` encapsula o processamento do Cubo Analisador Paraconsistente (CAP/PCA).
- `Capet` encapsula a CPAet do artigo de Hyghor Miranda Cortes et al., com filtro temporal das melhores evidencias baseado em `m_e`.
- `ParaAnalyzerThresholds` permite ajustar limiares sem mudar a API do algoritmo.

## Testes

Executar toda a suite via descoberta automatica:

```bash
python -m unittest discover -s tests
```

Executar o teste do `para-analisador` com saida detalhada e resumo profissional:

```bash
python tests/test_para_analyzer.py
```

Executar o teste do `NAP` com saida detalhada e resumo profissional:

```bash
python tests/test_nap.py
```

Executar o teste do `CAP` com saida detalhada e resumo profissional:

```bash
python tests/test_cap.py
```

Executar o teste do `CAPet` com saida detalhada e resumo profissional:

```bash
python tests/test_cpaet.py
```

Essas opcoes mostram:

- cabecalho da suite de testes
- descricao individual de cada caso testado
- status de cada teste
- resumo final com total de testes, falhas, erros e status da execucao

## Proximos passos naturais

- incluir outros algoritmos LPA2v na mesma arquitetura
- adicionar serializacao mais rica para integracao com APIs
- incluir exemplos por dominio de aplicacao

## Licenca

Este projeto e distribuido sob a licenca MIT. Veja o arquivo `LICENSE`.

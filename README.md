# LPA2v

Biblioteca Python orientada a objetos para algoritmos baseados em LPA2v.

Esta primeira versao foi criada para servir como base de crescimento da biblioteca e ja inclui os algoritmos `para-analisador`, `NAP` e `CAP`, modelados de forma extensivel para facilitar a entrada de novos algoritmos no futuro.

## Objetivos desta primeira versao

- disponibilizar uma biblioteca reutilizavel em projetos Python
- manter a logica central do `para-analisador` em uma API clara
- oferecer uma arquitetura orientada a objetos para novos algoritmos LPA2v
- facilitar integracao via codigo Python ou linha de comando

## Estrutura do projeto

```text
src/lpa2v/
  algorithms/
    base.py
    cap.py
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
from lpa2v import Cap, EvidencePair, Nap, ParaAnalyzer

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
```

## Uso de entrada legada

Nas implementacoes antigas em MATLAB, em alguns pontos o segundo valor era usado como complemento de `lambda`.

Para esse caso, a biblioteca oferece um atalho:

```python
from lpa2v import ParaAnalyzer

algorithm = ParaAnalyzer()
result = algorithm.analyze_legacy(favorable=0.7, contrary_complement=0.8)
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

Executar o `NAP`:

```bash
lpa2v nap --mu 0.70 --lambda 0.20
```

Executar o `CAP`:

```bash
lpa2v cap --external-interval 0.60 --mu 0.70 --lambda 0.20
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

## Principios de design

- `LPA2vAlgorithm` define o contrato base para algoritmos da biblioteca.
- `EvidencePairAlgorithm` concentra o tratamento padrao de entrada para algoritmos baseados em `mu` e `lambda`.
- `AlgorithmRegistry` centraliza descoberta e instanciacao por nome.
- `EvidencePair` padroniza a entrada de evidencias.
- `ParaAnalyzer` encapsula a classificacao nas 12 regioes.
- `Nap` encapsula o processamento completo do No de Analise Paraconsistente.
- `Cap` encapsula o processamento do Cubo Analisador Paraconsistente (CAP/PCA).
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

Essas opcoes mostram:

- cabecalho da suite de testes
- descricao individual de cada caso testado
- status de cada teste
- resumo final com total de testes, falhas, erros e status da execucao

## Proximos passos naturais

- incluir outros algoritmos LPA2v na mesma arquitetura
- adicionar serializacao mais rica para integracao com APIs
- incluir exemplos por dominio de aplicacao

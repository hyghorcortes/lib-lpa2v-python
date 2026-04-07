# LPA2v

Biblioteca Python orientada a objetos para algoritmos baseados em LPA2v.

Esta primeira versao foi criada para servir como base de crescimento da biblioteca e ja inclui o algoritmo `para-analisador`, modelado de forma extensivel para facilitar a entrada de novos algoritmos no futuro.

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
from lpa2v import EvidencePair, ParaAnalyzer

algorithm = ParaAnalyzer()
result = algorithm.run(EvidencePair(favorable=0.80, contrary=0.55))

print(result.state.value)   # QT-V
print(result.region_id)     # 8
print(result.gc)            # 0.25
print(result.gct)           # 0.35
```

## Uso com fabrica/registro de algoritmos

```python
from lpa2v import create_algorithm

algorithm = create_algorithm("para-analisador")
result = algorithm.run((0.60, 0.30))
print(result.to_dict())
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

## Principios de design

- `LPA2vAlgorithm` define o contrato base para algoritmos da biblioteca.
- `AlgorithmRegistry` centraliza descoberta e instanciacao por nome.
- `EvidencePair` padroniza a entrada de evidencias.
- `ParaAnalyzer` encapsula a classificacao nas 12 regioes.
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

Essa segunda opcao mostra:

- cabecalho da suite de testes
- descricao individual de cada caso testado
- status de cada teste
- resumo final com total de testes, falhas, erros e status da execucao

## Proximos passos naturais

- incluir outros algoritmos LPA2v na mesma arquitetura
- adicionar serializacao mais rica para integracao com APIs
- incluir exemplos por dominio de aplicacao

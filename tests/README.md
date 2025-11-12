# 🧪 Test Suite - Capstone Project AIM

Este diretório contém todos os testes do sistema Capstone Project AIM, organizados por tipo e funcionalidade.

## 📁 Estrutura de Testes

```
tests/
├── __init__.py                 # Inicialização do pacote de testes
├── conftest.py                 # Configurações pytest e fixtures
├── test_runner.py              # 🎯 PONTO DE ENTRADA PRINCIPAL
├── README.md                   # Este arquivo
│
├── unit/                       # 🧪 Testes Unitários
│   ├── __init__.py
│   ├── test_configuration.py   # Testes de configuração
│   └── test_models.py          # Testes de modelos
│
├── integration/                # 🔗 Testes de Integração
│   ├── __init__.py
│   ├── test_complete_system.py # Testes do sistema completo
│   ├── test_integrated_system.py # Testes de integração
│   └── test_embedding_evidence.py # Testes de embeddings
│
├── system/                     # 🖥️ Testes de Sistema
│   ├── __init__.py
│   ├── test_final_system.py    # Testes finais do sistema
│   ├── test_auto_update.py     # Testes de atualização automática
│   └── test_real_gemini.py     # Testes com Gemini real
│
└── performance/                # ⚡ Testes de Performance
    ├── __init__.py
    ├── test_models_simulation.py # Simulação de modelos
    └── test_gemini_real_vs_mock.py # Comparação real vs mock
```

## 🚀 Como Executar os Testes

### Método 1: Test Runner Principal (Recomendado)

```bash
# Executar todos os testes
python tests/test_runner.py

# Executar apenas testes unitários
python tests/test_runner.py --unit

# Executar apenas testes de integração
python tests/test_runner.py --integration

# Executar apenas testes de sistema
python tests/test_runner.py --system

# Executar apenas testes de performance
python tests/test_runner.py --performance

# Executar testes rápidos (exclui performance)
python tests/test_runner.py --fast

# Modo verboso
python tests/test_runner.py --verbose

# Com cobertura de código
python tests/test_runner.py --coverage

# Listar todos os testes disponíveis
python tests/test_runner.py --list

# Verificar configuração do ambiente
python tests/test_runner.py --check

# Executar um arquivo específico
python tests/test_runner.py --file test_configuration.py
```

### Método 2: Script Utilitário

```bash
# Usar o script wrapper
python scripts/run_tests.py --unit
python scripts/run_tests.py --integration
python scripts/run_tests.py --verbose
```

### Método 3: Pytest Direto

```bash
# Todos os testes
pytest tests/

# Apenas testes unitários
pytest -m unit

# Apenas testes de integração
pytest -m integration

# Apenas testes de sistema
pytest -m system

# Apenas testes de performance
pytest -m performance

# Testes rápidos (exclui performance)
pytest -m "not slow"

# Com cobertura
pytest --cov=src --cov-report=html
```

## 🛠️ Configuração do Ambiente

### Configuração Automática

```bash
# Executar configuração automática do ambiente
python scripts/setup_environment.py
```

### Configuração Manual

1. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov pytest-mock
   ```

2. **Configurar variáveis de ambiente:**
   ```bash
   cp .env.example .env
   # Editar .env com suas configurações
   ```

3. **Verificar configuração:**
   ```bash
   python tests/test_runner.py --check
   ```

## 📊 Tipos de Testes

### 🧪 Testes Unitários (`tests/unit/`)
- **Propósito**: Testar componentes individuais em isolamento
- **Escopo**: Funções, classes, módulos específicos
- **Velocidade**: Rápidos
- **Exemplos**: Configurações, modelos, utilitários

### 🔗 Testes de Integração (`tests/integration/`)
- **Propósito**: Testar interação entre componentes
- **Escopo**: Múltiplos módulos trabalhando juntos
- **Velocidade**: Médios
- **Exemplos**: Sistema RAG completo, embeddings

### 🖥️ Testes de Sistema (`tests/system/`)
- **Propósito**: Testar o sistema completo
- **Escopo**: Aplicação inteira
- **Velocidade**: Lentos
- **Exemplos**: Fluxo completo, atualizações automáticas

### ⚡ Testes de Performance (`tests/performance/`)
- **Propósito**: Medir performance e capacidade
- **Escopo**: Sistema sob carga
- **Velocidade**: Muito lentos
- **Exemplos**: Simulação de carga, comparações

## 🏷️ Marcadores de Testes

Os testes são automaticamente marcados baseados em sua localização:

- `@pytest.mark.unit` - Testes unitários
- `@pytest.mark.integration` - Testes de integração
- `@pytest.mark.system` - Testes de sistema
- `@pytest.mark.performance` - Testes de performance
- `@pytest.mark.slow` - Testes lentos

## 🔧 Fixtures Disponíveis

O arquivo `conftest.py` fornece fixtures úteis:

- `project_root` - Diretório raiz do projeto
- `src_path` - Diretório src
- `test_images_path` - Diretório de imagens de teste
- `temp_dir` - Diretório temporário
- `clean_temp_dir` - Diretório temporário limpo
- `mock_env_vars` - Variáveis de ambiente mock
- `set_mock_env` - Configurar ambiente mock

## 📈 Cobertura de Código

Para gerar relatório de cobertura:

```bash
# Com test runner
python tests/test_runner.py --coverage

# Com pytest
pytest --cov=src --cov-report=html --cov-report=term
```

O relatório HTML será gerado em `htmlcov/index.html`.

## 🐛 Debugging

### Executar um teste específico

```bash
# Com test runner
python tests/test_runner.py --file test_configuration.py

# Com pytest
pytest tests/unit/test_configuration.py -v
```

### Modo debug

```bash
# Com output detalhado
python tests/test_runner.py --verbose

# Com pytest
pytest -v -s --tb=long
```

## 📝 Adicionando Novos Testes

### Estrutura de um novo teste

```python
#!/usr/bin/env python3
"""
Descrição do teste
==================
"""

import pytest
from src.module import ClassToTest


def test_function_name():
    """Descrição do que o teste faz"""
    # Arrange
    test_data = "test"
    
    # Act
    result = ClassToTest.method(test_data)
    
    # Assert
    assert result == expected_value


@pytest.mark.unit
def test_with_marker():
    """Teste com marcador específico"""
    pass
```

### Onde colocar novos testes

- **Testes unitários**: `tests/unit/`
- **Testes de integração**: `tests/integration/`
- **Testes de sistema**: `tests/system/`
- **Testes de performance**: `tests/performance/`

## 🚨 Troubleshooting

### Problemas Comuns

1. **ImportError**: Verificar se o caminho para `src` está correto
2. **ModuleNotFoundError**: Executar `python tests/test_runner.py --check`
3. **Testes lentos**: Usar `--fast` para excluir testes de performance
4. **Falhas de configuração**: Verificar variáveis de ambiente

### Logs e Debug

```bash
# Ver logs detalhados
python tests/test_runner.py --verbose

# Executar com debug
pytest -v -s --tb=long tests/
```

## 📚 Recursos Adicionais

- [Documentação do Pytest](https://docs.pytest.org/)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Cobertura de Código](https://coverage.readthedocs.io/)

---

**💡 Dica**: Use `python tests/test_runner.py --list` para ver todos os testes disponíveis!

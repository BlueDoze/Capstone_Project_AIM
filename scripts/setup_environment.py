#!/usr/bin/env python3
"""
Script de Configuração do Ambiente
==================================

Script para configurar o ambiente de desenvolvimento e testes.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Verifica se a versão do Python é compatível"""
    print("🐍 Verificando versão do Python...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} não é suportado. Use Python 3.8+")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """Instala as dependências do projeto"""
    print("📦 Instalando dependências...")
    
    project_root = Path(__file__).parent.parent
    requirements_file = project_root / "requirements.txt"
    
    if not requirements_file.exists():
        print("⚠️ requirements.txt não encontrado")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, cwd=project_root)
        print("✅ Dependências instaladas com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False


def install_dev_dependencies():
    """Instala dependências de desenvolvimento"""
    print("🛠️ Instalando dependências de desenvolvimento...")
    
    dev_packages = [
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "black",
        "flake8",
        "mypy"
    ]
    
    try:
        for package in dev_packages:
            print(f"  📦 Instalando {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
        
        print("✅ Dependências de desenvolvimento instaladas")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências de desenvolvimento: {e}")
        return False


def create_env_example():
    """Cria arquivo .env.example se não existir"""
    print("📝 Criando .env.example...")
    
    project_root = Path(__file__).parent.parent
    env_example = project_root / ".env.example"
    
    if env_example.exists():
        print("✅ .env.example já existe")
        return True
    
    env_content = """# Configurações do Capstone Project AIM
# Copie este arquivo para .env e preencha com seus valores

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Google Cloud Project
GOOGLE_CLOUD_PROJECT_ID=your_project_id_here
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json

# Configurações do Flask
FLASK_ENV=development
FLASK_DEBUG=True
PORT=8081

# Configurações de desenvolvimento
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_example, 'w') as f:
            f.write(env_content)
        print("✅ .env.example criado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar .env.example: {e}")
        return False


def create_directories():
    """Cria diretórios necessários"""
    print("📁 Criando diretórios...")
    
    project_root = Path(__file__).parent.parent
    directories = [
        "temp",
        "logs",
        "cache"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"  📁 {directory}/")
    
    print("✅ Diretórios criados")
    return True


def check_environment_variables():
    """Verifica variáveis de ambiente necessárias"""
    print("🔍 Verificando variáveis de ambiente...")
    
    required_vars = [
        "GEMINI_API_KEY",
        "GOOGLE_CLOUD_PROJECT_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️ Variáveis de ambiente não configuradas:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\n💡 Configure essas variáveis no arquivo .env")
        return False
    
    print("✅ Variáveis de ambiente configuradas")
    return True


def run_tests():
    """Executa testes básicos para verificar a configuração"""
    print("🧪 Executando testes básicos...")
    
    project_root = Path(__file__).parent.parent
    test_runner = project_root / "tests" / "test_runner.py"
    
    if not test_runner.exists():
        print("⚠️ test_runner.py não encontrado")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, str(test_runner), "--unit", "--verbose"
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Testes básicos passaram")
            return True
        else:
            print("❌ Alguns testes falharam")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        return False


def main():
    """Função principal de configuração"""
    
    print("🚀 CONFIGURAÇÃO DO AMBIENTE - CAPSTONE PROJECT AIM")
    print("=" * 55)
    
    steps = [
        ("Verificar Python", check_python_version),
        ("Criar diretórios", create_directories),
        ("Criar .env.example", create_env_example),
        ("Instalar dependências", install_dependencies),
        ("Instalar dependências de desenvolvimento", install_dev_dependencies),
        ("Verificar variáveis de ambiente", check_environment_variables),
        ("Executar testes básicos", run_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ Erro em {step_name}: {e}")
            failed_steps.append(step_name)
    
    print("\n" + "=" * 55)
    
    if not failed_steps:
        print("🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        print("\n📝 Próximos passos:")
        print("1. Configure suas variáveis de ambiente no arquivo .env")
        print("2. Execute: python tests/test_runner.py --check")
        print("3. Execute: python tests/test_runner.py --unit")
    else:
        print("⚠️ CONFIGURAÇÃO CONCLUÍDA COM ALGUNS PROBLEMAS:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\n💡 Verifique os problemas acima e execute novamente se necessário")
    
    return len(failed_steps) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

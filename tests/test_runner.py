#!/usr/bin/env python3
"""
Test Runner Principal
====================

Este arquivo executa todos os testes do sistema de forma organizada.
É o ponto de entrada principal para executar todos os testes do Capstone Project AIM.

Uso:
    python tests/test_runner.py                    # Executa todos os testes
    python tests/test_runner.py --unit            # Apenas testes unitários
    python tests/test_runner.py --integration     # Apenas testes de integração
    python tests/test_runner.py --system          # Apenas testes de sistema
    python tests/test_runner.py --performance     # Apenas testes de performance
    python tests/test_runner.py --fast            # Testes rápidos (exclui performance)
    python tests/test_runner.py --verbose         # Modo verboso
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional


class TestRunner:
    """Gerenciador de execução de testes"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        self.python_executable = sys.executable
        
    def run_tests(self, 
                  test_type: Optional[str] = None,
                  verbose: bool = False,
                  fast: bool = False,
                  coverage: bool = False) -> bool:
        """
        Executa os testes conforme especificado
        
        Args:
            test_type: Tipo de teste ('unit', 'integration', 'system', 'performance')
            verbose: Modo verboso
            fast: Executa apenas testes rápidos (exclui performance)
            coverage: Executa com cobertura de código
            
        Returns:
            bool: True se todos os testes passaram, False caso contrário
        """
        
        print("🧪 CAPSTONE PROJECT AIM - TEST RUNNER")
        print("=" * 50)
        print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Diretório: {self.project_root}")
        print("=" * 50)
        
        # Construir comando pytest
        cmd = [self.python_executable, "-m", "pytest"]
        
        # Adicionar opções baseadas nos parâmetros
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
            
        if coverage:
            cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
        
        # Filtrar por tipo de teste
        if test_type:
            if test_type == "unit":
                cmd.extend(["-m", "unit"])
                print("🎯 Executando: TESTES UNITÁRIOS")
            elif test_type == "integration":
                cmd.extend(["-m", "integration"])
                print("🔗 Executando: TESTES DE INTEGRAÇÃO")
            elif test_type == "system":
                cmd.extend(["-m", "system"])
                print("🖥️  Executando: TESTES DE SISTEMA")
            elif test_type == "performance":
                cmd.extend(["-m", "performance"])
                print("⚡ Executando: TESTES DE PERFORMANCE")
        elif fast:
            cmd.extend(["-m", "not slow"])
            print("🚀 Executando: TESTES RÁPIDOS (excluindo performance)")
        else:
            print("🎯 Executando: TODOS OS TESTES")
        
        # Adicionar diretório de testes
        cmd.append(str(self.tests_dir))
        
        # Executar testes
        print(f"\n🔧 Comando: {' '.join(cmd)}")
        print("-" * 50)
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=False)
            success = result.returncode == 0
            
            print("-" * 50)
            if success:
                print("✅ TODOS OS TESTES PASSARAM!")
            else:
                print("❌ ALGUNS TESTES FALHARAM!")
                
            return success
            
        except KeyboardInterrupt:
            print("\n⚠️ Testes interrompidos pelo usuário")
            return False
        except Exception as e:
            print(f"\n❌ Erro ao executar testes: {e}")
            return False
    
    def run_specific_test(self, test_file: str, verbose: bool = False) -> bool:
        """
        Executa um teste específico
        
        Args:
            test_file: Nome do arquivo de teste
            verbose: Modo verboso
            
        Returns:
            bool: True se o teste passou, False caso contrário
        """
        
        print(f"🎯 Executando teste específico: {test_file}")
        
        cmd = [self.python_executable, "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        # Encontrar o arquivo de teste
        test_path = None
        for root, dirs, files in os.walk(self.tests_dir):
            if test_file in files:
                test_path = Path(root) / test_file
                break
        
        if not test_path:
            print(f"❌ Arquivo de teste não encontrado: {test_file}")
            return False
        
        cmd.append(str(test_path))
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Erro ao executar teste: {e}")
            return False
    
    def list_tests(self):
        """Lista todos os testes disponíveis"""
        
        print("📋 TESTES DISPONÍVEIS")
        print("=" * 30)
        
        test_categories = {
            "Unit Tests": self.tests_dir / "unit",
            "Integration Tests": self.tests_dir / "integration", 
            "System Tests": self.tests_dir / "system",
            "Performance Tests": self.tests_dir / "performance"
        }
        
        for category, path in test_categories.items():
            if path.exists():
                print(f"\n{category}:")
                for test_file in sorted(path.glob("test_*.py")):
                    print(f"  - {test_file.name}")
    
    def check_environment(self) -> bool:
        """Verifica se o ambiente está configurado corretamente"""
        
        print("🔍 VERIFICANDO AMBIENTE")
        print("-" * 25)
        
        checks = []
        
        # Verificar se pytest está instalado
        try:
            import pytest
            checks.append(("✅", "pytest", "instalado"))
        except ImportError:
            checks.append(("❌", "pytest", "não instalado"))
        
        # Verificar se src existe
        src_path = self.project_root / "src"
        if src_path.exists():
            checks.append(("✅", "src/", "existe"))
        else:
            checks.append(("❌", "src/", "não existe"))
        
        # Verificar se tests existe
        if self.tests_dir.exists():
            checks.append(("✅", "tests/", "existe"))
        else:
            checks.append(("❌", "tests/", "não existe"))
        
        # Verificar se main.py existe
        main_file = self.project_root / "main.py"
        if main_file.exists():
            checks.append(("✅", "main.py", "existe"))
        else:
            checks.append(("❌", "main.py", "não existe"))
        
        # Mostrar resultados
        for status, item, condition in checks:
            print(f"{status} {item}: {condition}")
        
        # Verificar se todos os checks passaram
        all_passed = all(status == "✅" for status, _, _ in checks)
        
        if all_passed:
            print("\n✅ Ambiente configurado corretamente!")
        else:
            print("\n❌ Ambiente precisa de configuração!")
        
        return all_passed


def main():
    """Função principal do test runner"""
    
    parser = argparse.ArgumentParser(
        description="Test Runner para Capstone Project AIM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python tests/test_runner.py                    # Todos os testes
  python tests/test_runner.py --unit            # Apenas unitários
  python tests/test_runner.py --integration     # Apenas integração
  python tests/test_runner.py --system          # Apenas sistema
  python tests/test_runner.py --performance     # Apenas performance
  python tests/test_runner.py --fast            # Testes rápidos
  python tests/test_runner.py --verbose         # Modo verboso
  python tests/test_runner.py --coverage        # Com cobertura
  python tests/test_runner.py --list            # Listar testes
  python tests/test_runner.py --check           # Verificar ambiente
        """
    )
    
    # Opções de tipo de teste
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("--unit", action="store_true", help="Executar apenas testes unitários")
    test_group.add_argument("--integration", action="store_true", help="Executar apenas testes de integração")
    test_group.add_argument("--system", action="store_true", help="Executar apenas testes de sistema")
    test_group.add_argument("--performance", action="store_true", help="Executar apenas testes de performance")
    test_group.add_argument("--fast", action="store_true", help="Executar apenas testes rápidos (exclui performance)")
    
    # Outras opções
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    parser.add_argument("--coverage", "-c", action="store_true", help="Executar com cobertura de código")
    parser.add_argument("--list", "-l", action="store_true", help="Listar todos os testes disponíveis")
    parser.add_argument("--check", action="store_true", help="Verificar se o ambiente está configurado")
    parser.add_argument("--file", "-f", help="Executar um arquivo de teste específico")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Executar ações baseadas nos argumentos
    if args.list:
        runner.list_tests()
        return
    
    if args.check:
        runner.check_environment()
        return
    
    if args.file:
        success = runner.run_specific_test(args.file, args.verbose)
        sys.exit(0 if success else 1)
    
    # Determinar tipo de teste
    test_type = None
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    elif args.system:
        test_type = "system"
    elif args.performance:
        test_type = "performance"
    
    # Executar testes
    success = runner.run_tests(
        test_type=test_type,
        verbose=args.verbose,
        fast=args.fast,
        coverage=args.coverage
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

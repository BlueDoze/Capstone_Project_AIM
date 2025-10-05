#!/usr/bin/env python3
"""
Script para Executar Testes
===========================

Script utilitário para executar testes de forma conveniente.
Este script é um wrapper simples para o test_runner.py principal.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Executa o test runner principal"""
    
    # Caminho para o test runner
    project_root = Path(__file__).parent.parent
    test_runner = project_root / "tests" / "test_runner.py"
    
    if not test_runner.exists():
        print("❌ test_runner.py não encontrado!")
        sys.exit(1)
    
    # Executar o test runner com os argumentos passados
    cmd = [sys.executable, str(test_runner)] + sys.argv[1:]
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

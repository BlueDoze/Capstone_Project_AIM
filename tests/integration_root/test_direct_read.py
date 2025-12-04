#!/usr/bin/env python3
"""
Teste de leitura direta do all_announcements.json
"""

import json
from pathlib import Path

print("=" * 60)
print("TESTE: Leitura Direta de all_announcements.json")
print("=" * 60)

# 1. Verificar se arquivo existe
announcements_path = Path('all_announcements.json')
if not announcements_path.exists():
    print("❌ Arquivo all_announcements.json não encontrado!")
    print("   Execute: python3 extract_all_announcements.py")
    exit(1)

print("✅ Arquivo all_announcements.json encontrado")

# 2. Ler arquivo
with open(announcements_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 3. Exibir informações
print(f"\n📊 DADOS CARREGADOS:")
print(f"   Course: {data.get('course', 'Unknown')}")
print(f"   Total: {data.get('total_announcements', 0)} announcements")
print(f"   Successful: {data.get('successful', 0)}")
print(f"   Failed: {data.get('failed', 0)}")
print(f"   Extracted: {data.get('extracted_at', 'Unknown')}")

# 4. Listar announcements
announcements = data.get('announcements', [])
print(f"\n📢 ANNOUNCEMENTS ({len(announcements)}):")
for i, ann in enumerate(announcements, 1):
    print(f"\n   {i}. {ann.get('title', 'Untitled')}")
    print(f"      Date: {ann.get('date', 'Unknown')}")
    print(f"      Content: {ann.get('content', '')[:100]}...")

print("\n" + "=" * 60)
print("✅ TESTE CONCLUÍDO COM SUCESSO!")
print("=" * 60)
print("\nO chatbot pode ler este arquivo diretamente!")
print("Não é necessário transformar para outro formato.")

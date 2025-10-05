"""
Validador de Recursos do Sistema RAG Multimodal
==============================================

Este módulo implementa validações completas de todos os recursos
necessários para o funcionamento do sistema RAG multimodal.
"""

import os
import sys
import time
import requests
import subprocess
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json

# Tentar importar bibliotecas do Google Cloud
try:
    from google.cloud import aiplatform
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
    GCP_LIBRARIES_AVAILABLE = True
except ImportError:
    GCP_LIBRARIES_AVAILABLE = False
    print("⚠️  Bibliotecas do Google Cloud não disponíveis")


class ResourceValidator:
    """Validador completo de recursos do sistema RAG multimodal"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.validation_results = {}
        self.errors = []
        self.warnings = []
    
    def validate_google_cloud_access(self) -> bool:
        """Valida acesso ao Google Cloud Platform"""
        print("🔍 Validando acesso ao Google Cloud Platform...")
        
        if not GCP_LIBRARIES_AVAILABLE:
            self.errors.append("Bibliotecas do Google Cloud não disponíveis")
            return False
        
        try:
            # Tentar obter credenciais padrão
            credentials, project = default()
            
            if project != self.project_id:
                self.warnings.append(f"Project ID diferente: esperado {self.project_id}, obtido {project}")
            
            print(f"✅ Credenciais obtidas para projeto: {project}")
            print(f"✅ Tipo de credencial: {type(credentials).__name__}")
            
            # Testar inicialização do AI Platform
            aiplatform.init(project=project, location=self.location)
            print(f"✅ AI Platform inicializado em {self.location}")
            
            self.validation_results['gcp_access'] = True
            return True
            
        except DefaultCredentialsError as e:
            error_msg = f"Credenciais padrão não encontradas: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
            
        except Exception as e:
            error_msg = f"Erro ao acessar Google Cloud: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def validate_project_permissions(self) -> bool:
        """Valida permissões do projeto"""
        print("\n🔐 Validando permissões do projeto...")
        
        if not GCP_LIBRARIES_AVAILABLE:
            self.errors.append("Bibliotecas do Google Cloud não disponíveis")
            return False
        
        try:
            # Testar permissões básicas
            from google.cloud import resourcemanager
            
            client = resourcemanager.ProjectsClient()
            project_path = f"projects/{self.project_id}"
            
            # Tentar obter informações do projeto
            project = client.get_project(name=project_path)
            print(f"✅ Projeto encontrado: {project.display_name}")
            print(f"✅ Estado do projeto: {project.state.name}")
            
            # Verificar se o projeto está ativo
            if project.state.name != "ACTIVE":
                self.warnings.append(f"Projeto não está ativo: {project.state.name}")
            
            self.validation_results['project_permissions'] = True
            return True
            
        except Exception as e:
            error_msg = f"Erro ao validar permissões: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def validate_model_availability(self) -> bool:
        """Valida disponibilidade dos modelos"""
        print("\n🤖 Validando disponibilidade dos modelos...")
        
        models_to_check = [
            "gemini-2.5-pro",
            "text-embedding-005", 
            "multimodalembedding@001"
        ]
        
        available_models = []
        
        for model in models_to_check:
            try:
                if "gemini" in model:
                    from vertexai.generative_models import GenerativeModel
                    test_model = GenerativeModel(model)
                    print(f"✅ Modelo {model} disponível")
                    available_models.append(model)
                    
                elif "embedding" in model:
                    if "text" in model:
                        from vertexai.language_models import TextEmbeddingModel
                        test_model = TextEmbeddingModel.from_pretrained(model)
                    else:
                        from vertexai.vision_models import MultiModalEmbeddingModel
                        test_model = MultiModalEmbeddingModel.from_pretrained(model)
                    
                    print(f"✅ Modelo {model} disponível")
                    available_models.append(model)
                    
            except Exception as e:
                error_msg = f"Modelo {model} não disponível: {e}"
                self.errors.append(error_msg)
                print(f"❌ {error_msg}")
        
        self.validation_results['available_models'] = available_models
        
        if len(available_models) == len(models_to_check):
            print("✅ Todos os modelos estão disponíveis")
            return True
        else:
            print(f"⚠️  Apenas {len(available_models)}/{len(models_to_check)} modelos disponíveis")
            return False
    
    def validate_api_quotas(self) -> bool:
        """Valida quotas de API"""
        print("\n📊 Validando quotas de API...")
        
        try:
            # Testar quota básica fazendo uma chamada simples
            from vertexai.generative_models import GenerativeModel
            
            model = GenerativeModel("gemini-2.5-pro")
            
            # Fazer uma chamada de teste simples
            start_time = time.time()
            response = model.generate_content("Teste de quota")
            end_time = time.time()
            
            if response and response.text:
                print(f"✅ Quota de API funcionando")
                print(f"✅ Tempo de resposta: {end_time - start_time:.2f}s")
                self.validation_results['api_quota'] = True
                return True
            else:
                self.errors.append("Resposta vazia da API")
                return False
                
        except Exception as e:
            error_msg = f"Erro ao testar quota de API: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def validate_directory_structure(self) -> bool:
        """Valida estrutura de diretórios"""
        print("\n📁 Validando estrutura de diretórios...")
        
        required_dirs = [
            "images/",
            "map/",
            "src/",
            "src/config/",
            "src/models/",
            "src/services/",
            "templates/",
            "static/"
        ]
        
        missing_dirs = []
        existing_dirs = []
        
        for directory in required_dirs:
            if os.path.exists(directory):
                existing_dirs.append(directory)
                print(f"✅ Diretório encontrado: {directory}")
            else:
                missing_dirs.append(directory)
                print(f"❌ Diretório ausente: {directory}")
        
        self.validation_results['existing_directories'] = existing_dirs
        self.validation_results['missing_directories'] = missing_dirs
        
        if not missing_dirs:
            print("✅ Todos os diretórios necessários existem")
            return True
        else:
            print(f"⚠️  {len(missing_dirs)} diretórios ausentes")
            return False
    
    def validate_file_permissions(self) -> bool:
        """Valida permissões de arquivo"""
        print("\n🔒 Validando permissões de arquivo...")
        
        test_files = [
            ".env",
            "main.py",
            "requirements.txt"
        ]
        
        permission_issues = []
        
        for file_path in test_files:
            if os.path.exists(file_path):
                # Verificar se pode ler
                if not os.access(file_path, os.R_OK):
                    permission_issues.append(f"Não é possível ler {file_path}")
                
                # Verificar se pode escrever (para .env)
                if file_path == ".env" and not os.access(file_path, os.W_OK):
                    permission_issues.append(f"Não é possível escrever em {file_path}")
                
                print(f"✅ Permissões OK para {file_path}")
            else:
                print(f"⚠️  Arquivo não encontrado: {file_path}")
        
        if permission_issues:
            for issue in permission_issues:
                self.errors.append(issue)
            return False
        
        print("✅ Todas as permissões de arquivo estão corretas")
        self.validation_results['file_permissions'] = True
        return True
    
    def validate_network_connectivity(self) -> bool:
        """Valida conectividade de rede"""
        print("\n🌐 Validando conectividade de rede...")
        
        test_urls = [
            "https://www.google.com",
            "https://ai.google.dev",
            "https://console.cloud.google.com"
        ]
        
        connectivity_results = {}
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    connectivity_results[url] = True
                    print(f"✅ Conectividade OK: {url}")
                else:
                    connectivity_results[url] = False
                    print(f"⚠️  Status {response.status_code}: {url}")
            except Exception as e:
                connectivity_results[url] = False
                print(f"❌ Erro de conectividade: {url} - {e}")
        
        self.validation_results['network_connectivity'] = connectivity_results
        
        successful_connections = sum(connectivity_results.values())
        if successful_connections == len(test_urls):
            print("✅ Conectividade de rede excelente")
            return True
        elif successful_connections > 0:
            print(f"⚠️  Conectividade parcial: {successful_connections}/{len(test_urls)}")
            return True
        else:
            self.errors.append("Sem conectividade de rede")
            return False
    
    def validate_dependencies(self) -> bool:
        """Valida dependências do sistema"""
        print("\n📦 Validando dependências...")
        
        required_packages = [
            "flask",
            "google-generativeai", 
            "python-dotenv",
            "vertexai",
            "google-cloud-aiplatform",
            "numpy",
            "pandas"
        ]
        
        missing_packages = []
        available_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                available_packages.append(package)
                print(f"✅ Pacote disponível: {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ Pacote ausente: {package}")
        
        self.validation_results['available_packages'] = available_packages
        self.validation_results['missing_packages'] = missing_packages
        
        if not missing_packages:
            print("✅ Todas as dependências estão instaladas")
            return True
        else:
            print(f"⚠️  {len(missing_packages)} pacotes ausentes")
            return False
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Executa validação completa de todos os recursos"""
        print("🚀 INICIANDO VALIDAÇÃO COMPLETA DE RECURSOS")
        print("=" * 60)
        
        validation_tests = [
            ("Google Cloud Access", self.validate_google_cloud_access),
            ("Project Permissions", self.validate_project_permissions),
            ("Model Availability", self.validate_model_availability),
            ("API Quotas", self.validate_api_quotas),
            ("Directory Structure", self.validate_directory_structure),
            ("File Permissions", self.validate_file_permissions),
            ("Network Connectivity", self.validate_network_connectivity),
            ("Dependencies", self.validate_dependencies)
        ]
        
        results = {}
        
        for test_name, test_function in validation_tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                results[test_name] = test_function()
            except Exception as e:
                print(f"❌ Erro durante {test_name}: {e}")
                results[test_name] = False
                self.errors.append(f"Erro em {test_name}: {e}")
        
        # Calcular score geral
        passed_tests = sum(results.values())
        total_tests = len(results)
        success_rate = (passed_tests / total_tests) * 100
        
        self.validation_results['overall_results'] = results
        self.validation_results['success_rate'] = success_rate
        self.validation_results['passed_tests'] = passed_tests
        self.validation_results['total_tests'] = total_tests
        
        print(f"\n{'='*60}")
        print("📊 RESULTADO FINAL DA VALIDAÇÃO")
        print(f"{'='*60}")
        print(f"✅ Testes aprovados: {passed_tests}/{total_tests}")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n❌ Erros encontrados ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.warnings:
            print(f"\n⚠️  Avisos ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if success_rate >= 80:
            print("\n🎉 VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
            print("✅ Sistema pronto para uso em produção")
        elif success_rate >= 60:
            print("\n⚠️  VALIDAÇÃO PARCIALMENTE BEM-SUCEDIDA")
            print("💡 Alguns problemas precisam ser resolvidos")
        else:
            print("\n❌ VALIDAÇÃO FALHOU")
            print("🔧 Múltiplos problemas precisam ser corrigidos")
        
        return self.validation_results
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Retorna resumo da validação"""
        return {
            'project_id': self.project_id,
            'location': self.location,
            'success_rate': self.validation_results.get('success_rate', 0),
            'passed_tests': self.validation_results.get('passed_tests', 0),
            'total_tests': self.validation_results.get('total_tests', 0),
            'errors': self.errors,
            'warnings': self.warnings,
            'results': self.validation_results.get('overall_results', {})
        }

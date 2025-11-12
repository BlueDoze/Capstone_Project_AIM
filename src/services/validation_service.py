"""
Serviço de Validação de Recursos
================================

Este módulo orquestra a validação completa de todos os recursos
do sistema RAG multimodal.
"""

import sys
import os
from typing import Dict, Any

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.settings import RAGConfig
from config.environment import EnvironmentManager
from services.initialization_service import InitializationService
from utils.validators import ResourceValidator


class ValidationService:
    """Serviço completo de validação do sistema RAG multimodal"""
    
    def __init__(self):
        self.config = None
        self.env_manager = None
        self.init_service = None
        self.resource_validator = None
        self.validation_results = {}
    
    def prepare_for_validation(self) -> bool:
        """Prepara o sistema para validação"""
        print("🔧 PREPARANDO SISTEMA PARA VALIDAÇÃO")
        print("=" * 50)
        
        try:
            # Carregar configurações
            self.config = RAGConfig()
            self.env_manager = EnvironmentManager()
            
            # Carregar variáveis de ambiente
            env_loaded = self.env_manager.load_env_variables()
            if not env_loaded:
                print("⚠️  Arquivo .env não encontrado")
            
            # Validar variáveis obrigatórias
            if not self.env_manager.validate_required_vars():
                print("❌ Variáveis obrigatórias não definidas")
                return False
            
            # Atualizar configuração
            self.config.PROJECT_ID = self.env_manager.get_project_id()
            
            # Criar validador de recursos
            self.resource_validator = ResourceValidator(
                project_id=self.config.PROJECT_ID,
                location=self.config.LOCATION
            )
            
            print("✅ Sistema preparado para validação")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao preparar sistema: {e}")
            return False
    
    def validate_system_initialization(self) -> bool:
        """Valida a inicialização do sistema"""
        print("\n🚀 VALIDANDO INICIALIZAÇÃO DO SISTEMA")
        print("=" * 45)
        
        try:
            # Criar serviço de inicialização
            self.init_service = InitializationService()
            
            # Executar fase de preparação
            prep_success = self.init_service.prepare_system()
            if not prep_success:
                print("❌ Falha na preparação do sistema")
                return False
            
            # Inicializar modelos
            model_success = self.init_service.initialize_models()
            if not model_success:
                print("❌ Falha na inicialização de modelos")
                return False
            
            # Validar recursos básicos
            resource_success = self.init_service.validate_resources()
            if not resource_success:
                print("❌ Falha na validação de recursos básicos")
                return False
            
            print("✅ Inicialização do sistema validada")
            return True
            
        except Exception as e:
            print(f"❌ Erro na validação de inicialização: {e}")
            return False
    
    def validate_comprehensive_resources(self) -> Dict[str, Any]:
        """Executa validação completa de recursos"""
        print("\n🔍 VALIDAÇÃO COMPLETA DE RECURSOS")
        print("=" * 40)
        
        if not self.resource_validator:
            print("❌ Validador de recursos não inicializado")
            return {}
        
        # Executar validação completa
        results = self.resource_validator.run_comprehensive_validation()
        
        self.validation_results['resource_validation'] = results
        return results
    
    def validate_end_to_end_functionality(self) -> bool:
        """Valida funcionalidade end-to-end do sistema"""
        print("\n🔄 VALIDAÇÃO END-TO-END")
        print("=" * 30)
        
        if not self.init_service:
            print("❌ Serviço de inicialização não disponível")
            return False
        
        try:
            # Testar resposta do Gemini
            print("🤖 Testando resposta do Gemini...")
            gemini_test = self.init_service.gemini_manager.test_gemini_response(
                "Responda apenas: SISTEMA FUNCIONANDO"
            )
            
            if gemini_test:
                print("✅ Gemini respondendo corretamente")
            else:
                print("❌ Gemini não está respondendo")
                return False
            
            # Testar embedding de texto
            print("📝 Testando embedding de texto...")
            text_embedding_test = self.init_service.embedding_manager.test_text_embedding_generation(
                "Teste de funcionalidade end-to-end"
            )
            
            if text_embedding_test:
                print("✅ Embedding de texto funcionando")
            else:
                print("❌ Embedding de texto com problemas")
                return False
            
            # Testar embedding multimodal (se houver imagem)
            print("🖼️  Testando embedding multimodal...")
            multimodal_test = self.init_service.embedding_manager.test_multimodal_embedding_generation()
            
            if multimodal_test:
                print("✅ Embedding multimodal funcionando")
            else:
                print("⚠️  Embedding multimodal não testado (sem imagem)")
            
            print("✅ Funcionalidade end-to-end validada")
            return True
            
        except Exception as e:
            print(f"❌ Erro na validação end-to-end: {e}")
            return False
    
    def run_complete_validation(self) -> Dict[str, Any]:
        """Executa validação completa de todo o sistema"""
        print("🎯 EXECUTANDO VALIDAÇÃO COMPLETA DO SISTEMA RAG MULTIMODAL")
        print("=" * 70)
        
        # 1. Preparar sistema
        prep_success = self.prepare_for_validation()
        if not prep_success:
            return {'success': False, 'error': 'Falha na preparação'}
        
        # 2. Validar inicialização
        init_success = self.validate_system_initialization()
        if not init_success:
            return {'success': False, 'error': 'Falha na inicialização'}
        
        # 3. Validar recursos completos
        resource_results = self.validate_comprehensive_resources()
        
        # 4. Validar funcionalidade end-to-end
        e2e_success = self.validate_end_to_end_functionality()
        
        # Compilar resultados finais
        final_results = {
            'success': prep_success and init_success and e2e_success,
            'preparation': prep_success,
            'initialization': init_success,
            'end_to_end': e2e_success,
            'resource_validation': resource_results,
            'summary': self.resource_validator.get_validation_summary() if self.resource_validator else {}
        }
        
        # Exibir resultado final
        print(f"\n{'='*70}")
        print("📊 RESULTADO FINAL DA VALIDAÇÃO COMPLETA")
        print(f"{'='*70}")
        
        if final_results['success']:
            print("🎉 VALIDAÇÃO COMPLETA BEM-SUCEDIDA!")
            print("✅ Sistema RAG multimodal totalmente funcional")
            print("✅ Pronto para uso em produção")
        else:
            print("⚠️  VALIDAÇÃO COMPLETA COM PROBLEMAS")
            print("💡 Verifique os erros acima para correções")
        
        return final_results
    
    def get_validation_report(self) -> str:
        """Gera relatório detalhado da validação"""
        if not self.validation_results:
            return "Nenhuma validação executada"
        
        report = []
        report.append("# Relatório de Validação do Sistema RAG Multimodal")
        report.append("=" * 60)
        
        # Resumo geral
        summary = self.validation_results.get('summary', {})
        report.append(f"\n## Resumo Geral")
        report.append(f"- Project ID: {summary.get('project_id', 'N/A')}")
        report.append(f"- Taxa de Sucesso: {summary.get('success_rate', 0):.1f}%")
        report.append(f"- Testes Aprovados: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)}")
        
        # Erros e avisos
        if summary.get('errors'):
            report.append(f"\n## Erros Encontrados ({len(summary['errors'])})")
            for error in summary['errors']:
                report.append(f"- {error}")
        
        if summary.get('warnings'):
            report.append(f"\n## Avisos ({len(summary['warnings'])})")
            for warning in summary['warnings']:
                report.append(f"- {warning}")
        
        return "\n".join(report)

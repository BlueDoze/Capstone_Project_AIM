"""
Gerenciamento de Variáveis de Ambiente
=====================================

Este módulo gerencia o carregamento e validação de variáveis de ambiente
necessárias para o funcionamento do sistema RAG multimodal.
"""

import os
from typing import Dict, List, Optional

# Tentar importar dotenv, mas não falhar se não estiver disponível
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  python-dotenv não disponível. Usando apenas variáveis de ambiente do sistema.")


class EnvironmentManager:
    """Gerencia variáveis de ambiente do sistema"""
    
    def __init__(self):
        self.required_vars: List[str] = [
            "GEMINI_API_KEY",
            "GOOGLE_CLOUD_PROJECT_ID"
        ]
        
        self.optional_vars: Dict[str, str] = {
            "VERTEX_AI_LOCATION": "us-central1",
            "EMBEDDING_SIZE": "512",
            "TOP_N_TEXT": "10",
            "TOP_N_IMAGE": "5"
        }
    
    def load_env_variables(self, env_file: str = ".env") -> bool:
        """Carrega variáveis de ambiente do arquivo .env"""
        if not DOTENV_AVAILABLE:
            print("⚠️  dotenv não disponível. Usando apenas variáveis de ambiente do sistema.")
            return True
            
        try:
            if os.path.exists(env_file):
                load_dotenv(env_file)
                print(f"✅ Arquivo {env_file} carregado com sucesso")
                return True
            else:
                print(f"⚠️  Arquivo {env_file} não encontrado")
                return False
        except Exception as e:
            print(f"❌ Erro ao carregar {env_file}: {e}")
            return False
    
    def validate_required_vars(self) -> bool:
        """Valida se todas as variáveis obrigatórias estão definidas"""
        missing_vars = []
        
        for var in self.required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Variáveis obrigatórias não definidas: {missing_vars}")
            print("💡 Adicione estas variáveis ao arquivo .env:")
            for var in missing_vars:
                print(f"   {var}=your_value_here")
            return False
        
        print("✅ Todas as variáveis obrigatórias estão definidas")
        return True
    
    def get_project_id(self) -> Optional[str]:
        """Obtém o Project ID do Google Cloud"""
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        if project_id:
            print(f"✅ Project ID obtido: {project_id}")
        else:
            print("❌ Project ID não encontrado")
        return project_id
    
    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Obtém todas as chaves de API necessárias"""
        api_keys = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "GOOGLE_CLOUD_PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        }
        
        # Verificar quais chaves estão disponíveis
        available_keys = [key for key, value in api_keys.items() if value]
        missing_keys = [key for key, value in api_keys.items() if not value]
        
        if available_keys:
            print(f"✅ Chaves disponíveis: {available_keys}")
        
        if missing_keys:
            print(f"❌ Chaves ausentes: {missing_keys}")
        
        return api_keys
    
    def get_optional_config(self) -> Dict[str, str]:
        """Obtém configurações opcionais com valores padrão"""
        config = {}
        
        for var, default_value in self.optional_vars.items():
            config[var] = os.getenv(var, default_value)
        
        print(f"✅ Configurações opcionais carregadas: {list(config.keys())}")
        return config
    
    def display_env_status(self) -> None:
        """Exibe o status das variáveis de ambiente"""
        print("🔍 STATUS DAS VARIÁVEIS DE AMBIENTE")
        print("=" * 40)
        
        # Variáveis obrigatórias
        print("📋 Variáveis Obrigatórias:")
        for var in self.required_vars:
            status = "✅" if os.getenv(var) else "❌"
            print(f"  {status} {var}")
        
        # Variáveis opcionais
        print("\n📋 Variáveis Opcionais:")
        for var, default_value in self.optional_vars.items():
            value = os.getenv(var, default_value)
            print(f"  ✅ {var} = {value}")
        
        print("=" * 40)

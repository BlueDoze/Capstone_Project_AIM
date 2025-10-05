"""
Gerenciamento de Modelos Gemini
===============================

Este módulo gerencia a inicialização e configuração dos modelos Gemini,
especificamente o Gemini 2.5 Pro para o sistema RAG multimodal.
"""

from typing import Optional, Dict, Any
import os

# Tentar importar Vertex AI, mas não falhar se não estiver disponível
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig, HarmCategory, HarmBlockThreshold
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    print("⚠️  Vertex AI não disponível. Instale com: pip install google-cloud-aiplatform vertexai")


class GeminiModelManager:
    """Gerencia modelos Gemini para o sistema RAG multimodal"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.model = None
        self.is_initialized = False
        
        # Configurações específicas do Gemini 2.5 Pro
        self.model_name = "gemini-2.5-pro"
        self.generation_config = None
        self.safety_settings = None
    
    def initialize_vertex_ai(self) -> bool:
        """Inicializa o Vertex AI"""
        if not VERTEX_AI_AVAILABLE:
            print("❌ Vertex AI não disponível")
            return False
            
        try:
            vertexai.init(project=self.project_id, location=self.location)
            print(f"✅ Vertex AI inicializado - Project: {self.project_id}, Location: {self.location}")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar Vertex AI: {e}")
            return False
    
    def initialize_gemini_2_5_pro(self) -> bool:
        """Inicializa especificamente o modelo Gemini 2.5 Pro"""
        if not VERTEX_AI_AVAILABLE:
            print("❌ Vertex AI não disponível para inicializar Gemini")
            return False
            
        try:
            # Inicializar modelo Gemini 2.5 Pro
            self.model = GenerativeModel(self.model_name)
            print(f"✅ Modelo {self.model_name} inicializado com sucesso")
            
            # Configurar parâmetros de geração
            self.generation_config = GenerationConfig(
                temperature=0.2,
                max_output_tokens=2048,
                top_p=0.95,
                top_k=40
            )
            
            # Configurar configurações de segurança
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            self.is_initialized = True
            print("✅ Configurações do Gemini 2.5 Pro aplicadas")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar Gemini 2.5 Pro: {e}")
            return False
    
    def validate_gemini_availability(self) -> bool:
        """Valida se o modelo Gemini está disponível"""
        if not self.is_initialized or not self.model:
            print("❌ Modelo Gemini não foi inicializado")
            return False
        
        print("✅ Modelo Gemini 2.5 Pro está disponível")
        return True
    
    def test_gemini_response(self, test_prompt: str = "Hello, can you respond with 'Gemini 2.5 Pro is working!'") -> bool:
        """Testa uma resposta básica do Gemini"""
        if not self.is_initialized or not self.model:
            print("❌ Modelo não inicializado para teste")
            return False
        
        try:
            print(f"🧪 Testando Gemini 2.5 Pro com prompt: '{test_prompt}'")
            
            response = self.model.generate_content(
                test_prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            if response and response.text:
                print(f"✅ Resposta do Gemini: {response.text}")
                return True
            else:
                print("❌ Resposta vazia do Gemini")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao testar Gemini: {e}")
            return False
    
    def get_gemini_model(self) -> Optional[GenerativeModel]:
        """Retorna o modelo Gemini inicializado"""
        if self.is_initialized:
            return self.model
        else:
            print("⚠️  Modelo Gemini não inicializado")
            return None
    
    def get_generation_config(self) -> Optional[GenerationConfig]:
        """Retorna a configuração de geração"""
        return self.generation_config
    
    def get_safety_settings(self) -> Optional[Dict]:
        """Retorna as configurações de segurança"""
        return self.safety_settings
    
    def display_model_status(self) -> None:
        """Exibe o status do modelo Gemini"""
        print("🤖 STATUS DO MODELO GEMINI 2.5 PRO")
        print("=" * 40)
        print(f"📋 Modelo: {self.model_name}")
        print(f"🔧 Project ID: {self.project_id}")
        print(f"📍 Location: {self.location}")
        print(f"✅ Inicializado: {'Sim' if self.is_initialized else 'Não'}")
        print(f"🔧 Configuração: {'Disponível' if self.generation_config else 'Não disponível'}")
        print(f"🛡️  Segurança: {'Configurada' if self.safety_settings else 'Não configurada'}")
        print("=" * 40)

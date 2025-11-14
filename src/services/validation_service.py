"""
Resource Validation Service
============================

This module orchestrates the complete validation of all resources
of the multimodal RAG system.
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
    """Complete validation service for the multimodal RAG system"""

    def __init__(self):
        self.config = None
        self.env_manager = None
        self.init_service = None
        self.resource_validator = None
        self.validation_results = {}

    def prepare_for_validation(self) -> bool:
        """Prepares the system for validation"""
        print("🔧 PREPARING SYSTEM FOR VALIDATION")
        print("=" * 50)

        try:
            # Load configurations
            self.config = RAGConfig()
            self.env_manager = EnvironmentManager()

            # Load environment variables
            env_loaded = self.env_manager.load_env_variables()
            if not env_loaded:
                print("⚠️  .env file not found")

            # Validate required variables
            if not self.env_manager.validate_required_vars():
                print("❌ Required variables not defined")
                return False

            # Update configuration
            self.config.PROJECT_ID = self.env_manager.get_project_id()

            # Create resource validator
            self.resource_validator = ResourceValidator(
                project_id=self.config.PROJECT_ID,
                location=self.config.LOCATION
            )

            print("✅ System prepared for validation")
            return True

        except Exception as e:
            print(f"❌ Error preparing system: {e}")
            return False
    
    def validate_system_initialization(self) -> bool:
        """Validates system initialization"""
        print("\n🚀 VALIDATING SYSTEM INITIALIZATION")
        print("=" * 45)

        try:
            # Create initialization service
            self.init_service = InitializationService()

            # Execute preparation phase
            prep_success = self.init_service.prepare_system()
            if not prep_success:
                print("❌ System preparation failed")
                return False

            # Initialize models
            model_success = self.init_service.initialize_models()
            if not model_success:
                print("❌ Model initialization failed")
                return False

            # Validate basic resources
            resource_success = self.init_service.validate_resources()
            if not resource_success:
                print("❌ Basic resource validation failed")
                return False

            print("✅ System initialization validated")
            return True

        except Exception as e:
            print(f"❌ Error in initialization validation: {e}")
            return False
    
    def validate_comprehensive_resources(self) -> Dict[str, Any]:
        """Executes comprehensive resource validation"""
        print("\n🔍 COMPREHENSIVE RESOURCE VALIDATION")
        print("=" * 40)

        if not self.resource_validator:
            print("❌ Resource validator not initialized")
            return {}

        # Execute comprehensive validation
        results = self.resource_validator.run_comprehensive_validation()

        self.validation_results['resource_validation'] = results
        return results
    
    def validate_end_to_end_functionality(self) -> bool:
        """Validates end-to-end system functionality"""
        print("\n🔄 END-TO-END VALIDATION")
        print("=" * 30)

        if not self.init_service:
            print("❌ Initialization service not available")
            return False

        try:
            # Test Gemini response
            print("🤖 Testing Gemini response...")
            gemini_test = self.init_service.gemini_manager.test_gemini_response(
                "Answer only: SYSTEM WORKING"
            )

            if gemini_test:
                print("✅ Gemini responding correctly")
            else:
                print("❌ Gemini is not responding")
                return False

            # Test text embedding
            print("📝 Testing text embedding...")
            text_embedding_test = self.init_service.embedding_manager.test_text_embedding_generation(
                "End-to-end functionality test"
            )

            if text_embedding_test:
                print("✅ Text embedding working")
            else:
                print("❌ Text embedding has issues")
                return False

            # Test multimodal embedding (if image available)
            print("🖼️  Testing multimodal embedding...")
            multimodal_test = self.init_service.embedding_manager.test_multimodal_embedding_generation()

            if multimodal_test:
                print("✅ Multimodal embedding working")
            else:
                print("⚠️  Multimodal embedding not tested (no image)")

            print("✅ End-to-end functionality validated")
            return True

        except Exception as e:
            print(f"❌ Error in end-to-end validation: {e}")
            return False
    
    def run_complete_validation(self) -> Dict[str, Any]:
        """Executes complete system validation"""
        print("🎯 EXECUTING COMPLETE VALIDATION OF MULTIMODAL RAG SYSTEM")
        print("=" * 70)

        # 1. Prepare system
        prep_success = self.prepare_for_validation()
        if not prep_success:
            return {'success': False, 'error': 'Preparation failed'}

        # 2. Validate initialization
        init_success = self.validate_system_initialization()
        if not init_success:
            return {'success': False, 'error': 'Initialization failed'}

        # 3. Validate comprehensive resources
        resource_results = self.validate_comprehensive_resources()

        # 4. Validate end-to-end functionality
        e2e_success = self.validate_end_to_end_functionality()

        # Compile final results
        final_results = {
            'success': prep_success and init_success and e2e_success,
            'preparation': prep_success,
            'initialization': init_success,
            'end_to_end': e2e_success,
            'resource_validation': resource_results,
            'summary': self.resource_validator.get_validation_summary() if self.resource_validator else {}
        }

        # Display final result
        print(f"\n{'='*70}")
        print("📊 COMPLETE VALIDATION FINAL RESULT")
        print(f"{'='*70}")

        if final_results['success']:
            print("🎉 COMPLETE VALIDATION SUCCESSFUL!")
            print("✅ Multimodal RAG system fully functional")
            print("✅ Ready for production use")
        else:
            print("⚠️  COMPLETE VALIDATION WITH ISSUES")
            print("💡 Check the errors above for corrections")

        return final_results
    
    def get_validation_report(self) -> str:
        """Generates detailed validation report"""
        if not self.validation_results:
            return "No validation executed"

        report = []
        report.append("# Multimodal RAG System Validation Report")
        report.append("=" * 60)

        # General summary
        summary = self.validation_results.get('summary', {})
        report.append(f"\n## General Summary")
        report.append(f"- Project ID: {summary.get('project_id', 'N/A')}")
        report.append(f"- Success Rate: {summary.get('success_rate', 0):.1f}%")
        report.append(f"- Passed Tests: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)}")

        # Errors and warnings
        if summary.get('errors'):
            report.append(f"\n## Errors Found ({len(summary['errors'])})")
            for error in summary['errors']:
                report.append(f"- {error}")

        if summary.get('warnings'):
            report.append(f"\n## Warnings ({len(summary['warnings'])})")
            for warning in summary['warnings']:
                report.append(f"- {warning}")

        return "\n".join(report)

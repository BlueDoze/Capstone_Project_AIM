"""
Multimodal RAG System Resource Validator
=========================================

This module implements comprehensive validations of all resources
required for the multimodal RAG system to function.
"""

import os
import sys
import time
import requests
import subprocess
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json

# Try to import Google Cloud libraries
try:
    from google.cloud import aiplatform
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
    GCP_LIBRARIES_AVAILABLE = True
except ImportError:
    GCP_LIBRARIES_AVAILABLE = False
    print("⚠️  Google Cloud libraries not available")


class ResourceValidator:
    """Complete resource validator for the multimodal RAG system"""

    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.validation_results = {}
        self.errors = []
        self.warnings = []

    def validate_google_cloud_access(self) -> bool:
        """Validates access to Google Cloud Platform"""
        print("🔍 Validating access to Google Cloud Platform...")

        if not GCP_LIBRARIES_AVAILABLE:
            self.errors.append("Google Cloud libraries not available")
            return False

        try:
            # Try to get default credentials
            credentials, project = default()

            if project != self.project_id:
                self.warnings.append(f"Different Project ID: expected {self.project_id}, got {project}")

            print(f"✅ Credentials obtained for project: {project}")
            print(f"✅ Credential type: {type(credentials).__name__}")

            # Test AI Platform initialization
            aiplatform.init(project=project, location=self.location)
            print(f"✅ AI Platform initialized in {self.location}")

            self.validation_results['gcp_access'] = True
            return True

        except DefaultCredentialsError as e:
            error_msg = f"Default credentials not found: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False

        except Exception as e:
            error_msg = f"Error accessing Google Cloud: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def validate_project_permissions(self) -> bool:
        """Validates project permissions"""
        print("\n🔐 Validating project permissions...")

        if not GCP_LIBRARIES_AVAILABLE:
            self.errors.append("Google Cloud libraries not available")
            return False

        try:
            # Test basic permissions
            from google.cloud import resourcemanager

            client = resourcemanager.ProjectsClient()
            project_path = f"projects/{self.project_id}"

            # Try to get project information
            project = client.get_project(name=project_path)
            print(f"✅ Project found: {project.display_name}")
            print(f"✅ Project state: {project.state.name}")

            # Check if project is active
            if project.state.name != "ACTIVE":
                self.warnings.append(f"Project is not active: {project.state.name}")

            self.validation_results['project_permissions'] = True
            return True

        except Exception as e:
            error_msg = f"Error validating permissions: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def validate_model_availability(self) -> bool:
        """Validates model availability"""
        print("\n🤖 Validating model availability...")

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
                    print(f"✅ Model {model} available")
                    available_models.append(model)

                elif "embedding" in model:
                    if "text" in model:
                        from vertexai.language_models import TextEmbeddingModel
                        test_model = TextEmbeddingModel.from_pretrained(model)
                    else:
                        from vertexai.vision_models import MultiModalEmbeddingModel
                        test_model = MultiModalEmbeddingModel.from_pretrained(model)

                    print(f"✅ Model {model} available")
                    available_models.append(model)

            except Exception as e:
                error_msg = f"Model {model} not available: {e}"
                self.errors.append(error_msg)
                print(f"❌ {error_msg}")

        self.validation_results['available_models'] = available_models

        if len(available_models) == len(models_to_check):
            print("✅ All models are available")
            return True
        else:
            print(f"⚠️  Only {len(available_models)}/{len(models_to_check)} models available")
            return False
    
    def validate_api_quotas(self) -> bool:
        """Validates API quotas"""
        print("\n📊 Validating API quotas...")

        try:
            # Test basic quota by making a simple call
            from vertexai.generative_models import GenerativeModel

            model = GenerativeModel("gemini-2.5-pro")

            # Make a simple test call
            start_time = time.time()
            response = model.generate_content("Quota test")
            end_time = time.time()

            if response and response.text:
                print(f"✅ API quota working")
                print(f"✅ Response time: {end_time - start_time:.2f}s")
                self.validation_results['api_quota'] = True
                return True
            else:
                self.errors.append("Empty API response")
                return False

        except Exception as e:
            error_msg = f"Error testing API quota: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def validate_directory_structure(self) -> bool:
        """Validates directory structure"""
        print("\n📁 Validating directory structure...")

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
                print(f"✅ Directory found: {directory}")
            else:
                missing_dirs.append(directory)
                print(f"❌ Directory missing: {directory}")

        self.validation_results['existing_directories'] = existing_dirs
        self.validation_results['missing_directories'] = missing_dirs

        if not missing_dirs:
            print("✅ All required directories exist")
            return True
        else:
            print(f"⚠️  {len(missing_dirs)} directories missing")
            return False
    
    def validate_file_permissions(self) -> bool:
        """Validates file permissions"""
        print("\n🔒 Validating file permissions...")

        test_files = [
            ".env",
            "main.py",
            "requirements.txt"
        ]

        permission_issues = []

        for file_path in test_files:
            if os.path.exists(file_path):
                # Check if readable
                if not os.access(file_path, os.R_OK):
                    permission_issues.append(f"Cannot read {file_path}")

                # Check if writable (for .env)
                if file_path == ".env" and not os.access(file_path, os.W_OK):
                    permission_issues.append(f"Cannot write to {file_path}")

                print(f"✅ Permissions OK for {file_path}")
            else:
                print(f"⚠️  File not found: {file_path}")

        if permission_issues:
            for issue in permission_issues:
                self.errors.append(issue)
            return False

        print("✅ All file permissions are correct")
        self.validation_results['file_permissions'] = True
        return True

    def validate_network_connectivity(self) -> bool:
        """Validates network connectivity"""
        print("\n🌐 Validating network connectivity...")

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
                    print(f"✅ Connectivity OK: {url}")
                else:
                    connectivity_results[url] = False
                    print(f"⚠️  Status {response.status_code}: {url}")
            except Exception as e:
                connectivity_results[url] = False
                print(f"❌ Connectivity error: {url} - {e}")

        self.validation_results['network_connectivity'] = connectivity_results

        successful_connections = sum(connectivity_results.values())
        if successful_connections == len(test_urls):
            print("✅ Excellent network connectivity")
            return True
        elif successful_connections > 0:
            print(f"⚠️  Partial connectivity: {successful_connections}/{len(test_urls)}")
            return True
        else:
            self.errors.append("No network connectivity")
            return False
    
    def validate_dependencies(self) -> bool:
        """Validates system dependencies"""
        print("\n📦 Validating dependencies...")

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
                print(f"✅ Package available: {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ Package missing: {package}")

        self.validation_results['available_packages'] = available_packages
        self.validation_results['missing_packages'] = missing_packages

        if not missing_packages:
            print("✅ All dependencies are installed")
            return True
        else:
            print(f"⚠️  {len(missing_packages)} packages missing")
            return False
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Executes comprehensive validation of all resources"""
        print("🚀 STARTING COMPREHENSIVE RESOURCE VALIDATION")
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
                print(f"❌ Error during {test_name}: {e}")
                results[test_name] = False
                self.errors.append(f"Error in {test_name}: {e}")

        # Calculate overall score
        passed_tests = sum(results.values())
        total_tests = len(results)
        success_rate = (passed_tests / total_tests) * 100

        self.validation_results['overall_results'] = results
        self.validation_results['success_rate'] = success_rate
        self.validation_results['passed_tests'] = passed_tests
        self.validation_results['total_tests'] = total_tests

        print(f"\n{'='*60}")
        print("📊 VALIDATION FINAL RESULT")
        print(f"{'='*60}")
        print(f"✅ Tests passed: {passed_tests}/{total_tests}")
        print(f"📈 Success rate: {success_rate:.1f}%")

        if self.errors:
            print(f"\n❌ Errors found ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")

        if success_rate >= 80:
            print("\n🎉 VALIDATION COMPLETED SUCCESSFULLY!")
            print("✅ System ready for production use")
        elif success_rate >= 60:
            print("\n⚠️  VALIDATION PARTIALLY SUCCESSFUL")
            print("💡 Some issues need to be resolved")
        else:
            print("\n❌ VALIDATION FAILED")
            print("🔧 Multiple issues need to be fixed")

        return self.validation_results
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Returns validation summary"""
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

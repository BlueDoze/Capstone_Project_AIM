"""
Pytest Configuration
====================

This file contains pytest configuration and shared fixtures
for all tests in the Capstone Project AIM test suite.
"""

import os
import sys
import pytest
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Add src directory to Python path
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))


@pytest.fixture(scope="session")
def project_root():
    """Fixture that returns the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def src_path():
    """Fixture that returns the src directory path."""
    return SRC_PATH


@pytest.fixture(scope="session")
def test_images_path():
    """Fixture that returns the test images directory path."""
    return PROJECT_ROOT / "images"


@pytest.fixture(scope="session")
def temp_dir():
    """Fixture that returns the temp directory path."""
    return PROJECT_ROOT / "temp"


@pytest.fixture(scope="function")
def clean_temp_dir(temp_dir):
    """Fixture that ensures temp directory is clean before each test."""
    # Create temp directory if it doesn't exist
    temp_dir.mkdir(exist_ok=True)
    
    # Clean up any existing files
    for file in temp_dir.glob("*"):
        if file.is_file():
            file.unlink()
    
    yield temp_dir
    
    # Clean up after test
    for file in temp_dir.glob("*"):
        if file.is_file():
            file.unlink()


@pytest.fixture(scope="session")
def mock_env_vars():
    """Fixture that provides mock environment variables for testing."""
    return {
        "GEMINI_API_KEY": "test_api_key",
        "GOOGLE_CLOUD_PROJECT_ID": "test_project_id",
        "GOOGLE_APPLICATION_CREDENTIALS": "test_credentials.json"
    }


@pytest.fixture(scope="function")
def set_mock_env(mock_env_vars):
    """Fixture that sets mock environment variables for testing."""
    # Store original values
    original_values = {}
    
    # Set mock values
    for key, value in mock_env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "system: mark test as a system test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        test_path = Path(item.fspath)
        
        if "unit" in str(test_path):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(test_path):
            item.add_marker(pytest.mark.integration)
        elif "system" in str(test_path):
            item.add_marker(pytest.mark.system)
        elif "performance" in str(test_path):
            item.add_marker(pytest.mark.performance)
        
        # Mark slow tests
        if any(keyword in item.name.lower() for keyword in ["slow", "performance", "load"]):
            item.add_marker(pytest.mark.slow)

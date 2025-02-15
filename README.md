# Terminusa Online Testing Suite

This directory contains the comprehensive testing suite for Terminusa Online, including unit tests, integration tests, and end-to-end tests for all game systems and components.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Contributing](#contributing)

## Overview

The testing suite is designed to ensure the reliability, performance, and correctness of all Terminusa Online systems. It includes:

- Unit tests for individual components
- Integration tests for system interactions
- Performance tests for optimization
- Security tests for vulnerability detection
- End-to-end tests for complete features

## Test Structure

```
tests/
├── conftest.py              # Shared test fixtures and utilities
├── .env.test               # Test environment configuration
├── test_ai_behavior.py     # AI and NPC behavior tests
├── test_analytics.py       # Game analytics tests
├── test_audit.py          # Audit system tests
├── test_backup.py         # Backup system tests
├── test_combat.py         # Combat system tests
├── test_economy.py        # Economy system tests
├── test_encryption.py     # Encryption and security tests
├── test_game_systems.py   # Core game systems tests
├── test_gates.py          # Gate/dungeon system tests
├── test_guild.py          # Guild system tests
├── test_logging.py        # Logging system tests
├── test_marketplace.py    # Marketplace system tests
├── test_metrics.py        # Metrics system tests
├── test_party.py          # Party system tests
├── test_permissions.py    # Permissions system tests
├── test_plugins.py        # Plugin system tests
├── test_progression.py    # Progression system tests
├── test_ranking.py        # Ranking system tests
├── test_resources.py      # Resource system tests
├── test_rewards.py        # Reward system tests
├── test_sessions.py       # Session management tests
├── test_telemetry.py      # Telemetry system tests
├── test_validation.py     # Input validation tests
└── test_web_api.py        # Web API tests
```

## Setup

1. Create a virtual environment:
```bash
python install_dependencies.py --dev
```

2. Activate the virtual environment:
- Windows:
```bash
.\.venv\Scripts\activate
```
- Unix/MacOS:
```bash
source .venv/bin/activate
```

3. Install test dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

### Run all tests:
```bash
python run_tests.py
```

### Run specific test categories:
```bash
python run_tests.py tests/test_combat.py
python run_tests.py tests/test_economy.py
```

### Run with coverage:
```bash
python run_tests.py --coverage
```

### Run in parallel:
```bash
python run_tests.py -n auto
```

### Generate HTML report:
```bash
python run_tests.py --html
```

## Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **Functional Tests**: Test complete features
- **Performance Tests**: Test system performance and optimization
- **Security Tests**: Test security measures and vulnerabilities
- **API Tests**: Test HTTP endpoints and API functionality
- **Game Tests**: Test game mechanics and logic
- **Network Tests**: Test network communication
- **Database Tests**: Test data storage and retrieval
- **Async Tests**: Test asynchronous operations

## Writing Tests

### Test File Structure:
```python
import unittest
from unittest.mock import Mock, patch

class TestComponent(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        pass

    def tearDown(self):
        """Clean up after test"""
        pass

    def test_feature(self):
        """Test specific feature"""
        # Arrange
        # Act
        # Assert
```

### Using Fixtures:
```python
import pytest

@pytest.fixture
def mock_database():
    """Database fixture for testing"""
    return MockDatabase()

def test_with_fixture(mock_database):
    """Test using fixture"""
    result = mock_database.query()
    assert result is not None
```

### Async Tests:
```python
import pytest

@pytest.mark.asyncio
async def test_async_feature():
    """Test async feature"""
    result = await async_function()
    assert result is not None
```

## CI/CD Integration

The test suite is integrated with our CI/CD pipeline:

1. Tests run automatically on push/PR
2. Coverage reports are generated
3. Test results are published
4. Failed tests block merging

## Contributing

1. Create a new test file for new features
2. Follow existing test patterns
3. Include docstrings and comments
4. Ensure tests are isolated
5. Add appropriate markers
6. Update documentation

### Test Checklist:

- [ ] Tests are isolated
- [ ] Mocks are used appropriately
- [ ] Edge cases are covered
- [ ] Error cases are tested
- [ ] Documentation is updated
- [ ] Coverage is maintained

## Available Test Markers

- @pytest.mark.slow
- @pytest.mark.integration
- @pytest.mark.unit
- @pytest.mark.api
- @pytest.mark.db
- @pytest.mark.async
- @pytest.mark.security
- @pytest.mark.performance
- @pytest.mark.game
- @pytest.mark.network

## Test Configuration

Configuration is managed through:

1. pytest.ini - Test suite configuration
2. .env.test - Environment variables
3. conftest.py - Shared fixtures

## Debugging Tests

1. Use pytest's -s flag to see print output:
```bash
python run_tests.py -s
```

2. Use pytest's --pdb flag for debugger:
```bash
python run_tests.py --pdb
```

3. Use logging for detailed output:
```python
import logging
logging.debug("Debug message")
```

## Performance Testing

1. Run performance tests:
```bash
python run_tests.py --benchmark
```

2. Profile tests:
```bash
python run_tests.py --profile
```

## Security Testing

1. Run security tests:
```bash
python run_tests.py -m security
```

2. Run vulnerability scan:
```bash
bandit -r .
```

## Maintenance

1. Clean test cache:
```bash
python run_tests.py --cache-clear
```

2. Update test dependencies:
```bash
python install_dependencies.py --upgrade
```

3. Verify test environment:
```bash
python run_tests.py --verify
```

## Support

For questions or issues:

1. Check existing test documentation
2. Review test logs
3. Contact the development team
4. Submit an issue

## License

This test suite is part of Terminusa Online and is subject to the same license terms.

# Contributing to Terminusa Online Monitoring

## Getting Started

### Development Environment

1. **Fork and Clone**
```bash
# Fork the repository on GitHub
git clone https://github.com/your-username/terminusa-monitoring.git
cd terminusa-monitoring

# Add upstream remote
git remote add upstream https://github.com/terminusa/monitoring.git
```

2. **Setup Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements-monitoring.txt
pip install -r requirements-dev.txt
```

3. **Configure Development Settings**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
FLASK_ENV=development
FLASK_DEBUG=1
MONITORING_CONFIG=config/monitoring_dev.py
```

## Development Workflow

### 1. Create a Branch

```bash
# Get latest changes
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-fix-name
```

### 2. Development Guidelines

#### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for classes and functions
- Keep functions focused and small
- Use meaningful variable names

```python
def calculate_metric_average(
    metrics: List[float],
    window_size: int = 60
) -> float:
    """
    Calculate moving average of metrics.

    Args:
        metrics: List of metric values
        window_size: Size of moving window in seconds

    Returns:
        Moving average of metrics
    """
    if not metrics:
        return 0.0
    return sum(metrics[-window_size:]) / len(metrics[-window_size:])
```

#### Testing
- Write tests for new features
- Update existing tests when changing functionality
- Aim for high test coverage

```python
def test_metric_average():
    metrics = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert calculate_metric_average(metrics, 3) == 4.0
    assert calculate_metric_average([], 3) == 0.0
```

#### Documentation
- Update relevant documentation
- Add inline comments for complex logic
- Include examples in docstrings

### 3. Making Changes

#### Commit Messages
```bash
# Format
<type>(<scope>): <subject>

# Examples
feat(metrics): add new metric collection system
fix(alerts): resolve notification delay issue
docs(api): update API documentation
test(collector): add tests for metric collector
```

#### Types
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Testing
- chore: Maintenance

### 4. Testing Your Changes

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_metrics.py

# Run with coverage
pytest --cov=monitoring

# Run linting
flake8 monitoring
mypy monitoring
```

### 5. Submitting Changes

1. **Update Your Branch**
```bash
git fetch upstream
git rebase upstream/main
```

2. **Push Changes**
```bash
git push origin feature/your-feature-name
```

3. **Create Pull Request**
- Go to GitHub
- Create Pull Request from your branch
- Fill out PR template
- Request review

## Pull Request Guidelines

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Added unit tests
- [ ] Updated existing tests
- [ ] Manually tested changes

## Documentation
- [ ] Updated relevant documentation
- [ ] Added inline comments
- [ ] Updated API docs if needed
```

### Review Process
1. Automated checks must pass
2. Code review required
3. Documentation review if needed
4. Changes requested must be addressed
5. Final approval needed

## Development Tools

### Recommended VSCode Extensions
- Python
- Pylance
- Python Test Explorer
- GitLens
- Docker

### Code Quality Tools
```bash
# Install development tools
pip install -r requirements-dev.txt

# Run formatters
black monitoring
isort monitoring

# Run linters
flake8 monitoring
pylint monitoring
mypy monitoring

# Run security checks
bandit -r monitoring
safety check
```

## Project Structure

### Core Components
```
monitoring/
├── game_systems/          # Core monitoring systems
│   ├── metric_collector/  # Metric collection
│   ├── alert_manager/    # Alert management
│   └── monitoring_init/  # Initialization
├── models/              # Database models
├── routes/             # API routes
└── tests/             # Test suite
```

### Supporting Files
```
monitoring/
├── docs/               # Documentation
├── scripts/           # Utility scripts
├── static/           # Frontend assets
└── templates/       # HTML templates
```

## Release Process

### Version Numbering
- Major.Minor.Patch (e.g., 1.2.3)
- Major: Breaking changes
- Minor: New features
- Patch: Bug fixes

### Release Steps
1. Update version number
2. Update changelog
3. Create release branch
4. Run full test suite
5. Create release tag
6. Deploy to staging
7. Deploy to production

## Continuous Integration

### GitHub Actions
```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pytest
```

## Getting Help

### Resources
- Documentation: /docs/
- Wiki: https://github.com/terminusa/monitoring/wiki
- Issues: https://github.com/terminusa/monitoring/issues

### Community
- Discord: #monitoring-dev
- Discussions: GitHub Discussions
- Email: dev@terminusa.online

### Reporting Issues
1. Check existing issues
2. Use issue template
3. Include reproduction steps
4. Attach relevant logs
5. Tag appropriately

## Code of Conduct

### Our Standards
- Be respectful and inclusive
- Focus on constructive feedback
- Maintain professional conduct
- Support fellow contributors

### Enforcement
- Issues reported to maintainers
- Fair warning system
- Temporary/permanent bans if needed

## License

### MIT License
- Free to use, modify, distribute
- Include original license
- No warranty provided

## Support

### Documentation
- Development Guide: /docs/development.md
- API Reference: /docs/api.md
- Architecture: /docs/architecture.md

### Contact
- GitHub Issues
- Discord: #monitoring-dev
- Email: dev@terminusa.online

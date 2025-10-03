# 📦 Publishing telescope-python to PyPI

This guide will help you publish the telescope-python package to PyPI using Poetry.

## 🚀 Quick Start

### Prerequisites
1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   # or
   pip install poetry
   ```

2. **PyPI Account**: Create accounts on:
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)
   - [PyPI](https://pypi.org/account/register/) (for production)

3. **API Tokens**: Generate API tokens for both:
   - TestPyPI: https://test.pypi.org/manage/account/token/
   - PyPI: https://pypi.org/manage/account/token/

## 📋 Step-by-Step Publishing

### Step 1: Set up Poetry
```bash
cd telescope-python

# Initialize Poetry (if not done)
poetry install

# Configure PyPI credentials
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.pypi pypi-YOUR_PYPI_TOKEN_HERE
poetry config pypi-token.testpypi pypi-YOUR_TESTPYPI_TOKEN_HERE
```

### Step 2: Prepare for Publishing
```bash
# Clean up old builds
rm -rf dist/ build/ *.egg-info/

# Update version (if needed)
poetry version patch  # or minor, major
# or manually edit pyproject.toml

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black telescope_client/
poetry run ruff check telescope_client/
```

### Step 3: Build the Package
```bash
# Build the package
poetry build

# This creates:
# - dist/telescope_python-1.0.0-py3-none-any.whl
# - dist/telescope-python-1.0.0.tar.gz
```

### Step 4: Test on TestPyPI (Recommended)
```bash
# Publish to TestPyPI first
poetry publish -r testpypi

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ telescope-python

# Test the package
python -c "from telescope import TelescopeClient; print('Import successful!')"
```

### Step 5: Publish to PyPI
```bash
# If TestPyPI worked, publish to real PyPI
poetry publish

# Package will be available at:
# https://pypi.org/project/telescope-python/
```

## 🔧 Configuration Files

### pyproject.toml
The main configuration file that replaces setup.py:
- Package metadata
- Dependencies
- Build configuration
- Development tools configuration

### Key Commands
```bash
# Version management
poetry version patch    # 1.0.0 -> 1.0.1
poetry version minor    # 1.0.0 -> 1.1.0
poetry version major    # 1.0.0 -> 2.0.0

# Dependency management
poetry add requests
poetry add --group dev pytest
poetry remove requests

# Publishing
poetry build           # Build package
poetry publish         # Publish to PyPI
poetry publish -r testpypi  # Publish to TestPyPI
```

## 📊 Package Information

### Installation
```bash
# Basic installation
pip install telescope-python

# With Django support
pip install telescope-python[django]

# With Flask support
pip install telescope-python[flask]

# With all integrations
pip install telescope-python[all]
```

### Usage
```python
from telescope import TelescopeClient

client = TelescopeClient(
    dsn="https://your-telescope-server.com",
    project_id="your-project-id",
    environment="production"
)

# Capture an exception
try:
    1 / 0
except Exception as e:
    client.capture_exception(e)
```

## 🔄 Automated Publishing (GitHub Actions)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Build package
      run: poetry build
    
    - name: Publish to PyPI
      env:
        POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
      run: poetry publish
```

## 🏷️ Version Strategy

### Semantic Versioning
- **MAJOR**: Breaking changes (2.0.0)
- **MINOR**: New features, backward compatible (1.1.0)
- **PATCH**: Bug fixes, backward compatible (1.0.1)

### Pre-release Versions
```bash
poetry version prerelease  # 1.0.0 -> 1.0.1a0
poetry version prerelease  # 1.0.1a0 -> 1.0.1a1
```

## 🧪 Testing Checklist

Before publishing:
- [ ] All tests pass (`poetry run pytest`)
- [ ] Code is formatted (`poetry run black .`)
- [ ] Linting passes (`poetry run ruff check .`)
- [ ] Version is updated
- [ ] README is up to date
- [ ] CHANGELOG is updated
- [ ] Test on TestPyPI first
- [ ] Manual installation test

## 🔗 Useful Links

- [Poetry Documentation](https://python-poetry.org/docs/)
- [PyPI](https://pypi.org/)
- [TestPyPI](https://test.pypi.org/)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging Guide](https://packaging.python.org/)

---

Happy Publishing! 🚀

# 🚀 Quick PyPI Publishing Setup

## 1. Install Poetry (if not already installed)
```bash
curl -sSL https://install.python-poetry.org | python3 -
# or
pip install poetry
```

## 2. Create PyPI Accounts & Tokens

### PyPI (Production)
1. Go to https://pypi.org/account/register/
2. Create account and verify email
3. Go to https://pypi.org/manage/account/token/
4. Create API token with "Entire account" scope
5. Copy the token (starts with `pypi-`)

### TestPyPI (Testing - Optional but Recommended)
1. Go to https://test.pypi.org/account/register/
2. Create account and verify email
3. Go to https://test.pypi.org/manage/account/token/
4. Create API token with "Entire account" scope
5. Copy the token (starts with `pypi-`)

## 3. Configure Poetry
```bash
# Configure PyPI token (REQUIRED)
poetry config pypi-token.pypi pypi-YOUR_PYPI_TOKEN_HERE

# Configure TestPyPI token (OPTIONAL but recommended)
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi pypi-YOUR_TESTPYPI_TOKEN_HERE
```

## 4. Publish Your Package

### Option A: Use the Interactive Script
```bash
./publish.sh
```
Follow the menu options:
- Option 1: Check configuration
- Option 6: Full workflow (recommended for first time)

### Option B: Manual Commands
```bash
# Install dependencies
poetry install

# Build the package
poetry build

# Test on TestPyPI first (recommended)
poetry publish -r testpypi

# If TestPyPI works, publish to PyPI
poetry publish
```

## 5. Verify Installation
```bash
# From TestPyPI
pip install --index-url https://test.pypi.org/simple/ telescope-python

# From PyPI (after publishing)
pip install telescope-client
```

## 6. Test the Package
```python
from telescope_client import TelescopeClient
print("✅ Import successful!")

# Test basic functionality
client = TelescopeClient(
    dsn="http://localhost:8080",
    project_id="test-project",
    environment="development"
)
print("✅ Client created successfully!")
```

## 🎉 That's it!

Your package will be available at:
- **TestPyPI**: https://test.pypi.org/project/telescope-client/
- **PyPI**: https://pypi.org/project/telescope-python/

## 📦 Installation for Users
```bash
# Basic installation
pip install telescope-python

# With Django support
pip install telescope-python[django]

# With all integrations
pip install telescope-python[all]
```

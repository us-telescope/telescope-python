#!/bin/bash

# 📦 Telescope Python Client Publishing Script
# This script helps you publish the telescope-client package to PyPI

set -e  # Exit on any error

echo "🔭 Telescope Python Client Publishing Script"
echo "============================================="
echo ""

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install it first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

echo "✅ Poetry is installed: $(poetry --version)"
echo ""

# Function to check if PyPI token is configured
check_pypi_config() {
    if poetry config pypi-token.pypi &> /dev/null; then
        echo "✅ PyPI token is configured"
    else
        echo "❌ PyPI token is not configured"
        echo "   Please run: poetry config pypi-token.pypi YOUR_PYPI_TOKEN"
        echo "   Get your token from: https://pypi.org/manage/account/token/"
        return 1
    fi
}

# Function to check if TestPyPI token is configured
check_testpypi_config() {
    if poetry config pypi-token.testpypi &> /dev/null; then
        echo "✅ TestPyPI token is configured"
    else
        echo "⚠️  TestPyPI token is not configured (optional for testing)"
        echo "   To configure: poetry config pypi-token.testpypi YOUR_TESTPYPI_TOKEN"
        echo "   Get your token from: https://test.pypi.org/manage/account/token/"
    fi
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    if [ -d "tests" ] && [ "$(ls -A tests)" ]; then
        poetry run pytest tests/ -v
        echo "✅ All tests passed"
    else
        echo "⚠️  No tests found in tests/ directory"
    fi
}

# Function to format code
format_code() {
    echo "🎨 Formatting code..."
    poetry run black telescope/ --check --diff || {
        echo "❌ Code formatting issues found. Run: poetry run black telescope/"
        return 1
    }
    echo "✅ Code is properly formatted"
}

# Function to lint code
lint_code() {
    echo "🔍 Linting code..."
    poetry run ruff check telescope/ || {
        echo "❌ Linting issues found. Run: poetry run ruff check telescope/ --fix"
        return 1
    }
    echo "✅ No linting issues found"
}

# Function to build package
build_package() {
    echo "🏗️  Building package..."
    
    # Clean previous builds
    rm -rf dist/ build/ *.egg-info/
    
    # Build the package
    poetry build
    
    echo "✅ Package built successfully"
    echo "   Files created:"
    ls -la dist/
}

# Function to publish to TestPyPI
publish_to_testpypi() {
    echo "🧪 Publishing to TestPyPI..."
    
    # Configure TestPyPI repository if not already done
    poetry config repositories.testpypi https://test.pypi.org/legacy/ || true
    
    # Publish to TestPyPI
    poetry publish -r testpypi
    
    echo "✅ Published to TestPyPI successfully!"
    echo "   Test installation with:"
    echo "   pip install --index-url https://test.pypi.org/simple/ telescope-client"
}

# Function to publish to PyPI
publish_to_pypi() {
    echo "🚀 Publishing to PyPI..."
    
    # Publish to PyPI
    poetry publish
    
    echo "✅ Published to PyPI successfully!"
    echo "   Package is now available at: https://pypi.org/project/telescope-client/"
    echo "   Install with: pip install telescope-client"
}

# Main menu
show_menu() {
    echo "What would you like to do?"
    echo "1. Check configuration"
    echo "2. Run tests and quality checks"
    echo "3. Build package"
    echo "4. Publish to TestPyPI (recommended first)"
    echo "5. Publish to PyPI (production)"
    echo "6. Full workflow (test + build + publish to TestPyPI)"
    echo "7. Exit"
    echo ""
}

# Main execution
while true; do
    show_menu
    read -p "Enter your choice (1-7): " choice
    echo ""
    
    case $choice in
        1)
            echo "🔧 Checking configuration..."
            check_pypi_config
            check_testpypi_config
            echo ""
            ;;
        2)
            echo "🧪 Running tests and quality checks..."
            run_tests
            format_code
            lint_code
            echo ""
            ;;
        3)
            build_package
            echo ""
            ;;
        4)
            if check_testpypi_config; then
                build_package
                publish_to_testpypi
            fi
            echo ""
            ;;
        5)
            if check_pypi_config; then
                echo "⚠️  This will publish to production PyPI. Are you sure? (y/N)"
                read -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    build_package
                    publish_to_pypi
                else
                    echo "❌ Publishing cancelled"
                fi
            fi
            echo ""
            ;;
        6)
            echo "🔄 Running full workflow..."
            run_tests
            format_code
            lint_code
            build_package
            if check_testpypi_config; then
                publish_to_testpypi
            fi
            echo ""
            ;;
        7)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please enter 1-7."
            echo ""
            ;;
    esac
done

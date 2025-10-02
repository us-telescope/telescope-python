"""
Setup configuration for Telescope Python Client
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="telescope-python",
    version="1.0.0",
    author="Ultron Labs",
    author_email="hello@ultron.studio",
    description="Python client for Telescope error monitoring with OpenTelemetry integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/us-telescope/telescope",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Logging",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "opentelemetry-exporter-otlp>=1.20.0",
        "opentelemetry-instrumentation-requests>=0.41b0",
        "opentelemetry-instrumentation-logging>=0.41b0",
    ],
    extras_require={
        "django": [
            "opentelemetry-instrumentation-django>=0.41b0",
            "opentelemetry-instrumentation-psycopg2>=0.41b0",
        ],
        "flask": [
            "opentelemetry-instrumentation-flask>=0.41b0",
            "opentelemetry-instrumentation-sqlalchemy>=0.41b0",
        ],
        "fastapi": [
            "opentelemetry-instrumentation-fastapi>=0.41b0",
            "opentelemetry-instrumentation-sqlalchemy>=0.41b0",
        ],
        "celery": [
            "opentelemetry-instrumentation-celery>=0.41b0",
        ],
        "all": [
            "opentelemetry-instrumentation-django>=0.41b0",
            "opentelemetry-instrumentation-psycopg2>=0.41b0",
            "opentelemetry-instrumentation-flask>=0.41b0",
            "opentelemetry-instrumentation-fastapi>=0.41b0",
            "opentelemetry-instrumentation-sqlalchemy>=0.41b0",
            "opentelemetry-instrumentation-celery>=0.41b0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "telescope-test=telescope_client.cli:test_connection",
        ],
    },
)

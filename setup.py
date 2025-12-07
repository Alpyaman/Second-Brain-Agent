"""
Setup configuration for Second Brain Agent.
Makes the package pip-installable and provides CLI commands.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="second-brain-agent",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Transform job descriptions into working code in minutes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Second-Brain-Agent",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "pylint>=2.17.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # Enhanced CLI with Typer
            "sba=src.cli.main:app",
            # Legacy CLI commands (backward compatibility)
            "sba-architect=architect:main",
            "sba-dev=dev_team:main",
            "sba-curator=curator:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

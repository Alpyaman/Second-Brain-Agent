"""
Code Generator Utilities

This module provides utilities for extracting and organizing code from LLM-generated
markdown responses into structured file dictionaries.
"""
import re
from typing import Dict, List, Tuple


def extract_code_blocks(markdown_text: str) -> List[Tuple[str, str, str]]:
    """
    Extract code blocks from markdown text with improved filename detection.

    Handles multiple filename patterns:
    1. ```python path/to/file.py
    2. # path/to/file.py as first line in code block
    3. ### path/to/file.py header before code block

    Args:
        markdown_text: Markdown text containing code blocks

    Returns:
        List of tuples (language, file_path, code_content)
    """
    code_blocks = []

    # Split by code block markers to process each block individually
    # Pattern to match code blocks with optional file paths
    # Matches: ```language [optional_path]
    pattern = r'```(\w+)(?:\s+([^\n]+))?\n(.*?)```'

    # Also check for headers before code blocks (e.g., ### app/main.py)
    lines = markdown_text.split('\n')
    markdown_with_headers = []

    for i, line in enumerate(lines):
        # Check if line is a header that looks like a file path
        if line.startswith('#') and any(ext in line for ext in ['.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml']):
            # Extract the file path from the header
            file_path = line.lstrip('#').strip()
            # Look ahead to see if next line starts a code block
            if i + 1 < len(lines) and lines[i + 1].startswith('```'):
                # Insert the file path into the code block header
                lines[i + 1] = lines[i + 1].replace('```', f'```python {file_path}\n', 1)
                continue
        markdown_with_headers.append(line)

    enhanced_markdown = '\n'.join(markdown_with_headers)
    matches = re.findall(pattern, enhanced_markdown, re.DOTALL)

    for language, file_path, code in matches:
        file_path = file_path.strip() if file_path else ""
        code = code.strip()

        # If no file path in header, check first line of code for comment with filename
        if not file_path and code:
            first_line = code.split('\n')[0].strip()
            # Check for comment with filename (e.g., # app/main.py or // app/main.js)
            if first_line.startswith('#') or first_line.startswith('//'):
                potential_path = first_line.lstrip('#/').strip()
                # Check if it looks like a file path
                if '.' in potential_path and '/' in potential_path and ' ' not in potential_path:
                    file_path = potential_path
                    # Remove the comment line from code
                    code = '\n'.join(code.split('\n')[1:]).strip()
        if code:
            code_blocks.append((language, file_path, code))

    return code_blocks


def extract_file_structure(markdown_text: str) -> Dict[str, str]:
    """
    Extract file structure mentions from markdown.

    Looks for patterns like:
    - `src/file.py` - description
    - **src/file.py**: description

    Args:
        markdown_text: Markdown text

    Returns:
        Dictionary mapping file paths to descriptions
    """
    file_structure = {}

    # Pattern to match file paths
    patterns = [
        r'`([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)`\s*-\s*(.+)',
        r'\*\*([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)\*\*:\s*(.+)',
        r'-\s+`([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)`:\s*(.+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, markdown_text, re.MULTILINE)
        for file_path, description in matches:
            file_structure[file_path.strip()] = description.strip()

    return file_structure


def extract_and_organize_code(
    markdown_text: str,
    language: str = 'python',
    base_path: str = ''
) -> Dict[str, str]:
    """
    Extract code blocks from markdown and organize them into files.

    Args:
        markdown_text: LLM-generated markdown with code blocks
        language: Primary programming language to filter for
        base_path: Base directory path to prepend to file paths

    Returns:
        Dictionary mapping file paths to code content
    """
    files = {}
    code_blocks = extract_code_blocks(markdown_text)

    # Counter for unnamed files
    unnamed_counter = 1

    for lang, file_path, code in code_blocks:
        # Skip if language doesn't match (unless it's a config file)
        if lang.lower() not in [language.lower(), 'json', 'yaml', 'yml', 'toml', 'env', 'txt', 'md']:
            continue

        # Determine file path
        if file_path:
            # Clean up the file path
            file_path = file_path.strip('`').strip()
            # Remove any leading slashes or dots
            file_path = file_path.lstrip('./')
        else:
            # Generate a file path based on language
            ext = get_extension_for_language(lang)
            file_path = f"unnamed_{unnamed_counter}{ext}"
            unnamed_counter += 1

        # Prepend base path if provided
        if base_path:
            file_path = f"{base_path}/{file_path}"

        # Store the code
        files[file_path] = code

    return files


def get_extension_for_language(language: str) -> str:
    """
    Get file extension for a programming language.

    Args:
        language: Programming language name

    Returns:
        File extension with dot
    """
    extensions = {
        'python': '.py',
        'javascript': '.js',
        'typescript': '.ts',
        'tsx': '.tsx',
        'jsx': '.jsx',
        'java': '.java',
        'cpp': '.cpp',
        'c': '.c',
        'go': '.go',
        'rust': '.rs',
        'ruby': '.rb',
        'php': '.php',
        'swift': '.swift',
        'kotlin': '.kt',
        'sql': '.sql',
        'html': '.html',
        'css': '.css',
        'scss': '.scss',
        'json': '.json',
        'yaml': '.yaml',
        'yml': '.yml',
        'toml': '.toml',
        'xml': '.xml',
        'markdown': '.md',
        'md': '.md',
        'txt': '.txt',
        'sh': '.sh',
        'bash': '.sh',
    }

    return extensions.get(language.lower(), '.txt')


def generate_gitignore(tech_stack: Dict[str, List[str]]) -> str:
    """
    Generate a .gitignore file based on the technology stack.

    Args:
        tech_stack: Dictionary with frontend, backend, database, etc.

    Returns:
        .gitignore file content
    """
    gitignore_lines = [
        "# Dependencies",
        "node_modules/",
        ".venv/",
        "venv/",
        "env/",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "",
        "# IDE",
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        "*~",
        "",
        "# Environment variables",
        ".env",
        ".env.local",
        ".env.*.local",
        "",
        "# Build outputs",
        "dist/",
        "build/",
        "*.egg-info/",
        ".next/",
        "out/",
        "",
        "# Logs",
        "*.log",
        "npm-debug.log*",
        "yarn-debug.log*",
        "yarn-error.log*",
        "",
        "# OS",
        ".DS_Store",
        "Thumbs.db",
        "",
        "# Testing",
        "coverage/",
        ".coverage",
        "htmlcov/",
        ".pytest_cache/",
        "",
        "# Database",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
    ]

    # Add specific entries based on tech stack
    frontend = tech_stack.get('frontend', [])
    backend = tech_stack.get('backend', [])

    if any('next' in str(t).lower() for t in frontend):
        gitignore_lines.extend(["", "# Next.js", ".next/", "out/", ".vercel/"])

    if any('python' in str(t).lower() for t in backend):
        gitignore_lines.extend(["", "# Python", "*.py[cod]", "__pycache__/", "*.so"])

    return '\n'.join(gitignore_lines) + '\n'


def generate_readme(
    project_name: str,
    tech_stack: Dict[str, List[str]],
    features: List[Dict[str, str]]
) -> str:
    """
    Generate a README.md file for the project.

    Args:
        project_name: Name of the project
        tech_stack: Technology stack dictionary
        features: List of features to implement

    Returns:
        README.md content
    """
    readme_lines = [
        f"# {project_name}",
        "",
        "## Overview",
        "",
        "This project was generated by the Second-Brain-Agent development team.",
        "",
        "## Technology Stack",
        "",
    ]

    # Add tech stack sections
    for category, technologies in tech_stack.items():
        if technologies:
            readme_lines.append(f"### {category.title()}")
            for tech in technologies:
                readme_lines.append(f"- {tech}")
            readme_lines.append("")

    # Add features section
    if features:
        readme_lines.extend([
            "## Features",
            "",
        ])
        for feature in features:
            feature_name = feature.get('feature_name', 'Feature')
            description = feature.get('description', '')
            readme_lines.append(f"### {feature_name}")
            if description:
                readme_lines.append(f"{description}")
            readme_lines.append("")

    # Add setup instructions
    frontend = tech_stack.get('frontend', [])
    backend = tech_stack.get('backend', [])

    readme_lines.extend([
        "## Setup",
        "",
    ])

    if backend:
        readme_lines.extend([
            "### Backend",
            "```bash",
            "cd backend",
            "python -m venv .venv",
            "source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate",
            "pip install -r requirements.txt",
            "```",
            "",
        ])

    if frontend:
        readme_lines.extend([
            "### Frontend",
            "```bash",
            "cd frontend",
            "npm install",
            "npm run dev",
            "```",
            "",
        ])

    readme_lines.extend([
        "## Development",
        "",
        "Follow the implementation plan in the Technical Design Document.",
        "",
        "## License",
        "",
        "MIT",
    ])

    return '\n'.join(readme_lines) + '\n'
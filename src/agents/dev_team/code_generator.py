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

    # Pattern to match code blocks
    # Group 1: language
    # Group 2: optional file path (non-greedy, stops at newline)
    # Group 3: code content
    pattern = r'```(\w+)(?:\s+([^\n]+?))?\n(.*?)```'

    matches = re.findall(pattern, markdown_text, re.DOTALL)

    for language, file_path, code in matches:
        file_path = file_path.strip() if file_path else ""
        code = code.strip()

        # Validate file_path - it must look like a valid file path
        if file_path:
            # Remove quotes if present (e.g., 'file.tsx', "file.py")
            file_path = file_path.strip("'\"`")
            
            # Skip if file_path looks like code directives or keywords
            code_directives = [
                'use client', 'use server', 'use strict', 'use module',
                'import', 'export', 'function', 'const', 'let', 'var',
                'from', 'require', 'return', 'class', 'interface', 'type'
            ]
            
            # Check if it's a code directive (case-insensitive)
            if file_path.lower() in [d.lower() for d in code_directives]:
                file_path = ""
            
            # Skip if it contains code-like patterns
            if file_path and any(char in file_path for char in ['(', ')', '{', '}', '=', ':', ';']):
                file_path = ""
            
            # Skip if it doesn't look like a file path (missing extension or has invalid chars)
            if file_path:
                # Must have a file extension (contain a dot followed by letters/numbers)
                if not re.search(r'\.[a-zA-Z0-9]+$', file_path):
                    file_path = ""
                # Must not start with special characters
                elif file_path.startswith(('#', '//', '/*', '*', '!', '@')):
                    file_path = ""
                # Must not contain spaces (unless it's a valid path)
                elif ' ' in file_path and not ('/' in file_path or '\\' in file_path):
                    file_path = ""
                # Must not look like a comment or string literal
                elif file_path.startswith("'") or file_path.startswith('"'):
                    file_path = ""

        # If no valid file path, check for markdown header before code block
        if not file_path:
            # Look backwards from this match to find a header
            match_start = markdown_text.find(f'```{language}')
            if match_start > 0:
                # Get 200 chars before the code block
                before_block = markdown_text[max(0, match_start - 200):match_start]
                # Look for markdown headers (### app/main.py)
                header_pattern = r'#+\s+([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)\s*$'
                header_matches = re.findall(header_pattern, before_block, re.MULTILINE)
                if header_matches:
                    file_path = header_matches[-1]  # Get the last (closest) header

        # If still no file path, check first line of code for comment with filename
        if not file_path and code:
            first_line = code.split('\n')[0].strip()
            # Check for comment with filename (e.g., # app/main.py or // app/main.js)
            # But skip if it looks like a directive or normal comment
            if first_line.startswith('#') or first_line.startswith('//'):
                potential_path = first_line.lstrip('#/').strip()
                # Remove any leading path indicators
                potential_path = potential_path.lstrip('/').strip()
                
                # Validate it looks like a file path
                if potential_path and '/' in potential_path and '.' in potential_path:
                    # Check it's not a code directive
                    if potential_path.lower() not in [d.lower() for d in code_directives]:
                        # Check it doesn't contain invalid characters
                        if not any(char in potential_path for char in ['(', ')', '{', '}', '=', ':', ';', "'", '"']):
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
            file_path = file_path.strip('`').strip('"\'').strip()
            # Remove any leading slashes or dots
            file_path = file_path.lstrip('./')
            
            # Final validation - ensure it's a valid file path
            # Must have an extension
            if not re.search(r'\.[a-zA-Z0-9]+$', file_path):
                file_path = ""
            # Must not contain invalid characters for filenames
            elif any(char in file_path for char in ['<', '>', '|', ':', '?', '*']):
                file_path = ""
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
"""
Parent-Child Code Parser

This module implements advanced code parsing to extract complete functions and classes
as "Parent Documents" while generating concise summaries as "Child Chunks" for RAG retrieval.

Architecture:
- Parent Document: Full function/class definition (100-500 lines)
- Child Chunk: LLM-generated summary (50-200 chars) used for vector search
- Linking: Child chunks reference their parent via parent_id metadata

This dramatically improves RAG quality by:
1. Searching on dense, meaningful summaries
2. Retrieving complete, contextual code blocks
3. Providing LLM with full function/class context
"""

import re
from typing import List, Dict, Tuple
from langchain_core.documents import Document

def extract_python_functions_and_classes(code: str, file_metadata: Dict) -> List[Tuple[str, str, str]]:
    """
    Extract complete Python functions and classes from code.

    Args:
        code: Python source code
        file_metadata: Original file metadata

    Returns:
        List of tuples: (type, name, full_code)
        - type: "function" or "class"
        - name: Name of the function/class
        - full_code: Complete code block including docstrings
    """
    code_blocks = []

    # Regex to match Python functions with proper indentation
    function_pattern = r'^((?:async\s+)?def\s+(\w+)\s*\([^)]*\):(?:.|\n)*?)(?=\n(?:def|class|$)|\Z)'

    # Regex to match Python classes with methods
    class_pattern = r'^(class\s+(\w+)(?:\([^)]*\))?:(?:.|\n)*?)(?=\nclass\s|\ndef\s(?!    )|\Z)'

    # Extract classes
    for match in re.finditer(class_pattern, code, re.MULTILINE):
        full_code = match.group(1).strip()
        class_name = match.group(2)
        code_blocks.append(("class", class_name, full_code))

    # Extract top-level functions (not inside classes)
    lines = code.split('\n')
    current_function = []
    function_name = None
    in_function = False
    base_indent = 0

    for line in lines:
        # Detect function definition at module level (no indentation or standard indentation)
        if re.match(r'^(async\s+)?def\s+\w+\s*\(', line):
            # Save previous function if exists
            if current_function and function_name:
                code_blocks.append(("function", function_name, '\n'.join(current_function)))

            # Start new function
            current_function = [line]
            function_name = re.search(r'def\s+(\w+)\s*\(', line).group(1)
            in_function = True
            base_indent = len(line) - len(line.lstrip())

        elif in_function:
            current_line_indent = len(line) - len(line.lstrip())

            # Continue collecting function lines
            if line.strip() == '' or current_line_indent > base_indent:
                current_function.append(line)
            else:
                # Function ended
                if current_function and function_name:
                    code_blocks.append(("function", function_name, '\n'.join(current_function)))
                current_function = []
                function_name = None
                in_function = False

    # Don't forget the last function
    if current_function and function_name:
        code_blocks.append(("function", function_name, '\n'.join(current_function)))

    return code_blocks

def extract_typescript_functions_and_classes(code: str, file_metadata: Dict) -> List[Tuple[str, str, str]]:
    """
    Extract complete TypeScript/JavaScript functions, classes, and React components.

    Args:
        code: TypeScript/JavaScript source code
        file_metadata: Original file metadata

    Returns:
        List of tuples: (type, name, full_code)
    """
    code_blocks = []

    # Match class definitions
    class_pattern = r'((?:export\s+)?(?:default\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{(?:[^{}]|\{[^{}]*\})*\})'

    for match in re.finditer(class_pattern, code):
        full_code = match.group(1).strip()
        class_name = match.group(2)
        code_blocks.append(("class", class_name, full_code))

    # Match function declarations
    function_pattern = r'((?:export\s+)?(?:async\s+)?function\s+(\w+)\s*[<(][^)]*\)[^{]*\{(?:[^{}]|\{[^{}]*\})*\})'

    for match in re.finditer(function_pattern, code):
        full_code = match.group(1).strip()
        func_name = match.group(2)
        code_blocks.append(("function", func_name, full_code))

    # Match arrow function declarations
    arrow_pattern = r'((?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{(?:[^{}]|\{[^{}]*\})*\})'

    for match in re.finditer(arrow_pattern, code):
        full_code = match.group(1).strip()
        func_name = match.group(2)
        code_blocks.append(("function", func_name, full_code))

    # Match React functional components (capitalized arrow functions)
    react_component_pattern = r'((?:export\s+)?(?:default\s+)?(?:const|function)\s+([A-Z]\w+)\s*[=:]?\s*(?:\([^)]*\))?\s*(?:=>\s*)?\{(?:[^{}]|\{[^{}]*\})*\})'

    for match in re.finditer(react_component_pattern, code):
        full_code = match.group(1).strip()
        component_name = match.group(2)
        # Only add if it's a capitalized name (React component convention)
        if component_name[0].isupper():
            code_blocks.append(("component", component_name, full_code))

    return code_blocks

def extract_code_blocks_by_language(code: str, file_extension: str, file_metadata: Dict) -> List[Tuple[str, str, str]]:
    """
    Extract code blocks (functions, classes) based on file language.

    Args:
        code: Source code content
        file_extension: File extension (.py, .ts, .js, etc.)
        file_metadata: Original file metadata

    Returns:
        List of tuples: (type, name, full_code)
    """
    if file_extension == '.py':
        return extract_python_functions_and_classes(code, file_metadata)
    elif file_extension in ['.ts', '.tsx', '.js', '.jsx']:
        return extract_typescript_functions_and_classes(code, file_metadata)
    else:
        # For unsupported languages, return empty (will fall back to traditional chunking)
        return []

def generate_code_summary(code_type: str, code_name: str, code_content: str, max_length: int = 200) -> str:
    """
    Generate a simple summary for a code block without using LLM.

    This creates a concise, searchable summary based on:
    - Code structure (function/class name)
    - Parameter count and names
    - Docstring if present
    - Return types if present

    Args:
        code_type: "function", "class", or "component"
        code_name: Name of the code block
        code_content: Full code content
        max_length: Maximum summary length

    Returns:
        Summary string optimized for vector search
    """
    summary_parts = []

    # Add type and name
    summary_parts.append(f"{code_type.capitalize()}: {code_name}")

    # Extract docstring if present
    docstring_match = re.search(r'"""(.*?)"""', code_content, re.DOTALL)
    if not docstring_match:
        docstring_match = re.search(r"'''(.*?)'''", code_content, re.DOTALL)

    if docstring_match:
        docstring = docstring_match.group(1).strip()
        # Get first line of docstring
        first_line = docstring.split('\n')[0].strip()
        summary_parts.append(first_line)

    # Extract parameters for functions
    if code_type in ["function", "component"]:
        # Python function parameters
        py_params = re.search(r'def\s+\w+\s*\((.*?)\):', code_content)
        if py_params:
            params = py_params.group(1).strip()
            if params and params != 'self':
                param_names = [p.split(':')[0].strip() for p in params.split(',') if p.strip() and p.strip() != 'self']
                if param_names:
                    summary_parts.append(f"Parameters: {', '.join(param_names[:5])}")  # Max 5 params

        # TypeScript/JavaScript parameters
        ts_params = re.search(r'(?:function\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)\s*\((.*?)\)', code_content)
        if ts_params:
            params = ts_params.group(1).strip()
            if params:
                param_names = [p.split(':')[0].strip() for p in params.split(',') if p.strip()]
                if param_names:
                    summary_parts.append(f"Parameters: {', '.join(param_names[:5])}")

    # Extract return type hints
    return_match = re.search(r'->\s*([\w\[\],\s]+):', code_content)  # Python
    if return_match:
        summary_parts.append(f"Returns: {return_match.group(1).strip()}")

    # Join parts and truncate
    summary = '. '.join(summary_parts)

    if len(summary) > max_length:
        summary = summary[:max_length-3] + '...'

    return summary

def create_parent_child_documents(code: str, file_metadata: Dict, file_extension: str) -> Tuple[List[Document], List[Document]]:
    """
    Create parent-child document pairs for advanced RAG.

    Parent Documents: Complete functions/classes with full context
    Child Documents: Concise summaries for vector search

    Args:
        code: Full source code content
        file_metadata: Metadata from original file
        file_extension: File extension (.py, .ts, etc.)

    Returns:
        Tuple of (parent_documents, child_documents)
        - parent_documents: Full code blocks
        - child_documents: Summaries that reference parents via parent_id
    """
    parent_docs = []
    child_docs = []

    # Extract code blocks
    code_blocks = extract_code_blocks_by_language(code, file_extension, file_metadata)

    if not code_blocks:
        # Fall back to traditional chunking for unsupported languages
        return [], []

    # Create parent-child pairs
    for idx, (code_type, code_name, code_content) in enumerate(code_blocks):
        # Generate unique parent ID
        parent_id = f"{file_metadata.get('filename', 'unknown')}_{code_name}_{idx}"

        # Create parent document (full code)
        parent_metadata = {
            **file_metadata,
            "parent_id": parent_id,
            "code_type": code_type,
            "code_name": code_name,
            "is_parent": True,
            "lines_of_code": len(code_content.split('\n')),
        }

        parent_doc = Document(page_content=code_content, metadata=parent_metadata)
        parent_docs.append(parent_doc)

        # Create child document (summary for search)
        summary = generate_code_summary(code_type, code_name, code_content)

        child_metadata = {
            **file_metadata,
            "parent_id": parent_id,
            "code_type": code_type,
            "code_name": code_name,
            "is_child": True,
            "is_summary": True,
        }

        child_doc = Document( page_content=summary, metadata=child_metadata)
        child_docs.append(child_doc)

    return parent_docs, child_docs

if __name__ == "__main__":
    # Test the parser
    test_python_code = '''
def calculate_total(items: List[Item]) -> float:
    """Calculate the total price of all items."""
    return sum(item.price for item in items)

class ShoppingCart:
    """Manages a shopping cart with items."""

    def __init__(self):
        self.items = []

    def add_item(self, item: Item):
        """Add an item to the cart."""
        self.items.append(item)
    '''

    blocks = extract_python_functions_and_classes(test_python_code, {})
    print(f"Found {len(blocks)} code blocks:")
    for code_type, name, code in blocks:
        summary = generate_code_summary(code_type, name, code)
        print(f"\n{code_type.upper()}: {name}")
        print(f"Summary: {summary}")
        print(f"Lines: {len(code.split(chr(10)))}")
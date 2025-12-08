"""
Test Code Generator

Automatically generates unit tests, integration tests, and mock data for Python and TypeScript code.
Supports pytest for Python and Jest/Vitest for TypeScript/JavaScript.

Author: Second Brain Agent
Date: December 8, 2024
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FunctionInfo:
    """Information about a function."""
    name: str
    params: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    is_async: bool
    decorators: List[str]


@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    methods: List[FunctionInfo]
    docstring: Optional[str]
    base_classes: List[str]


@dataclass
class ModuleInfo:
    """Information about a module."""
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[str]


class PythonTestGenerator:
    """Generate pytest tests for Python code."""
    
    def __init__(self):
        self.module_info: Optional[ModuleInfo] = None
    
    def parse_python_file(self, file_path: Path) -> ModuleInfo:
        """Parse Python file and extract information."""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    func_info = self._parse_function(node)
                    functions.append(func_info)
                elif isinstance(node, ast.ClassDef):
                    class_info = self._parse_class(node)
                    classes.append(class_info)
            
            self.module_info = ModuleInfo(
                functions=functions,
                classes=classes,
                imports=list(set(imports))
            )
            
            logger.info(f"Parsed {file_path}: {len(functions)} functions, {len(classes)} classes")
            return self.module_info
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            raise
    
    def _parse_function(self, node: ast.FunctionDef) -> FunctionInfo:
        """Parse function definition."""
        params = []
        for arg in node.args.args:
            if arg.arg != 'self' and arg.arg != 'cls':
                params.append(arg.arg)
        
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)
        
        docstring = ast.get_docstring(node)
        
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)
        
        return FunctionInfo(
            name=node.name,
            params=params,
            return_type=return_type,
            docstring=docstring,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            decorators=decorators
        )
    
    def _parse_class(self, node: ast.ClassDef) -> ClassInfo:
        """Parse class definition."""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                method_info = self._parse_function(item)
                methods.append(method_info)
        
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
        
        return ClassInfo(
            name=node.name,
            methods=methods,
            docstring=ast.get_docstring(node),
            base_classes=base_classes
        )
    
    def generate_pytest_tests(self, module_path: Path, test_style: str = "standard") -> str:
        """
        Generate pytest tests for a Python module.
        
        Args:
            module_path: Path to Python module
            test_style: Test style ('standard', 'tdd', 'bdd')
        
        Returns:
            Generated test code as string
        """
        self.parse_python_file(module_path)
        
        if not self.module_info:
            raise ValueError("Module info not available")
        
        # Generate test file content
        test_code = []
        
        # Header
        test_code.append('"""')
        test_code.append(f"Unit tests for {module_path.stem}")
        test_code.append("")
        test_code.append(f"Generated by Second Brain Agent on {datetime.now().strftime('%Y-%m-%d')}")
        test_code.append('"""')
        test_code.append("")
        
        # Imports
        test_code.append("import pytest")
        test_code.append("from unittest.mock import Mock, patch, MagicMock")
        
        # Calculate relative import path
        module_import = self._get_module_import_path(module_path)
        
        # Import classes
        if self.module_info.classes:
            class_names = [cls.name for cls in self.module_info.classes]
            test_code.append(f"from {module_import} import (")
            for name in class_names:
                test_code.append(f"    {name},")
            test_code.append(")")
        
        # Import functions
        if self.module_info.functions:
            func_names = [func.name for func in self.module_info.functions]
            test_code.append(f"from {module_import} import (")
            for name in func_names:
                test_code.append(f"    {name},")
            test_code.append(")")
        
        test_code.append("")
        test_code.append("")
        
        # Generate fixtures
        test_code.extend(self._generate_fixtures())
        
        # Generate function tests
        for func in self.module_info.functions:
            test_code.extend(self._generate_function_tests(func, test_style))
        
        # Generate class tests
        for cls in self.module_info.classes:
            test_code.extend(self._generate_class_tests(cls, test_style))
        
        # Footer
        test_code.append("")
        test_code.append('if __name__ == "__main__":')
        test_code.append('    pytest.main([__file__, "-v"])')
        
        return "\n".join(test_code)
    
    def _get_module_import_path(self, module_path: Path) -> str:
        """Get the import path for a module."""
        parts = module_path.parts
        
        # Find 'src' in path
        if 'src' in parts:
            src_index = parts.index('src')
            import_parts = parts[src_index:]
            
            # Remove .py extension
            import_path = '.'.join(import_parts).replace('.py', '')
            return import_path
        
        # Fallback: use filename
        return module_path.stem
    
    def _generate_fixtures(self) -> List[str]:
        """Generate pytest fixtures."""
        fixtures = []
        
        # Add common fixtures
        fixtures.append("@pytest.fixture")
        fixtures.append("def mock_data():")
        fixtures.append('    """Provide mock data for testing."""')
        fixtures.append("    return {")
        fixtures.append('        "id": 1,')
        fixtures.append('        "name": "Test Item",')
        fixtures.append('        "value": "test_value",')
        fixtures.append('        "active": True,')
        fixtures.append("    }")
        fixtures.append("")
        fixtures.append("")
        
        return fixtures
    
    def _generate_function_tests(self, func: FunctionInfo, test_style: str) -> List[str]:
        """Generate tests for a function."""
        tests = []
        
        # Skip private functions
        if func.name.startswith('_'):
            return tests
        
        # Test class for function
        tests.append(f"class Test{func.name.title().replace('_', '')}:")
        tests.append(f'    """Test {func.name} function."""')
        tests.append("")
        
        # Basic success test
        if test_style == "bdd":
            test_name = f"test_given_valid_input_when_{func.name}_then_returns_expected_result"
        else:
            test_name = f"test_{func.name}_success"
        
        tests.append(f"    def {test_name}(self):")
        tests.append(f'        """Test {func.name} with valid input."""')
        
        # Generate function call
        if func.params:
            # Create sample parameters
            param_values = self._generate_param_values(func.params)
            param_str = ", ".join([f"{p}={v}" for p, v in param_values.items()])
            
            if func.is_async:
                tests.append("        import asyncio")
                tests.append(f"        result = asyncio.run({func.name}({param_str}))")
            else:
                tests.append(f"        result = {func.name}({param_str})")
        else:
            if func.is_async:
                tests.append("        import asyncio")
                tests.append(f"        result = asyncio.run({func.name}())")
            else:
                tests.append(f"        result = {func.name}()")
        
        tests.append("        ")
        tests.append("        # Assertions")
        tests.append("        assert result is not None")
        
        if func.return_type:
            if 'str' in func.return_type.lower():
                tests.append("        assert isinstance(result, str)")
            elif 'int' in func.return_type.lower():
                tests.append("        assert isinstance(result, int)")
            elif 'bool' in func.return_type.lower():
                tests.append("        assert isinstance(result, bool)")
            elif 'list' in func.return_type.lower():
                tests.append("        assert isinstance(result, list)")
            elif 'dict' in func.return_type.lower():
                tests.append("        assert isinstance(result, dict)")
        
        tests.append("")
        
        # Error handling test
        tests.append(f"    def test_{func.name}_invalid_input(self):")
        tests.append(f'        """Test {func.name} with invalid input."""')
        tests.append("        with pytest.raises(Exception):")
        
        if func.params:
            tests.append(f"            {func.name}(None)")
        else:
            tests.append("            # TODO: Add invalid input test")
            tests.append("            pass")
        
        tests.append("")
        tests.append("")
        
        return tests
    
    def _generate_class_tests(self, cls: ClassInfo, test_style: str) -> List[str]:
        """Generate tests for a class."""
        tests = []
        
        tests.append(f"class Test{cls.name}:")
        tests.append(f'    """Test {cls.name} class."""')
        tests.append("")
        
        # Fixture for class instance
        tests.append("    @pytest.fixture")
        tests.append("    def instance(self):")
        tests.append(f'        """Create {cls.name} instance for testing."""')
        
        # Try to determine constructor parameters
        init_method = next((m for m in cls.methods if m.name == '__init__'), None)
        if init_method and init_method.params:
            param_values = self._generate_param_values(init_method.params)
            param_str = ", ".join([f"{p}={v}" for p, v in param_values.items()])
            tests.append(f"        return {cls.name}({param_str})")
        else:
            tests.append(f"        return {cls.name}()")
        
        tests.append("")
        
        # Test initialization
        tests.append("    def test_initialization(self, instance):")
        tests.append(f'        """Test {cls.name} initialization."""')
        tests.append(f"        assert isinstance(instance, {cls.name})")
        tests.append("")
        
        # Generate tests for each public method
        for method in cls.methods:
            if not method.name.startswith('_') or method.name == '__str__' or method.name == '__repr__':
                tests.extend(self._generate_method_tests(cls.name, method, test_style))
        
        tests.append("")
        
        return tests
    
    def _generate_method_tests(self, class_name: str, method: FunctionInfo, test_style: str) -> List[str]:
        """Generate tests for a class method."""
        tests = []
        
        # Skip special methods except __str__ and __repr__
        if method.name.startswith('__') and method.name not in ['__str__', '__repr__']:
            return tests
        
        test_name = f"test_{method.name}"
        
        tests.append(f"    def {test_name}(self, instance):")
        tests.append(f'        """Test {class_name}.{method.name} method."""')
        
        # Generate method call
        if method.params:
            param_values = self._generate_param_values(method.params)
            param_str = ", ".join([f"{p}={v}" for p, v in param_values.items()])
            
            if method.is_async:
                tests.append("        import asyncio")
                tests.append(f"        result = asyncio.run(instance.{method.name}({param_str}))")
            else:
                tests.append(f"        result = instance.{method.name}({param_str})")
        else:
            if method.is_async:
                tests.append("        import asyncio")
                tests.append(f"        result = asyncio.run(instance.{method.name}())")
            else:
                tests.append(f"        result = instance.{method.name}()")
        
        tests.append("        ")
        tests.append("        # Assertions")
        tests.append("        assert result is not None")
        tests.append("")
        
        return tests
    
    def _generate_param_values(self, params: List[str]) -> Dict[str, str]:
        """Generate sample parameter values based on parameter names."""
        values = {}
        
        for param in params:
            param_lower = param.lower()
            
            # String parameters
            if any(word in param_lower for word in ['name', 'title', 'text', 'description', 'message']):
                values[param] = f'"test_{param}"'
            # ID parameters
            elif any(word in param_lower for word in ['id', 'key']):
                values[param] = '1'
            # Boolean parameters
            elif any(word in param_lower for word in ['is_', 'has_', 'should_', 'enabled', 'active']):
                values[param] = 'True'
            # Number parameters
            elif any(word in param_lower for word in ['count', 'number', 'amount', 'size', 'length']):
                values[param] = '10'
            # Path parameters
            elif any(word in param_lower for word in ['path', 'file', 'directory', 'folder']):
                values[param] = 'Path("test.txt")'
            # List parameters
            elif any(word in param_lower for word in ['list', 'items', 'array']):
                values[param] = '[]'
            # Dict parameters
            elif any(word in param_lower for word in ['dict', 'config', 'options', 'params']):
                values[param] = '{}'
            # Default
            else:
                values[param] = '"test_value"'
        
        return values


class TypeScriptTestGenerator:
    """Generate Jest/Vitest tests for TypeScript/JavaScript code."""
    
    def generate_jest_tests(self, file_path: Path) -> str:
        """
        Generate Jest tests for TypeScript/JavaScript file.
        
        Args:
            file_path: Path to TypeScript/JavaScript file
        
        Returns:
            Generated test code as string
        """
        content = file_path.read_text(encoding='utf-8')
        
        # Parse exports (simple regex-based approach)
        functions = self._parse_ts_functions(content)
        classes = self._parse_ts_classes(content)
        
        test_code = []
        
        # Header
        test_code.append("/**")
        test_code.append(f" * Unit tests for {file_path.stem}")
        test_code.append(" *")
        test_code.append(f" * Generated by Second Brain Agent on {datetime.now().strftime('%Y-%m-%d')}")
        test_code.append(" */")
        test_code.append("")
        
        # Imports
        file_name = file_path.stem
        if functions:
            func_names = ", ".join(functions)
            test_code.append(f"import {{ {func_names} }} from './{file_name}';")
        if classes:
            class_names = ", ".join(classes)
            test_code.append(f"import {{ {class_names} }} from './{file_name}';")
        
        test_code.append("")
        
        # Generate function tests
        for func in functions:
            test_code.extend(self._generate_ts_function_tests(func))
        
        # Generate class tests
        for cls in classes:
            test_code.extend(self._generate_ts_class_tests(cls))
        
        return "\n".join(test_code)
    
    def _parse_ts_functions(self, content: str) -> List[str]:
        """Parse TypeScript/JavaScript functions."""
        functions = []
        
        # Match exported functions
        patterns = [
            r'export\s+(?:async\s+)?function\s+(\w+)',
            r'export\s+const\s+(\w+)\s*=\s*(?:async\s*)?\(',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                functions.append(match.group(1))
        
        return functions
    
    def _parse_ts_classes(self, content: str) -> List[str]:
        """Parse TypeScript/JavaScript classes."""
        classes = []
        
        # Match exported classes
        pattern = r'export\s+class\s+(\w+)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            classes.append(match.group(1))
        
        return classes
    
    def _generate_ts_function_tests(self, func_name: str) -> List[str]:
        """Generate Jest tests for a TypeScript function."""
        tests = []
        
        tests.append(f"describe('{func_name}', () => {{")
        tests.append("  test('should work with valid input', () => {{")
        tests.append(f"    const result = {func_name}('test');")
        tests.append("    expect(result).toBeDefined();")
        tests.append("  });")
        tests.append("")
        tests.append("  test('should handle invalid input', () => {{")
        tests.append(f"    expect(() => {func_name}(null)).toThrow();")
        tests.append("  });")
        tests.append("});")
        tests.append("")
        
        return tests
    
    def _generate_ts_class_tests(self, class_name: str) -> List[str]:
        """Generate Jest tests for a TypeScript class."""
        tests = []
        
        tests.append(f"describe('{class_name}', () => {{")
        tests.append(f"  let instance: {class_name};")
        tests.append("")
        tests.append("  beforeEach(() => {")
        tests.append(f"    instance = new {class_name}();")
        tests.append("  });")
        tests.append("")
        tests.append("  test('should be instantiated', () => {")
        tests.append("    expect(instance).toBeInstanceOf(" + class_name + ");")
        tests.append("  });")
        tests.append("});")
        tests.append("")
        
        return tests


class MockDataGenerator:
    """Generate mock data for tests."""
    
    @staticmethod
    def generate_mock_user() -> str:
        """Generate mock user data."""
        return '''def mock_user():
    """Generate mock user data."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "created_at": datetime.now().isoformat(),
    }'''
    
    @staticmethod
    def generate_mock_api_response() -> str:
        """Generate mock API response."""
        return '''def mock_api_response():
    """Generate mock API response."""
    return {
        "status": "success",
        "data": {"id": 1, "name": "Test Item"},
        "message": "Operation successful",
        "timestamp": datetime.now().isoformat(),
    }'''
    
    @staticmethod
    def generate_mock_database_record() -> str:
        """Generate mock database record."""
        return '''def mock_database_record():
    """Generate mock database record."""
    from unittest.mock import MagicMock
    
    record = MagicMock()
    record.id = 1
    record.name = "Test Record"
    record.created_at = datetime.now()
    return record'''


class TestGenerator:
    """Main test generator class."""
    
    def __init__(self):
        self.python_generator = PythonTestGenerator()
        self.ts_generator = TypeScriptTestGenerator()
        self.mock_generator = MockDataGenerator()
    
    def generate_tests(
        self,
        file_path: Path,
        test_type: str = "unit",
        test_style: str = "standard",
        include_mocks: bool = True
    ) -> str:
        """
        Generate tests for a file.
        
        Args:
            file_path: Path to source file
            test_type: Type of tests ('unit', 'integration', 'e2e')
            test_style: Test style ('standard', 'tdd', 'bdd')
            include_mocks: Whether to include mock data generators
        
        Returns:
            Generated test code
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type
        suffix = file_path.suffix.lower()
        
        if suffix == '.py':
            test_code = self.python_generator.generate_pytest_tests(file_path, test_style)
        elif suffix in ['.ts', '.tsx', '.js', '.jsx']:
            test_code = self.ts_generator.generate_jest_tests(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
        
        logger.info(f"Generated {test_type} tests for {file_path}")
        return test_code
    
    def save_tests(
        self,
        source_file: Path,
        output_dir: Optional[Path] = None,
        test_type: str = "unit",
        test_style: str = "standard"
    ) -> Path:
        """
        Generate and save tests to file.
        
        Args:
            source_file: Path to source file
            output_dir: Output directory for tests (default: tests/unit/)
            test_type: Type of tests
            test_style: Test style
        
        Returns:
            Path to generated test file
        """
        # Generate tests
        test_code = self.generate_tests(source_file, test_type, test_style)
        
        # Determine output path
        if output_dir is None:
            output_dir = Path.cwd() / "tests" / test_type
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine test filename
        if source_file.suffix == '.py':
            test_filename = f"test_{source_file.stem}.py"
        else:
            test_filename = f"{source_file.stem}.test{source_file.suffix}"
        
        test_file = output_dir / test_filename
        
        # Write test file
        test_file.write_text(test_code, encoding='utf-8')
        
        logger.info(f"Test file saved: {test_file}")
        return test_file


# Convenience function
def generate_tests(
    file_path: Path,
    output_dir: Optional[Path] = None,
    test_type: str = "unit",
    test_style: str = "standard"
) -> Path:
    """
    Generate tests for a file.
    
    Args:
        file_path: Path to source file
        output_dir: Output directory for tests
        test_type: Type of tests ('unit', 'integration', 'e2e')
        test_style: Test style ('standard', 'tdd', 'bdd')
    
    Returns:
        Path to generated test file
    """
    generator = TestGenerator()
    return generator.save_tests(file_path, output_dir, test_type, test_style)

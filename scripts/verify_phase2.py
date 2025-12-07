#!/usr/bin/env python3
"""
Phase 2 Setup Verification Script
Checks that all Phase 2 features are properly installed and working.
"""

import sys
from pathlib import Path
from typing import Tuple


def print_header(text: str):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def check_module(module_name: str, import_statement: str) -> Tuple[bool, str]:
    """
    Check if a module can be imported.
    
    Returns:
        (success, error_message)
    """
    try:
        exec(import_statement)
        return True, ""
    except Exception as e:
        return False, str(e)


def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    return file_path.exists()


def main():
    """Run all verification checks."""
    print_header("Phase 2 Setup Verification")
    
    all_checks_passed = True
    
    # ========================================================================
    # Check Python Version
    # ========================================================================
    print("📌 Checking Python version...")
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"   ✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"   ✗ Python {python_version.major}.{python_version.minor} (requires 3.8+)")
        all_checks_passed = False
    
    # ========================================================================
    # Check Dependencies
    # ========================================================================
    print("\n📌 Checking Phase 2 dependencies...")
    
    dependencies = [
        ("Typer", "import typer"),
        ("Rich", "import rich"),
        ("Pydantic Settings", "from pydantic_settings import BaseSettings"),
        ("Pydantic", "import pydantic"),
    ]
    
    for name, import_stmt in dependencies:
        success, error = check_module(name, import_stmt)
        if success:
            print(f"   ✓ {name}")
        else:
            print(f"   ✗ {name}: {error}")
            all_checks_passed = False
    
    # ========================================================================
    # Check Phase 2 Modules
    # ========================================================================
    print("\n📌 Checking Phase 2 modules...")
    
    modules = [
        ("CLI Main", "from src.cli.main import app"),
        ("Output Manager", "from src.utils.output_manager import OutputManager"),
        ("Settings", "from src.core.settings import settings"),
        ("Progress", "from src.utils.progress import ProjectProgress"),
    ]
    
    for name, import_stmt in modules:
        success, error = check_module(name, import_stmt)
        if success:
            print(f"   ✓ {name}")
        else:
            print(f"   ✗ {name}: {error}")
            all_checks_passed = False
    
    # ========================================================================
    # Check File Structure
    # ========================================================================
    print("\n📌 Checking file structure...")
    
    required_files = [
        Path("src/cli/__init__.py"),
        Path("src/cli/main.py"),
        Path("src/utils/output_manager.py"),
        Path("src/core/settings.py"),
        Path("src/utils/progress.py"),
        Path("docs/PHASE2_EXAMPLES.md"),
        Path("docs/PHASE2_SUMMARY.md"),
    ]
    
    for file_path in required_files:
        if check_file_exists(file_path):
            print(f"   ✓ {file_path}")
        else:
            print(f"   ✗ {file_path} (missing)")
            all_checks_passed = False
    
    # ========================================================================
    # Test CLI Commands
    # ========================================================================
    print("\n📌 Testing CLI functionality...")
    
    try:
        from src.cli.main import app
        print("   ✓ CLI app created successfully")
        
        # Check if commands are registered
        commands = [cmd.name for cmd in app.registered_commands]
        expected_commands = ['architect', 'dev-team', 'version', 'info']
        
        for cmd in expected_commands:
            if cmd in commands:
                print(f"   ✓ Command '{cmd}' registered")
            else:
                print(f"   ✗ Command '{cmd}' not found")
                all_checks_passed = False
    except Exception as e:
        print(f"   ✗ CLI initialization failed: {e}")
        all_checks_passed = False
    
    # ========================================================================
    # Test Settings
    # ========================================================================
    print("\n📌 Testing configuration...")
    
    try:
        from src.core.settings import settings
        
        # Test basic settings
        print(f"   ✓ Default model: {settings.default_model}")
        print(f"   ✓ Max tokens: {settings.max_tokens}")
        print(f"   ✓ Output dir: {settings.output_dir}")
        
        # Test methods
        config = settings.get_model_config()
        print("   ✓ Model config retrieved")
        
    except Exception as e:
        print(f"   ✗ Settings test failed: {e}")
        all_checks_passed = False
    
    # ========================================================================
    # Test Output Manager
    # ========================================================================
    print("\n📌 Testing output manager...")
    
    try:
        from src.utils.output_manager import OutputManager
        
        manager = OutputManager(base_dir=Path("./test_output"))
        print("   ✓ OutputManager initialized")
        
        # Clean up test directory
        import shutil
        if Path("./test_output").exists():
            shutil.rmtree("./test_output")
        
    except Exception as e:
        print(f"   ✗ Output manager test failed: {e}")
        all_checks_passed = False
    
    # ========================================================================
    # Test Progress
    # ========================================================================
    print("\n Testing progress tracking...")
    
    try:
        from src.utils.progress import ProjectProgress
        
        progress = ProjectProgress("Test")
        print("   ✓ ProjectProgress initialized")
        
    except Exception as e:
        print(f"   ✗ Progress test failed: {e}")
        all_checks_passed = False
    
    # ========================================================================
    # Final Summary
    # ========================================================================
    print_header("Verification Summary")
    
    if all_checks_passed:
        print("✅ All checks passed! Phase 2 is ready to use.\n")
        print("Next steps:")
        print("  1. Try the CLI: sba --help")
        print("  2. Run a demo: make demo-architect")
        print("  3. Check examples: cat docs/PHASE2_EXAMPLES.md")
        print()
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.\n")
        print("Common fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Reinstall package: pip install -e .")
        print("  3. Check Python version: python --version (requires 3.8+)")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

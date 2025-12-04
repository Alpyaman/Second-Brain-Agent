"""
Development Team Agent - TDD to Working Code

This module provides the Rapid Prototyper functionality that transforms
Technical Design Documents into actual working code files.
"""

# Lazy imports to avoid dependency issues
def __getattr__(name):
    # Main execution functions
    if name == 'run_dev_team':
        from src.agents.dev_team.graph import run_dev_team
        return run_dev_team
    elif name == 'run_dev_team_v2':
        from src.agents.dev_team.graph import run_dev_team_v2
        return run_dev_team_v2
    elif name == 'create_dev_team_graph':
        from src.agents.dev_team.graph import create_dev_team_graph
        return create_dev_team_graph
    elif name == 'create_dev_team_graph_v2':
        from src.agents.dev_team.graph import create_dev_team_graph_v2
        return create_dev_team_graph_v2
    # State
    elif name == 'DevTeamState':
        from src.agents.dev_team.state import DevTeamState
        return DevTeamState
    # TDD parsing
    elif name == 'parse_tdd_to_state':
        from src.agents.dev_team.parsers import parse_tdd_to_state
        return parse_tdd_to_state
    elif name == 'extract_technology_stack':
        from src.agents.dev_team.parsers import extract_technology_stack
        return extract_technology_stack
    elif name == 'extract_api_endpoints':
        from src.agents.dev_team.parsers import extract_api_endpoints
        return extract_api_endpoints
    elif name == 'extract_data_model':
        from src.agents.dev_team.parsers import extract_data_model
        return extract_data_model
    elif name == 'extract_features_to_implement':
        from src.agents.dev_team.parsers import extract_features_to_implement
        return extract_features_to_implement
    # Code generation
    elif name == 'extract_code_blocks':
        from src.agents.dev_team.code_generator import extract_code_blocks
        return extract_code_blocks
    elif name == 'extract_file_structure':
        from src.agents.dev_team.code_generator import extract_file_structure
        return extract_file_structure
    elif name == 'generate_gitignore':
        from src.agents.dev_team.code_generator import generate_gitignore
        return generate_gitignore
    elif name == 'generate_readme':
        from src.agents.dev_team.code_generator import generate_readme
        return generate_readme
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Main execution functions
    'run_dev_team',
    'run_dev_team_v2',
    'create_dev_team_graph',
    'create_dev_team_graph_v2',
    # State
    'DevTeamState',
    # TDD parsing
    'parse_tdd_to_state',
    'extract_technology_stack',
    'extract_api_endpoints',
    'extract_data_model',
    'extract_features_to_implement',
    # Code generation
    'extract_code_blocks',
    'extract_file_structure',
    'generate_gitignore',
    'generate_readme'
]
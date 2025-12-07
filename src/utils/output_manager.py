"""
Output Management System for Second Brain Agent.
Handles organized file generation and project structure creation.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import json

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class OutputManager:
    """
    Manages output generation with organized directory structures.
    
    Features:
    - Timestamped project directories
    - Structured file organization
    - Template-based generation
    - Metadata tracking
    """
    
    def __init__(self, base_dir: Path = Path("./output")):
        """
        Initialize output manager.
        
        Args:
            base_dir: Base directory for all outputs
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"OutputManager initialized with base_dir: {self.base_dir}")
    
    def create_project_dir(
        self,
        project_name: str,
        use_timestamp: bool = True,
    ) -> Path:
        """
        Create a new project directory with optional timestamp.
        
        Args:
            project_name: Name of the project
            use_timestamp: Whether to append timestamp to directory name
            
        Returns:
            Path to created project directory
        """
        if use_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dir_name = f"{project_name}_{timestamp}"
        else:
            dir_name = project_name
        
        project_dir = self.base_dir / dir_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created project directory: {project_dir}")
        return project_dir
    
    def save_structured_output(
        self,
        project_dir: Path,
        state: Dict,
        include_docker: bool = True,
        include_tests: bool = True,
    ) -> Dict[str, Path]:
        """
        Save output in organized structure with all necessary files.
        
        Args:
            project_dir: Project directory to save to
            state: State dictionary from agent execution
            include_docker: Whether to include Docker configuration
            include_tests: Whether to include test structure
            
        Returns:
            Dictionary mapping component names to their paths
        """
        created_files = {}
        
        # Create directory structure
        backend_dir = project_dir / "backend"
        frontend_dir = project_dir / "frontend"
        docs_dir = project_dir / "docs"
        
        for directory in [backend_dir, frontend_dir, docs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Backend structure
        backend_src = backend_dir / "src"
        backend_src.mkdir(exist_ok=True)
        
        backend_code_file = backend_src / "main.py"
        backend_code_file.write_text(
            state.get('backend_code', '# Backend code placeholder'),
            encoding='utf-8'
        )
        created_files['backend_code'] = backend_code_file
        
        # Backend requirements
        backend_requirements = backend_dir / "requirements.txt"
        backend_requirements.write_text(
            self._generate_backend_requirements(state),
            encoding='utf-8'
        )
        created_files['backend_requirements'] = backend_requirements
        
        # Frontend structure
        frontend_src = frontend_dir / "src"
        frontend_src.mkdir(exist_ok=True)
        
        frontend_code_file = frontend_src / "App.tsx"
        frontend_code_file.write_text(
            state.get('frontend_code', '// Frontend code placeholder'),
            encoding='utf-8'
        )
        created_files['frontend_code'] = frontend_code_file
        
        # Frontend package.json
        frontend_package = frontend_dir / "package.json"
        frontend_package.write_text(
            self._generate_package_json(state),
            encoding='utf-8'
        )
        created_files['frontend_package'] = frontend_package
        
        # Documentation
        design_doc = docs_dir / "DESIGN.md"
        design_doc.write_text(
            state.get('design_document', '# Design Document'),
            encoding='utf-8'
        )
        created_files['design_doc'] = design_doc
        
        # Architecture document
        arch_doc = docs_dir / "ARCHITECTURE.md"
        arch_doc.write_text(
            self._generate_architecture_doc(state),
            encoding='utf-8'
        )
        created_files['architecture_doc'] = arch_doc
        
        # API documentation
        api_doc = docs_dir / "API.md"
        api_doc.write_text(
            self._generate_api_doc(state),
            encoding='utf-8'
        )
        created_files['api_doc'] = api_doc
        
        # Docker configuration
        if include_docker:
            docker_compose = project_dir / "docker-compose.yml"
            docker_compose.write_text(
                self._generate_docker_compose(state),
                encoding='utf-8'
            )
            created_files['docker_compose'] = docker_compose
            
            # Backend Dockerfile
            backend_dockerfile = backend_dir / "Dockerfile"
            backend_dockerfile.write_text(
                self._generate_backend_dockerfile(state),
                encoding='utf-8'
            )
            created_files['backend_dockerfile'] = backend_dockerfile
            
            # Frontend Dockerfile
            frontend_dockerfile = frontend_dir / "Dockerfile"
            frontend_dockerfile.write_text(
                self._generate_frontend_dockerfile(state),
                encoding='utf-8'
            )
            created_files['frontend_dockerfile'] = frontend_dockerfile
        
        # Tests structure
        if include_tests:
            backend_tests = backend_dir / "tests"
            backend_tests.mkdir(exist_ok=True)
            
            test_file = backend_tests / "test_api.py"
            test_file.write_text(
                self._generate_test_template(state),
                encoding='utf-8'
            )
            created_files['backend_tests'] = test_file
        
        # Project README
        readme = project_dir / "README.md"
        readme.write_text(
            self._generate_readme(state, project_dir.name),
            encoding='utf-8'
        )
        created_files['readme'] = readme
        
        # .gitignore
        gitignore = project_dir / ".gitignore"
        gitignore.write_text(
            self._generate_gitignore(),
            encoding='utf-8'
        )
        created_files['gitignore'] = gitignore
        
        # Save metadata
        metadata = {
            'created_at': datetime.now().isoformat(),
            'project_name': project_dir.name,
            'components': list(created_files.keys()),
            'state_summary': {
                'iteration_count': state.get('iteration_count', 1),
                'review_status': state.get('review_status', 'pending'),
            }
        }
        
        metadata_file = project_dir / ".sba_metadata.json"
        metadata_file.write_text(
            json.dumps(metadata, indent=2),
            encoding='utf-8'
        )
        created_files['metadata'] = metadata_file
        
        logger.info(f"Saved {len(created_files)} files to {project_dir}")
        return created_files
    
    def _generate_backend_requirements(self, state: Dict) -> str:
        """Generate backend requirements.txt based on framework."""
        framework = state.get('backend_framework', 'fastapi').lower()
        
        if 'fastapi' in framework:
            return """fastapi==0.104.1
            uvicorn[standard]==0.24.0
            pydantic==2.5.0
            sqlalchemy==2.0.23
            alembic==1.12.1
            python-jose[cryptography]==3.3.0
            passlib[bcrypt]==1.7.4
            python-multipart==0.0.6
            """
        elif 'django' in framework:
            return """Django==4.2.7
            djangorestframework==3.14.0
            django-cors-headers==4.3.1
            psycopg2-binary==2.9.9
            python-dotenv==1.0.0
            """
        else:
            return """flask==3.0.0
            flask-cors==4.0.0
            flask-sqlalchemy==3.1.1
            python-dotenv==1.0.0
            """
    
    def _generate_package_json(self, state: Dict) -> str:
        """Generate frontend package.json."""
        framework = state.get('frontend_framework', 'react').lower()
        
        if 'nextjs' in framework:
            return """{
            "name": "frontend",
            "version": "0.1.0",
            "private": true,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": {
                "next": "14.0.3",
                "react": "^18",
                "react-dom": "^18",
                "axios": "^1.6.2"
            },
            "devDependencies": {
                "@types/node": "^20",
                "@types/react": "^18",
                "@types/react-dom": "^18",
                "typescript": "^5"
            }
            }
            """
        else:
            return """{
            "name": "frontend",
            "version": "0.1.0",
            "private": true,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1",
                "axios": "^1.6.2",
                "typescript": "^4.9.5"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            }
            }
            """
    
    def _generate_docker_compose(self, state: Dict) -> str:
        """Generate docker-compose.yml."""
        return """version: '3.8'

        services:
        backend:
            build: ./backend
            ports:
            - "8000:8000"
            environment:
            - DATABASE_URL=postgresql://user:password@db:5432/appdb
            depends_on:
            - db
            volumes:
            - ./backend:/app
            command: uvicorn src.main:app --host 0.0.0.0 --reload

        frontend:
            build: ./frontend
            ports:
            - "3000:3000"
            environment:
            - REACT_APP_API_URL=http://localhost:8000
            volumes:
            - ./frontend:/app
            - /app/node_modules
            command: npm start

        db:
            image: postgres:15-alpine
            environment:
            - POSTGRES_USER=user
            - POSTGRES_PASSWORD=password
            - POSTGRES_DB=appdb
            ports:
            - "5432:5432"
            volumes:
            - postgres_data:/var/lib/postgresql/data

        volumes:
        postgres_data:
        """
    
    def _generate_backend_dockerfile(self, state: Dict) -> str:
        """Generate backend Dockerfile."""
        return """FROM python:3.11-slim

        WORKDIR /app

        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt

        COPY . .

        EXPOSE 8000

        CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
        """
            
    def _generate_frontend_dockerfile(self, state: Dict) -> str:
        """Generate frontend Dockerfile."""
        return """FROM node:18-alpine

        WORKDIR /app

        COPY package*.json ./
        RUN npm install

        COPY . .

        EXPOSE 3000

        CMD ["npm", "start"]
        """
    
    def _generate_architecture_doc(self, state: Dict) -> str:
        """Generate architecture documentation."""
        return f"""# Architecture Documentation

        ## Overview
        This document describes the system architecture.

        ## System Components

        ### Backend
        - Framework: {state.get('backend_framework', 'FastAPI')}
        - Database: PostgreSQL
        - Authentication: JWT

        ### Frontend  
        - Framework: {state.get('frontend_framework', 'React')}
        - State Management: Context API
        - Styling: Tailwind CSS

        ### Infrastructure
        - Containerization: Docker
        - Orchestration: Docker Compose
        - Database: PostgreSQL 15

        ## Data Flow

        1. User interacts with Frontend (React)
        2. Frontend makes API calls to Backend (FastAPI)
        3. Backend processes requests and queries Database
        4. Responses flow back through the same chain

        ## Security Considerations

        - JWT-based authentication
        - CORS configuration
        - Environment variable management
        - SQL injection prevention via ORM

        ## Deployment

        See docker-compose.yml for local deployment.
        For production, consider:
        - Using managed database service
        - Setting up reverse proxy (nginx)
        - Implementing CI/CD pipeline
        """
    
    def _generate_api_doc(self, state: Dict) -> str:
        """Generate API documentation."""
        return """# API Documentation

        ## Base URL
        ```
        http://localhost:8000/api/v1
        ```

        ## Authentication
        All authenticated endpoints require JWT token in header:
        ```
        Authorization: Bearer <token>
        ```

        ## Endpoints

        ### Authentication

        #### POST /auth/register
        Register a new user.

        **Request:**
        ```json
        {
        "email": "user@example.com",
        "password": "securepassword"
        }
        ```

        **Response:**
        ```json
        {
        "id": 1,
        "email": "user@example.com",
        "created_at": "2024-01-01T00:00:00Z"
        }
        ```

        #### POST /auth/login
        Login and get access token.

        **Request:**
        ```json
        {
        "email": "user@example.com",
        "password": "securepassword"
        }
        ```

        **Response:**
        ```json
        {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "token_type": "bearer"
        }
        ```

        ## Error Responses

        All errors follow this format:
        ```json
        {
        "detail": "Error message here"
        }
        ```

        ### Status Codes
        - 200: Success
        - 201: Created
        - 400: Bad Request
        - 401: Unauthorized
        - 404: Not Found
        - 500: Internal Server Error
        """
    
    def _generate_test_template(self, state: Dict) -> str:
        """Generate test template."""
        return """import pytest
        from fastapi.testclient import TestClient
        from src.main import app

        client = TestClient(app)


        def test_health_check():
            \"\"\"Test health check endpoint.\"\"\"
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}


        def test_create_item():
            \"\"\"Test item creation.\"\"\"
            response = client.post(
                "/api/v1/items",
                json={"name": "Test Item", "description": "Test Description"}
            )
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Item"
        """
    
    def _generate_readme(self, state: Dict, project_name: str) -> str:
        """Generate project README."""
        return f"""# {project_name}

        Generated by Second Brain Agent

        ## Overview
        This project was automatically generated from a job description using AI-powered multi-agent system.

        ## Quick Start

        ### Prerequisites
        - Docker & Docker Compose
        - Node.js 18+ (for local development)
        - Python 3.11+ (for local development)

        ### Running with Docker (Recommended)

        1. Start all services:
        ```bash
        docker-compose up
        ```

        2. Access the application:
        - Frontend: http://localhost:3000
        - Backend API: http://localhost:8000
        - API Docs: http://localhost:8000/docs

        ### Local Development

        #### Backend
        ```bash
        cd backend
        pip install -r requirements.txt
        uvicorn src.main:app --reload
        ```

        #### Frontend
        ```bash
        cd frontend
        npm install
        npm start
        ```

        ## Project Structure

        ```
        .
        ├── backend/          # FastAPI backend
        │   ├── src/         # Source code
        │   ├── tests/       # Unit tests
        │   └── Dockerfile
        ├── frontend/         # React frontend
        │   ├── src/         # Source code
        │   └── Dockerfile
        ├── docs/            # Documentation
        │   ├── DESIGN.md
        │   ├── ARCHITECTURE.md
        │   └── API.md
        └── docker-compose.yml
        ```

        ## Documentation

        - [Design Document](docs/DESIGN.md)
        - [Architecture](docs/ARCHITECTURE.md)
        - [API Reference](docs/API.md)

        ## Testing

        ### Backend Tests
        ```bash
        cd backend
        pytest
        ```

        ### Frontend Tests
        ```bash
        cd frontend
        npm test
        ```

        ## Generated By
        - Tool: Second Brain Agent
        - Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
        - Iteration: {state.get('iteration_count', 1)}

        ## Next Steps

        1. Review the generated code
        2. Customize configuration (environment variables)
        3. Add business logic
        4. Implement additional features
        5. Deploy to production

        ## License
        See LICENSE file for details.
        """
            
    def _generate_gitignore(self) -> str:
        """Generate .gitignore file."""
        return """# Python
        __pycache__/
        *.py[cod]
        *$py.class
        *.so
        .Python
        env/
        venv/
        .venv/
        *.egg-info/
        dist/
        build/

        # Node
        node_modules/
        npm-debug.log*
        yarn-debug.log*
        yarn-error.log*
        .pnpm-debug.log*

        # Environment
        .env
        .env.local
        .env.*.local

        # IDEs
        .vscode/
        .idea/
        *.swp
        *.swo
        *~

        # OS
        .DS_Store
        Thumbs.db

        # Database
        *.db
        *.sqlite
        *.sqlite3

        # Logs
        logs/
        *.log

        # Build
        dist/
        build/
        .next/
        out/

        # Testing
        .coverage
        htmlcov/
        .pytest_cache/
        coverage/

        # Docker
        .dockerignore
        """


def create_project_output(
    project_name: str,
    state: Dict,
    output_dir: Optional[Path] = None,
    **kwargs
) -> Path:
    """
    Convenience function to create complete project output.
    
    Args:
        project_name: Name of the project
        state: State dictionary from agent execution
        output_dir: Optional custom output directory
        **kwargs: Additional options for OutputManager
        
    Returns:
        Path to created project directory
    """
    manager = OutputManager(output_dir or Path("./output"))
    project_dir = manager.create_project_dir(project_name)
    manager.save_structured_output(project_dir, state, **kwargs)
    
    logger.info(f"Project created successfully: {project_dir}")
    return project_dir

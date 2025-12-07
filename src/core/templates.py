"""
Project Template System for Second Brain Agent.
Provides pre-built templates for common project types.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ProjectTemplate:
    """Represents a project template."""
    name: str
    description: str
    category: str
    tech_stack: Dict[str, str]
    features: List[str]
    job_description: str
    tdd_template: str
    
    def to_dict(self) -> Dict:
        """Convert template to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tech_stack": self.tech_stack,
            "features": self.features
        }


# ============================================================================
# Template Definitions
# ============================================================================

TEMPLATES = {
    "rest-api": ProjectTemplate(
        name="REST API",
        description="RESTful API with FastAPI and PostgreSQL",
        category="backend",
        tech_stack={
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "orm": "SQLAlchemy",
            "auth": "JWT"
        },
        features=[
            "User authentication",
            "CRUD operations",
            "Database migrations",
            "API documentation (OpenAPI)",
            "Error handling",
            "Logging"
        ],
        job_description="""
        Build a RESTful API with the following features:
        - User authentication and authorization using JWT tokens
        - CRUD operations for main resources
        - PostgreSQL database with SQLAlchemy ORM
        - Input validation and error handling
        - API documentation with OpenAPI/Swagger
        - Logging and monitoring
        - Docker containerization
        """,
        tdd_template="""
        # Technical Design Document: REST API
        
        ## Architecture
        RESTful API built with FastAPI framework
        
        ## Components
        1. Authentication Service - JWT-based user authentication
        2. Resource Manager - CRUD operations for resources
        3. Database Layer - PostgreSQL with SQLAlchemy
        4. API Gateway - Request routing and validation
        
        ## API Endpoints
        - POST /api/auth/register - User registration
        - POST /api/auth/login - User login
        - GET /api/resources - List resources
        - POST /api/resources - Create resource
        - GET /api/resources/{id} - Get resource
        - PUT /api/resources/{id} - Update resource
        - DELETE /api/resources/{id} - Delete resource
        
        ## Database Schema
        - users table: id, username, email, password_hash
        - resources table: id, name, description, user_id, created_at
        
        ## Tech Stack
        - Backend: FastAPI 0.100+
        - Database: PostgreSQL 15+
        - ORM: SQLAlchemy 2.0+
        - Auth: python-jose, passlib
        """
    ),
    
    "fullstack-webapp": ProjectTemplate(
        name="Fullstack Web App",
        description="Complete web application with React frontend and FastAPI backend",
        category="fullstack",
        tech_stack={
            "frontend": "React + TypeScript",
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "styling": "Tailwind CSS"
        },
        features=[
            "React SPA frontend",
            "FastAPI REST backend",
            "PostgreSQL database",
            "User authentication",
            "Responsive design",
            "Real-time updates"
        ],
        job_description="""
        Build a fullstack web application with:
        - React frontend with TypeScript and Tailwind CSS
        - FastAPI backend with PostgreSQL database
        - User authentication and session management
        - Responsive design for mobile and desktop
        - Real-time data updates
        - Docker compose for development
        """,
        tdd_template="""
        # Technical Design Document: Fullstack Web App
        
        ## Architecture
        Three-tier architecture: Frontend (React) + Backend (FastAPI) + Database (PostgreSQL)
        
        ## Frontend Components
        1. Authentication pages (Login, Register)
        2. Dashboard with data visualization
        3. Resource management interface
        4. User profile management
        
        ## Backend API
        - Authentication endpoints
        - Resource CRUD endpoints
        - WebSocket for real-time updates
        
        ## Tech Stack
        - Frontend: React 18+, TypeScript, Tailwind CSS, Axios
        - Backend: FastAPI, SQLAlchemy, python-jose
        - Database: PostgreSQL 15+
        """
    ),
    
    "microservice": ProjectTemplate(
        name="Microservice",
        description="Microservice with gRPC communication",
        category="backend",
        tech_stack={
            "framework": "FastAPI",
            "communication": "gRPC",
            "database": "MongoDB",
            "messaging": "RabbitMQ"
        },
        features=[
            "gRPC service definitions",
            "Event-driven architecture",
            "Message queue integration",
            "Service discovery",
            "Health checks",
            "Metrics and monitoring"
        ],
        job_description="""
        Build a microservice with:
        - gRPC API for service-to-service communication
        - Event-driven architecture with message queues
        - MongoDB for data persistence
        - Health check endpoints
        - Prometheus metrics
        - Docker containerization with health checks
        """,
        tdd_template="""
        # Technical Design Document: Microservice
        
        ## Architecture
        Microservice architecture with gRPC and event-driven patterns
        
        ## Service Definition
        - gRPC service methods
        - Message schemas
        - Health check interface
        
        ## Tech Stack
        - Framework: FastAPI + grpcio
        - Database: MongoDB
        - Messaging: RabbitMQ/Redis
        - Monitoring: Prometheus
        """
    ),
    
    "graphql-api": ProjectTemplate(
        name="GraphQL API",
        description="GraphQL API with Strawberry",
        category="backend",
        tech_stack={
            "framework": "Strawberry GraphQL",
            "database": "PostgreSQL",
            "orm": "SQLAlchemy"
        },
        features=[
            "GraphQL schema",
            "Query and mutation resolvers",
            "DataLoader for N+1 prevention",
            "Subscriptions for real-time",
            "Authentication",
            "GraphiQL playground"
        ],
        job_description="""
        Build a GraphQL API with:
        - Strawberry GraphQL framework
        - Query, mutation, and subscription support
        - DataLoader for efficient data fetching
        - JWT authentication
        - GraphiQL interface
        - PostgreSQL database
        """,
        tdd_template="""
        # Technical Design Document: GraphQL API
        
        ## Architecture
        GraphQL API with Strawberry framework
        
        ## Schema
        - Types, Queries, Mutations, Subscriptions
        - Input types and validation
        - Custom scalars
        
        ## Tech Stack
        - Framework: Strawberry GraphQL
        - Database: PostgreSQL
        - Auth: JWT
        """
    ),
    
    "cli-tool": ProjectTemplate(
        name="CLI Tool",
        description="Command-line interface tool with Typer",
        category="utility",
        tech_stack={
            "framework": "Typer",
            "ui": "Rich",
            "config": "Pydantic"
        },
        features=[
            "Multiple commands",
            "Beautiful CLI output",
            "Configuration file support",
            "Progress indicators",
            "Error handling",
            "Help documentation"
        ],
        job_description="""
        Build a CLI tool with:
        - Typer for CLI framework
        - Rich for beautiful output
        - Multiple subcommands
        - Configuration file support
        - Progress bars and spinners
        - Comprehensive help text
        """,
        tdd_template="""
        # Technical Design Document: CLI Tool
        
        ## Architecture
        Command-line application with Typer and Rich
        
        ## Commands
        - init: Initialize configuration
        - run: Execute main functionality
        - config: Manage configuration
        - version: Show version info
        
        ## Tech Stack
        - CLI: Typer
        - UI: Rich
        - Config: Pydantic Settings
        """
    )
}


class TemplateManager:
    """Manages project templates."""
    
    def __init__(self):
        """Initialize template manager."""
        self.templates = TEMPLATES
        logger.info(f"Template manager initialized with {len(self.templates)} templates")
    
    def list_templates(self, category: Optional[str] = None) -> List[ProjectTemplate]:
        """
        List available templates.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of templates
        """
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    def get_template(self, name: str) -> Optional[ProjectTemplate]:
        """
        Get template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template or None if not found
        """
        return self.templates.get(name)
    
    def get_categories(self) -> List[str]:
        """Get list of available categories."""
        return list(set(t.category for t in self.templates.values()))
    
    def apply_template(
        self,
        template_name: str,
        customizations: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Apply template with optional customizations.
        
        Args:
            template_name: Name of template to apply
            customizations: Optional customizations to apply
            
        Returns:
            Dictionary with job_description and tdd
        """
        template = self.get_template(template_name)
        
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        job_description = template.job_description
        tdd = template.tdd_template
        
        # Apply customizations
        if customizations:
            for key, value in customizations.items():
                placeholder = f"{{{key}}}"
                job_description = job_description.replace(placeholder, value)
                tdd = tdd.replace(placeholder, value)
        
        logger.info(f"Applied template: {template_name}")
        
        return {
            "job_description": job_description.strip(),
            "tdd": tdd.strip(),
            "template": template.to_dict()
        }


# Global instance
template_manager = TemplateManager()


# Convenience functions

def list_templates(category: Optional[str] = None) -> List[ProjectTemplate]:
    """List available templates."""
    return template_manager.list_templates(category)


def get_template(name: str) -> Optional[ProjectTemplate]:
    """Get template by name."""
    return template_manager.get_template(name)


def apply_template(name: str, **customizations) -> Dict[str, str]:
    """Apply template with customizations."""
    return template_manager.apply_template(name, customizations)

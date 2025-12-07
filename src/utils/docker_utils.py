"""
Docker Optimization Utilities for Second Brain Agent.
Provides helpers for generating optimized Docker configurations.
"""

from typing import Dict, List

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DockerOptimizer:
    """Optimize Docker configurations for generated projects."""
    
    def __init__(self):
        """Initialize Docker optimizer."""
        logger.info("Docker optimizer initialized")
    
    def generate_multi_stage_dockerfile(
        self,
        language: str = "python",
        **options
    ) -> str:
        """
        Generate optimized multi-stage Dockerfile.
        
        Args:
            language: Programming language
            **options: Additional options
            
        Returns:
            Dockerfile content
        """
        if language == "python":
            return self._generate_python_dockerfile(**options)
        elif language == "node":
            return self._generate_node_dockerfile(**options)
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def _generate_python_dockerfile(
        self,
        python_version: str = "3.11",
        use_poetry: bool = False,
        **options
    ) -> str:
        """Generate optimized Python Dockerfile."""
        base_image = f"python:{python_version}-slim"
        
        if use_poetry:
            return f"""# Multi-stage Dockerfile for Python with Poetry
FROM {base_image} as builder

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \\
    && poetry install --no-dev --no-interaction --no-ansi

# Runtime stage
FROM {base_image}

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python{python_version}/site-packages /usr/local/lib/python{python_version}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        else:
            return f"""# Multi-stage Dockerfile for Python with pip
FROM {base_image} as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM {base_image}

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    def _generate_node_dockerfile(
        self,
        node_version: str = "20",
        **options
    ) -> str:
        """Generate optimized Node.js Dockerfile."""
        return f"""# Multi-stage Dockerfile for Node.js
FROM node:{node_version}-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY src/ ./src/

# Build application
RUN npm run build

# Runtime stage
FROM node:{node_version}-alpine

WORKDIR /app

# Copy dependencies and build from builder
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY package*.json ./

# Create non-root user
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:3000/health', (r) => {{process.exit(r.statusCode === 200 ? 0 : 1)}})"

# Expose port
EXPOSE 3000

# Run application
CMD ["node", "dist/main.js"]
"""
    
    def generate_docker_compose(
        self,
        services: List[str],
        **options
    ) -> str:
        """
        Generate docker-compose.yml with best practices.
        
        Args:
            services: List of services to include
            **options: Additional options
            
        Returns:
            docker-compose.yml content
        """
        compose = {
            "version": "3.9",
            "services": {},
            "networks": {
                "app-network": {
                    "driver": "bridge"
                }
            },
            "volumes": {}
        }
        
        for service in services:
            if service == "backend":
                compose["services"]["backend"] = self._backend_service()
            elif service == "frontend":
                compose["services"]["frontend"] = self._frontend_service()
            elif service == "postgres":
                compose["services"]["postgres"] = self._postgres_service()
                compose["volumes"]["postgres-data"] = None
            elif service == "redis":
                compose["services"]["redis"] = self._redis_service()
                compose["volumes"]["redis-data"] = None
            elif service == "nginx":
                compose["services"]["nginx"] = self._nginx_service()
        
        # Convert to YAML string
        import yaml
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)
    
    def _backend_service(self) -> Dict:
        """Backend service configuration."""
        return {
            "build": {
                "context": "./backend",
                "dockerfile": "Dockerfile"
            },
            "ports": ["8000:8000"],
            "environment": {
                "DATABASE_URL": "postgresql://user:pass@postgres:5432/db",
                "REDIS_URL": "redis://redis:6379/0"
            },
            "depends_on": ["postgres", "redis"],
            "networks": ["app-network"],
            "restart": "unless-stopped",
            "healthcheck": {
                "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3,
                "start_period": "40s"
            }
        }
    
    def _frontend_service(self) -> Dict:
        """Frontend service configuration."""
        return {
            "build": {
                "context": "./frontend",
                "dockerfile": "Dockerfile"
            },
            "ports": ["3000:3000"],
            "environment": {
                "REACT_APP_API_URL": "http://localhost:8000"
            },
            "depends_on": ["backend"],
            "networks": ["app-network"],
            "restart": "unless-stopped"
        }
    
    def _postgres_service(self) -> Dict:
        """PostgreSQL service configuration."""
        return {
            "image": "postgres:15-alpine",
            "environment": {
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass",
                "POSTGRES_DB": "db"
            },
            "ports": ["5432:5432"],
            "volumes": [
                "postgres-data:/var/lib/postgresql/data"
            ],
            "networks": ["app-network"],
            "restart": "unless-stopped",
            "healthcheck": {
                "test": ["CMD-SHELL", "pg_isready -U user"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5
            }
        }
    
    def _redis_service(self) -> Dict:
        """Redis service configuration."""
        return {
            "image": "redis:7-alpine",
            "ports": ["6379:6379"],
            "volumes": [
                "redis-data:/data"
            ],
            "networks": ["app-network"],
            "restart": "unless-stopped",
            "healthcheck": {
                "test": ["CMD", "redis-cli", "ping"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5
            }
        }
    
    def _nginx_service(self) -> Dict:
        """Nginx service configuration."""
        return {
            "image": "nginx:alpine",
            "ports": ["80:80", "443:443"],
            "volumes": [
                "./nginx.conf:/etc/nginx/nginx.conf:ro"
            ],
            "depends_on": ["backend", "frontend"],
            "networks": ["app-network"],
            "restart": "unless-stopped"
        }
    
    def generate_dockerignore(self) -> str:
        """Generate .dockerignore file."""
        return """# Git
.git
.gitignore

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
.venv
venv/
ENV/
env/

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Documentation
docs/
*.md

# CI/CD
.github/
.gitlab-ci.yml

# Development
.env
.env.local
*.sqlite
*.db

# Build
dist/
build/
*.egg-info/
"""
    
    def optimize_image_size(self, dockerfile: str) -> List[str]:
        """
        Suggest optimizations for image size.
        
        Args:
            dockerfile: Dockerfile content
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        if "apt-get update" in dockerfile and "--no-install-recommends" not in dockerfile:
            suggestions.append("Add --no-install-recommends to apt-get install")
        
        if "apt-get update" in dockerfile and "rm -rf /var/lib/apt/lists/*" not in dockerfile:
            suggestions.append("Clean apt cache with: rm -rf /var/lib/apt/lists/*")
        
        if "pip install" in dockerfile and "--no-cache-dir" not in dockerfile:
            suggestions.append("Add --no-cache-dir to pip install")
        
        if "FROM" in dockerfile and "alpine" not in dockerfile.lower():
            suggestions.append("Consider using Alpine-based images for smaller size")
        
        if "COPY . ." in dockerfile:
            suggestions.append("Use specific COPY commands instead of COPY . .")
        
        if "USER" not in dockerfile:
            suggestions.append("Run as non-root user for security")
        
        if "HEALTHCHECK" not in dockerfile:
            suggestions.append("Add HEALTHCHECK instruction")
        
        return suggestions


# Global instance
docker_optimizer = DockerOptimizer()


# Convenience functions

def generate_dockerfile(language: str = "python", **options) -> str:
    """Generate optimized Dockerfile."""
    return docker_optimizer.generate_multi_stage_dockerfile(language, **options)


def generate_compose(services: List[str], **options) -> str:
    """Generate docker-compose.yml."""
    return docker_optimizer.generate_docker_compose(services, **options)


def generate_dockerignore() -> str:
    """Generate .dockerignore."""
    return docker_optimizer.generate_dockerignore()

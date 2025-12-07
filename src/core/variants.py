"""
Project Variants Generator for Second Brain Agent.
Generates alternative architectural approaches for the same project.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ArchitectureVariant:
    """Represents an architecture variant."""
    name: str
    description: str
    tech_stack: Dict[str, str]
    pros: List[str]
    cons: List[str]
    use_cases: List[str]
    complexity: str  # "low", "medium", "high"
    scalability: str  # "low", "medium", "high"
    cost: str  # "low", "medium", "high"


class VariantGenerator:
    """
    Generate architectural variants for projects.
    
    Provides multiple implementation approaches for the same requirements.
    """
    
    def __init__(self):
        """Initialize variant generator."""
        logger.info("Variant generator initialized")
    
    def generate_backend_variants(
        self,
        requirements: Dict
    ) -> List[ArchitectureVariant]:
        """
        Generate backend architecture variants.
        
        Args:
            requirements: Project requirements dictionary
            
        Returns:
            List of architecture variants
        """
        variants = []
        
        # Monolithic variant
        variants.append(ArchitectureVariant(
            name="Monolithic Architecture",
            description="Single application with all components",
            tech_stack={
                "framework": "FastAPI/Django",
                "database": "PostgreSQL",
                "cache": "Redis",
                "deployment": "Single server"
            },
            pros=[
                "Simple deployment",
                "Easier development",
                "Lower initial cost",
                "Straightforward debugging"
            ],
            cons=[
                "Limited scalability",
                "Tight coupling",
                "Harder to maintain at scale"
            ],
            use_cases=[
                "Small to medium projects",
                "MVPs and prototypes",
                "Limited team size"
            ],
            complexity="low",
            scalability="medium",
            cost="low"
        ))
        
        # Microservices variant
        variants.append(ArchitectureVariant(
            name="Microservices Architecture",
            description="Multiple independent services",
            tech_stack={
                "services": "FastAPI services",
                "api_gateway": "Kong/Nginx",
                "message_broker": "RabbitMQ/Kafka",
                "databases": "PostgreSQL + MongoDB",
                "orchestration": "Kubernetes"
            },
            pros=[
                "High scalability",
                "Independent deployments",
                "Technology flexibility",
                "Fault isolation"
            ],
            cons=[
                "Complex infrastructure",
                "Distributed system challenges",
                "Higher operational cost"
            ],
            use_cases=[
                "Large-scale applications",
                "Multiple teams",
                "Need for independent scaling"
            ],
            complexity="high",
            scalability="high",
            cost="high"
        ))
        
        # Serverless variant
        variants.append(ArchitectureVariant(
            name="Serverless Architecture",
            description="Function-as-a-Service approach",
            tech_stack={
                "functions": "AWS Lambda/Cloud Functions",
                "api": "API Gateway",
                "database": "DynamoDB/Firestore",
                "storage": "S3"
            },
            pros=[
                "Auto-scaling",
                "Pay-per-use pricing",
                "No server management",
                "Quick deployment"
            ],
            cons=[
                "Cold start latency",
                "Vendor lock-in",
                "Limited execution time",
                "Debugging complexity"
            ],
            use_cases=[
                "Event-driven workloads",
                "Variable traffic",
                "Quick prototyping"
            ],
            complexity="medium",
            scalability="high",
            cost="medium"
        ))
        
        # Modular monolith variant
        variants.append(ArchitectureVariant(
            name="Modular Monolith",
            description="Well-structured monolith with clear boundaries",
            tech_stack={
                "framework": "FastAPI with modules",
                "database": "PostgreSQL",
                "cache": "Redis",
                "deployment": "Container-based"
            },
            pros=[
                "Simpler than microservices",
                "Clear module boundaries",
                "Easier to refactor",
                "Better than pure monolith"
            ],
            cons=[
                "Still a single deployment unit",
                "Requires discipline",
                "Potential for coupling"
            ],
            use_cases=[
                "Growing applications",
                "Teams transitioning to microservices",
                "Need for structure without complexity"
            ],
            complexity="medium",
            scalability="medium",
            cost="low"
        ))
        
        logger.info(f"Generated {len(variants)} backend variants")
        return variants
    
    def generate_frontend_variants(
        self,
        requirements: Dict
    ) -> List[ArchitectureVariant]:
        """
        Generate frontend architecture variants.
        
        Args:
            requirements: Project requirements dictionary
            
        Returns:
            List of architecture variants
        """
        variants = []
        
        # SPA variant
        variants.append(ArchitectureVariant(
            name="Single Page Application (SPA)",
            description="Client-side rendered React app",
            tech_stack={
                "framework": "React + TypeScript",
                "routing": "React Router",
                "state": "Redux/Zustand",
                "styling": "Tailwind CSS"
            },
            pros=[
                "Rich interactivity",
                "Smooth user experience",
                "Decoupled from backend"
            ],
            cons=[
                "SEO challenges",
                "Initial load time",
                "JavaScript required"
            ],
            use_cases=[
                "Interactive dashboards",
                "Admin panels",
                "Internal tools"
            ],
            complexity="medium",
            scalability="high",
            cost="medium"
        ))
        
        # SSR variant
        variants.append(ArchitectureVariant(
            name="Server-Side Rendering (SSR)",
            description="Next.js with server rendering",
            tech_stack={
                "framework": "Next.js",
                "rendering": "SSR + ISR",
                "styling": "Tailwind CSS",
                "deployment": "Vercel/Node"
            },
            pros=[
                "Better SEO",
                "Faster initial load",
                "Hybrid rendering options"
            ],
            cons=[
                "Server complexity",
                "Higher hosting cost",
                "More complex caching"
            ],
            use_cases=[
                "Public-facing websites",
                "E-commerce",
                "Content-heavy sites"
            ],
            complexity="medium",
            scalability="high",
            cost="medium"
        ))
        
        # Static site variant
        variants.append(ArchitectureVariant(
            name="Static Site Generation (SSG)",
            description="Pre-built static pages",
            tech_stack={
                "framework": "Next.js/Astro",
                "rendering": "Static",
                "hosting": "CDN",
                "cms": "Headless CMS"
            },
            pros=[
                "Blazing fast",
                "Excellent SEO",
                "Low hosting cost",
                "High security"
            ],
            cons=[
                "Build time for changes",
                "Limited dynamic content",
                "Not suitable for user-specific content"
            ],
            use_cases=[
                "Blogs and documentation",
                "Marketing sites",
                "Portfolio websites"
            ],
            complexity="low",
            scalability="high",
            cost="low"
        ))
        
        logger.info(f"Generated {len(variants)} frontend variants")
        return variants
    
    def generate_database_variants(
        self,
        requirements: Dict
    ) -> List[ArchitectureVariant]:
        """
        Generate database architecture variants.
        
        Args:
            requirements: Project requirements dictionary
            
        Returns:
            List of database variants
        """
        variants = []
        
        # SQL variant
        variants.append(ArchitectureVariant(
            name="Relational Database (SQL)",
            description="PostgreSQL or MySQL",
            tech_stack={
                "database": "PostgreSQL 15+",
                "orm": "SQLAlchemy",
                "migrations": "Alembic",
                "pooling": "PgBouncer"
            },
            pros=[
                "ACID compliance",
                "Strong consistency",
                "Complex queries",
                "Mature tooling"
            ],
            cons=[
                "Schema rigidity",
                "Vertical scaling limits",
                "Migration complexity"
            ],
            use_cases=[
                "Structured data",
                "Complex relationships",
                "Financial applications"
            ],
            complexity="medium",
            scalability="medium",
            cost="medium"
        ))
        
        # NoSQL variant
        variants.append(ArchitectureVariant(
            name="NoSQL Database",
            description="MongoDB or similar",
            tech_stack={
                "database": "MongoDB",
                "odm": "Motor/Beanie",
                "search": "MongoDB Atlas Search"
            },
            pros=[
                "Flexible schema",
                "Horizontal scaling",
                "Fast reads",
                "Good for JSON data"
            ],
            cons=[
                "Eventual consistency",
                "Complex joins",
                "Less mature for transactions"
            ],
            use_cases=[
                "Rapid prototyping",
                "Unstructured data",
                "High write loads"
            ],
            complexity="medium",
            scalability="high",
            cost="medium"
        ))
        
        # Hybrid variant
        variants.append(ArchitectureVariant(
            name="Polyglot Persistence",
            description="Multiple databases for different needs",
            tech_stack={
                "transactional": "PostgreSQL",
                "cache": "Redis",
                "search": "Elasticsearch",
                "analytics": "ClickHouse"
            },
            pros=[
                "Optimized for each use case",
                "Best performance",
                "Flexible architecture"
            ],
            cons=[
                "Operational complexity",
                "Data synchronization",
                "Higher cost"
            ],
            use_cases=[
                "Large applications",
                "Diverse data needs",
                "Performance-critical systems"
            ],
            complexity="high",
            scalability="high",
            cost="high"
        ))
        
        logger.info(f"Generated {len(variants)} database variants")
        return variants
    
    def compare_variants(
        self,
        variants: List[ArchitectureVariant],
        priorities: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Compare variants based on priorities.
        
        Args:
            variants: List of variants to compare
            priorities: Optional priority weights (complexity, scalability, cost)
            
        Returns:
            Sorted list of variants with scores
        """
        if not priorities:
            priorities = {
                "complexity": 0.3,
                "scalability": 0.4,
                "cost": 0.3
            }
        
        # Score mapping
        score_map = {"low": 3, "medium": 2, "high": 1}
        
        results = []
        for variant in variants:
            # Calculate weighted score
            score = (
                score_map[variant.complexity] * priorities.get("complexity", 0.3) +
                score_map[variant.scalability] * priorities.get("scalability", 0.4) +
                score_map[variant.cost] * priorities.get("cost", 0.3)
            )
            
            results.append({
                "variant": variant,
                "score": score,
                "recommendation": self._get_recommendation(variant, score)
            })
        
        # Sort by score (higher is better)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"Compared {len(variants)} variants")
        return results
    
    def _get_recommendation(
        self,
        variant: ArchitectureVariant,
        score: float
    ) -> str:
        """Generate recommendation text."""
        if score >= 2.5:
            return "Highly recommended for your use case"
        elif score >= 2.0:
            return "Good fit with some trade-offs"
        else:
            return "Consider only if specific requirements demand it"

# Global instance
variant_generator = VariantGenerator()


# Convenience functions

def generate_variants(project_type: str, requirements: Dict = None) -> Dict[str, List]:
    """Generate all variants for a project type."""
    if requirements is None:
        requirements = {}
    
    return {
        "backend": variant_generator.generate_backend_variants(requirements),
        "frontend": variant_generator.generate_frontend_variants(requirements),
        "database": variant_generator.generate_database_variants(requirements)
    }


def compare_variants(variants: List[ArchitectureVariant], **priorities) -> List[Dict]:
    """Compare variants with custom priorities."""
    return variant_generator.compare_variants(variants, priorities)

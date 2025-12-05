#!/usr/bin/env python3
"""
Automated Brain Ingestion Script

Ingests recommended GitHub repositories into frontend_brain, backend_brain, and fullstack_brain
to improve code generation quality.

Usage:
    python ingest_all_brains.py                    # Ingest all repositories
    python ingest_all_brains.py --priority 1       # Only Priority 1 (essential)
    python ingest_all_brains.py --priority 2       # Only Priority 2 (advanced)
    python ingest_all_brains.py --quick            # Quick start (5 repos only)
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ingestion.ingest_expert import ingest_expert_knowledge

# Repository lists organized by priority
REPOSITORIES = {
    "priority_1": {
        "name": "Essential Repositories",
        "repos": [
            {
                "expert": "fullstack",
                "repo": "https://github.com/tiangolo/full-stack-fastapi-template",
                "name": "FastAPI + React Template",
                "why": "Complete integration patterns, authentication, JWT"
            },
            {
                "expert": "fullstack",
                "repo": "https://github.com/t3-oss/create-t3-app",
                "name": "T3 Stack",
                "why": "Modern full-stack TypeScript patterns"
            },
            {
                "expert": "backend",
                "repo": "https://github.com/zhanymkanov/fastapi-best-practices",
                "name": "FastAPI Best Practices",
                "why": "Authentication, JWT, database patterns, project structure"
            },
            {
                "expert": "backend",
                "repo": "https://github.com/nsidnev/fastapi-realworld-example-app",
                "name": "FastAPI RealWorld Example",
                "why": "Complete CRUD API with auth, follows RealWorld spec"
            },
            {
                "expert": "frontend",
                "repo": "https://github.com/shadcn-ui/ui",
                "name": "shadcn/ui Components",
                "why": "High-quality React components, form patterns, TypeScript"
            },
            {
                "expert": "frontend",
                "repo": "https://github.com/vercel/next.js",
                "name": "Next.js",
                "why": "Official Next.js patterns, authentication examples, API routes"
            },
        ]
    },
    "priority_2": {
        "name": "Advanced Patterns",
        "repos": [
            {
                "expert": "frontend",
                "repo": "https://github.com/nextauthjs/next-auth",
                "name": "NextAuth.js",
                "why": "Complete auth patterns for Next.js"
            },
            {
                "expert": "backend",
                "repo": "https://github.com/fastapi-users/fastapi-users",
                "name": "FastAPI Users",
                "why": "Complete user management, registration, login patterns"
            },
            {
                "expert": "backend",
                "repo": "https://github.com/encode/django-rest-framework",
                "name": "Django REST Framework",
                "why": "REST API patterns, serializers, viewsets, permissions"
            },
            {
                "expert": "frontend",
                "repo": "https://github.com/react-hook-form/react-hook-form",
                "name": "React Hook Form",
                "why": "Form validation patterns, TypeScript integration"
            },
            {
                "expert": "frontend",
                "repo": "https://github.com/colinhacks/zod",
                "name": "Zod",
                "why": "Schema validation patterns used with React Hook Form"
            },
            {
                "expert": "frontend",
                "repo": "https://github.com/TanStack/query",
                "name": "TanStack Query",
                "why": "API data fetching patterns, caching, mutations"
            },
        ]
    },
    "priority_3": {
        "name": "Specialized Patterns",
        "repos": [
            {
                "expert": "frontend",
                "repo": "https://github.com/pmndrs/zustand",
                "name": "Zustand",
                "why": "Modern state management patterns"
            },
            {
                "expert": "frontend",
                "repo": "https://github.com/radix-ui/primitives",
                "name": "Radix UI Primitives",
                "why": "Accessible component patterns"
            },
            {
                "expert": "backend",
                "repo": "https://github.com/sqlalchemy/sqlalchemy",
                "name": "SQLAlchemy",
                "why": "Database ORM patterns, migrations, relationships"
            },
        ]
    }
}

# Quick start - minimum viable set
QUICK_START = [
    {
        "expert": "fullstack",
        "repo": "https://github.com/tiangolo/full-stack-fastapi-template",
        "name": "FastAPI + React Template"
    },
    {
        "expert": "backend",
        "repo": "https://github.com/zhanymkanov/fastapi-best-practices",
        "name": "FastAPI Best Practices"
    },
    {
        "expert": "frontend",
        "repo": "https://github.com/shadcn-ui/ui",
        "name": "shadcn/ui Components"
    },
    {
        "expert": "frontend",
        "repo": "https://github.com/vercel/next.js",
        "name": "Next.js"
    },
    {
        "expert": "backend",
        "repo": "https://github.com/nsidnev/fastapi-realworld-example-app",
        "name": "FastAPI RealWorld Example"
    },
]


def ingest_repository(expert_type: str, repo_url: str, name: str, why: str = None):
    """Ingest a single repository."""
    print(f"\n{'='*70}")
    print(f"📦 Ingesting: {name}")
    if why:
        print(f"   Why: {why}")
    print(f"   Type: {expert_type}")
    print(f"   URL: {repo_url}")
    print(f"{'='*70}\n")
    
    try:
        result = ingest_expert_knowledge(
            expert_type=expert_type,
            repo_url=repo_url,
            verbose=True
        )
        
        if result.get('success'):
            files = result.get('files_processed', 0)
            chunks = result.get('chunks_created', 0)
            print(f"✅ Successfully ingested {name}")
            print(f"   Files: {files}, Chunks: {chunks}")
            return True
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ Failed to ingest {name}")
            print(f"   Error: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error ingesting {name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Ingest recommended repositories into brain collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Quick start (5 essential repos)
    python ingest_all_brains.py --quick
    
    # Only Priority 1 (essential)
    python ingest_all_brains.py --priority 1
    
    # Priority 1 and 2
    python ingest_all_brains.py --priority 1 --priority 2
    
    # All repositories
    python ingest_all_brains.py
        """
    )
    
    parser.add_argument(
        "--priority",
        action="append",
        choices=["1", "2", "3"],
        help="Which priority level to ingest (can specify multiple)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick start mode - ingest only 5 essential repositories"
    )
    
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip repositories that have already been ingested"
    )
    
    args = parser.parse_args()
    
    # Determine what to ingest
    repos_to_ingest = []
    
    if args.quick:
        print("🚀 Quick Start Mode: Ingesting 5 essential repositories...\n")
        repos_to_ingest = QUICK_START
    elif args.priority:
        print(f"📦 Ingesting Priority {', '.join(args.priority)} repositories...\n")
        for priority in args.priority:
            key = f"priority_{priority}"
            if key in REPOSITORIES:
                repos_to_ingest.extend(REPOSITORIES[key]["repos"])
    else:
        print("📦 Ingesting ALL recommended repositories...\n")
        for priority_key in ["priority_1", "priority_2", "priority_3"]:
            repos_to_ingest.extend(REPOSITORIES[priority_key]["repos"])
    
    if not repos_to_ingest:
        print("❌ No repositories selected. Use --quick or --priority 1/2/3")
        return
    
    # Show summary
    print(f"\n📊 Summary: Will ingest {len(repos_to_ingest)} repositories\n")
    
    # Confirm
    if not args.quick:
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    # Ingest repositories
    success_count = 0
    fail_count = 0
    
    for repo_info in repos_to_ingest:
        success = ingest_repository(
            expert_type=repo_info["expert"],
            repo_url=repo_info["repo"],
            name=repo_info["name"],
            why=repo_info.get("why")
        )
        
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # Final summary
    print("\n" + "="*70)
    print("📊 INGESTION COMPLETE")
    print("="*70)
    print(f"✅ Successfully ingested: {success_count}")
    if fail_count > 0:
        print(f"❌ Failed: {fail_count}")
    print("\n💡 Next steps:")
    print("   1. Test code generation with: python app.py")
    print("   2. Query brains: python src/main.py --mode query --brain frontend_brain --query 'authentication'")
    print("   3. See BRAIN_REPOSITORIES.md for full list and details")
    print("="*70)


if __name__ == "__main__":
    main()


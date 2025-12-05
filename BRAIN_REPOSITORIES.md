# Recommended GitHub Repositories for Brain Ingestion

This document lists high-quality GitHub repositories to ingest into `frontend_brain`, `backend_brain`, and `fullstack_brain` collections to improve code generation quality.

## 🎯 Priority 1: Essential Repositories (Start Here)

### Full-Stack Integration Patterns
These show how frontend and backend work together - **CRITICAL for fixing integration issues**

```bash
# 1. FastAPI + React Template (MOST IMPORTANT - Shows integration)
python src/ingest_expert.py --expert fullstack --repo https://github.com/tiangolo/full-stack-fastapi-template
# Why: Complete FastAPI backend + React frontend with authentication, JWT, database

# 2. T3 Stack (Next.js + tRPC + Prisma)
python src/ingest_expert.py --expert fullstack --repo https://github.com/t3-oss/create-t3-app
# Why: Modern full-stack TypeScript patterns, shows tRPC integration
```

### Backend Patterns
```bash
# 3. FastAPI Best Practices
python src/ingest_expert.py --expert backend --repo https://github.com/zhanymkanov/fastapi-best-practices
# Why: Authentication, JWT, database patterns, project structure

# 4. FastAPI RealWorld Example
python src/ingest_expert.py --expert backend --repo https://github.com/nsidnev/fastapi-realworld-example-app
# Why: Complete CRUD API with auth, follows RealWorld spec
```

### Frontend Patterns
```bash
# 5. shadcn/ui Components
python src/ingest_expert.py --expert frontend --repo https://github.com/shadcn-ui/ui
# Why: High-quality React components, form patterns, TypeScript

# 6. Next.js Examples
python src/ingest_expert.py --expert frontend --repo https://github.com/vercel/next.js
# Why: Official Next.js patterns, authentication examples, API routes
```

---

## 🚀 Priority 2: Advanced Patterns

### Authentication & Security
```bash
# 7. NextAuth.js (Next.js Authentication)
python src/ingest_expert.py --expert frontend --repo https://github.com/nextauthjs/next-auth
# Why: Complete auth patterns for Next.js

# 8. FastAPI Security
python src/ingest_expert.py --expert backend --repo https://github.com/tiangolo/fastapi
# Why: Official FastAPI security patterns, OAuth2, JWT examples
```

### Database Patterns
```bash
# 9. SQLAlchemy Patterns
python src/ingest_expert.py --expert backend --repo https://github.com/sqlalchemy/sqlalchemy
# Why: Database ORM patterns, migrations, relationships

# 10. Prisma Examples
python src/ingest_expert.py --expert frontend --repo https://github.com/prisma/prisma-examples
# Why: Database client patterns, TypeScript integration
```

### API Design
```bash
# 11. Django REST Framework
python src/ingest_expert.py --expert backend --repo https://github.com/encode/django-rest-framework
# Why: REST API patterns, serializers, viewsets, permissions

# 12. FastAPI Users
python src/ingest_expert.py --expert backend --repo https://github.com/fastapi-users/fastapi-users
# Why: Complete user management, registration, login patterns
```

---

## 📦 Priority 3: Specialized Patterns

### Form Handling & Validation
```bash
# 13. React Hook Form
python src/ingest_expert.py --expert frontend --repo https://github.com/react-hook-form/react-hook-form
# Why: Form validation patterns, TypeScript integration

# 14. Zod (TypeScript-first schema validation)
python src/ingest_expert.py --expert frontend --repo https://github.com/colinhacks/zod
# Why: Schema validation patterns used with React Hook Form
```

### State Management
```bash
# 15. Zustand (Lightweight state management)
python src/ingest_expert.py --expert frontend --repo https://github.com/pmndrs/zustand
# Why: Modern state management patterns

# 16. TanStack Query (React Query)
python src/ingest_expert.py --expert frontend --repo https://github.com/TanStack/query
# Why: API data fetching patterns, caching, mutations
```

### Testing Patterns
```bash
# 17. FastAPI Testing
python src/ingest_expert.py --expert backend --repo https://github.com/tiangolo/fastapi
# Why: Test patterns (check tests/ directory)

# 18. React Testing Library Examples
python src/ingest_expert.py --expert frontend --repo https://github.com/testing-library/react-testing-library
# Why: Component testing patterns
```

### File Upload & Processing
```bash
# 19. FastAPI File Upload Examples
python src/ingest_expert.py --expert backend --repo https://github.com/tiangolo/fastapi
# Why: File upload patterns (check docs/examples/)

# 20. React File Upload Components
python src/ingest_expert.py --expert frontend --repo https://github.com/react-dropzone/react-dropzone
# Why: File upload UI patterns
```

---

## 🎨 UI/UX Patterns

### Component Libraries
```bash
# 21. Radix UI Primitives
python src/ingest_expert.py --expert frontend --repo https://github.com/radix-ui/primitives
# Why: Accessible component patterns (used by shadcn/ui)

# 22. Headless UI
python src/ingest_expert.py --expert frontend --repo https://github.com/tailwindlabs/headlessui
# Why: Unstyled component patterns
```

### Styling Patterns
```bash
# 23. Tailwind CSS Examples
python src/ingest_expert.py --expert frontend --repo https://github.com/tailwindlabs/tailwindcss
# Why: Utility-first CSS patterns

# 24. Styled Components
python src/ingest_expert.py --expert frontend --repo https://github.com/styled-components/styled-components
# Why: CSS-in-JS patterns
```

---

## 🔧 DevOps & Configuration

### Docker & Deployment
```bash
# 25. Docker Compose Examples
python src/ingest_expert.py --expert backend --repo https://github.com/tiangolo/full-stack-fastapi-template
# Why: Docker configurations (already in fullstack, but good reference)

# 26. GitHub Actions for Python
python src/ingest_expert.py --expert backend --repo https://github.com/actions/starter-workflows
# Why: CI/CD patterns
```

---

## 📋 Complete Ingestion Script

Save this as `ingest_all_brains.sh` (or `.bat` for Windows):

```bash
#!/bin/bash

echo "🚀 Starting brain ingestion..."

# Priority 1: Essential
echo "📦 Priority 1: Essential repositories..."
python src/ingest_expert.py --expert fullstack --repo https://github.com/tiangolo/full-stack-fastapi-template
python src/ingest_expert.py --expert fullstack --repo https://github.com/t3-oss/create-t3-app
python src/ingest_expert.py --expert backend --repo https://github.com/zhanymkanov/fastapi-best-practices
python src/ingest_expert.py --expert backend --repo https://github.com/nsidnev/fastapi-realworld-example-app
python src/ingest_expert.py --expert frontend --repo https://github.com/shadcn-ui/ui
python src/ingest_expert.py --expert frontend --repo https://github.com/vercel/next.js

# Priority 2: Advanced
echo "📦 Priority 2: Advanced patterns..."
python src/ingest_expert.py --expert frontend --repo https://github.com/nextauthjs/next-auth
python src/ingest_expert.py --expert backend --repo https://github.com/fastapi-users/fastapi-users
python src/ingest_expert.py --expert backend --repo https://github.com/encode/django-rest-framework

# Priority 3: Specialized
echo "📦 Priority 3: Specialized patterns..."
python src/ingest_expert.py --expert frontend --repo https://github.com/react-hook-form/react-hook-form
python src/ingest_expert.py --expert frontend --repo https://github.com/colinhacks/zod
python src/ingest_expert.py --expert frontend --repo https://github.com/TanStack/query

echo "✅ Brain ingestion complete!"
```

---

## 🎯 Quick Start (Minimum Viable)

If you only have time for 3-5 repositories, start with these:

```bash
# 1. FastAPI + React integration (CRITICAL)
python src/ingest_expert.py --expert fullstack --repo https://github.com/tiangolo/full-stack-fastapi-template

# 2. FastAPI best practices
python src/ingest_expert.py --expert backend --repo https://github.com/zhanymkanov/fastapi-best-practices

# 3. React components
python src/ingest_expert.py --expert frontend --repo https://github.com/shadcn-ui/ui

# 4. Next.js patterns
python src/ingest_expert.py --expert frontend --repo https://github.com/vercel/next.js

# 5. Complete API example
python src/ingest_expert.py --expert backend --repo https://github.com/nsidnev/fastapi-realworld-example-app
```

---

## 📊 Expected Improvements After Ingestion

After ingesting these repositories, you should see:

✅ **Consistent Integration**: Frontend and backend will use matching patterns (no more tRPC/FastAPI mismatches)

✅ **Complete Authentication**: Proper JWT flows, protected routes, token refresh

✅ **Better File Structure**: Proper project organization, entry points, configuration files

✅ **Production Patterns**: Error handling, validation, security best practices

✅ **Complete Components**: Full-featured forms, API clients, state management

✅ **Database Patterns**: Proper ORM usage, migrations, relationships

---

## 🔍 How to Verify Ingestion

Check what's been ingested:

```bash
# Query the brains to see what patterns are available
python src/main.py --mode query --brain frontend_brain --query "authentication patterns"
python src/main.py --mode query --brain backend_brain --query "JWT token generation"
python src/main.py --mode query --brain fullstack_brain --query "FastAPI React integration"
```

---

## 💡 Tips

1. **Start with Priority 1** - These fix the most common issues
2. **Ingest incrementally** - Test code generation after each batch
3. **Focus on your stack** - If you use Django, prioritize Django repos over FastAPI
4. **Update regularly** - Re-run ingestion periodically to get latest patterns
5. **Monitor size** - Large repositories take time to ingest, be patient

---

## 🐛 Troubleshooting

**Issue**: Ingestion fails or times out
- **Solution**: Try ingesting smaller repositories first, or use `--path` with a local clone

**Issue**: Not seeing improvements in generated code
- **Solution**: Make sure to query the right brain (frontend_brain vs backend_brain), and check that ingestion completed successfully

**Issue**: Duplicate patterns
- **Solution**: The system handles duplicates, but you can check collection stats before re-ingesting


# Quick Start: Brain Ingestion Guide

## 🚀 Fastest Way to Improve Code Generation

### Option 1: Automated Script (Recommended)

```bash
# Quick start - 5 essential repositories (5-10 minutes)
python ingest_all_brains.py --quick

# Or ingest all Priority 1 repositories (6 repos)
python ingest_all_brains.py --priority 1
```

### Option 2: Manual - Essential 5 Repositories

Run these commands one by one:

```bash
# 1. FastAPI + React integration (MOST IMPORTANT)
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

## 📋 Complete List by Category

### 🔴 Priority 1: Essential (Start Here)

**Full-Stack Integration:**
- `tiangolo/full-stack-fastapi-template` - FastAPI + React integration
- `t3-oss/create-t3-app` - Next.js + tRPC + Prisma

**Backend:**
- `zhanymkanov/fastapi-best-practices` - FastAPI patterns
- `nsidnev/fastapi-realworld-example-app` - Complete CRUD API

**Frontend:**
- `shadcn-ui/ui` - React components
- `vercel/next.js` - Next.js patterns

### 🟡 Priority 2: Advanced

**Authentication:**
- `nextauthjs/next-auth` - Next.js auth
- `fastapi-users/fastapi-users` - FastAPI user management

**Forms & Validation:**
- `react-hook-form/react-hook-form` - Form handling
- `colinhacks/zod` - Schema validation

**API Patterns:**
- `encode/django-rest-framework` - Django REST
- `TanStack/query` - Data fetching

### 🟢 Priority 3: Specialized

**State Management:**
- `pmndrs/zustand` - State management

**UI Components:**
- `radix-ui/primitives` - Accessible components

**Database:**
- `sqlalchemy/sqlalchemy` - ORM patterns

---

## ✅ What This Fixes

After ingestion, you'll see improvements in:

1. **Integration Consistency** - Frontend and backend will match (no more tRPC/FastAPI mismatches)
2. **Complete Authentication** - Proper JWT flows, protected routes
3. **Better File Structure** - Proper entry points, config files
4. **Production Patterns** - Error handling, validation, security
5. **Complete Components** - Full-featured forms, API clients

---

## 🔍 Verify It Worked

```bash
# Query the brains to see what's available
python src/main.py --mode query --brain frontend_brain --query "authentication patterns"
python src/main.py --mode query --brain backend_brain --query "JWT token generation"
```

---

## 📚 Full Documentation

See `BRAIN_REPOSITORIES.md` for complete list with explanations.


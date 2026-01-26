# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Amaejozu is a cosmetics price tracking application that monitors product prices on Rakuten Market and notifies users of price drops via email. The workspace contains two separate repositories that work together.

## Repository Structure

```
workspace/
├── Amaejozu-backend/   # FastAPI backend (Python)
└── Amaejozu-frontend/  # Next.js frontend (TypeScript)
```

## Development Commands

### Backend (Amaejozu-backend/)

```bash
# Start development server (auto-runs in Dev Container)
uvicorn app.main:app --host 0.0.0.0 --reload

# Run tests
pytest

# Lint with ruff
ruff check .

# Database migrations
alembic upgrade head              # Apply all migrations
alembic revision -m "message"     # Create new migration
alembic downgrade -1              # Rollback one migration
```

### Frontend (Amaejozu-frontend/)

```bash
# Start development server (auto-runs in Dev Container)
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

## Architecture

### Backend (FastAPI)

- **app/main.py**: Application entry point with FastAPI routes and CORS configuration
- **app/auth.py**: JWT authentication with bcrypt password hashing
- **app/config.py**: Pydantic settings loaded from `.env`
- **app/database.py**: SQLAlchemy engine and session management (Azure MySQL with SSL)
- **app/models/**: SQLAlchemy ORM models (user, product, watchlist, brand, category, etc.)
- **app/schemas/**: Pydantic request/response schemas
- **app/routers/**: API route handlers organized by feature
- **app/services/**: External service integrations (Rakuten API, email via Resend)
- **alembic/**: Database migration scripts

### Frontend (Next.js)

- **src/app/page.tsx**: Single-page app with screen-based navigation (not file-based routing)
- **src/components/**: Feature screens (Auth, Home, Search, Watchlist, Settings, ProductDetail, Top10)
- **src/components/ui/**: Reusable UI components (Radix UI + Tailwind CSS)
- **src/lib/**: Utility functions
- **src/types/**: TypeScript type definitions

The frontend uses client-side state management with React useState/useEffect. Screen navigation is handled via state, not Next.js routing.

## API Endpoints

Backend runs on `http://localhost:8000`. Key endpoints:
- `/docs` - Swagger UI documentation
- `/auth/*` - Authentication (login, signup, password reset)
- `/app/api/products/search` - Rakuten API product search
- `/api/products/search` - Database product search with filters
- `/api/watchlist/*` - User watchlist management

## Environment Variables

### Backend (.env)
- `DATABASE_URL` - MySQL connection string
- `RAKUTEN_APP_ID`, `RAKUTEN_AFFILIATE_ID` - Rakuten API credentials
- `RESEND_API_KEY` - Email service for notifications
- `SECRET_KEY` - JWT signing key
- `AZURE_OPENAI_KEY` - AI features (optional)

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)

## Dev Container Setup

Both projects use VS Code Dev Containers. Open each folder separately in VS Code and click "Reopen in Container". The backend container auto-starts uvicorn, the frontend auto-starts npm run dev.

Ports:
- Frontend: 3000
- Backend: 8000

## Git Workflow

Branch naming: `<type>/#<issue>-<description>` (e.g., `feature/#17-add-watchlist-api`)

Link PRs to issues with `Closes #XX` in the PR description.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start Commands

### Initial Setup

```bash
# Copy environment configuration
cp .env.example .env

# Start all services via Docker
docker-compose up -d

# Initialize database (first time only)
cd apps/api
python init_db.py
```

### Development Commands

```bash
# Start development servers
pnpm dev               # Start both API and web in development mode
pnpm dev:api          # Start only the FastAPI backend
pnpm dev:web          # Start only the Next.js frontend

# API development (from apps/api/)
python main.py         # Run FastAPI with hot reload
python main.py DEBUG=1 # Run with debugger on port 5678

# Frontend development (from apps/web/)
npm run dev           # Next.js development server
npm run build         # Production build
npm run lint          # ESLint checking
```

### Database Management

```bash
# Database initialization (first deployment)
cd apps/api
python init_db.py

# After model changes during development
alembic revision --autogenerate -m "description"
alembic upgrade head

# Database utilities
python db_manager.py  # Interactive database management helper
alembic current        # Check current migration status
alembic stamp head     # Force mark as latest (troubleshooting)
```

## Architecture Overview

LineRAG is a **multi-tenant RAG (Retrieval-Augmented Generation) system** built with modern full-stack technologies:

### Core Architecture

- **Backend**: FastAPI with SQLAlchemy ORM and Alembic migrations
- **Frontend**: Next.js 15 with NextAuth.js authentication
- **RAG Engine**: RAG-Anything framework with multimodal document processing
- **Vector Database**: Qdrant for document embeddings
- **Relational Database**: PostgreSQL for multi-tenant data
- **Build System**: Turborepo monorepo with pnpm workspaces

### Multi-Tenant Design

The system supports multiple companies sharing the same infrastructure with complete data isolation:

- **Company Isolation**: Each company has separate LINE channels, RAG working directories, and data access
- **User Management**: Dual user system with SystemUser (web admin) and TenantUser (LINE bot users)
- **Resource Quotas**: Per-company limits on documents, queries, and storage
- **Audit Logging**: Complete tracking of all operations across tenants

### Key Services

- **MultiTenantRAGService**: Manages per-company RAG-Anything instances
- **MultiTenantUserService**: Handles user authentication and permissions across companies
- **Document Processing**: Supports PDFs, Office docs, images with MinerU parser integration

### Data Models

- **Company**: Tenant configuration, LINE channel settings, subscription plans
- **SystemUser**: Web portal administrators with company access permissions
- **TenantUser**: LINE bot users belonging to specific companies
- **DocumentMetadata**: Multi-modal document tracking with processing status
- **AuditLog**: Complete operation history for compliance and monitoring

## File Structure

```bash
LineRAG/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── models/         # SQLAlchemy data models
│   │   │   ├── services/       # Business logic (multitenant_rag, multitenant_user)
│   │   │   ├── routers/        # API endpoints (ask, ingest, webhook, system_users, tenant_users)
│   │   │   └── schemas/        # Pydantic request/response models
│   │   ├── alembic/           # Database migrations
│   │   ├── init_db.py         # Database initialization script
│   │   └── requirements.txt    # Python dependencies
│   └── web/                   # Next.js frontend
│       ├── src/app/           # App router structure
│       ├── src/components/    # Reusable UI components
│       └── package.json       # Node.js dependencies
├── docker-compose.yml         # Multi-service container orchestration
└── turbo.json                # Monorepo build configuration
```

## Development Guidelines

### Database Changes

Always create migrations after modifying SQLAlchemy models:

1. Update model in `apps/api/app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Apply migration: `alembic upgrade head`

### Multi-Tenant Considerations

- All database queries must include `company_id` filtering
- RAG operations are isolated per company working directory
- User authentication flows differ for SystemUser vs TenantUser
- LINE webhook routes automatically to correct company based on channel token

### API Debugging

Set `DEBUG=1` environment variable to enable debugpy on port 5678 for remote debugging in VS Code.

### Testing Services

- API health check: `http://localhost:8000/api/health`
- API documentation: `http://localhost:8000/api/docs`
- Frontend: `http://localhost:3000`
- Qdrant admin: `http://localhost:6333/dashboard`

## Environment Configuration

Required environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/linerag

# OpenAI API
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://api.openai.com/v1

# NextAuth
NEXTAUTH_SECRET=your-secret-key

# Optional LINE Bot integration
LINE_CHANNEL_ACCESS_TOKEN=your-token
LINE_CHANNEL_SECRET=your-secret
ADMIN_LINE_IDS=admin_line_id_1,admin_line_id_2
```

## Common Operations

### Adding New Company

1. Insert Company record with LINE channel credentials
2. Set `rag_working_dir` path (e.g., `./rag_storage/company_N`)
3. Create SystemUser with company access permissions
4. Initialize company-specific RAG service instance

### Troubleshooting Multi-Tenant Issues

- Check company isolation: Verify all queries filter by `company_id`
- RAG service issues: Confirm company working directories exist with proper permissions
- Authentication problems: Distinguish between SystemUser (web) and TenantUser (LINE) contexts
- Migration conflicts: Use `alembic stamp head` then retry migrations

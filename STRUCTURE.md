# Code Structure Documentation

## Backend Structure

```
backend/
├── app/                    # Main application package
│   ├── __init__.py        # App initialization
│   └── main.py            # FastAPI application entry point
├── api/                    # API endpoints and route handlers
├── config/                # Configuration settings
├── services/              # Business logic and external service integrations
├── utils/                 # Utility functions and helpers
├── database/              # Database-related code
└── SQL Files:
    ├── setup_vector.sql   # Vector search setup
    ├── vector_search.sql  # Vector search implementation
    ├── create_table.sql   # Database table creation
    └── fix_rls.sql        # Row Level Security fixes
```

### Key Components

- **app/**: Core application package
  - `main.py`: FastAPI server setup, middleware configuration, and route registration
  - `__init__.py`: Application initialization and configuration

- **api/**: Route handlers and endpoint definitions
  - Search endpoints
  - Analysis endpoints
  - Subreddit-specific endpoints

- **services/**: Business logic implementation
  - Reddit data fetching
  - OpenAI integration
  - Data analysis services

- **database/**: Database operations and models
  - Supabase integration
  - Vector search implementation
  - Data models and schemas

## Frontend Structure

```
frontend/
├── src/                   # Source code
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   └── lib/             # Utility functions and shared code
├── public/               # Static assets
└── Configuration:
    ├── next.config.ts    # Next.js configuration
    ├── tailwind.config.ts # Tailwind CSS configuration
    ├── tsconfig.json     # TypeScript configuration
    └── package.json      # Dependencies and scripts
```

### Key Components

- **src/**: Main source code
  - `app/`: Next.js pages and routing
  - `components/`: Reusable React components
  - `lib/`: Shared utilities and API clients

- **Configuration Files**:
  - `next.config.ts`: Next.js framework configuration
  - `tailwind.config.ts`: UI styling configuration
  - `tsconfig.json`: TypeScript compiler settings

## Database Structure

The application uses Supabase with PostgreSQL, featuring:

- Vector search capabilities for efficient data querying
- Row Level Security (RLS) for data access control
- Custom SQL functions for specialized operations

## API Integration Points

- Reddit API: Data collection and subreddit analysis
- OpenAI API: AI-powered analysis and processing
- Supabase: Database operations and vector search 

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/nikonr7/Guliver
cd Guliver
```

### 2. Backend Setup

1. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
```env
# Reddit API Credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_reddit_user_agent

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```


### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

## Running the Application

### 1. Start the Backend Server

```bash
cd backend
python -m app.main
```
The backend server will start at `http://localhost:8000`


In a new terminal:
```bash
cd frontend
npm run dev
```
The frontend will be available at `http://localhost:3000`

## Required Dependencies

### Backend Dependencies
```
openai>=1.0.0
python-dotenv
supabase
requests
tqdm
colorama
aiohttp
fastapi>=0.68.0
uvicorn>=0.15.0
pydantic>=1.8.0
python-multipart
numpy>=1.24.0
pandas>=1.5.0
postgrest>=0.10.6
```

### Frontend Dependencies
```json
{
  "dependencies": {
    "@heroicons/react": "^2.2.0",
    "@supabase/supabase-js": "^2.39.3",
    "next": "14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.7",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.1"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-config-next": "14.1.0",
    "postcss": "^8",
    "tailwindcss": "^3.4.1",
    "typescript": "^5"
  }
}
```
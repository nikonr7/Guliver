# Guliver Project

This project consists of a Next.js frontend and a FastAPI backend with PostgreSQL database integration.

## Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- npm or yarn
- PostgreSQL database

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
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
   - Copy the `.env.example` file to `.env` (if it exists)
   - Configure your environment variables in the `.env` file

4. Set up the database:
```bash
# Run the SQL scripts in the following order
psql -U your_username -d your_database -f create_table.sql
psql -U your_username -d your_database -f setup_vector.sql
psql -U your_username -d your_database -f fix_rls.sql
```

### 3. Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

## Running the Application

### 1. Start the Backend Server

```bash
cd backend
uvicorn main:app --reload
```
The backend server will start at `http://localhost:8000`

### 2. Start the Frontend Development Server

In a new terminal:
```bash
cd frontend
npm run dev
```
The frontend will be available at `http://localhost:3000`

## Environment Variables

Make sure to set up the following environment variables in your `.env` file:

```env
# Backend
DATABASE_URL=your_database_url
OPENAI_API_KEY=your_openai_api_key

# Add any other required environment variables
```

## Additional Notes

- The backend API documentation will be available at `http://localhost:8000/docs`
- Make sure your PostgreSQL database is running before starting the backend server
- For production deployment, use `npm run build` for the frontend and configure appropriate production settings

## Troubleshooting

If you encounter any issues:

1. Ensure all dependencies are correctly installed
2. Verify that your environment variables are properly set
3. Check if the database is running and accessible
4. Ensure all required ports (3000, 8000) are available 
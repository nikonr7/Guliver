import os

PROBLEM_KEYWORDS = [
    "need tool for", "need software for", "looking for tool", "looking for app",
    "recommend tool", "recommend software", "any tools for", "any apps for",
    "frustrated with", "tired of manually", "hate doing", "waste time",
    "wasting time", "takes forever to", "pain point", "pain in the",
    "annoying process", "automate this", "efficiency", "productivity",
    "automation", "workflow", "business needs", "company requires",
    "enterprise solution", "scale our", "manage multiple", "track all",
    "monitor our", "integrate with", "data entry", "manual process",
    "repetitive tasks", "time consuming", "complex workflow",
    "communication gap", "coordination", "collaboration", "solution for",
    "struggle with", "difficult to", "can't figure out", "need to improve",
    "optimize", "streamline", "simplify", "how to solve", "help managing",
    "better way to", "alternative to"
]

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

REDDIT_USER_AGENT = 'MarketResearchBot/1.0'
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
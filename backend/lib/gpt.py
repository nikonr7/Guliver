from openai import AsyncOpenAI
from .reddit import *
from .log_utils import *

class OpenAIClient:
    _client = None
    
    def __new__(cls):
        if cls._client == None:
            cls._client = super().__new__(cls)
            cls._client =  AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        return cls._client

async def analyze_text(text: str) -> str:
    """Analyze text using AI to extract market problems or startup ideas."""
    client = OpenAIClient()
    
    print_step("Analyzing post")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": """You are an expert market research analyst and startup advisor. 
Your task is to analyze both the post and its comments to determine whether they present problems or opportunities for startups. Analyze all discussions to identify:
1. Clear market opportunities and gaps
2. Specific user pain points and problems
3. Potential startup ideas or business solutions
4. Market size indicators and trends
5. Competitive landscape insights

Pay special attention to user comments as they often provide validation of problems and additional context. Be precise, practical, and focus on actionable insights."""},
                {"role": "user", "content": f"Analyze this Reddit post and its comments to extract valuable market insights:\n\n{text}"}
            ],
            max_tokens=500,
            temperature=0.6
        )
        analysis = response.choices[0].message.content.strip()
        print_success("Analysis completed successfully")
        return analysis
    except Exception as e:
        print_error(f"Error during analysis: {e}")
        return ""


async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using advanced text embedding model."""
    client = OpenAIClient()

    print_step("Generating embedding...")
    try:
        response = await client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        print_success("Successfully generated embedding")
        return response.data[0].embedding
    except Exception as e:
        print_error(f"Error generating embedding: {e}")
        return []


async def batch_generate_embeddings(texts: List[str], batch_size: int = 20) -> List[List[float]]:
    """Generate embeddings for multiple texts in batches."""

    client = OpenAIClient()
    
    print_step(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}...")
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            print(f"{Fore.YELLOW}Processing batch of {len(batch)} texts{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}First text in batch (truncated): {batch[0][:100]}...{Style.RESET_ALL}")
            
            response = await client.embeddings.create(
                model="text-embedding-ada-002",
                input=batch
            )
            
            print(f"{Fore.YELLOW}Got response with {len(response.data)} embeddings{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}First embedding length: {len(response.data[0].embedding)}{Style.RESET_ALL}")
            
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            print_success(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        except Exception as e:
            print_error(f"Error in batch {i//batch_size + 1}: {e}")
            # Print full exception details
            import traceback
            print(f"{Fore.RED}Full error: {traceback.format_exc()}{Style.RESET_ALL}")
            # Fill with empty embeddings for failed batch
            all_embeddings.extend([[] for _ in batch])
    
    print(f"{Fore.YELLOW}Total embeddings generated: {len(all_embeddings)}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Number of non-empty embeddings: {sum(1 for e in all_embeddings if e)}{Style.RESET_ALL}")
    
    return all_embeddings

async def analyze_post_with_comments(post: dict) -> str:
    """Analyze post content together with all its comments."""

    client = OpenAIClient()

    print_step("Fetching comments...")
    comments = await fetch_comments_async(post['id'])
    
    # Combine post content with comments
    full_content = f"POST TITLE: {post['title']}\n\nPOST CONTENT: {post['selftext']}\n\n"
    if comments:
        full_content += "COMMENTS:\n"
        for i, comment in enumerate(comments, 1):
            full_content += f"\nComment {i}:\n{comment}\n"
    
    print_step("Analyzing post and comments...")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": """You are an expert market research analyst and startup advisor. 
Analyze both the main post and its comments to identify:
1. Clear market opportunities and gaps
2. Specific user pain points and problems
3. Potential startup ideas or business solutions
4. Market size indicators and trends
5. Competitive landscape insights
6. Additional insights from comment discussions

Focus on actionable insights and note when comments provide additional context or validation to the main post's points."""},
                {"role": "user", "content": f"Analyze this Reddit post and its comments to extract valuable market insights:\n\n{full_content}"}
            ],
            max_tokens=1000,  # Increased for more comments
            temperature=0.6
        )
        analysis = response.choices[0].message.content.strip()
        print_success("Analysis completed successfully")
        return analysis
    except Exception as e:
        print_error(f"Error during analysis: {e}")
        return ""

async def analyze_problem_posts(subreddit: str, timeframe: str = 'week', min_score: int = 5) -> List[Dict]:
    """Main function to find and analyze problem-related posts."""
    # Find posts with problem-related keywords
    posts = await search_problem_posts(subreddit, timeframe, min_score)
    if not posts:
        return []
    
    # Analyze each post with all its comments
    analyzed_posts = []
    for post in posts:
        analysis = await analyze_post_with_comments(post)
        if analysis:
            post['analysis'] = analysis
            analyzed_posts.append(post)
    
    return analyzed_posts
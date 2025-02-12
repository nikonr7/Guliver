from typing import List, Optional
from ..config import openai_client
from ..utils.logging import print_step, print_success, print_error

async def analyze_text(text: str) -> str:
    """Analyze text using AI to extract market problems or startup ideas."""
    print_step("Analyzing post")
    try:
        response = await openai_client.chat.completions.create(
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

async def analyze_post_with_comments(post: dict) -> str:
    """Analyze post content together with all its comments."""
    from .reddit import fetch_comments_async  # Import here to avoid circular dependency
    
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
        response = await openai_client.chat.completions.create(
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
            max_tokens=1000,
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
    print_step("Generating embedding...")
    try:
        response = await openai_client.embeddings.create(
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
    print_step(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}...")
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            print_step(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            response = await openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=batch
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            print_success(f"Processed batch {i//batch_size + 1}")
        except Exception as e:
            print_error(f"Error in batch {i//batch_size + 1}: {e}")
            # Fill with empty embeddings for failed batch
            all_embeddings.extend([[] for _ in batch])
        
    print_success(f"Total embeddings generated: {len(all_embeddings)}")
    return all_embeddings 

async def analyze_posts_batch(posts: List[dict], batch_size: int = 5) -> List[str]:
    """Analyze multiple posts in a single batch to improve performance."""
    print_step(f"Analyzing batch of {len(posts)} posts")
    try:
        # Prepare all posts content
        posts_content = []
        for i, post in enumerate(posts, 1):
            content = f"POST {i}:\nTitle: {post['title']}\nContent: {post.get('selftext', '')}\n\n"
            if 'comments' in post:
                content += "Comments:\n"
                for j, comment in enumerate(post['comments'], 1):
                    content += f"Comment {j}: {comment}\n"
            posts_content.append(content)

        # Split posts into batches
        batches = [posts_content[i:i + batch_size] for i in range(0, len(posts_content), batch_size)]
        all_analyses = []

        for batch in batches:
            batch_content = "\n---\n".join(batch)
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": """You are an expert market research analyst and startup advisor. 
Your task is to analyze multiple posts and their comments to determine whether they present problems or opportunities for startups.
For each post, provide a separate analysis that identifies:
1. Clear market opportunities and gaps
2. Specific user pain points and problems
3. Potential startup ideas or business solutions
4. Market size indicators and trends
5. Competitive landscape insights

Format your response as:
[POST 1]
<your analysis for post 1>

[POST 2]
<your analysis for post 2>

And so on for each post. Be precise, practical, and focus on actionable insights."""},
                    {"role": "user", "content": f"Analyze these Reddit posts and their comments to extract valuable market insights:\n\n{batch_content}"}
                ],
                max_tokens=1000 * len(batch),  # Scale tokens based on batch size
                temperature=0.6
            )
            
            # Split the response into individual post analyses
            analysis = response.choices[0].message.content.strip()
            post_analyses = analysis.split('[POST')[1:]  # Split by [POST and remove empty first element
            all_analyses.extend([a.split(']', 1)[1].strip() for a in post_analyses])

        print_success(f"Successfully analyzed {len(posts)} posts in {len(batches)} batches")
        return all_analyses
    except Exception as e:
        print_error(f"Error during batch analysis: {e}")
        return [""] * len(posts)  # Return empty analyses for all posts in case of error 
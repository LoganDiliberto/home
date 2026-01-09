"""News tool for the agent."""

import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from core.tool import Tool

logger = logging.getLogger(__name__)


class NewsTool(Tool):
    """Tool for getting news articles."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the news tool.
        
        Args:
            api_key: NewsAPI.org API key (if None, tool will return error when used)
        """
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/top-headlines"
        self.everything_url = "https://newsapi.org/v2/everything"
    
    def name(self) -> str:
        """Get the tool name."""
        return "get_news"
    
    def description(self) -> str:
        """Get the tool description."""
        return "Gets recent news articles. Can fetch top headlines by country/category or search for specific topics. Returns article titles, sources, descriptions, and publication times."
    
    def parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for news articles (e.g., 'technology', 'sports', 'politics'). If not provided, returns top headlines."
                },
                "country": {
                    "type": "string",
                    "description": "Two-letter country code for top headlines (e.g., 'us', 'gb', 'ca'). Default is 'us'.",
                    "default": "us"
                },
                "category": {
                    "type": "string",
                    "enum": ["business", "entertainment", "general", "health", "science", "sports", "technology"],
                    "description": "News category for top headlines. Only used if query is not provided."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of articles to return (1-20). Default is 5.",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": []
        }
    
    def execute(self, **kwargs) -> str:
        """Execute the news query."""
        if not self.api_key:
            return "Error: News API key not configured. Please set NEWS_API_KEY environment variable."
        
        query = kwargs.get("query", "")
        country = kwargs.get("country", "us")
        category = kwargs.get("category", "")
        max_results = kwargs.get("max_results", 5)
        
        try:
            if query:
                # Search for specific topics
                params = {
                    "q": query,
                    "apiKey": self.api_key,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": min(max_results, 20)
                }
                url = self.everything_url
            else:
                # Get top headlines
                params = {
                    "country": country,
                    "apiKey": self.api_key,
                    "pageSize": min(max_results, 20)
                }
                if category:
                    params["category"] = category
                url = self.base_url
            
            # Make API request
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "ok":
                return f"Error: News API returned status: {data.get('status', 'unknown')}"
            
            articles = data.get("articles", [])
            
            if not articles:
                if query:
                    return f"No news articles found for query: {query}"
                else:
                    return f"No top headlines found for country: {country}"
            
            # Format response
            result_parts = []
            
            if query:
                result_parts.append(f"Found {len(articles)} news articles about '{query}':")
            else:
                category_str = f" in {category}" if category else ""
                result_parts.append(f"Top {len(articles)} headlines{category_str}:")
            
            result_parts.append("")  # Empty line
            
            for i, article in enumerate(articles[:max_results], 1):
                title = article.get("title", "No title")
                source = article.get("source", {}).get("name", "Unknown source")
                description = article.get("description", "")
                published_at = article.get("publishedAt", "")
                url = article.get("url", "")
                
                # Format date
                if published_at:
                    try:
                        dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        date_str = dt.strftime("%B %d, %Y at %I:%M %p")
                    except:
                        date_str = published_at[:10]  # Just the date part
                else:
                    date_str = "Unknown date"
                
                result_parts.append(f"{i}. {title}")
                result_parts.append(f"   Source: {source} | Published: {date_str}")
                if description:
                    # Truncate long descriptions
                    desc = description[:150] + "..." if len(description) > 150 else description
                    result_parts.append(f"   {desc}")
                result_parts.append("")  # Empty line between articles
            
            return "\n".join(result_parts)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news data: {e}", exc_info=True)
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    return "Error: Invalid news API key"
                elif e.response.status_code == 429:
                    return "Error: News API rate limit exceeded. Please try again later."
                else:
                    return f"Error: News API request failed with status {e.response.status_code}"
            return f"Error: Failed to fetch news data - {str(e)}"
        except Exception as e:
            logger.error(f"Error in news tool: {e}", exc_info=True)
            return f"Error getting news: {str(e)}"


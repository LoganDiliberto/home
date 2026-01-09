"""Web search tool for the agent."""

import logging
from typing import Dict, Any, Optional
from core.tool import Tool

logger = logging.getLogger(__name__)


class WebSearchTool(Tool):
    """Tool for performing web searches."""
    
    def __init__(self, openai_client: Optional[Any] = None):
        """
        Initialize the web search tool.
        
        Args:
            openai_client: OpenAI client instance (optional, for future use with external APIs)
        """
        self.openai_client = openai_client
    
    def name(self) -> str:
        """Get the tool name."""
        return "web_search"
    
    def description(self) -> str:
        """Get the tool description."""
        return "Searches the web for current information, news, facts, or any query. Use this when you need up-to-date information that may not be in your training data, or when the user asks about current events, recent news, or real-time data."
    
    def parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web"
                }
            },
            "required": ["query"]
        }
    
    def execute(self, **kwargs) -> str:
        """Execute the web search."""
        query = kwargs.get("query", "")
        
        if not query:
            return "Error: No search query provided"
        
        # Note: OpenAI's web_search is handled at the API level via web_search_options
        # This tool serves as a signal to the agent that web search should be used
        # The actual search will be performed by OpenAI's model when web_search_options is enabled
        # In the future, this could be extended to use external search APIs like Google Custom Search
        
        logger.info(f"Web search requested for query: {query}")
        
        # Return a message indicating that web search will be performed
        # The agent will use OpenAI's built-in web search capabilities
        return f"Performing web search for: {query}. The search results will be included in the response."


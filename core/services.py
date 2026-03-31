"""Service container for dependency injection."""

import logging
from typing import Any, Dict, Optional, List
from openai import OpenAI
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ServiceContainer:
    """Container for managing service dependencies."""
    
    def __init__(self):
        """Initialize the service container."""
        self._services: Dict[str, Any] = {}
        self._tools: List[Any] = []
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize all services."""
        if self._initialized:
            return
        
        logger.info("Initializing service container...")
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self._services['openai_client'] = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        else:
            self._services['openai_client'] = None
            logger.warning("OpenAI API key not found. LLM features will be disabled")
        
        # Import spotify_controller lazily to avoid circular imports
        # We'll store it as a module reference
        import spotify_controller
        self._services['spotify_controller'] = spotify_controller
        
        # Initialize agent tools
        self._initialize_tools()
        
        self._initialized = True
        logger.info("Service container initialized")
    
    def _initialize_tools(self) -> None:
        """Initialize all agent tools."""
        logger.info("Initializing agent tools...")
        
        from commands.tools import MathTool, LightTool, PlugTool, SpotifyTool
        
        # Initialize math tool (no API key needed)
        math_tool = MathTool()
        self._tools.append(math_tool)
        logger.info("MathTool initialized")
        
        # Initialize light tool (no API key needed)
        light_tool = LightTool()
        self._tools.append(light_tool)
        logger.info("LightTool initialized")
        
        plug_tool = PlugTool()
        self._tools.append(plug_tool)
        logger.info("PlugTool initialized")

        spotify_tool = SpotifyTool()
        self._tools.append(spotify_tool)
        logger.info("SpotifyTool initialized")
        
        logger.info(f"Initialized {len(self._tools)} agent tools")
    
    def get(self, service_name: str) -> Optional[Any]:
        """
        Get a service by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The service instance, or None if not found
        """
        if not self._initialized:
            self.initialize()
        
        return self._services.get(service_name)
    
    def register(self, service_name: str, service: Any) -> None:
        """
        Register a service with the container.
        
        Args:
            service_name: Name of the service
            service: Service instance to register
        """
        self._services[service_name] = service
        logger.debug(f"Registered service: {service_name}")
    
    @property
    def openai_client(self) -> Optional[OpenAI]:
        """Get the OpenAI client."""
        return self.get('openai_client')
    
    @property
    def spotify_controller(self):
        """Get the Spotify controller module."""
        return self.get('spotify_controller')
    
    def get_tools(self) -> List[Any]:
        """
        Get all registered agent tools.
        
        Returns:
            List of tool instances
        """
        if not self._initialized:
            self.initialize()
        return self._tools.copy()
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Any]:
        """
        Get a tool by its name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            Tool instance, or None if not found
        """
        if not self._initialized:
            self.initialize()
        
        for tool in self._tools:
            if tool.name() == tool_name:
                return tool
        return None


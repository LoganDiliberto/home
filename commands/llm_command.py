"""Agent-based LLM command handler with tools and chat history."""

import logging
import json
from typing import TYPE_CHECKING, List, Dict, Any, Optional
from core.command import Command

if TYPE_CHECKING:
    from core.services import ServiceContainer

logger = logging.getLogger(__name__)


class LLMCommand(Command):
    """Agent-based LLM fallback command with tool calling capabilities."""
    
    def __init__(self):
        """Initialize the LLM command with empty chat history."""
        self.chat_history: List[Dict[str, Any]] = []
        # Limit history to last 20 messages to avoid token limits
        self.max_history = 20
        # System message to guide the agent
        self.system_message = {
            "role": "system",
            "content": "You are a helpful voice assistant. You have access to various tools to help answer questions. Use the tools when appropriate to provide accurate and up-to-date information. When using tools, execute them and provide clear, concise responses based on the results."
        }
    
    def can_handle(self, command: str) -> bool:
        """This command can handle any command (fallback)."""
        return True
    
    def _get_tools(self, services: 'ServiceContainer') -> List[Any]:
        """Get all available tools from services."""
        return services.get_tools()
    
    def _get_tool_by_name(self, services: 'ServiceContainer', tool_name: str) -> Optional[Any]:
        """Get a specific tool by name."""
        return services.get_tool_by_name(tool_name)
    
    def _tools_to_openai_functions(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """Convert tool instances to OpenAI function definitions."""
        return [tool.to_openai_function() for tool in tools]
    
    def _execute_tool(self, services: 'ServiceContainer', tool_name: str, arguments: str) -> str:
        """Execute a tool with given arguments."""
        try:
            # Parse arguments JSON
            if isinstance(arguments, str):
                args_dict = json.loads(arguments)
            else:
                args_dict = arguments
            
            # Get the tool
            tool = self._get_tool_by_name(services, tool_name)
            if not tool:
                return f"Error: Tool '{tool_name}' not found"
            
            # Execute the tool
            logger.info(f"Executing tool: {tool_name} with arguments: {args_dict}")
            result = tool.execute(**args_dict)
            logger.info(f"Tool {tool_name} returned: {result[:100]}...")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing tool arguments JSON: {e}")
            return f"Error: Invalid tool arguments format - {str(e)}"
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return f"Error executing tool {tool_name}: {str(e)}"
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute agent command with tool calling capabilities."""
        logger.info("No specific command matched, sending to agent")
        
        client = services.openai_client
        if not client:
            logger.warning("OpenAI client not available")
            return "OpenAI API key not configured"
        
        model = "gpt-4o-mini"
        
        # Get available tools
        tools = self._get_tools(services)
        functions = self._tools_to_openai_functions(tools)
        
        logger.info(f"Agent has access to {len(tools)} tools: {[tool.name() for tool in tools]}")
        
        # Initialize chat history with system message if empty
        if not self.chat_history:
            self.chat_history = [self.system_message.copy()]
        
        # Add user message to chat history
        self.chat_history.append({"role": "user", "content": command})
        
        # Trim history if it exceeds max_history
        if len(self.chat_history) > self.max_history:
            # Keep system message, then keep most recent messages
            system_messages = [msg for msg in self.chat_history if msg.get("role") == "system"]
            other_messages = [msg for msg in self.chat_history if msg.get("role") != "system"]
            self.chat_history = system_messages + other_messages[-(self.max_history - len(system_messages)):]
        
        
        logger.info(f"Sending prompt to agent: {command[:100]}...")
        
        try:
            # Prepare messages for API call
            messages = self.chat_history.copy()
            
            # Track if web_search_options is supported (try once, remember result)
            web_search_supported = True
            
            # Tool calling loop
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Prepare API call parameters
                api_params = {
                    "model": model,
                    "messages": messages,
                }
                
                # Add tools if available
                if functions:
                    api_params["tools"] = functions
                
                
                # Make the API call
                try:
                    response = client.chat.completions.create(**api_params)
                except Exception as api_error:
                    logger.warning(f"Failure, trying again: {api_error}")
                    response = client.chat.completions.create(**api_params)
                
                response_message = response.choices[0].message
                response_text = response_message.content
                
                # Convert response message to dict format for messages list
                assistant_message: Dict[str, Any] = {
                    "role": "assistant",
                    "content": response_text if response_text else None
                }
                
                # Check if the model wants to use tools
                if response_message.tool_calls and len(response_message.tool_calls) > 0:
                    logger.info(f"Agent requested {len(response_message.tool_calls)} tool call(s) (iteration {iteration})")
                    
                    # Add tool calls to the assistant message
                    tool_calls_list = []
                    for tool_call in response_message.tool_calls:
                        tool_calls_list.append({
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        })
                    
                    assistant_message["tool_calls"] = tool_calls_list
                    messages.append(assistant_message)
                    
                    # Execute each tool call and add results
                    for tool_call in response_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments
                        tool_call_id = tool_call.id
                        
                        logger.info(f"Executing tool: {tool_name}")
                        tool_result = self._execute_tool(services, tool_name, tool_args)
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": tool_result
                        })
                    
                    # Continue the loop to get the agent's response with tool results
                    continue
                else:
                    # No tool calls, we have the final response
                    if response_text:
                        messages.append(assistant_message)
                    break
            
            # Update chat history with the full conversation
            self.chat_history = messages
            
            if not response_text:
                response_text = "I apologize, but I couldn't generate a response. Please try again."
            
            logger.info(f"Agent response received: {response_text[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
            # Remove the user message from history if there was an error
            if self.chat_history and self.chat_history[-1].get("role") == "user":
                self.chat_history.pop()
            return f"Error getting response from AI: {str(e)}"
    
    def get_priority(self) -> int:
        """Lowest priority - this is the fallback handler."""
        return -100

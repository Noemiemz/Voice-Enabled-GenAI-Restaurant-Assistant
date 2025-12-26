"""
LangChain-enhanced base agent for the restaurant assistant system.
Provides common functionality with LangChain integration.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import json
import uuid

# LangChain imports
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.schema import SystemMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool
from langchain_classic.chains import LLMChain
from langchain_classic.llms.base import LLM


class AgentMessage(BaseModel):
    """Base message format for agent communication with LangChain support."""
    sender: str = Field(..., description="Name of the sending agent")
    receiver: str = Field(..., description="Name of the receiving agent")
    message_type: str = Field(..., description="Type of message (query, response, error, etc.)")
    content: Dict[str, Any] = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    langchain_messages: Optional[List[Dict[str, Any]]] = Field(None, description="LangChain message format")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return self.model_dump()
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return self.model_dump_json()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """Create message from JSON string."""
        return cls(**json.loads(json_str))
    
    def to_langchain_messages(self) -> List:
        """Convert to LangChain message format."""
        if self.langchain_messages:
            return self.langchain_messages
        
        # Convert our message to LangChain format
        messages = []
        
        # Add system message with context
        messages.append(SystemMessage(content=f"Agent communication: {self.message_type}"))
        
        # Add human message with content
        content_str = json.dumps(self.content)
        messages.append(HumanMessage(content=f"From {self.sender} to {self.receiver}: {content_str}"))
        
        return messages


class LangChainBaseAgent:
    """Base class for all LangChain-enhanced agents in the system."""
    
    def __init__(self, name: str, llm: LLM, description: str = "", memory: Optional[ConversationBufferMemory] = None):
        """
        Initialize the LangChain base agent.
        
        Args:
            name: Unique identifier for the agent
            llm: Language model to use
            description: Description of the agent's purpose
            memory: Optional conversation memory
        """
        self.name = name
        self.description = description
        self.llm = llm
        self.conversation_history = []
        
        # Set up memory
        self.memory = memory or ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Set up basic LLM chain for general processing
        self.basic_chain = self._create_basic_chain()
        
        # Agent tools will be registered by subclasses
        self.tools = []
        self.agent_executor = None
    
    def _create_basic_chain(self) -> LLMChain:
        """Create a basic LLM chain for general processing."""
        from langchain_classic.prompts import PromptTemplate
        
        template = """
        You are a helpful restaurant assistant named {agent_name}.
        Current task: {task}
        Context: {context}
        
        Respond appropriately:
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["agent_name", "task", "context"]
        )
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            memory=self.memory
        )
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a LangChain tool with the agent."""
        self.tools.append(tool)
        
        # If we have tools, set up the agent executor
        if len(self.tools) > 0:
            self._setup_agent_executor()
    
    def _setup_agent_executor(self) -> None:
        """Set up the LangChain agent executor."""
        from langchain_classic.agents import initialize_agent
        from langchain_classic.agents.agent_types import AgentType
        
        # Create the agent
        self.agent_executor = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
    
    def send_message(self, receiver: str, message_type: str, content: Dict[str, Any], 
                    conversation_id: Optional[str] = None) -> AgentMessage:
        """
        Create and send a message to another agent with LangChain processing.
        
        Args:
            receiver: Name of the receiving agent
            message_type: Type of message
            content: Message content
            conversation_id: Optional conversation identifier
            
        Returns:
            AgentMessage object
        """
        # Process content with LLM if needed
        processed_content = self._process_content_with_llm(message_type, content)
        
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=processed_content,
            conversation_id=conversation_id
        )
        
        # Store in conversation history
        self._add_to_conversation_history(message)
        
        return message
    
    def _process_content_with_llm(self, message_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Process message content with LLM if appropriate."""
        # For certain message types, we might want LLM processing
        if message_type in ["user_query", "complex_decision"]:
            try:
                # Use our basic chain to enhance the content
                task = f"Process {message_type} message"
                context = json.dumps(content)
                
                result = self.basic_chain.run({
                    "agent_name": self.name,
                    "task": task,
                    "context": context
                })
                
                # Add LLM processing result to content
                content["llm_processing"] = {
                    "enhanced_content": result,
                    "original_content": content.copy()
                }
                
            except Exception as e:
                content["llm_error"] = str(e)
        
        return content
    
    def receive_message(self, message: AgentMessage) -> Dict[str, Any]:
        """
        Receive and process a message from another agent with LangChain.
        
        Args:
            message: AgentMessage object
            
        Returns:
            Response content
        """
        # Store in conversation history
        self._add_to_conversation_history(message)
        
        # Add to LangChain memory
        self._add_to_langchain_memory(message)
        
        # Process the message (to be implemented by subclasses)
        return self._process_message(message)
    
    def _add_to_langchain_memory(self, message: AgentMessage) -> None:
        """Add message to LangChain memory."""
        try:
            # Convert our message to LangChain format
            langchain_messages = message.to_langchain_messages()
            
            # Add to memory
            for msg in langchain_messages:
                if isinstance(msg, SystemMessage):
                    self.memory.chat_memory.add_system_message(msg.content)
                elif isinstance(msg, HumanMessage):
                    self.memory.chat_memory.add_user_message(msg.content)
                elif isinstance(msg, AIMessage):
                    self.memory.chat_memory.add_ai_message(msg.content)
                    
        except Exception as e:
            print(f"Error adding to LangChain memory: {e}")
    
    def _add_to_conversation_history(self, message: AgentMessage) -> None:
        """Add message to conversation history."""
        self.conversation_history.append(message.to_dict())
    
    def _process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """
        Process an incoming message. To be implemented by subclasses.
        
        Args:
            message: AgentMessage object
            
        Returns:
            Response content
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement _process_message method")
    
    def get_conversation_history(self, conversation_id: Optional[str] = None) -> list:
        """
        Get conversation history.
        
        Args:
            conversation_id: Optional conversation identifier to filter by
            
        Returns:
            List of message dictionaries
        """
        if conversation_id:
            return [msg for msg in self.conversation_history if msg.get('conversation_id') == conversation_id]
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        self.memory.clear()
    
    def use_agent_executor(self, input_data: str) -> str:
        """
        Use the LangChain agent executor to process input.
        
        Args:
            input_data: Input for the agent
            
        Returns:
            Agent response
            
        Raises:
            RuntimeError: If agent executor is not set up
        """
        if not self.agent_executor:
            raise RuntimeError("Agent executor not set up. Register tools first.")
        
        return self.agent_executor.run(input=input_data)
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"
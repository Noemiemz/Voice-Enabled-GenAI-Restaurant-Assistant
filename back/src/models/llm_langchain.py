"""
LangChain wrapper for the Mistral LLM.
Integrates the existing Mistral wrapper with LangChain's LLM interface.
"""

from typing import Any, Dict, List, Optional, Union
from langchain_classic.llms.base import LLM
from langchain.chat_models.base import BaseChatModel
from langchain_classic.schema import (
    AIMessage, 
    BaseMessage, 
    ChatMessage, 
    ChatResult, 
    HumanMessage, 
    SystemMessage
)
from langchain_classic.callbacks.manager import CallbackManagerForLLMRun
from models.llm import MistralWrapper, MistralModel
from smolagents.models import ChatMessage as SmolChatMessage
import json
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LangChainMistralLLM(LLM):
    """
    LangChain wrapper for Mistral LLM.
    Implements the LLM interface for compatibility with LangChain.
    """
    
    mistral_wrapper: MistralWrapper = None
    model_name: str = "mistral-small-2506"
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def __init__(self, api_key: Optional[str] = None, **kwargs: Any):
        """Initialize the LangChain Mistral LLM wrapper."""
        super().__init__(**kwargs)
        self.mistral_wrapper = MistralWrapper(api_key=api_key)
        self.model_name = kwargs.get('model_name', 'mistral-small-2506')
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 1000)
    
    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return "mistral"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> str:
        """Call the Mistral LLM with the given prompt."""
        
        try:
            # Use the Mistral wrapper to generate response
            response = self.mistral_wrapper.generate_from_prompt(
                user_prompt=prompt,
                history=[],
                **kwargs
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in LangChain Mistral LLM call: {e}")
            raise ValueError(f"Mistral LLM error: {str(e)}")
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> List[str]:
        """Generate responses for multiple prompts."""
        return [self._call(prompt, stop, run_manager, **kwargs) for prompt in prompts]
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


class LangChainMistralChatModel(BaseChatModel):
    """
    LangChain chat model wrapper for Mistral.
    Implements the BaseChatModel interface for chat-based interactions.
    """
    
    mistral_model: MistralModel = None
    model_name: str = "mistral-small-2506"
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def __init__(self, api_key: Optional[str] = None, **kwargs: Any):
        """Initialize the LangChain Mistral chat model."""
        super().__init__(**kwargs)
        self.mistral_model = MistralModel(api_key=api_key)
        self.model_name = kwargs.get('model_name', 'mistral-small-2506')
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 1000)
    
    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return "mistral-chat"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> ChatResult:
        """Generate a chat response from Mistral."""
        
        try:
            # Convert LangChain messages to Mistral format
            mistral_messages = self._convert_messages(messages)
            
            # Call Mistral model
            response = self.mistral_model.generate(mistral_messages, **kwargs)
            
            # Convert response back to LangChain format
            ai_message = self._convert_to_ai_message(response)
            
            # Create chat result
            chat_result = ChatResult(
                generations=[[ai_message]],
                llm_output={}
            )
            
            return chat_result
            
        except Exception as e:
            logger.error(f"Error in LangChain Mistral chat generation: {e}")
            raise ValueError(f"Mistral chat error: {str(e)}")
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Convert LangChain messages to Mistral format."""
        mistral_messages = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                mistral_messages.append({"role": "system", "content": message.content})
            elif isinstance(message, HumanMessage):
                mistral_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                mistral_messages.append({"role": "assistant", "content": message.content})
            elif isinstance(message, ChatMessage):
                mistral_messages.append({"role": message.role, "content": message.content})
            else:
                mistral_messages.append({"role": "user", "content": str(message)})
        
        return mistral_messages
    
    def _convert_to_ai_message(self, response: SmolChatMessage) -> AIMessage:
        """Convert Mistral response to LangChain AIMessage."""
        return AIMessage(content=response.content)
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


def create_mistral_llm(api_key: Optional[str] = None, **kwargs: Any) -> LLM:
    """Create a LangChain-compatible Mistral LLM."""
    return LangChainMistralLLM(api_key=api_key, **kwargs)


def create_mistral_chat_model(api_key: Optional[str] = None, **kwargs: Any) -> BaseChatModel:
    """Create a LangChain-compatible Mistral chat model."""
    return LangChainMistralChatModel(api_key=api_key, **kwargs)


def get_mistral_api_key() -> Optional[str]:
    """Get Mistral API key from environment variables."""
    import os
    return os.getenv('MISTRAL_API_KEY')


def create_default_mistral_llm() -> LLM:
    """Create a default Mistral LLM with environment API key."""
    api_key = get_mistral_api_key()
    if not api_key:
        logger.warning("No Mistral API key found in environment variables")
        # Fallback to mock for testing
        from langchain_classic.llms.fake import FakeListLLM
        return FakeListLLM(responses=["Mock Mistral response"])
    
    return create_mistral_llm(api_key=api_key)


def create_default_mistral_chat_model() -> BaseChatModel:
    """Create a default Mistral chat model with environment API key."""
    api_key = get_mistral_api_key()
    if not api_key:
        logger.warning("No Mistral API key found in environment variables")
        # Fallback to mock for testing
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(model_name="gpt-3.5-turbo")  # Fallback
    
    return create_mistral_chat_model(api_key=api_key)


# Example usage
if __name__ == "__main__":
    logger.info("Testing Mistral LangChain integration...")
    
    # Create LLM
    llm = create_default_mistral_llm()
    logger.info(f"Created LLM: {llm}")
    
    # Create chat model
    chat_model = create_default_mistral_chat_model()
    logger.info(f"Created chat model: {chat_model}")
    
    # Test simple call
    try:
        result = llm("Hello, how are you?")
        logger.info(f"LLM result: {result}")
    except Exception as e:
        logger.error(f"LLM test failed: {e}")
    
    # Test chat call
    try:
        from langchain_classic.schema import HumanMessage
        messages = [HumanMessage(content="What's the weather today?")]
        result = chat_model.generate([messages])
        logger.info(f"Chat result: {result}")
    except Exception as e:
        logger.error(f"Chat test failed: {e}")
    
    logger.info("Mistral LangChain integration test complete")
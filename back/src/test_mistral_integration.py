"""
Test script for Mistral LangChain integration.
Verifies that the Mistral wrapper works correctly with LangChain.
"""

import logging
from models.llm_langchain import create_mistral_llm, create_mistral_chat_model
from agents_langchain.langchain_integration import setup_langchain_agents


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_mistral_llm_creation():
    """Test Mistral LLM creation."""
    logger.info("Testing Mistral LLM creation...")
    
    try:
        # Try to create Mistral LLM
        llm = create_mistral_llm()
        logger.info(f"✅ Mistral LLM created successfully: {llm}")
        logger.info(f"   LLM Type: {llm._llm_type}")
        logger.info(f"   Model Name: {llm.model_name}")
        return True
    except Exception as e:
        logger.warning(f"❌ Mistral LLM creation failed: {e}")
        return False


def test_mistral_chat_model_creation():
    """Test Mistral chat model creation."""
    logger.info("Testing Mistral chat model creation...")
    
    try:
        # Try to create Mistral chat model
        chat_model = create_mistral_chat_model()
        logger.info(f"✅ Mistral chat model created successfully: {chat_model}")
        logger.info(f"   Model Type: {chat_model._llm_type}")
        return True
    except Exception as e:
        logger.warning(f"❌ Mistral chat model creation failed: {e}")
        return False


def test_agent_system_with_mistral():
    """Test agent system with Mistral LLM."""
    logger.info("Testing agent system with Mistral LLM...")
    
    try:
        # Try to create agent system with Mistral
        llm = create_mistral_llm()
        system = setup_langchain_agents(llm=llm, use_mock_db=True)
        
        logger.info(f"✅ Agent system with Mistral created successfully")
        logger.info(f"   UI Agent: {system['ui_agent'].name}")
        logger.info(f"   Orchestrator: {system['orchestrator'].name}")
        logger.info(f"   Tools: {len(system['orchestrator'].tools)}")
        return True
    except Exception as e:
        logger.warning(f"❌ Agent system with Mistral failed: {e}")
        return False


def test_fallback_to_mock():
    """Test fallback to mock LLM when Mistral is not available."""
    logger.info("Testing fallback to mock LLM...")
    
    try:
        # This should always work (falls back to mock)
        from agents_langchain.langchain_integration import setup_langchain_agents
        system = setup_langchain_agents(use_mock_db=True)
        
        logger.info(f"✅ Fallback system created successfully")
        logger.info(f"   LLM Type: {system['llm'].__class__.__name__}")
        return True
    except Exception as e:
        logger.error(f"❌ Fallback system creation failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("🚀 Starting Mistral LangChain integration tests...")
    
    tests = [
        ("Mistral LLM Creation", test_mistral_llm_creation),
        ("Mistral Chat Model Creation", test_mistral_chat_model_creation),
        ("Agent System with Mistral", test_agent_system_with_mistral),
        ("Fallback to Mock", test_fallback_to_mock)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Mistral integration is working correctly.")
    else:
        logger.warning("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
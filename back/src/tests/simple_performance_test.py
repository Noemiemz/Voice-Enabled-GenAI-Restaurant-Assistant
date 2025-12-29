#!/usr/bin/env python3
"""
Simple performance test script for the Restaurant Assistant API
This script tests the query "what is the list of dishes available?" with minimal overhead
"""

import os
import sys
import time
import json
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our components to ensure they're initialized
from models.mongodb import MongoDBManager
from agents.agent_manager import AgentManager
from run.app import app
from utils.timing import log_timing

def test_menu_query_directly():
    """Test the menu query directly without starting a full server"""
    
    print("=== Simple Performance Test ===")
    print("Testing query: 'what is the list of dishes available?'")
    print()
    
    # Initialize components
    print("Initializing components...")
    db_manager = MongoDBManager()
    agent_manager = AgentManager()
    
    # Try to initialize agents
    try:
        agent_manager.initialize()
        print("[SUCCESS] Agents initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize agents: {e}")
        return
    
    # Create orchestrator
    try:
        from agents.orchestrator import create_orchestrator_agent
        orchestrator = create_orchestrator_agent(agent_manager)
        print("[SUCCESS] Orchestrator created")
    except Exception as e:
        print(f"[ERROR] Failed to create orchestrator: {e}")
        return
    
    # Test the query
    test_query = "what is the list of dishes available?"
    user_id = "test_user"
    
    print(f"Running test query: '{test_query}'")
    print()
    
    # Start overall timing
    overall_start = time.time()
    
    try:
        # Create context
        from utils.utils import Context
        context = Context(user_id=user_id, verbose=True)
        config = {"configurable": {"thread_id": user_id}}
        
        # Start orchestrator timing
        orchestrator_start = time.time()
        
        # Invoke the orchestrator
        result = orchestrator.invoke(
            {"messages": [{"role": "user", "content": test_query}]},
            config=config,
            context=context,
        )
        
        # End orchestrator timing
        orchestrator_duration = time.time() - orchestrator_start
        
        # Extract the response
        response = result["messages"][-1].content if result.get("messages") else "No response"
        
        # End overall timing
        overall_duration = time.time() - overall_start
        
        print(f"[SUCCESS] Query completed in {overall_duration:.3f}s")
        print(f"Orchestrator processing time: {orchestrator_duration:.3f}s")
        print(f"Response length: {len(response)} characters")
        print()
        
        # Show response preview
        print("Response preview:")
        print("-" * 50)
        print(response[:300] + "..." if len(response) > 300 else response)
        print("-" * 50)
        print()
        
        # Log the timing data
        log_timing("test_query_execution", overall_duration, {
            "query": test_query,
            "response_length": len(response),
            "orchestrator_time": orchestrator_duration,
            "overhead_time": overall_duration - orchestrator_duration
        })
        
    except Exception as e:
        error_duration = time.time() - overall_start
        print(f"[ERROR] Query failed after {error_duration:.3f}s: {e}")
        log_timing("test_query_error", error_duration, {
            "query": test_query,
            "error": str(e)
        })
        return
    
    # Analyze timing logs
    print("=== Timing Log Analysis ===")
    analyze_timing_logs()


def analyze_timing_logs():
    """Analyze the timing logs generated during the test"""
    
    try:
        from pathlib import Path
        import json
        from datetime import datetime
        
        # Get the logs directory
        current_dir = Path(__file__).parent.parent
        log_dir = current_dir / "data" / "logs"
        
        if not log_dir.exists():
            print("No timing logs found")
            return
        
        # Find today's performance log
        today_date = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f"performance_log_{today_date}.jsonl"
        
        if not log_file.exists():
            print("No performance log file found for today")
            return
        
        # Read and analyze the log
        operations = {}
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    operation = entry.get('operation', 'unknown')
                    duration = entry.get('duration_seconds', 0)
                    
                    if operation not in operations:
                        operations[operation] = {
                            'count': 0,
                            'total_time': 0,
                            'min_time': float('inf'),
                            'max_time': 0,
                            'contexts': []
                        }
                    
                    operations[operation]['count'] += 1
                    operations[operation]['total_time'] += duration
                    operations[operation]['min_time'] = min(operations[operation]['min_time'], duration)
                    operations[operation]['max_time'] = max(operations[operation]['max_time'], duration)
                    operations[operation]['contexts'].append(entry.get('context', {}))
                    
                except json.JSONDecodeError:
                    continue
        
        # Print analysis results
        if operations:
            print("Timing breakdown by operation:")
            print("-" * 60)
            
            # Sort by total time descending
            sorted_ops = sorted(operations.items(), key=lambda x: x[1]['total_time'], reverse=True)
            
            for op_name, op_data in sorted_ops:
                avg_time = op_data['total_time'] / op_data['count'] if op_data['count'] > 0 else 0
                print(f"{op_name}:")
                print(f"  Count: {op_data['count']}")
                print(f"  Total: {op_data['total_time']:.6f}s")
                print(f"  Average: {avg_time:.6f}s")
                print(f"  Min: {op_data['min_time']:.6f}s")
                print(f"  Max: {op_data['max_time']:.6f}s")
                
                # Show key context info for the most recent call
                if op_data['contexts']:
                    latest_context = op_data['contexts'][-1]
                    if latest_context:
                        # Show only key context info to avoid clutter
                        key_context = {}
                        if 'query_length' in latest_context:
                            key_context['query_length'] = latest_context['query_length']
                        if 'response_length' in latest_context:
                            key_context['response_length'] = latest_context['response_length']
                        if 'agent_name' in latest_context:
                            key_context['agent_name'] = latest_context['agent_name']
                        if 'operation' in latest_context:
                            key_context['operation'] = latest_context['operation']
                        if key_context:
                            print(f"  Context: {key_context}")
                print()
        else:
            print("No timing operations found in log")
            
    except Exception as e:
        print(f"Error analyzing timing logs: {e}")


if __name__ == "__main__":
    # Set environment variables for testing
    os.environ["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY", "")  # Use existing or empty for mock
    os.environ["MONGODB_URI"] = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    os.environ["MONGODB_DB_NAME"] = os.getenv("MONGODB_DB_NAME", "Restaurant_DB")
    
    test_menu_query_directly()
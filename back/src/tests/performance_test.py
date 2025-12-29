#!/usr/bin/env python3
"""
Performance test script for the Restaurant Assistant API
This script tests the query "what is the list of dishes available?" and analyzes timing data
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our components to ensure they're initialized
from models.mongodb import MongoDBManager
from agents.agent_manager import AgentManager
from run.app import app

import threading
import time
from werkzeug.serving import make_server

class TestServer(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server('127.0.0.1', 5001, app)
        self.ctx = app.app_context()
        self.ctx.push()
        
    def run(self):
        print("Starting test server on port 5001...")
        self.server.serve_forever()
        
    def shutdown(self):
        print("Shutting down test server...")
        self.server.shutdown()


def run_performance_test():
    """Run performance test for the menu query"""
    
    print("=== Restaurant Assistant Performance Test ===")
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
    
    # Start test server in a separate thread
    test_server = TestServer(app)
    test_server.start()
    time.sleep(2)  # Give server time to start
    
    try:
        # Test the query multiple times to get average performance
        test_query = "what is the list of dishes available?"
        num_tests = 3
        
        print(f"Running {num_tests} test queries...")
        print()
        
        total_time = 0
        responses = []
        
        for i in range(num_tests):
            print(f"Test {i+1}/{num_tests}:")
            
            # Make the API request
            start_time = time.time()
            
            try:
                response = requests.post(
                    'http://127.0.0.1:5001/query',
                    json={'query': test_query},
                    headers={'X-User-ID': 'test_user'},
                    timeout=30
                )
                
                request_time = time.time() - start_time
                total_time += request_time
                
                if response.status_code == 200:
                    result = response.json()
                    responses.append(result)
                    
                    print(f"  [SUCCESS] Success: {request_time:.3f}s")
                    print(f"  Response length: {len(result.get('response', ''))} characters")
                    
                    # Show performance breakdown if available
                    if 'performance' in result:
                        perf = result['performance']
                        print(f"  Total processing: {perf.get('total_processing_time', 0):.3f}s")
                        print(f"  Orchestrator time: {perf.get('orchestrator_time', 0):.3f}s")
                    print()
                else:
                    print(f"  [ERROR] Failed: Status {response.status_code}")
                    print(f"  Response: {response.text}")
                    print()
                    
            except Exception as e:
                print(f"  [ERROR] Error: {e}")
                print()
        
        # Calculate statistics
        if responses:
            avg_time = total_time / len(responses)
            print("=== Performance Summary ===")
            print(f"Average response time: {avg_time:.3f}s")
            print(f"Total time for {len(responses)} tests: {total_time:.3f}s")
            print()
            
            # Show a sample response
            print("Sample response:")
            print("-" * 50)
            sample_response = responses[0].get('response', 'No response')
            print(sample_response[:500] + "..." if len(sample_response) > 500 else sample_response)
            print("-" * 50)
            print()
        
        # Analyze timing logs
        print("=== Timing Log Analysis ===")
        analyze_timing_logs()
        
    finally:
        # Shutdown the test server
        test_server.shutdown()
        test_server.join()
        print("Test server stopped")


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
                        print(f"  Context: {latest_context}")
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
    
    run_performance_test()
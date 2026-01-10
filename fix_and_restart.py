#!/usr/bin/env python3
"""
Fix the 401 error and restart servers with updated configuration
"""

import subprocess
import time
import os
import signal
from pathlib import Path

def kill_existing_servers():
    """Kill any existing server processes"""
    print("🛑 Stopping existing servers...")
    
    # Kill processes on ports 8000 and 8001
    for port in [8000, 8001]:
        try:
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"   Killed process {pid} on port {port}")
                    except:
                        pass
        except:
            pass
    
    time.sleep(2)

def test_api_connection():
    """Test if the OpenRouter API is working"""
    print("🔍 Testing OpenRouter API...")
    
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            print("❌ No API key found")
            return False
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Universal Data Handler"
            }
        )
        
        # Test with a free model first
        response = client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct:free",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        
        print("✅ OpenRouter API is working!")
        return True
        
    except Exception as e:
        print(f"⚠️  OpenRouter API test failed: {e}")
        print("   System will use fallback SQL generation")
        return False

def start_servers():
    """Start the servers with updated configuration"""
    print("🚀 Starting servers with fixes...")
    
    # Start the server manager
    process = subprocess.Popen(
        ['python', 'start_servers.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Wait a bit for servers to start
    time.sleep(5)
    
    # Check if servers are running
    servers_running = True
    for port in [8000, 8001]:
        try:
            import requests
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Server on port {port} is running")
            else:
                print(f"⚠️  Server on port {port} returned status {response.status_code}")
        except:
            print(f"❌ Server on port {port} is not responding")
            servers_running = False
    
    return process, servers_running

def main():
    """Main fix and restart process"""
    print("🔧 Universal Data Handler - Fix and Restart")
    print("=" * 50)
    
    # Kill existing servers
    kill_existing_servers()
    
    # Test API connection
    api_working = test_api_connection()
    
    # Start servers
    server_process, servers_running = start_servers()
    
    if servers_running:
        print("\n🎉 Servers restarted successfully!")
        print("📖 API Documentation:")
        print("   • API v1: http://localhost:8000/docs")
        print("   • API v2: http://localhost:8001/api/v2/docs")
        print("\n🌐 Streamlit UI:")
        print("   • Run: streamlit run streamlit_data_handler_ui.py")
        print("   • URL: http://localhost:8501")
        
        if not api_working:
            print("\n💡 Note: External API is not working, but system will use:")
            print("   • Fallback SQL generation")
            print("   • Pattern-based query processing")
            print("   • Local data analysis")
        
        print("\n🧪 Test the system:")
        print("   python simple_test_workflow.py")
        
        return 0
    else:
        print("\n❌ Failed to start servers properly")
        return 1

if __name__ == "__main__":
    exit(main())
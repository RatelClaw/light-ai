#!/usr/bin/env python3
"""
Startup script for Universal Data Handler
Starts both API servers (v1 and v2) and optionally the Streamlit UI
"""

import subprocess
import time
import sys
import signal
import os
from pathlib import Path

class ServerManager:
    def __init__(self):
        self.processes = []
        self.running = True
    
    def start_server(self, command, name, delay=2):
        """Start a server process"""
        print(f"🚀 Starting {name}...")
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            self.processes.append((process, name))
            print(f"✅ {name} started (PID: {process.pid})")
            time.sleep(delay)
            return process
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return None
    
    def check_servers(self):
        """Check if servers are running"""
        for process, name in self.processes:
            if process.poll() is not None:
                print(f"⚠️  {name} has stopped")
                return False
        return True
    
    def stop_all(self):
        """Stop all server processes"""
        print("\n🛑 Stopping all servers...")
        self.running = False
        
        for process, name in self.processes:
            try:
                if os.name != 'nt':
                    # Unix-like systems
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    # Windows
                    process.terminate()
                print(f"✅ Stopped {name}")
            except Exception as e:
                print(f"⚠️  Error stopping {name}: {e}")
        
        # Wait for processes to terminate
        for process, name in self.processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\n📡 Received signal {signum}")
        self.stop_all()
        sys.exit(0)

def main():
    # Check if virtual environment is activated
    if not os.environ.get('VIRTUAL_ENV') and not sys.prefix != sys.base_prefix:
        print("⚠️  Warning: Virtual environment not detected")
        print("💡 Recommendation: Activate your virtual environment first:")
        print("   source .venv/bin/activate  # On Unix/macOS")
        print("   .venv\\Scripts\\activate     # On Windows")
        print()
    
    manager = ServerManager()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    print("🌟 Universal Data Handler - Server Manager")
    print("=" * 50)
    
    # Start API v1 (port 8000)
    api_v1_cmd = "python -m light_ai.fastapi_server --host 127.0.0.1 --port 8000"
    manager.start_server(api_v1_cmd, "API v1 (Port 8000)")
    
    # Start API v2 (port 8001)
    api_v2_cmd = "python -m light_ai.api_v2 --host 127.0.0.1 --port 8001"
    manager.start_server(api_v2_cmd, "API v2 (Port 8001)")
    
    # Check if servers started successfully
    time.sleep(3)
    if not manager.check_servers():
        print("❌ Some servers failed to start")
        manager.stop_all()
        return 1
    
    print("\n🎉 All servers started successfully!")
    print("📖 API Documentation:")
    print("   • API v1 (Basic): http://127.0.0.1:8000/docs")
    print("   • API v2 (Advanced): http://127.0.0.1:8001/api/v2/docs")
    print("\n🚀 To start Streamlit UI, run in another terminal:")
    print("   streamlit run streamlit_data_handler_ui.py")
    print("\n⏹️  Press Ctrl+C to stop all servers")
    
    # Keep running and monitor servers
    try:
        while manager.running:
            time.sleep(5)
            if not manager.check_servers():
                print("❌ Server monitoring detected failures")
                break
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_all()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
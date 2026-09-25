
"""
run_app.py
Entry point to launch the NefroAI Chronic Kidney Disease (CKD) Web Application.
Run with:
    python run_app.py
or:
    streamlit run frontend/app.py
"""

import os
import sys
import socket
import subprocess

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(root_dir, "frontend", "app.py")
    
    print("================================================================")
    print("       NefroAI: Chronic Kidney Disease Clinical Platform        ")
    print("   Explainable AI & Personalized Healthcare  ")
    print("================================================================")
    print(f"Starting Streamlit dashboard from: {app_path}")
    print("Connecting to local MongoDB Compass at: mongodb://localhost:27017")
    port = 8501
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_busy = (sock.connect_ex(("127.0.0.1", port)) == 0)
    sock.close()
    
    if is_busy:
        print(f"[NOTE] Port {port} is already active with a running dashboard.")
        print(f"You can open your browser directly at: http://localhost:{port}")
        print("Or starting an alternate session on port 8502...\n")
        port = 8502

    print(f"Dashboard URL: http://localhost:{port}")
    print("Press Ctrl+C to stop.\n")
    
    cmd = [sys.executable, "-m", "streamlit", "run", app_path, "--server.port", str(port)]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nNefroAI application stopped.")

if __name__ == "__main__":
    main()

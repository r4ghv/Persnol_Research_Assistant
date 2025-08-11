#!/usr/bin/env python3
"""Simple launcher for the Personal Research Assistant"""

import subprocess
import sys
import time

def main():
    print("🚀 Launching Personal Research Assistant...")
    print("📱 The enhanced interface will open in your browser")
    print("✨ Features include:")
    print("   • Beautiful gradient design")
    print("   • Interactive paper summary cards")
    print("   • Enhanced styling and layout")
    print("   • Better visual organization")
    print()
    print("⏳ Starting application...")
    
    try:
        # Launch the main application
        process = subprocess.Popen([sys.executable, "main.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # Wait a moment for the app to start
        time.sleep(3)
        
        print("✅ Application started successfully!")
        print("🌐 Check your browser for the interface")
        print("📱 Press Ctrl+C to stop the application")
        
        # Wait for the process to complete
        process.wait()
        
    except KeyboardInterrupt:
        print("\n👋 Stopping Research Assistant...")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

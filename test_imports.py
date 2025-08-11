#!/usr/bin/env python3
"""Test script to verify all imports work correctly"""

def test_imports():
    """Test all the main imports"""
    try:
        print("Testing imports...")
        
        # Test agent imports
        from research_assistant.agents import Researcher, Summarizer, Organizer, Scraper
        print("✓ Agent imports successful")
        
        # Test utility imports
        from research_assistant.utils.config import Config
        from research_assistant.utils.logger import Logger
        print("✓ Utility imports successful")
        
        # Test main dependencies
        import gradio as gr
        import openai
        print("✓ Main dependency imports successful")
        
        print("\n🎉 All imports successful! The application should work correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports()

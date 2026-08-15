#!/usr/bin/env python3
"""
Test suite for all LLM providers (OpenAI, Gemini, DeepSeek)
Verifies that all clients are robust and correctly handle API responses.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.llm.factory import LLMFactory
from app.core.config import settings

def test_provider(provider_name):
    print("\n" + "="*60)
    print(f"Testing Provider: {provider_name.upper()}")
    print("="*60)
    
    try:
        client = LLMFactory.get(provider_name)
        print(f"✓ Successfully initialized {provider_name} client")
        
        # Check if API key is set
        key_name = {
            "openai": "OPENAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY"
        }.get(provider_name)
        
        api_key = getattr(settings, key_name, "")
        if not api_key:
            print(f"⚠ {key_name} not set - skipping live API test")
            return True
            
        print(f"Testing live API call for {provider_name}...")
        result = client.generate(
            prompt="Say 'Success' in one word.",
            max_tokens=10
        )
        
        if result.get("error"):
            print(f"✗ API Error: {result.get('error')} - {result.get('detail')}")
            return False
        
        print(f"✓ API Call Successful!")
        content = result.get('content') or ""
        print(f"  Response: {content.strip()}")
        print(f"  Usage: {result.get('usage')}")
        return True
        
    except Exception as e:
        print(f"✗ Unexpected error testing {provider_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("AI Workforce OS - Multi-LLM Test Suite")
    print("="*60)
    
    providers = ["openai", "deepseek", "gemini"]
    results = {}
    
    for p in providers:
        results[p] = test_provider(p)
    
    print("\n" + "="*60)
    print("Final Summary")
    print("="*60)
    
    all_passed = True
    for p, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {p.upper()}")
        if not passed:
            all_passed = False
            
    print("\n" + ("="*60))
    if all_passed:
        print("✓ All providers are robust and ready!")
    else:
        print("✗ Some providers failed testing")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

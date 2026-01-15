#!/usr/bin/env python3
"""
Test OpenRouter API connection to diagnose the 401 error
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

def test_openrouter_api():
    """Test OpenRouter API connection"""
    print("🔍 Testing OpenRouter API Connection")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ No API key found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-10:]}")
    
    # Test different client configurations
    configs_to_test = [
        {
            "name": "Standard OpenRouter",
            "base_url": "https://openrouter.ai/api/v1",
            "headers": {}
        },
        {
            "name": "OpenRouter with Headers",
            "base_url": "https://openrouter.ai/api/v1", 
            "headers": {
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Universal Data Handler"
            }
        }
    ]
    
    for config in configs_to_test:
        print(f"\n🧪 Testing: {config['name']}")
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=config["base_url"],
                default_headers=config["headers"] if config["headers"] else None
            )
            
            # Test with a simple request
            response = client.chat.completions.create(
                model="anthropic/claude-3.5-sonnet",
                messages=[
                    {"role": "user", "content": "Say 'Hello, this is a test'"}
                ],
                max_tokens=50
            )
            
            print(f"✅ Success: {response.choices[0].message.content}")
            return True
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            
            # Try alternative models
            alternative_models = [
                "openai/gpt-3.5-turbo",
                "meta-llama/llama-3.1-8b-instruct:free",
                "microsoft/wizardlm-2-8x22b"
            ]
            
            for model in alternative_models:
                print(f"   🔄 Trying alternative model: {model}")
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "user", "content": "Say 'Hello'"}
                        ],
                        max_tokens=20
                    )
                    print(f"   ✅ Success with {model}: {response.choices[0].message.content}")
                    return True, model
                except Exception as model_error:
                    print(f"   ❌ {model} failed: {model_error}")
    
    print("\n❌ All connection attempts failed")
    return False

def test_api_key_validity():
    """Test if the API key format is valid"""
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    print(f"\n🔑 API Key Analysis:")
    print(f"   Length: {len(api_key) if api_key else 0}")
    print(f"   Starts with 'sk-or-': {api_key.startswith('sk-or-') if api_key else False}")
    print(f"   Format appears valid: {len(api_key) > 50 and api_key.startswith('sk-or-') if api_key else False}")

if __name__ == "__main__":
    test_api_key_validity()
    result = test_openrouter_api()
    
    if isinstance(result, tuple):
        success, working_model = result
        if success:
            print(f"\n💡 Recommendation: Use model '{working_model}' in your config")
    elif result:
        print(f"\n✅ OpenRouter connection is working!")
    else:
        print(f"\n❌ OpenRouter connection failed. Check your API key or try a different model.")
#!/usr/bin/env python3
"""
Test script to verify Firecrawl API integration
Run this to diagnose Firecrawl issues before running full analysis
"""

import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

def test_firecrawl_basic():
    """Test basic Firecrawl functionality"""
    print("=" * 60)
    print("Firecrawl API Test")
    print("=" * 60)

    try:
        from firecrawl import FirecrawlApp
        print("✅ Firecrawl package imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Firecrawl: {e}")
        print("\nInstall with: pip install firecrawl")
        return False

    # Get API key from environment
    api_key = os.getenv('FIRECRAWL_API_KEY', 'fc-e216d6ab6935403bb05906afb27c9fc2')
    print(f"\n📌 Using API Key: {api_key[:10]}...")

    # Test simple scrape
    print("\n🔍 Testing simple scrape of example.com...")
    try:
        app = FirecrawlApp(api_key=api_key)
        result = app.scrape('https://example.com')

        print(f"✅ Scrape successful!")
        print(f"   Result type: {type(result).__name__}")
        print(f"   Has __dict__: {hasattr(result, '__dict__')}")
        print(f"   Is dict: {isinstance(result, dict)}")

        # Check available methods
        if hasattr(result, 'to_dict'):
            print(f"   Has to_dict(): ✅")
            result_dict = result.to_dict()
        elif hasattr(result, 'dict'):
            print(f"   Has dict(): ✅")
            result_dict = result.dict()
        elif isinstance(result, dict):
            print(f"   Is plain dict: ✅")
            result_dict = result
        else:
            print(f"   Converting via attributes...")
            result_dict = {
                'markdown': getattr(result, 'markdown', ''),
                'html': getattr(result, 'html', ''),
                'metadata': getattr(result, 'metadata', {}),
            }

        print(f"\n📄 Result structure:")
        print(f"   Keys: {list(result_dict.keys())}")

        if 'markdown' in result_dict:
            markdown_preview = result_dict.get('markdown', '')[:100]
            print(f"   Markdown preview: {markdown_preview}...")

        if 'metadata' in result_dict:
            metadata = result_dict.get('metadata', {})
            if hasattr(metadata, '__dict__') and not isinstance(metadata, dict):
                if hasattr(metadata, 'to_dict'):
                    metadata = metadata.to_dict()
                elif hasattr(metadata, 'dict'):
                    metadata = metadata.dict()
                else:
                    metadata = metadata.__dict__

            print(f"   Metadata keys: {list(metadata.keys()) if isinstance(metadata, dict) else 'N/A'}")
            if isinstance(metadata, dict):
                title = metadata.get('title', 'N/A')
                print(f"   Title: {title}")

        print("\n✅ Firecrawl is working correctly!")
        return True

    except Exception as e:
        print(f"❌ Scrape failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def test_firecrawl_with_formats():
    """Test Firecrawl with different format options"""
    print("\n" + "=" * 60)
    print("Testing Firecrawl with Format Options")
    print("=" * 60)

    try:
        from firecrawl import FirecrawlApp
        api_key = os.getenv('FIRECRAWL_API_KEY', 'fc-e216d6ab6935403bb05906afb27c9fc2')
        app = FirecrawlApp(api_key=api_key)

        print("\n🔍 Testing with formats=['markdown', 'html']...")
        try:
            result = app.scrape('https://example.com', formats=['markdown', 'html'])
            print(f"✅ Scrape with formats successful!")
            print(f"   Result type: {type(result).__name__}")
        except TypeError as e:
            print(f"⚠️  Formats parameter not supported: {e}")
            print("   Trying without formats...")
            result = app.scrape('https://example.com')
            print(f"✅ Scrape without formats successful!")
            print(f"   Result type: {type(result).__name__}")

        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_django_scraper():
    """Test the Django scraper service"""
    print("\n" + "=" * 60)
    print("Testing Django Scraper Service")
    print("=" * 60)

    try:
        # Set up Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()

        print("✅ Django setup complete")

        from domain_intelligence.services.scraper import DomainScraper

        print("\n🔍 Testing DomainScraper with example.com...")
        scraper = DomainScraper('example.com')
        result = scraper.scrape()

        print(f"✅ Scraping successful!")
        print(f"   Domain: {result.get('domain')}")
        print(f"   Scraping method: {result.get('metadata', {}).get('scraping_method')}")
        print(f"   Website data keys: {list(result.get('website_data', {}).keys())}")

        if 'external_data' in result:
            print(f"   External data keys: {list(result.get('external_data', {}).keys())}")

        return True
    except Exception as e:
        print(f"❌ Django scraper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n🚀 Starting Firecrawl Integration Tests\n")

    # Test 1: Basic Firecrawl
    test1 = test_firecrawl_basic()

    # Test 2: Firecrawl with formats
    test2 = test_firecrawl_with_formats()

    # Test 3: Django integration
    test3 = test_django_scraper()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Basic Firecrawl:        {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Firecrawl with formats: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Django Scraper:         {'✅ PASS' if test3 else '❌ FAIL'}")

    if all([test1, test2, test3]):
        print("\n🎉 All tests passed! Firecrawl is ready to use.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        sys.exit(1)

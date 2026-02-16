#!/usr/bin/env python3
"""
Test script to verify article content scraping works
Run this to test article scraping before running full analysis
"""

import os
import sys
import django

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from domain_intelligence.services.scraper import DomainScraper

def test_article_scraping():
    """Test article content scraping"""
    print("=" * 60)
    print("Article Content Scraping Test")
    print("=" * 60)

    # Create scraper instance
    scraper = DomainScraper('shopify.com')

    # Test article URLs
    test_urls = [
        'https://techcrunch.com/2024/02/13/shopify-earnings/',
        'https://www.theverge.com/2024/02/12/shopify-ai/',
        'https://www.reuters.com/business/retail-consumer/shopify/',
    ]

    print("\n🔍 Testing article content extraction...\n")

    for idx, url in enumerate(test_urls, 1):
        print(f"\nTest {idx}: {url}")
        print("-" * 60)

        content = scraper._scrape_article_content(url)

        print(f"Content length: {len(content)}")
        print(f"Preview: {content[:200]}...")

        if content and content != "Content not available":
            print("✅ SUCCESS - Content extracted")
        else:
            print("❌ FAILED - No content extracted")

    print("\n" + "=" * 60)
    print("Testing News Feed Scraping")
    print("=" * 60)

    print("\n🔍 Fetching news from Google News RSS...\n")

    news_items = scraper._fetch_company_news()

    print(f"\nFound {len(news_items)} news articles\n")

    for idx, item in enumerate(news_items, 1):
        print(f"\nArticle {idx}:")
        print(f"  Title: {item.get('title', 'N/A')[:60]}...")
        print(f"  Source: {item.get('source', 'N/A')}")
        print(f"  URL: {item.get('url', 'N/A')[:60]}...")
        print(f"  Content length: {len(item.get('content', ''))}")
        print(f"  Content preview: {item.get('content', 'N/A')[:150]}...")

        if item.get('content') and item.get('content') != "Content not available":
            print("  ✅ Has content")
        else:
            print("  ❌ No content")

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    articles_with_content = sum(1 for item in news_items if item.get('content') and item.get('content') != "Content not available")

    print(f"\nTotal articles: {len(news_items)}")
    print(f"Articles with content: {articles_with_content}")
    print(f"Success rate: {(articles_with_content / len(news_items) * 100) if news_items else 0:.1f}%")

    if articles_with_content >= 3:
        print("\n✅ Article scraping is working!")
        return True
    else:
        print("\n⚠️  Article scraping needs improvement")
        return False


if __name__ == '__main__':
    print("\n🚀 Starting Article Scraping Test\n")

    try:
        success = test_article_scraping()

        if success:
            print("\n🎉 All tests passed! Article scraping is working correctly.")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed. Check the output above.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

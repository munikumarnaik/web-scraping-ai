import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class DomainScraper:
    """Service for scraping domain-related information using Firecrawl or BeautifulSoup"""

    def __init__(self, domain_name: str):
        self.domain_name = domain_name
        self.timeout = settings.SCRAPING_TIMEOUT
        self.provider = settings.SCRAPING_PROVIDER
        self.firecrawl_api_key = settings.FIRECRAWL_API_KEY

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def scrape(self) -> Dict:
        """Main scraping method - chooses provider based on configuration"""
        try:
            if self.provider == 'firecrawl' and self.firecrawl_api_key:
                logger.info(f"Using Firecrawl API to scrape {self.domain_name}")
                return self._scrape_with_firecrawl()
            else:
                logger.info(f"Using BeautifulSoup to scrape {self.domain_name}")
                return self._scrape_with_beautifulsoup()
        except Exception as e:
            logger.error(f"Error scraping {self.domain_name}: {str(e)}")
            raise

    def _get_url(self) -> str:
        """Construct URL from domain name"""
        if not self.domain_name.startswith(('http://', 'https://')):
            return f"https://{self.domain_name}"
        return self.domain_name

    def _scrape_with_firecrawl(self) -> Dict:
        """Scrape using Firecrawl API"""
        from firecrawl import FirecrawlApp

        try:
            app = FirecrawlApp(api_key=self.firecrawl_api_key)
            url = self._get_url()

            # Scrape the main page
            logger.info(f"Scraping {url} with Firecrawl...")
            # Try different API versions
            try:
                # Try newest API (v4+)
                scrape_result = app.scrape(url, formats=['markdown', 'html'])
            except TypeError:
                try:
                    # Try older API with params dict
                    if hasattr(app, 'scrape_url'):
                        scrape_result = app.scrape_url(url, params={
                            'formats': ['markdown', 'html'],
                            'onlyMainContent': True
                        })
                    else:
                        scrape_result = app.scrape(url, params={
                            'formats': ['markdown', 'html'],
                            'onlyMainContent': True
                        })
                except:
                    # Fallback to simplest call
                    scrape_result = app.scrape(url)

            # Extract data from Firecrawl response
            metadata = scrape_result.get('metadata', {})

            website_data = {
                'url': url,
                'status_code': scrape_result.get('statusCode', 200),
                'title': metadata.get('title', ''),
                'description': metadata.get('description', ''),
                'keywords': metadata.get('keywords', ''),
                'author': metadata.get('author', ''),
                'og_title': metadata.get('ogTitle', ''),
                'og_description': metadata.get('ogDescription', ''),
                'og_image': metadata.get('ogImage', ''),
                'og_url': metadata.get('ogUrl', ''),
                'markdown': scrape_result.get('markdown', ''),
                'html': scrape_result.get('html', ''),
                'content': scrape_result.get('markdown', '')[:5000],  # Limit content
                'language': metadata.get('language', ''),
                'source_url': metadata.get('sourceURL', url),
            }

            # Try to crawl additional pages (limited)
            try:
                logger.info(f"Crawling {url} for additional pages...")
                # Try different API versions for crawl
                try:
                    # Try newest API (v4+)
                    crawl_result = app.crawl(url, limit=5)
                except TypeError:
                    try:
                        # Try older API with params dict
                        if hasattr(app, 'crawl_url'):
                            crawl_result = app.crawl_url(url, params={
                                'limit': 5,
                                'scrapeOptions': {
                                    'formats': ['markdown'],
                                    'onlyMainContent': True
                                }
                            })
                        else:
                            crawl_result = app.crawl(url, params={
                                'limit': 5,
                                'scrapeOptions': {
                                    'formats': ['markdown'],
                                    'onlyMainContent': True
                                }
                            })
                    except:
                        # Fallback to simplest call
                        crawl_result = app.crawl(url)

                additional_pages = []
                if crawl_result and 'data' in crawl_result:
                    for page in crawl_result['data'][:5]:
                        page_metadata = page.get('metadata', {})
                        additional_pages.append({
                            'url': page_metadata.get('sourceURL', ''),
                            'title': page_metadata.get('title', ''),
                            'description': page_metadata.get('description', ''),
                            'content': page.get('markdown', '')[:1000]
                        })

                website_data['additional_pages'] = additional_pages

            except Exception as crawl_error:
                logger.warning(f"Crawl failed, continuing with single page: {str(crawl_error)}")
                website_data['additional_pages'] = []

            return {
                'domain': self.domain_name,
                'website_data': website_data,
                'metadata': {
                    'scraping_method': 'firecrawl',
                    'og_tags': {
                        'og:title': metadata.get('ogTitle', ''),
                        'og:description': metadata.get('ogDescription', ''),
                        'og:image': metadata.get('ogImage', ''),
                        'og:url': metadata.get('ogUrl', ''),
                    },
                    'keywords': metadata.get('keywords', '').split(',') if metadata.get('keywords') else [],
                    'language': metadata.get('language', ''),
                },
                'external_data': self._enrich_with_external_data(),
            }

        except Exception as e:
            logger.error(f"Firecrawl scraping failed: {str(e)}")
            # Fallback to BeautifulSoup
            logger.info("Falling back to BeautifulSoup scraper...")
            return self._scrape_with_beautifulsoup()

    def _scrape_with_beautifulsoup(self) -> Dict:
        """Scrape using traditional BeautifulSoup method (fallback)"""
        try:
            data = {
                'domain': self.domain_name,
                'website_data': self._scrape_website(),
                'metadata': self._extract_metadata(),
                'external_data': self._enrich_with_external_data(),
            }
            data['metadata']['scraping_method'] = 'beautifulsoup'
            return data
        except Exception as e:
            logger.error(f"BeautifulSoup scraping failed: {str(e)}")
            raise

    def _scrape_website(self) -> Dict:
        """Scrape main website content using BeautifulSoup"""
        url = self._get_url()
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            return {
                'url': url,
                'status_code': response.status_code,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'headings': self._extract_headings(soup),
                'content': self._extract_content(soup),
                'links': self._extract_links(soup, url),
            }
        except Exception as e:
            logger.warning(f"Error scraping website {url}: {str(e)}")
            return {
                'url': url,
                'error': str(e),
                'status_code': None,
            }

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()

        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc.get('content').strip()

        return None

    def _extract_headings(self, soup: BeautifulSoup) -> List[str]:
        """Extract all headings"""
        headings = []
        for tag in ['h1', 'h2', 'h3']:
            for heading in soup.find_all(tag):
                text = heading.get_text().strip()
                if text:
                    headings.append(text)
        return headings[:20]

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content text"""
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text[:5000]

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract internal links"""
        links = []
        domain = urlparse(base_url).netloc

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            if parsed.netloc == domain and full_url not in links:
                links.append(full_url)

            if len(links) >= 10:
                break

        return links

    def _extract_metadata(self) -> Dict:
        """Extract additional metadata"""
        url = self._get_url()
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'lxml')

            metadata = {
                'og_tags': {},
                'twitter_tags': {},
                'keywords': [],
            }

            # OpenGraph tags
            for tag in soup.find_all('meta', property=True):
                if tag.get('property', '').startswith('og:'):
                    metadata['og_tags'][tag['property']] = tag.get('content', '')

            # Twitter tags
            for tag in soup.find_all('meta', attrs={'name': True}):
                if tag.get('name', '').startswith('twitter:'):
                    metadata['twitter_tags'][tag['name']] = tag.get('content', '')

            # Keywords
            keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_tag and keywords_tag.get('content'):
                metadata['keywords'] = [
                    k.strip() for k in keywords_tag['content'].split(',')
                ]

            return metadata
        except Exception as e:
            logger.warning(f"Error extracting metadata: {str(e)}")
            return {}

    def _fetch_company_news(self) -> List[Dict]:
        """Fetch recent news articles about the company"""
        try:
            # Simple Google News search (no API key needed)
            company_name = self.domain_name.split('.')[0].capitalize()
            search_url = f"https://news.google.com/search?q={company_name}+company"

            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'lxml')

            news_items = []
            # Extract article titles and snippets
            articles = soup.find_all('article', limit=5)
            for article in articles:
                title_elem = article.find('a')
                if title_elem:
                    news_items.append({
                        'title': title_elem.get_text().strip(),
                        'source': 'Google News'
                    })

            logger.info(f"Fetched {len(news_items)} news items for {self.domain_name}")
            return news_items[:5]
        except Exception as e:
            logger.warning(f"Failed to fetch news: {str(e)}")
            return []

    def _fetch_linkedin_data(self) -> Dict:
        """Fetch LinkedIn company information"""
        try:
            # Try to fetch LinkedIn company page info
            company_name = self.domain_name.split('.')[0]
            linkedin_url = f"https://www.linkedin.com/company/{company_name}"

            response = requests.get(linkedin_url, headers=self.headers, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'lxml')

            linkedin_data = {
                'company_url': linkedin_url,
                'found': response.status_code == 200,
                'employee_count': 'Not available',
                'industry': 'Not available'
            }

            # Try to extract basic info (LinkedIn may block scraping)
            if response.status_code == 200:
                # Look for employee count
                text = soup.get_text()
                if 'employees' in text.lower():
                    logger.info(f"LinkedIn page found for {self.domain_name}")

            return linkedin_data
        except Exception as e:
            logger.warning(f"Failed to fetch LinkedIn data: {str(e)}")
            return {
                'company_url': f"https://www.linkedin.com/company/{self.domain_name.split('.')[0]}",
                'found': False,
                'employee_count': linkedin_data['employee_count'],
                'industry': 'Not available'
            }

    def _enrich_with_external_data(self) -> Dict:
        """Enrich company data with external sources"""
        return {
            'news': self._fetch_company_news(),
            'linkedin': self._fetch_linkedin_data(),
            'industry_insights': self._get_industry_insights()
        }

    def _get_industry_insights(self) -> Dict:
        """Get general industry insights"""
        try:
            domain_parts = self.domain_name.split('.')
            company_name = domain_parts[0].capitalize()

            # Search for industry information
            search_query = f"{company_name} industry market trends"
            search_url = f"https://www.google.com/search?q={search_query}"

            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'lxml')

            # Extract snippets from search results
            snippets = []
            for result in soup.find_all('div', class_='BNeawe', limit=3):
                text = result.get_text().strip()
                if len(text) > 50:
                    snippets.append(text[:200])

            return {
                'market_snippets': snippets[:3],
                'source': 'Web Search'
            }
        except Exception as e:
            logger.warning(f"Failed to get industry insights: {str(e)}")
            return {
                'market_snippets': [],
                'source': 'Not available'
            }

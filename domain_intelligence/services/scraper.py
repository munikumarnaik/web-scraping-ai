import logging
import requests
import re
import html
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
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

    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract clean text from HTML using BeautifulSoup"""
        if not html_content:
            return ""

        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')

            # Remove script, style, nav, footer, header tags
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'link', 'meta']):
                tag.decompose()

            # Get text content
            text = soup.get_text(separator=' ', strip=True)

            # Clean up the extracted text
            return self._clean_text(text)
        except Exception as e:
            logger.warning(f"Error extracting text from HTML: {str(e)}")
            # Fallback to regex cleaning
            return self._clean_text(html_content)

    def _clean_text(self, text: str) -> str:
        """Clean HTML tags, decode entities, and make text readable"""
        if not text:
            return ""

        # Multiple rounds of HTML entity decoding (sometimes double-encoded)
        for _ in range(3):
            try:
                decoded = html.unescape(text)
                if decoded == text:
                    break
                text = decoded
            except:
                break

        # Remove script and style tags with their content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

        # Remove excessive whitespace (newlines, tabs, multiple spaces)
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        # Remove special unicode characters that don't render well
        text = re.sub(r'[\u200b-\u200f\u202a-\u202e\u2060-\u206f]', '', text)

        # Clean up common encoding issues
        text = text.replace('â€™', "'")
        text = text.replace('â€œ', '"')
        text = text.replace('â€', '"')
        text = text.replace('â€"', '-')
        text = text.replace('Ã©', 'é')
        text = text.replace('Ã¨', 'è')

        return text.strip()

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

            # Log what we received
            logger.info(f"Firecrawl returned type: {type(scrape_result).__name__}")
            logger.debug(f"Firecrawl result attributes: {dir(scrape_result)}")

            # Convert Document object to dict if needed
            if hasattr(scrape_result, '__dict__'):
                # If it's a Document object, convert to dict
                if hasattr(scrape_result, 'to_dict'):
                    logger.info("Converting using to_dict() method")
                    scrape_result = scrape_result.to_dict()
                elif hasattr(scrape_result, 'dict'):
                    logger.info("Converting using dict() method")
                    scrape_result = scrape_result.dict()
                elif not isinstance(scrape_result, dict):
                    logger.info("Converting using attribute access")
                    scrape_result = {
                        'markdown': getattr(scrape_result, 'markdown', ''),
                        'html': getattr(scrape_result, 'html', ''),
                        'metadata': getattr(scrape_result, 'metadata', {}),
                        'statusCode': getattr(scrape_result, 'status_code', 200)
                    }

            # Extract data from Firecrawl response
            metadata = scrape_result.get('metadata', {})

            # Convert metadata to dict if it's an object
            if hasattr(metadata, '__dict__') and not isinstance(metadata, dict):
                if hasattr(metadata, 'to_dict'):
                    metadata = metadata.to_dict()
                elif hasattr(metadata, 'dict'):
                    metadata = metadata.dict()
                else:
                    metadata = metadata.__dict__

            # Get and clean content properly
            markdown_content = scrape_result.get('markdown', '')
            html_content = scrape_result.get('html', '')

            # Prefer markdown (it's already cleaner), otherwise extract text from HTML
            if markdown_content and len(markdown_content.strip()) > 100:
                # We have good markdown content
                clean_content = self._clean_text(markdown_content)
            elif html_content:
                # Extract text from HTML using BeautifulSoup
                clean_content = self._extract_text_from_html(html_content)
            else:
                # Fallback
                clean_content = self._clean_text(markdown_content or html_content)

            website_data = {
                'url': url,
                'status_code': scrape_result.get('statusCode', 200),
                'title': self._clean_text(metadata.get('title', '')),
                'description': self._clean_text(metadata.get('description', '')),
                'keywords': metadata.get('keywords', ''),
                'author': metadata.get('author', ''),
                'og_title': self._clean_text(metadata.get('ogTitle', '')),
                'og_description': self._clean_text(metadata.get('ogDescription', '')),
                'og_image': metadata.get('ogImage', ''),
                'og_url': metadata.get('ogUrl', ''),
                # 'markdown': scrape_result.get('markdown', ''),  # Keep raw markdown
                # Don't include raw HTML - it's too messy
                'content': clean_content[:5000],  # Cleaned and limited content
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

                # Convert crawl result to dict if needed
                if hasattr(crawl_result, '__dict__') and not isinstance(crawl_result, dict):
                    if hasattr(crawl_result, 'to_dict'):
                        crawl_result = crawl_result.to_dict()
                    elif hasattr(crawl_result, 'dict'):
                        crawl_result = crawl_result.dict()

                additional_pages = []
                if crawl_result and 'data' in crawl_result:
                    for page in crawl_result['data'][:5]:
                        # Convert page to dict if needed
                        if hasattr(page, '__dict__') and not isinstance(page, dict):
                            if hasattr(page, 'to_dict'):
                                page = page.to_dict()
                            elif hasattr(page, 'dict'):
                                page = page.dict()

                        page_metadata = page.get('metadata', {})

                        # Convert metadata to dict if needed
                        if hasattr(page_metadata, '__dict__') and not isinstance(page_metadata, dict):
                            if hasattr(page_metadata, 'to_dict'):
                                page_metadata = page_metadata.to_dict()
                            elif hasattr(page_metadata, 'dict'):
                                page_metadata = page_metadata.dict()

                        # Clean page content properly
                        page_markdown = page.get('markdown', '')
                        page_html = page.get('html', '')

                        # Prefer markdown, otherwise extract from HTML
                        if page_markdown and len(page_markdown.strip()) > 50:
                            clean_page_content = self._clean_text(page_markdown)
                        elif page_html:
                            clean_page_content = self._extract_text_from_html(page_html)
                        else:
                            clean_page_content = self._clean_text(page_markdown or page_html)

                        additional_pages.append({
                            'url': page_metadata.get('sourceURL', ''),
                            'title': self._clean_text(page_metadata.get('title', '')),
                            'description': self._clean_text(page_metadata.get('description', '')),
                            'content': clean_page_content[:1000]
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
            logger.error(f"Firecrawl scraping failed: {str(e)}", exc_info=True)
            logger.error(f"Error type: {type(e).__name__}")
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
        if title_tag:
            return self._clean_text(title_tag.get_text())
        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return self._clean_text(meta_desc.get('content'))

        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return self._clean_text(og_desc.get('content'))

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

        # Additional cleaning to remove any remaining HTML entities
        text = self._clean_text(text)

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
        """Fetch recent news articles using Google News RSS feed (top 10 with URLs)"""
        try:
            # Get company name
            company_name = self.domain_name.split('.')[0].capitalize()

            # Try Google News RSS feed first
            from urllib.parse import quote
            search_query = quote(f"{company_name} company")
            rss_url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"

            logger.info(f"Fetching news from RSS: {rss_url}")

            response = requests.get(rss_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            news_items = []

            # Parse RSS/XML
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)

                # Find all items in the RSS feed
                items = root.findall('.//item')

                for item in items[:5]:  # Get top 5 (with full content)
                    try:
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        pub_date_elem = item.find('pubDate')
                        source_elem = item.find('source')
                        description_elem = item.find('description')

                        title = self._clean_text(title_elem.text) if title_elem is not None and title_elem.text else ''
                        link = link_elem.text if link_elem is not None and link_elem.text else ''
                        pub_date = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else 'Recently'
                        source = self._clean_text(source_elem.text) if source_elem is not None and source_elem.text else 'Unknown'
                        description = self._clean_text(description_elem.text) if description_elem is not None and description_elem.text else ''

                        # Filter out short titles
                        if title and len(title) > 10 and link:
                            logger.info(f"Processing news article: {title[:50]}...")

                            # Try to scrape article content from the URL
                            article_content = self._scrape_article_content(link)

                            # If scraping failed, use RSS description as fallback
                            if article_content == "Content not available" or len(article_content) < 100:
                                if description and len(description) > 50:
                                    logger.info(f"Using RSS description as fallback ({len(description)} chars)")
                                    article_content = description[:800]
                                else:
                                    logger.warning(f"No content available for article: {title[:50]}")

                            logger.info(f"Final article content length: {len(article_content)}")

                            news_items.append({
                                'title': title,
                                'url': link,
                                'source': source,
                                'published': pub_date,
                                'content': article_content
                            })

                    except Exception as item_error:
                        logger.debug(f"Error parsing RSS item: {str(item_error)}")
                        continue

                logger.info(f"Fetched {len(news_items)} news items from RSS for {self.domain_name}")

            except ET.ParseError as parse_error:
                logger.warning(f"Failed to parse RSS feed: {str(parse_error)}")
                # Fallback to HTML scraping
                return self._fetch_news_fallback(company_name)

            # If RSS worked, return the results
            if news_items:
                return news_items[:5]

            # Otherwise try fallback
            logger.info("No RSS items found, trying fallback method...")
            return self._fetch_news_fallback(company_name)

        except Exception as e:
            logger.warning(f"Failed to fetch news via RSS: {str(e)}")
            # Try fallback method
            try:
                company_name = self.domain_name.split('.')[0].capitalize()
                return self._fetch_news_fallback(company_name)
            except:
                return []

    def _fetch_news_fallback(self, company_name: str) -> List[Dict]:
        """Fallback method to scrape Google News HTML"""
        try:
            from urllib.parse import quote
            search_query = quote(f"{company_name} company")
            search_url = f"https://news.google.com/search?q={search_query}"

            logger.info(f"Trying fallback news scraping from: {search_url}")

            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'lxml')

            news_items = []
            articles = soup.find_all('article', limit=15)

            for article in articles:
                try:
                    # Find title link
                    link = article.find('a')
                    if link:
                        title = self._clean_text(link.get_text())
                        href = link.get('href', '')

                        # Convert relative URL to absolute
                        if href.startswith('./'):
                            href = f"https://news.google.com{href[1:]}"
                        elif not href.startswith('http'):
                            href = f"https://news.google.com/{href}"

                        # Get source if available
                        source = 'Google News'
                        time_elem = article.find('time')
                        pub_time = self._clean_text(time_elem.get_text()) if time_elem else 'Recently'

                        if title and len(title) > 10 and href:
                            # Scrape article content
                            article_content = self._scrape_article_content(href)

                            news_items.append({
                                'title': title,
                                'url': href,
                                'source': source,
                                'published': pub_time,
                                'content': article_content
                            })

                        if len(news_items) >= 5:
                            break

                except Exception as item_error:
                    logger.debug(f"Error parsing fallback item: {str(item_error)}")
                    continue

            logger.info(f"Fetched {len(news_items)} news items via fallback for {company_name}")
            return news_items[:5]

        except Exception as e:
            logger.warning(f"Fallback news scraping failed: {str(e)}")
            return []

    def _scrape_article_content(self, url: str) -> str:
        """Scrape content from a news article URL"""
        try:
            logger.info(f"Scraping article content from: {url}")

            # Handle Google News redirects
            if 'news.google.com' in url:
                logger.info("Google News URL detected, following redirect...")
                try:
                    # Follow redirect to get actual article URL
                    response = requests.get(
                        url,
                        headers=self.headers,
                        timeout=15,
                        allow_redirects=True
                    )
                    actual_url = response.url
                    logger.info(f"Redirected to actual article: {actual_url}")

                    # Check if we actually got redirected to a different site
                    if 'news.google.com' in actual_url:
                        logger.warning("Redirect still points to Google News, trying alternative method...")
                        # The redirect didn't work, return empty
                        return "Content not available"

                except Exception as redirect_error:
                    logger.warning(f"Error following redirect: {str(redirect_error)}")
                    return "Content not available"
            else:
                # Fetch the article page directly
                try:
                    response = requests.get(url, headers=self.headers, timeout=15, allow_redirects=True)
                except Exception as e:
                    logger.warning(f"Error fetching article: {str(e)}")
                    return "Content not available"

            # Check response status
            try:
                response.raise_for_status()
            except Exception as e:
                logger.warning(f"Bad response status: {response.status_code}")
                return "Content not available"

            # Parse HTML
            soup = BeautifulSoup(response.text, 'lxml')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'form']):
                tag.decompose()

            # Try to find article content - common article containers
            article_content = None

            # Method 1: Look for <article> tag
            article_tag = soup.find('article')
            if article_tag:
                article_content = article_tag.get_text(separator=' ', strip=True)
                if len(article_content) > 200:
                    logger.info("Found content using <article> tag")

            # Method 2: Look for common article class names (partial match)
            if not article_content or len(article_content) < 100:
                for class_pattern in ['article', 'story', 'post', 'content', 'body', 'text']:
                    # Find elements with class containing the pattern
                    content_divs = soup.find_all(class_=lambda x: x and class_pattern in x.lower())
                    for content_div in content_divs:
                        text = content_div.get_text(separator=' ', strip=True)
                        if len(text) > 100:
                            article_content = text
                            logger.info(f"Found content using class pattern: {class_pattern}")
                            break
                    if article_content and len(article_content) > 100:
                        break

            # Method 3: Look for common ID names
            if not article_content or len(article_content) < 100:
                for id_name in ['article-content', 'article-body', 'main-content']:
                    content_div = soup.find(id=id_name)
                    if content_div:
                        article_content = content_div.get_text(separator=' ', strip=True)
                        if len(article_content) > 100:
                            break

            # Method 4: Find paragraphs in main/article tags
            if not article_content or len(article_content) < 100:
                main_tag = soup.find('main') or soup.find('article')
                if main_tag:
                    paragraphs = main_tag.find_all('p')
                    if paragraphs:
                        article_content = ' '.join([p.get_text(strip=True) for p in paragraphs])

            # Method 5: Fallback - get all paragraphs
            if not article_content or len(article_content) < 100:
                paragraphs = soup.find_all('p')
                if paragraphs and len(paragraphs) > 2:  # At least 2 paragraphs
                    article_content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
                    if len(article_content) > 100:
                        logger.info("Found content using all paragraphs method")

            # Method 6: Super aggressive - get all text from body
            if not article_content or len(article_content) < 100:
                body = soup.find('body')
                if body:
                    # Remove navigation, footer, header, sidebar
                    for unwanted in body.find_all(['nav', 'footer', 'header', 'aside', 'menu']):
                        unwanted.decompose()
                    article_content = body.get_text(separator=' ', strip=True)
                    if len(article_content) > 100:
                        logger.info("Found content using body text method")

            # Clean the extracted content
            if article_content and len(article_content) > 100:  # Lowered threshold
                article_content = self._clean_text(article_content)
                # Limit to 800 characters for summary
                final_content = article_content[:800] + ('...' if len(article_content) > 800 else '')
                logger.info(f"✅ Successfully extracted {len(article_content)} characters from article")
                return final_content
            else:
                logger.warning(f"❌ Could not extract sufficient content from: {url}")
                logger.warning(f"Extracted only: {len(article_content) if article_content else 0} characters")
                return "Content not available"

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout scraping article: {url}")
            return "Content not available (timeout)"
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error scraping article {url}: {str(e)}")
            return "Content not available"
        except Exception as e:
            logger.warning(f"Unexpected error scraping article {url}: {str(e)}")
            return "Content not available"

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

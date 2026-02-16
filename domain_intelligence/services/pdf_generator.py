import logging
import io
from datetime import datetime
from typing import Dict, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Service for generating PDF reports from business intelligence data"""

    def __init__(self, domain_name: str, business_intelligence: Dict, scraped_data: Dict = None):
        self.domain_name = domain_name
        self.bi_data = business_intelligence
        self.scraped_data = scraped_data or {}
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Only add styles if they don't exist
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=TA_CENTER,
            ))

        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=12,
                spaceBefore=12,
            ))

        if 'CustomBody' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomBody',
                parent=self.styles['Normal'],
                fontSize=11,
                leading=14,
                spaceAfter=10,
            ))

    def generate(self) -> io.BytesIO:
        """Generate PDF and return as BytesIO object"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        story = []

        # Title
        story.append(Paragraph(
            f"Business Intelligence Report",
            self.styles['CustomTitle']
        ))
        story.append(Paragraph(
            f"Domain: {self.domain_name}",
            self.styles['Heading2']
        ))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 0.3 * inch))

        # Add sections
        self._add_section(story, "1. Industry Overview",
                          self.bi_data.get('industry_overview', 'N/A'))

        self._add_section(story, "2. Market Size and Growth Trends",
                          self._format_dict(self.bi_data.get('market_size_and_trends', {})))

        self._add_section(story, "3. Target Customer Segments",
                          self._format_list(self.bi_data.get('target_customer_segments', [])))

        self._add_section(story, "4. Customer Pain Points",
                          self._format_list(self.bi_data.get('customer_pain_points', [])))

        self._add_section(story, "5. Buying Behavior",
                          self._format_dict(self.bi_data.get('buying_behavior', {})))

        story.append(PageBreak())

        self._add_section(story, "6. Top Competitors",
                          self._format_list(self.bi_data.get('top_competitors', [])))

        self._add_section(story, "7. Common Sales Objections",
                          self._format_list(self.bi_data.get('common_objections', [])))

        self._add_section(story, "8. Unique Selling Propositions",
                          self._format_list(self.bi_data.get('unique_selling_propositions', [])))

        self._add_section(story, "9. Emerging Opportunities (3-5 years)",
                          self._format_list(self.bi_data.get('emerging_opportunities', [])))

        self._add_section(story, "10. Recommended Sales Strategies",
                          self._format_list(self.bi_data.get('recommended_strategies', [])))

        self._add_section(story, "11. AI-Driven Automation Opportunities",
                          self._format_list(self.bi_data.get('ai_automation_opportunities', [])))

        story.append(PageBreak())

        # New Sales Intelligence Sections
        self._add_section(story, "12. Sales Team Challenges",
                          self._format_challenges(self.bi_data.get('sales_team_challenges', [])))

        self._add_section(story, "13. Sales Upskilling Recommendations",
                          self._format_upskilling(self.bi_data.get('sales_upskilling_recommendations', [])))

        # Add external data section if available
        if self.scraped_data:
            story.append(PageBreak())

            # Recent news section
            external_data = self.scraped_data.get('external_data', {})
            news_items = external_data.get('news', [])
            if news_items:
                self._add_section(story, "14. Recent News & Market Updates",
                                  self._format_news(news_items))

        doc.build(story)
        buffer.seek(0)
        return buffer

    def _add_section(self, story: list, title: str, content: str):
        """Add a section to the PDF"""
        story.append(Paragraph(title, self.styles['SectionHeader']))
        story.append(Paragraph(content, self.styles['CustomBody']))
        story.append(Spacer(1, 0.2 * inch))

    def _format_list(self, items: list) -> str:
        """Format list items as bullet points"""
        if not items:
            return "No data available"

        formatted = "<br/>".join([f"• {item}" for item in items])
        return formatted

    def _format_dict(self, data: dict) -> str:
        """Format dictionary as key-value pairs"""
        if not data:
            return "No data available"

        formatted = "<br/>".join([
            f"<b>{key.replace('_', ' ').title()}:</b> {value}"
            for key, value in data.items()
        ])
        return formatted

    def _format_challenges(self, challenges: list) -> str:
        """Format sales team challenges with impact and frequency"""
        if not challenges:
            return "No data available"

        formatted_items = []
        for idx, item in enumerate(challenges, 1):
            if isinstance(item, dict):
                challenge = item.get('challenge', 'N/A')
                impact = item.get('impact', 'N/A')
                frequency = item.get('frequency', 'N/A')
                formatted_items.append(
                    f"<b>Challenge {idx}:</b> {challenge}<br/>"
                    f"<b>Impact:</b> {impact}<br/>"
                    f"<b>Frequency:</b> {frequency}<br/><br/>"
                )
            else:
                formatted_items.append(f"• {item}<br/>")

        return "".join(formatted_items)

    def _format_upskilling(self, recommendations: list) -> str:
        """Format sales upskilling recommendations with details"""
        if not recommendations:
            return "No data available"

        formatted_items = []
        for idx, item in enumerate(recommendations, 1):
            if isinstance(item, dict):
                skill_area = item.get('skill_area', 'N/A')
                training_type = item.get('training_type', 'N/A')
                priority = item.get('priority', 'N/A')
                expected_outcome = item.get('expected_outcome', 'N/A')
                formatted_items.append(
                    f"<b>Recommendation {idx}:</b> {skill_area}<br/>"
                    f"<b>Training Type:</b> {training_type}<br/>"
                    f"<b>Priority:</b> {priority}<br/>"
                    f"<b>Expected Outcome:</b> {expected_outcome}<br/><br/>"
                )
            else:
                formatted_items.append(f"• {item}<br/>")

        return "".join(formatted_items)

    def _format_news(self, news_items: list) -> str:
        """Format news articles with titles, URLs, sources, and content"""
        if not news_items:
            return "No recent news available"

        formatted_items = []
        for idx, item in enumerate(news_items, 1):
            if isinstance(item, dict):
                title = item.get('title', 'N/A')
                url = item.get('url', '')
                source = item.get('source', 'Unknown')
                published = item.get('published', '')
                content = item.get('content', '')

                # Format article with content
                if url and url.startswith('http'):
                    formatted_items.append(
                        f"<b>{idx}. {title}</b><br/>"
                        f"<b>Source:</b> {source}"
                        f"{' | <b>Published:</b> ' + published if published else ''}<br/>"
                        f"<b>URL:</b> <a href='{url}'>{url[:60]}...</a><br/>"
                    )
                else:
                    formatted_items.append(
                        f"<b>{idx}. {title}</b><br/>"
                        f"<b>Source:</b> {source}"
                        f"{' | <b>Published:</b> ' + published if published else ''}<br/>"
                    )

                # Add article content if available
                if content and content != "Content not available":
                    formatted_items.append(f"<b>Summary:</b> {content}<br/><br/>")
                else:
                    formatted_items.append("<br/>")

            else:
                formatted_items.append(f"• {item}<br/>")

        return "".join(formatted_items)

import logging
import json
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating business intelligence using LLMs"""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER

        import groq
        self.client = groq.Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def generate_business_intelligence(
        self,
        domain_name: str,
        scraped_data: Dict
    ) -> Dict:
        """
        Generate business intelligence report using LLM

        Args:
            domain_name: The domain name being analyzed
            scraped_data: Scraped data from the domain

        Returns:
            Business intelligence report as structured JSON
        """
        prompt = self._build_prompt(domain_name, scraped_data)

        try:
            response = self._call_groq(prompt)
            bi_data = self._parse_response(response)
            return bi_data
        except Exception as e:
            logger.error(f"Error generating business intelligence: {str(e)}")
            raise

    def generate_sales_training(
        self,
        domain_name: str,
        business_intelligence: Dict,
        training_type: str
    ) -> Dict:
        """
        Generate sales training content based on business intelligence

        Args:
            domain_name: The domain name
            business_intelligence: The BI report
            training_type: Type of training to generate

        Returns:
            Training content as structured data
        """
        prompt = self._build_training_prompt(domain_name, business_intelligence, training_type)

        try:
            response = self._call_groq(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error generating sales training: {str(e)}")
            raise

    def _build_prompt(self, domain_name: str, scraped_data: Dict) -> str:
        """Build the prompt for business intelligence generation"""

        website_data = scraped_data.get('website_data', {})
        title = website_data.get('title', 'N/A')
        description = website_data.get('description', 'N/A')
        content = website_data.get('content', 'N/A')[:2000]

        # Include external data
        external_data = scraped_data.get('external_data', {})
        news = external_data.get('news', [])
        linkedin = external_data.get('linkedin', {})
        industry_insights = external_data.get('industry_insights', {})

        # Include news titles and content summaries
        news_summary = ""
        if news:
            for idx, item in enumerate(news[:5], 1):
                title = item.get('title', '')
                content = item.get('content', '')
                if content and content != "Content not available":
                    news_summary += f"{idx}. {title}\n   Summary: {content[:200]}...\n\n"
                else:
                    news_summary += f"{idx}. {title}\n\n"
        else:
            news_summary = "No recent news available"
        market_snippets = "\n".join([f"- {snippet}" for snippet in industry_insights.get('market_snippets', [])[:2]]) if industry_insights else "No market insights available"

        prompt = f"""You are a business intelligence and sales strategist AI.

Given the domain: "{domain_name}"

Website Information:
- Title: {title}
- Description: {description}
- Content Preview: {content}

Recent News & Market Context:
{news_summary}

Industry Market Insights:
{market_snippets}

LinkedIn: {linkedin.get('company_url', 'Not available')} (Found: {linkedin.get('found', False)})

Generate a comprehensive structured business intelligence report including:

1. Industry overview (2-3 paragraphs)
2. Market size and growth trends (provide estimates with growth percentages)
3. Target customer segments (3-5 key segments)
4. Customer pain points (5-7 main pain points)
5. Buying behavior (decision-making process, budget cycles, key influencers)
6. Top competitors and their positioning (3-5 competitors with brief analysis)
7. Common sales objections (5-7 objections with responses)
8. Unique selling propositions (3-5 USPs)
9. Emerging opportunities in next 3-5 years (4-6 opportunities)
10. Recommended sales strategies (5-7 actionable strategies)
11. AI-driven automation opportunities (4-6 specific opportunities)
12. **Sales team challenges** - What challenges do sales people face when selling similar products/services? (5-7 specific challenges)
13. **Sales upskilling recommendations** - What skills, training, and knowledge do sales teams need to succeed? (5-7 actionable upskilling areas with specific training suggestions)

Output MUST be in valid JSON format following this exact structure:
{{
  "industry_overview": "string",
  "market_size_and_trends": {{
    "market_size": "string",
    "growth_rate": "string",
    "key_trends": "string"
  }},
  "target_customer_segments": ["segment1", "segment2", ...],
  "customer_pain_points": ["pain1", "pain2", ...],
  "buying_behavior": {{
    "decision_process": "string",
    "budget_cycle": "string",
    "key_influencers": "string"
  }},
  "top_competitors": [
    {{"name": "competitor1", "positioning": "string"}},
    ...
  ],
  "common_objections": [
    {{"objection": "string", "response": "string"}},
    ...
  ],
  "unique_selling_propositions": ["usp1", "usp2", ...],
  "emerging_opportunities": ["opportunity1", "opportunity2", ...],
  "recommended_strategies": ["strategy1", "strategy2", ...],
  "ai_automation_opportunities": ["opportunity1", "opportunity2", ...],
  "sales_team_challenges": [
    {{"challenge": "string", "impact": "string", "frequency": "string"}},
    ...
  ],
  "sales_upskilling_recommendations": [
    {{"skill_area": "string", "training_type": "string", "priority": "string", "expected_outcome": "string"}},
    ...
  ]
}}

Return ONLY valid JSON, no additional text."""

        return prompt

    def _build_training_prompt(
        self,
        domain_name: str,
        bi_data: Dict,
        training_type: str
    ) -> str:
        """Build prompt for sales training generation"""

        prompt = f"""You are an expert sales trainer and AI educator.

Based on this business intelligence for "{domain_name}":
{json.dumps(bi_data, indent=2)}

Create a comprehensive {training_type} training module for sales personnel.

The training should include:
1. Learning objectives (3-5 clear objectives)
2. Key concepts (main ideas salespeople need to understand)
3. Practical scenarios (2-3 real-world scenarios)
4. Practice exercises (interactive exercises)
5. Assessment questions (5-7 questions to test understanding)
6. Action items (specific steps to implement learning)

Return the response as valid JSON with this structure:
{{
  "learning_objectives": ["objective1", ...],
  "key_concepts": ["concept1", ...],
  "scenarios": [
    {{"situation": "string", "approach": "string", "outcome": "string"}},
    ...
  ],
  "exercises": ["exercise1", ...],
  "assessment": [
    {{"question": "string", "correct_answer": "string", "explanation": "string"}},
    ...
  ],
  "action_items": ["action1", ...]
}}

Return ONLY valid JSON."""

        return prompt

    def _call_groq(self, prompt: str) -> str:
        """Call Groq API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a business intelligence expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8000  # Increased for more comprehensive analysis
        )
        return response.choices[0].message.content.strip()

    def _parse_response(self, response: str) -> Dict:
        """Parse and validate LLM response"""
        try:
            # Try to extract JSON from response
            # Sometimes LLMs add markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            data = json.loads(response)

            # Validate required fields
            required_fields = [
                'industry_overview',
                'market_size_and_trends',
                'target_customer_segments',
                'customer_pain_points',
                'buying_behavior',
                'top_competitors',
                'common_objections',
                'unique_selling_propositions',
                'emerging_opportunities',
                'recommended_strategies',
                'ai_automation_opportunities',
                'sales_team_challenges',
                'sales_upskilling_recommendations'
            ]

            for field in required_fields:
                if field not in data:
                    if field in ['industry_overview', 'buying_behavior', 'market_size_and_trends']:
                        data[field] = "No data available" if field == 'industry_overview' else {}
                    else:
                        data[field] = []

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}\nResponse: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")

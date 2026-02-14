import logging
import json
import io
from celery import shared_task
from django.utils import timezone
from .models import DomainAnalysis, SalesTraining, ScrapingLog
from .services import DomainScraper, PDFGenerator, S3Uploader, LLMService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_domain_analysis(self, analysis_id: int):
    """
    Main task for processing domain analysis
    This runs asynchronously via Celery
    """
    try:
        analysis = DomainAnalysis.objects.get(id=analysis_id)
        logger.info(f"Starting analysis for domain: {analysis.domain_name}")

        # Step 1: Scrape domain
        analysis.status = 'scraping'
        analysis.save()

        scraper = DomainScraper(analysis.domain_name)
        scraped_data = scraper.scrape()

        # Log scraping activity
        ScrapingLog.objects.create(
            domain_analysis=analysis,
            url=scraped_data.get('website_data', {}).get('url', ''),
            status_code=scraped_data.get('website_data', {}).get('status_code'),
            success=True,
            scraped_content_length=len(str(scraped_data))
        )

        analysis.scraped_data = scraped_data
        analysis.scraped_at = timezone.now()
        analysis.save()

        # Step 2: Generate business intelligence
        analysis.status = 'analyzing'
        analysis.save()

        llm_service = LLMService()
        business_intelligence = llm_service.generate_business_intelligence(
            analysis.domain_name,
            scraped_data
        )

        analysis.business_intelligence = business_intelligence
        analysis.save()

        # Step 3: Generate and upload PDF
        pdf_generator = PDFGenerator(analysis.domain_name, business_intelligence)
        pdf_buffer = pdf_generator.generate()

        s3_uploader = S3Uploader()
        pdf_url = s3_uploader.upload_pdf(pdf_buffer, analysis.domain_name)

        if pdf_url:
            analysis.pdf_url = pdf_url

        # Step 4: Upload JSON data
        json_data = {
            'domain': analysis.domain_name,
            'scraped_data': scraped_data,
            'business_intelligence': business_intelligence,
            'generated_at': timezone.now().isoformat()
        }

        json_buffer = io.BytesIO(json.dumps(json_data, indent=2).encode('utf-8'))
        json_url = s3_uploader.upload_json(json_buffer, analysis.domain_name)

        if json_url:
            analysis.json_url = json_url

        # Step 5: Generate sales training modules
        generate_sales_training_modules.delay(analysis.id, business_intelligence)

        # Mark as completed
        analysis.mark_completed()
        logger.info(f"Successfully completed analysis for: {analysis.domain_name}")

    except Exception as e:
        logger.error(f"Error processing domain analysis {analysis_id}: {str(e)}")
        try:
            analysis = DomainAnalysis.objects.get(id=analysis_id)
            analysis.mark_failed(e)
        except Exception:
            pass

        # Retry the task
        raise self.retry(exc=e, countdown=60)


@shared_task
def generate_sales_training_modules(analysis_id: int, business_intelligence: dict):
    """
    Generate sales training modules based on business intelligence
    """
    try:
        analysis = DomainAnalysis.objects.get(id=analysis_id)
        llm_service = LLMService()

        training_types = [
            ('objection_handling', 'Objection Handling', 'intermediate'),
            ('product_knowledge', 'Product Knowledge Training', 'beginner'),
            ('pitch_strategy', 'Sales Pitch Strategy', 'intermediate'),
            ('competitor_analysis', 'Competitor Analysis', 'advanced'),
        ]

        for training_type, title, difficulty in training_types:
            try:
                content = llm_service.generate_sales_training(
                    analysis.domain_name,
                    business_intelligence,
                    training_type
                )

                SalesTraining.objects.create(
                    domain_analysis=analysis,
                    title=title,
                    content=content,
                    training_type=training_type,
                    difficulty_level=difficulty,
                    estimated_duration_minutes=45
                )

                logger.info(f"Created training module: {title} for {analysis.domain_name}")

            except Exception as e:
                logger.error(f"Error creating training module {training_type}: {str(e)}")

    except Exception as e:
        logger.error(f"Error generating sales training for analysis {analysis_id}: {str(e)}")

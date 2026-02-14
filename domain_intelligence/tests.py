from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import DomainAnalysis, SalesTraining
from .services import DomainScraper, PDFGenerator, LLMService


class DomainAnalysisModelTest(TestCase):
    """Test DomainAnalysis model"""

    def setUp(self):
        self.analysis = DomainAnalysis.objects.create(
            domain_name="example.com",
            status="pending"
        )

    def test_domain_analysis_creation(self):
        """Test creating a domain analysis"""
        self.assertEqual(self.analysis.domain_name, "example.com")
        self.assertEqual(self.analysis.status, "pending")
        self.assertIsNone(self.analysis.completed_at)

    def test_mark_completed(self):
        """Test marking analysis as completed"""
        self.analysis.mark_completed()
        self.assertEqual(self.analysis.status, "completed")
        self.assertIsNotNone(self.analysis.completed_at)

    def test_mark_failed(self):
        """Test marking analysis as failed"""
        error = "Test error"
        self.analysis.mark_failed(error)
        self.assertEqual(self.analysis.status, "failed")
        self.assertEqual(self.analysis.error_message, error)
        self.assertIsNotNone(self.analysis.completed_at)


class DomainAnalysisAPITest(APITestCase):
    """Test Domain Analysis API endpoints"""

    def test_create_analysis(self):
        """Test creating a new analysis via API"""
        url = '/api/analyses/create_analysis/'
        data = {'domain_name': 'test.com'}

        with patch('domain_intelligence.tasks.process_domain_analysis.delay'):
            response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('analysis', response.data)
        self.assertEqual(response.data['analysis']['domain_name'], 'test.com')

    def test_create_analysis_validation(self):
        """Test validation when creating analysis"""
        url = '/api/analyses/create_analysis/'
        data = {'domain_name': ''}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_analysis_detail(self):
        """Test retrieving analysis details"""
        analysis = DomainAnalysis.objects.create(
            domain_name="example.com",
            status="completed"
        )

        url = f'/api/analyses/{analysis.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['domain_name'], 'example.com')

    def test_status_check(self):
        """Test status check endpoint"""
        analysis = DomainAnalysis.objects.create(
            domain_name="example.com",
            status="analyzing"
        )

        url = f'/api/analyses/{analysis.id}/status_check/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'analyzing')
        self.assertFalse(response.data['pdf_ready'])


class DomainScraperTest(TestCase):
    """Test DomainScraper service"""

    @patch('domain_intelligence.services.scraper.requests.get')
    def test_scrape_website(self, mock_get):
        """Test website scraping"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
            <html>
                <head>
                    <title>Test Site</title>
                    <meta name="description" content="Test description">
                </head>
                <body>
                    <h1>Welcome</h1>
                    <p>Test content</p>
                </body>
            </html>
        """
        mock_get.return_value = mock_response

        scraper = DomainScraper("example.com")
        data = scraper.scrape()

        self.assertIn('domain', data)
        self.assertEqual(data['domain'], 'example.com')
        self.assertIn('website_data', data)
        self.assertEqual(data['website_data']['status_code'], 200)
        self.assertEqual(data['website_data']['title'], 'Test Site')


class PDFGeneratorTest(TestCase):
    """Test PDF Generator service"""

    def test_pdf_generation(self):
        """Test PDF generation from business intelligence"""
        bi_data = {
            'industry_overview': 'Test overview',
            'market_size_and_trends': {'market_size': '$1B'},
            'target_customer_segments': ['Segment 1'],
            'customer_pain_points': ['Pain 1'],
            'buying_behavior': {},
            'top_competitors': [],
            'common_objections': [],
            'unique_selling_propositions': [],
            'emerging_opportunities': [],
            'recommended_strategies': [],
            'ai_automation_opportunities': []
        }

        generator = PDFGenerator('example.com', bi_data)
        pdf_buffer = generator.generate()

        self.assertIsNotNone(pdf_buffer)
        self.assertGreater(pdf_buffer.tell(), 0)
        pdf_buffer.seek(0)
        self.assertTrue(pdf_buffer.read(4) == b'%PDF')


class SalesTrainingTest(TestCase):
    """Test SalesTraining model"""

    def setUp(self):
        self.analysis = DomainAnalysis.objects.create(
            domain_name="example.com"
        )

    def test_create_training_module(self):
        """Test creating a sales training module"""
        training = SalesTraining.objects.create(
            domain_analysis=self.analysis,
            title="Test Training",
            content={'test': 'data'},
            training_type="objection_handling",
            difficulty_level="intermediate"
        )

        self.assertEqual(training.title, "Test Training")
        self.assertEqual(training.training_type, "objection_handling")
        self.assertEqual(training.difficulty_level, "intermediate")

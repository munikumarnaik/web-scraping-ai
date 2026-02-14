from django.db import models
from django.utils import timezone


class DomainAnalysis(models.Model):
    """Main model for domain analysis requests"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scraping', 'Scraping'),
        ('analyzing', 'Analyzing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    domain_name = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Scraped data
    scraped_data = models.JSONField(null=True, blank=True)
    scraped_at = models.DateTimeField(null=True, blank=True)

    # Business intelligence report
    business_intelligence = models.JSONField(null=True, blank=True)

    # Files
    pdf_url = models.URLField(max_length=500, null=True, blank=True)
    json_url = models.URLField(max_length=500, null=True, blank=True)

    # Metadata
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'domain_analyses'
        ordering = ['-created_at']
        verbose_name = 'Domain Analysis'
        verbose_name_plural = 'Domain Analyses'

    def __str__(self):
        return f"{self.domain_name} - {self.status}"

    def mark_completed(self):
        """Mark analysis as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self, error):
        """Mark analysis as failed"""
        self.status = 'failed'
        self.error_message = str(error)
        self.completed_at = timezone.now()
        self.save()


class SalesTraining(models.Model):
    """Model for AI-generated sales training content"""

    domain_analysis = models.ForeignKey(
        DomainAnalysis,
        on_delete=models.CASCADE,
        related_name='training_modules'
    )

    title = models.CharField(max_length=255)
    content = models.JSONField()
    training_type = models.CharField(
        max_length=50,
        choices=[
            ('objection_handling', 'Objection Handling'),
            ('product_knowledge', 'Product Knowledge'),
            ('pitch_strategy', 'Pitch Strategy'),
            ('competitor_analysis', 'Competitor Analysis'),
            ('customer_psychology', 'Customer Psychology'),
        ]
    )

    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='intermediate'
    )

    estimated_duration_minutes = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sales_training'
        ordering = ['-created_at']
        verbose_name = 'Sales Training'
        verbose_name_plural = 'Sales Training Modules'

    def __str__(self):
        return f"{self.title} - {self.training_type}"


class ScrapingLog(models.Model):
    """Log for scraping activities"""

    domain_analysis = models.ForeignKey(
        DomainAnalysis,
        on_delete=models.CASCADE,
        related_name='scraping_logs'
    )

    url = models.URLField(max_length=500)
    status_code = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    scraped_content_length = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scraping_logs'
        ordering = ['-created_at']
        verbose_name = 'Scraping Log'
        verbose_name_plural = 'Scraping Logs'

    def __str__(self):
        return f"{self.url} - {'Success' if self.success else 'Failed'}"

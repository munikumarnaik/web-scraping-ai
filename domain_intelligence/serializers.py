from rest_framework import serializers
from .models import DomainAnalysis, SalesTraining, ScrapingLog


class DomainAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for creating a new domain analysis"""
    domain_name = serializers.CharField(max_length=255, required=True)

    def validate_domain_name(self, value):
        """Validate domain name format"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Domain name cannot be empty")
        return value.strip().lower()


class BusinessIntelligenceSerializer(serializers.Serializer):
    """Serializer for business intelligence report structure"""
    industry_overview = serializers.CharField()
    market_size_and_trends = serializers.DictField()
    target_customer_segments = serializers.ListField()
    customer_pain_points = serializers.ListField()
    buying_behavior = serializers.DictField()
    top_competitors = serializers.ListField()
    common_objections = serializers.ListField()
    unique_selling_propositions = serializers.ListField()
    emerging_opportunities = serializers.ListField()
    recommended_strategies = serializers.ListField()
    ai_automation_opportunities = serializers.ListField()


class ScrapingLogSerializer(serializers.ModelSerializer):
    """Serializer for scraping logs"""

    class Meta:
        model = ScrapingLog
        fields = ['id', 'url', 'status_code', 'success', 'error_message', 'created_at']
        read_only_fields = fields


class SalesTrainingSerializer(serializers.ModelSerializer):
    """Serializer for sales training modules"""

    class Meta:
        model = SalesTraining
        fields = [
            'id', 'title', 'content', 'training_type',
            'difficulty_level', 'estimated_duration_minutes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DomainAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for domain analysis model"""
    training_modules = SalesTrainingSerializer(many=True, read_only=True)
    scraping_logs = ScrapingLogSerializer(many=True, read_only=True)

    class Meta:
        model = DomainAnalysis
        fields = [
            'id', 'domain_name', 'status', 'scraped_data',
            'business_intelligence', 'pdf_url', 'json_url',
            'error_message', 'created_at', 'updated_at',
            'completed_at', 'training_modules', 'scraping_logs'
        ]
        read_only_fields = [
            'id', 'status', 'scraped_data', 'business_intelligence',
            'pdf_url', 'json_url', 'error_message', 'created_at',
            'updated_at', 'completed_at'
        ]


class DomainAnalysisListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing domain analyses"""

    class Meta:
        model = DomainAnalysis
        fields = [
            'id', 'domain_name', 'status', 'pdf_url',
            'created_at', 'completed_at'
        ]
        read_only_fields = fields

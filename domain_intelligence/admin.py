from django.contrib import admin
from .models import DomainAnalysis, SalesTraining, ScrapingLog


@admin.register(DomainAnalysis)
class DomainAnalysisAdmin(admin.ModelAdmin):
    list_display = ['domain_name', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['domain_name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']

    fieldsets = (
        ('Domain Information', {
            'fields': ('domain_name', 'status')
        }),
        ('Data', {
            'fields': ('scraped_data', 'business_intelligence')
        }),
        ('Files', {
            'fields': ('pdf_url', 'json_url')
        }),
        ('Metadata', {
            'fields': ('error_message', 'created_at', 'updated_at', 'completed_at')
        }),
    )


@admin.register(SalesTraining)
class SalesTrainingAdmin(admin.ModelAdmin):
    list_display = ['title', 'training_type', 'difficulty_level', 'estimated_duration_minutes', 'created_at']
    list_filter = ['training_type', 'difficulty_level', 'created_at']
    search_fields = ['title', 'domain_analysis__domain_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    list_display = ['url', 'success', 'status_code', 'created_at']
    list_filter = ['success', 'created_at']
    search_fields = ['url', 'domain_analysis__domain_name']
    readonly_fields = ['created_at']

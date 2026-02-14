from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import DomainAnalysis, SalesTraining
from .serializers import (
    DomainAnalysisSerializer,
    DomainAnalysisListSerializer,
    DomainAnalysisRequestSerializer,
    SalesTrainingSerializer,
)
from .tasks import process_domain_analysis


class DomainAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for domain analysis operations

    Endpoints:
    - GET /api/analyses/ - List all analyses
    - POST /api/analyses/create/ - Create new analysis
    - GET /api/analyses/{id}/ - Get specific analysis
    - GET /api/analyses/{id}/download_pdf/ - Download PDF report
    - GET /api/analyses/{id}/download_json/ - Download JSON data
    """

    queryset = DomainAnalysis.objects.all()
    serializer_class = DomainAnalysisSerializer

    def get_serializer_class(self):
        """Use different serializer for list view"""
        if self.action == 'list':
            return DomainAnalysisListSerializer
        return DomainAnalysisSerializer

    @action(detail=False, methods=['post'])
    def create_analysis(self, request):
        """
        Create a new domain analysis

        Request body:
        {
            "domain_name": "example.com"
        }
        """
        serializer = DomainAnalysisRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        domain_name = serializer.validated_data['domain_name']

        # Create analysis record
        analysis = DomainAnalysis.objects.create(
            domain_name=domain_name,
            status='pending'
        )

        # Trigger async processing
        process_domain_analysis.delay(analysis.id)

        # Return response
        response_serializer = DomainAnalysisSerializer(analysis)
        return Response(
            {
                'message': 'Domain analysis initiated successfully',
                'analysis': response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Get PDF download URL"""
        analysis = self.get_object()

        if not analysis.pdf_url:
            return Response(
                {'error': 'PDF not yet generated'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'pdf_url': analysis.pdf_url,
            'domain_name': analysis.domain_name
        })

    @action(detail=True, methods=['get'])
    def download_json(self, request, pk=None):
        """Get JSON download URL"""
        analysis = self.get_object()

        if not analysis.json_url:
            return Response(
                {'error': 'JSON not yet generated'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'json_url': analysis.json_url,
            'domain_name': analysis.domain_name
        })

    @action(detail=True, methods=['get'])
    def training_modules(self, request, pk=None):
        """Get sales training modules for this analysis"""
        analysis = self.get_object()
        modules = analysis.training_modules.all()
        serializer = SalesTrainingSerializer(modules, many=True)

        return Response({
            'domain_name': analysis.domain_name,
            'training_modules': serializer.data
        })

    @action(detail=True, methods=['get'])
    def status_check(self, request, pk=None):
        """Check the status of an analysis"""
        analysis = self.get_object()

        return Response({
            'id': analysis.id,
            'domain_name': analysis.domain_name,
            'status': analysis.status,
            'created_at': analysis.created_at,
            'completed_at': analysis.completed_at,
            'pdf_ready': bool(analysis.pdf_url),
            'json_ready': bool(analysis.json_url),
            'error': analysis.error_message
        })


class SalesTrainingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for sales training operations

    Endpoints:
    - GET /api/training/ - List all training modules
    - GET /api/training/{id}/ - Get specific training module
    """

    queryset = SalesTraining.objects.all()
    serializer_class = SalesTrainingSerializer

    def get_queryset(self):
        """Allow filtering by domain analysis"""
        queryset = super().get_queryset()
        analysis_id = self.request.query_params.get('analysis_id')

        if analysis_id:
            queryset = queryset.filter(domain_analysis_id=analysis_id)

        return queryset

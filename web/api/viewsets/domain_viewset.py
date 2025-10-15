"""
Domain ViewSet using service layer.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from targetApp.models import Domain
from api.serializers import DomainSerializer
from services.domain_service import DomainService
from reconPoint.error_handlers import ValidationException, ResourceNotFoundException
import logging

logger = logging.getLogger(__name__)


class DomainViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Domain operations.
    
    Provides CRUD operations and additional actions for domain management.
    """
    queryset = Domain.objects.select_related('project', 'domain_info').all()
    serializer_class = DomainSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'project__slug']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'insert_date', 'start_scan_date']
    ordering = ['-insert_date']
    
    def create(self, request, *args, **kwargs):
        """
        Create a new domain.
        
        Request body:
        {
            "name": "example.com",
            "project_id": 1,
            "description": "Optional description",
            "h1_team_handle": "optional",
            "ip_address_cidr": "optional"
        }
        """
        try:
            domain = DomainService.create_domain(
                name=request.data.get('name'),
                project_id=request.data.get('project_id'),
                description=request.data.get('description'),
                h1_team_handle=request.data.get('h1_team_handle'),
                ip_address_cidr=request.data.get('ip_address_cidr'),
                request_headers=request.data.get('request_headers')
            )
            
            serializer = self.get_serializer(domain)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationException as e:
            return Response(
                {'error': str(e), 'field': getattr(e, 'field', None)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ResourceNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error creating domain: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """
        Update a domain.
        
        Request body:
        {
            "name": "newname.com",
            "description": "Updated description"
        }
        """
        try:
            domain_id = int(kwargs.get('pk'))
            
            # Filter out None values
            update_fields = {
                k: v for k, v in request.data.items()
                if v is not None and k not in ['id', 'project_id']
            }
            
            domain = DomainService.update_domain(domain_id, **update_fields)
            
            serializer = self.get_serializer(domain)
            return Response(serializer.data)
            
        except ValidationException as e:
            return Response(
                {'error': str(e), 'field': getattr(e, 'field', None)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ResourceNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error updating domain: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a domain."""
        try:
            domain_id = int(kwargs.get('pk'))
            DomainService.delete_domain(domain_id, request.user)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except ResourceNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error deleting domain: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        Get comprehensive statistics for a domain.
        
        Returns:
        {
            "id": 1,
            "name": "example.com",
            "statistics": {
                "total_scans": 10,
                "total_subdomains": 50,
                "total_vulnerabilities": 15,
                ...
            }
        }
        """
        try:
            stats = DomainService.get_domain_with_stats(int(pk))
            return Response(stats)
            
        except ResourceNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error getting domain statistics: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def scan_history(self, request, pk=None):
        """
        Get scan history for a domain.
        
        Query params:
        - limit: Maximum number of scans to return (default: 10)
        """
        try:
            limit = int(request.query_params.get('limit', 10))
            scans = DomainService.get_domain_scan_history(int(pk), limit=limit)
            
            return Response({
                'domain_id': int(pk),
                'scans': scans
            })
            
        except ResourceNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error getting scan history: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def start_scan(self, request, pk=None):
        """
        Start a new scan for the domain.
        
        Request body:
        {
            "scan_type_id": 1,
            "out_of_scope_subdomains": ["test.example.com"],
            "imported_subdomains": ["api.example.com"]
        }
        """
        try:
            from services.scan_service import ScanService
            
            scan = ScanService.create_scan(
                domain_id=int(pk),
                scan_type_id=request.data.get('scan_type_id'),
                initiated_by_user=request.user,
                out_of_scope_subdomains=request.data.get('out_of_scope_subdomains'),
                imported_subdomains=request.data.get('imported_subdomains')
            )
            
            # TODO: Dispatch Celery task to start scan
            
            return Response({
                'scan_id': scan.id,
                'status': 'initiated',
                'message': f'Scan initiated for domain {scan.domain.name}'
            }, status=status.HTTP_201_CREATED)
            
        except (ValidationException, ResourceNotFoundException) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"Error starting scan: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search domains with advanced filtering.
        
        Query params:
        - project_id: Filter by project
        - search: Search term
        - limit: Results per page (default: 100)
        - offset: Pagination offset (default: 0)
        """
        try:
            project_id = request.query_params.get('project_id')
            search = request.query_params.get('search')
            limit = int(request.query_params.get('limit', 100))
            offset = int(request.query_params.get('offset', 0))
            
            if project_id:
                project_id = int(project_id)
            
            results = DomainService.list_domains(
                project_id=project_id,
                search=search,
                limit=limit,
                offset=offset
            )
            
            return Response(results)
            
        except Exception as e:
            logger.exception(f"Error searching domains: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

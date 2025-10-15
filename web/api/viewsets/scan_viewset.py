"""
Scan ViewSet using service layer.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from startScan.models import ScanHistory
from api.serializers import ScanHistorySerializer
from services.scan_service import ScanService
from reconPoint.error_handlers import ValidationException, ResourceNotFoundException
import logging

logger = logging.getLogger(__name__)


class ScanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Scan operations.
    
    Provides read operations and actions for scan management.
    """
    queryset = ScanHistory.objects.select_related('domain', 'scan_type').all()
    serializer_class = ScanHistorySerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-start_scan_date']
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get detailed scan information.
        
        Returns comprehensive scan details including progress, statistics, and activities.
        """
        try:
            scan_id = int(kwargs.get('pk'))
            scan_details = ScanService.get_scan_details(scan_id)
            
            return Response(scan_details)
            
        except ResourceNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error retrieving scan: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def abort(self, request, pk=None):
        """
        Abort a running scan.
        
        Only pending or running scans can be aborted.
        """
        try:
            scan_id = int(pk)
            scan = ScanService.abort_scan(scan_id, request.user)
            
            return Response({
                'scan_id': scan.id,
                'status': 'aborted',
                'message': f'Scan {scan_id} has been aborted'
            })
            
        except ResourceNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"Error aborting scan: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def vulnerabilities(self, request, pk=None):
        """
        Get vulnerabilities discovered in a scan.
        
        Query params:
        - severity: Filter by severity (0-4)
        - limit: Results per page (default: 100)
        - offset: Pagination offset (default: 0)
        """
        try:
            scan_id = int(pk)
            severity = request.query_params.get('severity')
            limit = int(request.query_params.get('limit', 100))
            offset = int(request.query_params.get('offset', 0))
            
            if severity is not None:
                severity = int(severity)
            
            results = ScanService.get_scan_vulnerabilities(
                scan_id=scan_id,
                severity=severity,
                limit=limit,
                offset=offset
            )
            
            return Response(results)
            
        except ResourceNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error getting scan vulnerabilities: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def subdomains(self, request, pk=None):
        """
        Get subdomains discovered in a scan.
        
        Query params:
        - limit: Results per page (default: 100)
        - offset: Pagination offset (default: 0)
        """
        try:
            scan_id = int(pk)
            limit = int(request.query_params.get('limit', 100))
            offset = int(request.query_params.get('offset', 0))
            
            results = ScanService.get_scan_subdomains(
                scan_id=scan_id,
                limit=limit,
                offset=offset
            )
            
            return Response(results)
            
        except ResourceNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error getting scan subdomains: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        Get real-time scan progress.
        
        Returns progress percentage and current status.
        """
        try:
            scan_id = int(pk)
            scan_details = ScanService.get_scan_details(scan_id)
            
            return Response({
                'scan_id': scan_id,
                'status': scan_details['status'],
                'progress': scan_details['progress'],
                'start_date': scan_details['start_date'],
                'activities': scan_details['activities']
            })
            
        except ResourceNotFoundException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Error getting scan progress: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

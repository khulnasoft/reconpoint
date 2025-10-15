"""
Data export utilities for reconPoint.
Support for JSON, CSV, XML, and streaming exports.
"""
import csv
import json
import logging
from typing import List, Dict, Any, Iterator, Optional
from io import StringIO
from datetime import datetime

from django.http import StreamingHttpResponse, HttpResponse
from django.core.serializers import serialize
from django.db.models import QuerySet


logger = logging.getLogger(__name__)


class DataExporter:
    """Base class for data exporters."""
    
    def __init__(self, queryset: QuerySet, fields: Optional[List[str]] = None):
        """
        Initialize data exporter.
        
        Args:
            queryset: QuerySet to export
            fields: List of fields to include (None for all)
        """
        self.queryset = queryset
        self.fields = fields
    
    def export(self) -> Any:
        """
        Export data.
        
        Returns:
            Exported data
        """
        raise NotImplementedError


class JSONExporter(DataExporter):
    """Export data to JSON format."""
    
    def export(self, indent: int = 2) -> str:
        """
        Export to JSON.
        
        Args:
            indent: JSON indentation level
            
        Returns:
            JSON string
        """
        data = []
        
        for obj in self.queryset:
            obj_data = {}
            
            if self.fields:
                for field in self.fields:
                    obj_data[field] = self._get_field_value(obj, field)
            else:
                # Export all fields
                for field in obj._meta.fields:
                    obj_data[field.name] = self._get_field_value(obj, field.name)
            
            data.append(obj_data)
        
        return json.dumps(data, indent=indent, default=str)
    
    def _get_field_value(self, obj: Any, field_name: str) -> Any:
        """
        Get field value from object.
        
        Args:
            obj: Model instance
            field_name: Field name
            
        Returns:
            Field value
        """
        value = getattr(obj, field_name, None)
        
        # Convert datetime to ISO format
        if isinstance(value, datetime):
            return value.isoformat()
        
        return value


class CSVExporter(DataExporter):
    """Export data to CSV format."""
    
    def export(self) -> str:
        """
        Export to CSV.
        
        Returns:
            CSV string
        """
        output = StringIO()
        
        # Get fields
        if self.fields:
            fieldnames = self.fields
        else:
            first_obj = self.queryset.first()
            if first_obj:
                fieldnames = [field.name for field in first_obj._meta.fields]
            else:
                return ""
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for obj in self.queryset:
            row = {}
            for field in fieldnames:
                value = getattr(obj, field, None)
                
                # Convert to string
                if isinstance(value, datetime):
                    row[field] = value.isoformat()
                else:
                    row[field] = str(value) if value is not None else ''
            
            writer.writerow(row)
        
        return output.getvalue()


class XMLExporter(DataExporter):
    """Export data to XML format."""
    
    def export(self) -> str:
        """
        Export to XML.
        
        Returns:
            XML string
        """
        return serialize('xml', self.queryset, fields=self.fields)


class StreamingExporter:
    """Export large datasets using streaming."""
    
    def __init__(
        self,
        queryset: QuerySet,
        format: str = 'json',
        chunk_size: int = 1000,
        fields: Optional[List[str]] = None
    ):
        """
        Initialize streaming exporter.
        
        Args:
            queryset: QuerySet to export
            format: Export format (json, csv, xml)
            chunk_size: Number of records per chunk
            fields: List of fields to include
        """
        self.queryset = queryset
        self.format = format.lower()
        self.chunk_size = chunk_size
        self.fields = fields
    
    def stream(self) -> Iterator[str]:
        """
        Stream data in chunks.
        
        Yields:
            Data chunks as strings
        """
        if self.format == 'json':
            yield from self._stream_json()
        elif self.format == 'csv':
            yield from self._stream_csv()
        elif self.format == 'xml':
            yield from self._stream_xml()
        else:
            raise ValueError(f"Unsupported format: {self.format}")
    
    def _stream_json(self) -> Iterator[str]:
        """Stream JSON data."""
        yield '['
        
        first = True
        for chunk in self._get_chunks():
            for obj in chunk:
                if not first:
                    yield ','
                first = False
                
                obj_data = self._serialize_object(obj)
                yield json.dumps(obj_data, default=str)
        
        yield ']'
    
    def _stream_csv(self) -> Iterator[str]:
        """Stream CSV data."""
        output = StringIO()
        
        # Get fields
        if self.fields:
            fieldnames = self.fields
        else:
            first_obj = self.queryset.first()
            if first_obj:
                fieldnames = [field.name for field in first_obj._meta.fields]
            else:
                return
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        yield output.getvalue()
        output.truncate(0)
        output.seek(0)
        
        # Write data
        for chunk in self._get_chunks():
            for obj in chunk:
                row = {}
                for field in fieldnames:
                    value = getattr(obj, field, None)
                    if isinstance(value, datetime):
                        row[field] = value.isoformat()
                    else:
                        row[field] = str(value) if value is not None else ''
                
                writer.writerow(row)
            
            yield output.getvalue()
            output.truncate(0)
            output.seek(0)
    
    def _stream_xml(self) -> Iterator[str]:
        """Stream XML data."""
        yield '<?xml version="1.0" encoding="utf-8"?>\n'
        yield '<objects>\n'
        
        for chunk in self._get_chunks():
            yield serialize('xml', chunk, fields=self.fields)
        
        yield '</objects>'
    
    def _get_chunks(self) -> Iterator[List[Any]]:
        """
        Get data in chunks.
        
        Yields:
            Chunks of model instances
        """
        queryset = self.queryset
        count = 0
        
        while True:
            chunk = list(queryset[count:count + self.chunk_size])
            if not chunk:
                break
            
            yield chunk
            count += self.chunk_size
    
    def _serialize_object(self, obj: Any) -> Dict[str, Any]:
        """
        Serialize model instance to dictionary.
        
        Args:
            obj: Model instance
            
        Returns:
            Dictionary representation
        """
        data = {}
        
        if self.fields:
            fields = self.fields
        else:
            fields = [field.name for field in obj._meta.fields]
        
        for field in fields:
            value = getattr(obj, field, None)
            
            if isinstance(value, datetime):
                data[field] = value.isoformat()
            else:
                data[field] = value
        
        return data


def export_to_response(
    queryset: QuerySet,
    format: str = 'json',
    filename: Optional[str] = None,
    fields: Optional[List[str]] = None,
    streaming: bool = False
) -> HttpResponse:
    """
    Export queryset to HTTP response.
    
    Args:
        queryset: QuerySet to export
        format: Export format (json, csv, xml)
        filename: Download filename
        fields: List of fields to include
        streaming: Whether to use streaming export
        
    Returns:
        HTTP response with exported data
    """
    format = format.lower()
    
    # Set content type
    content_types = {
        'json': 'application/json',
        'csv': 'text/csv',
        'xml': 'application/xml'
    }
    content_type = content_types.get(format, 'text/plain')
    
    # Set filename
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_{timestamp}.{format}'
    
    if streaming:
        # Use streaming response for large datasets
        exporter = StreamingExporter(queryset, format=format, fields=fields)
        response = StreamingHttpResponse(
            exporter.stream(),
            content_type=content_type
        )
    else:
        # Regular response
        if format == 'json':
            exporter = JSONExporter(queryset, fields=fields)
            data = exporter.export()
        elif format == 'csv':
            exporter = CSVExporter(queryset, fields=fields)
            data = exporter.export()
        elif format == 'xml':
            exporter = XMLExporter(queryset, fields=fields)
            data = exporter.export()
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        response = HttpResponse(data, content_type=content_type)
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def export_scan_results(
    scan_id: int,
    format: str = 'json',
    include_subdomains: bool = True,
    include_endpoints: bool = True,
    include_vulnerabilities: bool = True
) -> HttpResponse:
    """
    Export complete scan results.
    
    Args:
        scan_id: Scan history ID
        format: Export format
        include_subdomains: Include subdomain data
        include_endpoints: Include endpoint data
        include_vulnerabilities: Include vulnerability data
        
    Returns:
        HTTP response with exported data
    """
    from startScan.models import ScanHistory, Subdomain, EndPoint, Vulnerability
    
    scan = ScanHistory.objects.get(id=scan_id)
    
    data = {
        'scan': {
            'id': scan.id,
            'domain': scan.domain.name,
            'start_date': scan.start_scan_date.isoformat() if scan.start_scan_date else None,
            'status': scan.scan_status,
            'engine': scan.scan_type.engine_name if scan.scan_type else None
        }
    }
    
    if include_subdomains:
        subdomains = Subdomain.objects.filter(scan_history=scan)
        data['subdomains'] = [
            {
                'name': sub.name,
                'http_status': sub.http_status,
                'is_important': sub.is_important
            }
            for sub in subdomains
        ]
    
    if include_endpoints:
        endpoints = EndPoint.objects.filter(scan_history=scan)
        data['endpoints'] = [
            {
                'url': ep.url,
                'http_status': ep.http_status,
                'content_length': ep.content_length
            }
            for ep in endpoints
        ]
    
    if include_vulnerabilities:
        vulnerabilities = Vulnerability.objects.filter(scan_history=scan)
        data['vulnerabilities'] = [
            {
                'name': vuln.name,
                'severity': vuln.severity,
                'description': vuln.description
            }
            for vuln in vulnerabilities
        ]
    
    # Export based on format
    if format == 'json':
        content = json.dumps(data, indent=2, default=str)
        content_type = 'application/json'
    else:
        # For CSV/XML, flatten the structure
        content = json.dumps(data, indent=2, default=str)
        content_type = 'application/json'
    
    response = HttpResponse(content, content_type=content_type)
    filename = f'scan_{scan_id}_results.{format}'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

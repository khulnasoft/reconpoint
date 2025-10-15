#!/usr/bin/env python3
"""
Performance Benchmark Script for reconPoint Database
Tests query performance before and after index migration
"""

import os
import sys
import django
import time
from datetime import datetime

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../web'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reconPoint.settings')
django.setup()

from django.db import connection
from django.test.utils import CaptureQueriesContext
from startScan.models import Subdomain, Vulnerability, EndPoint, ScanHistory
from targetApp.models import Domain


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{text}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.NC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.NC}")


def benchmark_query(name, query_func):
    """
    Benchmark a query function
    
    Args:
        name: Name of the query being tested
        query_func: Function that executes the query
    
    Returns:
        dict with benchmark results
    """
    print(f"\n{Colors.YELLOW}Testing: {name}{Colors.NC}")
    
    # Warm up query (first run might be slower)
    try:
        _ = query_func()
    except Exception as e:
        print_warning(f"Warmup failed: {e}")
    
    # Run benchmark
    times = []
    num_runs = 5
    
    for i in range(num_runs):
        with CaptureQueriesContext(connection) as queries:
            start_time = time.time()
            try:
                result = query_func()
                end_time = time.time()
                
                query_time = sum(float(q['time']) for q in queries)
                total_time = end_time - start_time
                times.append({
                    'query_time': query_time,
                    'total_time': total_time,
                    'num_queries': len(queries),
                    'result_count': len(result) if hasattr(result, '__len__') else 0
                })
            except Exception as e:
                print_warning(f"Run {i+1} failed: {e}")
                continue
    
    if not times:
        return None
    
    # Calculate averages
    avg_query_time = sum(t['query_time'] for t in times) / len(times)
    avg_total_time = sum(t['total_time'] for t in times) / len(times)
    avg_num_queries = sum(t['num_queries'] for t in times) / len(times)
    result_count = times[0]['result_count'] if times else 0
    
    print(f"  Average query time: {avg_query_time*1000:.2f}ms")
    print(f"  Average total time: {avg_total_time*1000:.2f}ms")
    print(f"  Number of queries: {avg_num_queries:.1f}")
    print(f"  Results returned: {result_count}")
    
    return {
        'name': name,
        'avg_query_time': avg_query_time,
        'avg_total_time': avg_total_time,
        'avg_num_queries': avg_num_queries,
        'result_count': result_count
    }


def run_benchmarks():
    """Run all performance benchmarks"""
    print_header("reconPoint Database Performance Benchmark")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Check if we have data
    print_header("Data Statistics")
    print(f"Subdomains: {Subdomain.objects.count()}")
    print(f"Vulnerabilities: {Vulnerability.objects.count()}")
    print(f"Endpoints: {EndPoint.objects.count()}")
    print(f"Scan Histories: {ScanHistory.objects.count()}")
    print(f"Domains: {Domain.objects.count()}")
    
    if Subdomain.objects.count() == 0:
        print_warning("No data found in database. Benchmarks may not be meaningful.")
    
    print_header("Running Benchmarks")
    
    # Subdomain queries
    results.append(benchmark_query(
        "Subdomain: Filter by name (indexed)",
        lambda: list(Subdomain.objects.filter(name__icontains='example')[:100])
    ))
    
    results.append(benchmark_query(
        "Subdomain: Filter by http_status (indexed)",
        lambda: list(Subdomain.objects.filter(http_status=200)[:100])
    ))
    
    results.append(benchmark_query(
        "Subdomain: Filter by is_important (indexed)",
        lambda: list(Subdomain.objects.filter(is_important=True)[:100])
    ))
    
    # Get a scan_history_id if available
    scan_history = ScanHistory.objects.first()
    if scan_history:
        results.append(benchmark_query(
            "Subdomain: Filter by scan_history (indexed)",
            lambda: list(Subdomain.objects.filter(scan_history=scan_history)[:100])
        ))
    
    # Vulnerability queries
    results.append(benchmark_query(
        "Vulnerability: Filter by severity (indexed)",
        lambda: list(Vulnerability.objects.filter(severity=3)[:100])
    ))
    
    results.append(benchmark_query(
        "Vulnerability: Order by discovered_date (indexed)",
        lambda: list(Vulnerability.objects.order_by('-discovered_date')[:100])
    ))
    
    if scan_history:
        results.append(benchmark_query(
            "Vulnerability: Filter by scan_history and severity (indexed)",
            lambda: list(Vulnerability.objects.filter(
                scan_history=scan_history,
                severity__gte=2
            )[:100])
        ))
    
    # Endpoint queries
    subdomain = Subdomain.objects.first()
    if subdomain:
        results.append(benchmark_query(
            "Endpoint: Filter by subdomain (indexed)",
            lambda: list(EndPoint.objects.filter(subdomain=subdomain)[:100])
        ))
    
    results.append(benchmark_query(
        "Endpoint: Filter by http_status (indexed)",
        lambda: list(EndPoint.objects.filter(http_status=200)[:100])
    ))
    
    # ScanHistory queries
    results.append(benchmark_query(
        "ScanHistory: Filter by scan_status (indexed)",
        lambda: list(ScanHistory.objects.filter(scan_status=2)[:100])
    ))
    
    results.append(benchmark_query(
        "ScanHistory: Order by start_scan_date (indexed)",
        lambda: list(ScanHistory.objects.order_by('-start_scan_date')[:100])
    ))
    
    # Domain queries
    results.append(benchmark_query(
        "Domain: Filter by name (indexed)",
        lambda: list(Domain.objects.filter(name__icontains='example')[:100])
    ))
    
    results.append(benchmark_query(
        "Domain: Order by start_scan_date (indexed)",
        lambda: list(Domain.objects.order_by('-start_scan_date')[:100])
    ))
    
    # Print summary
    print_header("Benchmark Summary")
    
    valid_results = [r for r in results if r is not None]
    
    if valid_results:
        print(f"\n{'Query':<50} {'Avg Time (ms)':<15} {'Results':<10}")
        print("-" * 75)
        
        for result in valid_results:
            print(f"{result['name']:<50} {result['avg_query_time']*1000:>10.2f}ms    {result['result_count']:>6}")
        
        avg_time = sum(r['avg_query_time'] for r in valid_results) / len(valid_results)
        print("-" * 75)
        print(f"{'Average across all queries':<50} {avg_time*1000:>10.2f}ms")
        
        print_success(f"\nCompleted {len(valid_results)} benchmark tests")
    else:
        print_warning("No valid benchmark results")
    
    # Check index usage
    print_header("Index Usage Statistics")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as scans,
                idx_tup_read as tuples_read
            FROM pg_stat_user_indexes
            WHERE indexname LIKE '%_idx'
            ORDER BY idx_scan DESC
            LIMIT 20;
        """)
        
        rows = cursor.fetchall()
        if rows:
            print(f"\n{'Schema':<15} {'Table':<25} {'Index':<30} {'Scans':<10} {'Tuples':<10}")
            print("-" * 100)
            for row in rows:
                print(f"{row[0]:<15} {row[1]:<25} {row[2]:<30} {row[3]:<10} {row[4]:<10}")
        else:
            print_warning("No index usage statistics available yet")
    
    print_header("Benchmark Complete")
    print_info("Save these results to compare before/after migration")
    print_info("Expected improvement: 50-70% faster queries after adding indexes")


if __name__ == '__main__':
    try:
        run_benchmarks()
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.NC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

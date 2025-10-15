"""
Performance Monitoring Utility for reconPoint
Tracks database query performance before and after optimizations
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Any
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.core.management.base import BaseCommand
from startScan.models import Subdomain, Vulnerability, EndPoint, ScanHistory
from targetApp.models import Domain


class PerformanceMonitor:
    """Monitor and benchmark database query performance."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'benchmarks': [],
            'summary': {}
        }
    
    def benchmark_query(self, name: str, query_func, iterations: int = 5) -> Dict[str, Any]:
        """Benchmark a query function multiple times.
        
        Args:
            name: Name of the benchmark
            query_func: Function that executes the query
            iterations: Number of times to run the query
            
        Returns:
            Dictionary with benchmark results
        """
        times = []
        query_counts = []
        
        for i in range(iterations):
            with CaptureQueriesContext(connection) as queries:
                start = time.time()
                result = query_func()
                end = time.time()
                
                execution_time = (end - start) * 1000  # Convert to milliseconds
                times.append(execution_time)
                query_counts.append(len(queries))
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        avg_queries = sum(query_counts) / len(query_counts)
        
        benchmark_result = {
            'name': name,
            'avg_time_ms': round(avg_time, 2),
            'min_time_ms': round(min_time, 2),
            'max_time_ms': round(max_time, 2),
            'avg_query_count': round(avg_queries, 2),
            'iterations': iterations,
            'result_count': len(result) if hasattr(result, '__len__') else 1
        }
        
        self.results['benchmarks'].append(benchmark_result)
        return benchmark_result
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all performance benchmarks."""
        
        print("=" * 70)
        print("reconPoint Performance Benchmark")
        print("=" * 70)
        print(f"Started at: {self.results['timestamp']}")
        print()
        
        # Benchmark 1: Subdomain queries
        print("1. Benchmarking Subdomain queries...")
        
        self.benchmark_query(
            "Subdomain: Filter by name (LIKE)",
            lambda: list(Subdomain.objects.filter(name__icontains='example')[:100])
        )
        
        self.benchmark_query(
            "Subdomain: Filter by scan_history",
            lambda: list(Subdomain.objects.filter(scan_history_id=1)[:100])
        )
        
        self.benchmark_query(
            "Subdomain: Filter by http_status",
            lambda: list(Subdomain.objects.filter(http_status=200)[:100])
        )
        
        self.benchmark_query(
            "Subdomain: Filter by is_important",
            lambda: list(Subdomain.objects.filter(is_important=True)[:100])
        )
        
        # Benchmark 2: Vulnerability queries
        print("2. Benchmarking Vulnerability queries...")
        
        self.benchmark_query(
            "Vulnerability: Filter by severity",
            lambda: list(Vulnerability.objects.filter(severity=4)[:100])
        )
        
        self.benchmark_query(
            "Vulnerability: Filter by scan_history + severity",
            lambda: list(Vulnerability.objects.filter(
                scan_history_id=1, 
                severity__gte=3
            )[:100])
        )
        
        self.benchmark_query(
            "Vulnerability: Filter by open_status",
            lambda: list(Vulnerability.objects.filter(open_status=True)[:100])
        )
        
        # Benchmark 3: EndPoint queries
        print("3. Benchmarking EndPoint queries...")
        
        self.benchmark_query(
            "EndPoint: Filter by subdomain",
            lambda: list(EndPoint.objects.filter(subdomain_id=1)[:100])
        )
        
        self.benchmark_query(
            "EndPoint: Filter by http_status",
            lambda: list(EndPoint.objects.filter(http_status=200)[:100])
        )
        
        # Benchmark 4: ScanHistory queries
        print("4. Benchmarking ScanHistory queries...")
        
        self.benchmark_query(
            "ScanHistory: Filter by scan_status",
            lambda: list(ScanHistory.objects.filter(scan_status=2)[:100])
        )
        
        self.benchmark_query(
            "ScanHistory: Filter by domain + date",
            lambda: list(ScanHistory.objects.filter(
                domain_id=1
            ).order_by('-start_scan_date')[:100])
        )
        
        # Benchmark 5: Complex queries (N+1 problems)
        print("5. Benchmarking complex queries...")
        
        self.benchmark_query(
            "Complex: Subdomains with related data (NO optimization)",
            lambda: self._get_subdomains_unoptimized()
        )
        
        self.benchmark_query(
            "Complex: Subdomains with related data (WITH optimization)",
            lambda: self._get_subdomains_optimized()
        )
        
        # Calculate summary
        self._calculate_summary()
        
        # Print results
        self._print_results()
        
        return self.results
    
    def _get_subdomains_unoptimized(self) -> List:
        """Get subdomains without query optimization (demonstrates N+1)."""
        subdomains = list(Subdomain.objects.all()[:10])
        for subdomain in subdomains:
            # This causes N+1 queries
            _ = subdomain.scan_history.domain.name if subdomain.scan_history else None
            _ = list(subdomain.technologies.all())
            _ = list(subdomain.ip_addresses.all())
        return subdomains
    
    def _get_subdomains_optimized(self) -> List:
        """Get subdomains with query optimization."""
        subdomains = list(
            Subdomain.objects.select_related(
                'scan_history',
                'scan_history__domain',
                'target_domain'
            ).prefetch_related(
                'technologies',
                'ip_addresses'
            )[:10]
        )
        for subdomain in subdomains:
            _ = subdomain.scan_history.domain.name if subdomain.scan_history else None
            _ = list(subdomain.technologies.all())
            _ = list(subdomain.ip_addresses.all())
        return subdomains
    
    def _calculate_summary(self):
        """Calculate summary statistics."""
        if not self.results['benchmarks']:
            return
        
        total_avg_time = sum(b['avg_time_ms'] for b in self.results['benchmarks'])
        total_queries = sum(b['avg_query_count'] for b in self.results['benchmarks'])
        
        self.results['summary'] = {
            'total_benchmarks': len(self.results['benchmarks']),
            'total_avg_time_ms': round(total_avg_time, 2),
            'avg_time_per_benchmark_ms': round(
                total_avg_time / len(self.results['benchmarks']), 2
            ),
            'total_avg_queries': round(total_queries, 2),
            'slowest_query': max(
                self.results['benchmarks'], 
                key=lambda x: x['avg_time_ms']
            )['name'],
            'fastest_query': min(
                self.results['benchmarks'], 
                key=lambda x: x['avg_time_ms']
            )['name']
        }
    
    def _print_results(self):
        """Print benchmark results in a formatted table."""
        print()
        print("=" * 70)
        print("BENCHMARK RESULTS")
        print("=" * 70)
        print()
        
        # Print individual benchmarks
        print(f"{'Benchmark':<50} {'Avg Time':<12} {'Queries':<8}")
        print("-" * 70)
        
        for benchmark in self.results['benchmarks']:
            print(
                f"{benchmark['name']:<50} "
                f"{benchmark['avg_time_ms']:>8.2f} ms  "
                f"{benchmark['avg_query_count']:>6.1f}"
            )
        
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        summary = self.results['summary']
        print(f"Total Benchmarks:        {summary['total_benchmarks']}")
        print(f"Total Avg Time:          {summary['total_avg_time_ms']:.2f} ms")
        print(f"Avg Time per Benchmark:  {summary['avg_time_per_benchmark_ms']:.2f} ms")
        print(f"Total Avg Queries:       {summary['total_avg_queries']:.2f}")
        print(f"Slowest Query:           {summary['slowest_query']}")
        print(f"Fastest Query:           {summary['fastest_query']}")
        print()
    
    def save_results(self, filename: str = None):
        """Save results to JSON file."""
        if filename is None:
            filename = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Results saved to: {filename}")
        return filename
    
    def compare_with_previous(self, previous_file: str):
        """Compare current results with previous benchmark."""
        try:
            with open(previous_file, 'r') as f:
                previous = json.load(f)
            
            print()
            print("=" * 70)
            print("COMPARISON WITH PREVIOUS BENCHMARK")
            print("=" * 70)
            print(f"Previous: {previous['timestamp']}")
            print(f"Current:  {self.results['timestamp']}")
            print()
            
            print(f"{'Benchmark':<50} {'Before':<12} {'After':<12} {'Change':<10}")
            print("-" * 70)
            
            improvements = []
            
            for current_b in self.results['benchmarks']:
                # Find matching previous benchmark
                previous_b = next(
                    (b for b in previous['benchmarks'] if b['name'] == current_b['name']),
                    None
                )
                
                if previous_b:
                    before = previous_b['avg_time_ms']
                    after = current_b['avg_time_ms']
                    change = ((after - before) / before) * 100
                    
                    improvements.append(change)
                    
                    change_str = f"{change:+.1f}%"
                    if change < 0:
                        change_str = f"✓ {change_str}"
                    
                    print(
                        f"{current_b['name']:<50} "
                        f"{before:>8.2f} ms  "
                        f"{after:>8.2f} ms  "
                        f"{change_str:>10}"
                    )
            
            if improvements:
                avg_improvement = sum(improvements) / len(improvements)
                print()
                print(f"Average Performance Change: {avg_improvement:+.1f}%")
                if avg_improvement < 0:
                    print(f"✓ Performance IMPROVED by {abs(avg_improvement):.1f}%")
                else:
                    print(f"⚠ Performance DEGRADED by {avg_improvement:.1f}%")
            
            print()
        
        except FileNotFoundError:
            print(f"Previous benchmark file not found: {previous_file}")
        except Exception as e:
            print(f"Error comparing benchmarks: {e}")


class Command(BaseCommand):
    """Django management command for running performance benchmarks."""
    
    help = 'Run performance benchmarks on database queries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save results to JSON file'
        )
        parser.add_argument(
            '--compare',
            type=str,
            help='Compare with previous benchmark file'
        )
        parser.add_argument(
            '--iterations',
            type=int,
            default=5,
            help='Number of iterations per benchmark (default: 5)'
        )
    
    def handle(self, *args, **options):
        monitor = PerformanceMonitor()
        
        # Run benchmarks
        results = monitor.run_all_benchmarks()
        
        # Save if requested
        if options['save']:
            filename = monitor.save_results()
            self.stdout.write(
                self.style.SUCCESS(f'Results saved to {filename}')
            )
        
        # Compare if requested
        if options['compare']:
            monitor.compare_with_previous(options['compare'])
        
        self.stdout.write(
            self.style.SUCCESS('Benchmark completed successfully!')
        )


# Standalone usage
if __name__ == '__main__':
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reconPoint.settings')
    django.setup()
    
    monitor = PerformanceMonitor()
    monitor.run_all_benchmarks()
    monitor.save_results()

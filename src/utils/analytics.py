"""
Analytics and Monitoring System for Second Brain Agent

This module provides comprehensive analytics tracking, performance monitoring,
and reporting capabilities for project generation metrics.

Features:
- Project generation tracking
- Performance metrics (time, tokens, cost)
- Success/failure rate analysis
- Cache hit rate monitoring
- Cost optimization insights
- Detailed reporting

Author: Second Brain Agent Team
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class GenerationMetrics:
    """Metrics for a single project generation"""
    project_name: str
    timestamp: str
    duration_seconds: float
    tokens_used: int
    estimated_cost: float
    success: bool
    project_type: str  # rest-api, fullstack, microservice, etc.
    framework: str  # fastapi, django, react, etc.
    cache_hits: int
    cache_misses: int
    llm_requests: int
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class ProjectAnalytics:
    """
    Analytics system for tracking project generation metrics.
    
    Tracks performance, costs, and success rates across all project generations.
    Provides insights for optimization and cost control.
    """
    
    def __init__(self, analytics_dir: Path = None):
        """
        Initialize analytics system.
        
        Args:
            analytics_dir: Directory to store analytics data
        """
        self.analytics_dir = analytics_dir or Path("./analytics")
        self.analytics_dir.mkdir(exist_ok=True)
        
        self.metrics_file = self.analytics_dir / "generation_metrics.jsonl"
        self.summary_file = self.analytics_dir / "summary.json"
        
        logger.info(f"Analytics initialized at: {self.analytics_dir}")
    
    def track_generation(
        self,
        project_name: str,
        duration_seconds: float,
        tokens_used: int,
        estimated_cost: float,
        success: bool,
        project_type: str = "unknown",
        framework: str = "unknown",
        cache_hits: int = 0,
        cache_misses: int = 0,
        llm_requests: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Track a project generation event.
        
        Args:
            project_name: Name of the generated project
            duration_seconds: Time taken to generate
            tokens_used: Total tokens consumed
            estimated_cost: Estimated API cost
            success: Whether generation succeeded
            project_type: Type of project (rest-api, fullstack, etc.)
            framework: Primary framework used
            cache_hits: Number of cache hits
            cache_misses: Number of cache misses
            llm_requests: Number of LLM API calls
            error_message: Error message if failed
        """
        metrics = GenerationMetrics(
            project_name=project_name,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration_seconds,
            tokens_used=tokens_used,
            estimated_cost=estimated_cost,
            success=success,
            project_type=project_type,
            framework=framework,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            llm_requests=llm_requests,
            error_message=error_message
        )
        
        # Append to JSONL file
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(metrics.to_dict()) + '\n')
        
        logger.info(
            f"Tracked generation: {project_name} "
            f"(success={success}, duration={duration_seconds:.1f}s, cost=${estimated_cost:.4f})"
        )
        
        # Update summary
        self._update_summary()
    
    def _load_all_metrics(self) -> List[GenerationMetrics]:
        """Load all metrics from file"""
        metrics = []
        if not self.metrics_file.exists():
            return metrics
        
        with open(self.metrics_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    metrics.append(GenerationMetrics(**data))
        
        return metrics
    
    def _update_summary(self):
        """Update summary statistics"""
        metrics = self._load_all_metrics()
        
        if not metrics:
            return
        
        total = len(metrics)
        successful = sum(1 for m in metrics if m.success)
        failed = total - successful
        
        total_duration = sum(m.duration_seconds for m in metrics)
        total_tokens = sum(m.tokens_used for m in metrics)
        total_cost = sum(m.estimated_cost for m in metrics)
        
        total_cache_hits = sum(m.cache_hits for m in metrics)
        total_cache_misses = sum(m.cache_misses for m in metrics)
        total_requests = sum(m.llm_requests for m in metrics)
        
        # Calculate averages
        avg_duration = total_duration / total if total > 0 else 0
        avg_tokens = total_tokens / total if total > 0 else 0
        avg_cost = total_cost / total if total > 0 else 0
        
        # Cache statistics
        cache_rate = (
            total_cache_hits / (total_cache_hits + total_cache_misses)
            if (total_cache_hits + total_cache_misses) > 0
            else 0
        )
        
        # Project type distribution
        type_distribution = defaultdict(int)
        for m in metrics:
            type_distribution[m.project_type] += 1
        
        # Framework distribution
        framework_distribution = defaultdict(int)
        for m in metrics:
            framework_distribution[m.framework] += 1
        
        # Recent metrics (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_metrics = [
            m for m in metrics
            if datetime.fromisoformat(m.timestamp) > seven_days_ago
        ]
        
        summary = {
            'generated_at': datetime.now().isoformat(),
            'total_projects': total,
            'successful_projects': successful,
            'failed_projects': failed,
            'success_rate': successful / total if total > 0 else 0,
            'total_duration_hours': total_duration / 3600,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'averages': {
                'duration_seconds': avg_duration,
                'tokens_per_project': avg_tokens,
                'cost_per_project': avg_cost
            },
            'cache_statistics': {
                'total_hits': total_cache_hits,
                'total_misses': total_cache_misses,
                'cache_hit_rate': cache_rate,
                'total_requests': total_requests
            },
            'distributions': {
                'by_type': dict(type_distribution),
                'by_framework': dict(framework_distribution)
            },
            'recent_7_days': {
                'total': len(recent_metrics),
                'successful': sum(1 for m in recent_metrics if m.success),
                'avg_duration': (
                    sum(m.duration_seconds for m in recent_metrics) / len(recent_metrics)
                    if recent_metrics else 0
                ),
                'total_cost': sum(m.estimated_cost for m in recent_metrics)
            }
        }
        
        with open(self.summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.debug("Summary updated")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get current analytics summary"""
        if not self.summary_file.exists():
            return {}
        
        with open(self.summary_file, 'r') as f:
            return json.load(f)
    
    def generate_report(self, format: str = "text") -> str:
        """
        Generate analytics report.
        
        Args:
            format: Output format ('text', 'markdown', 'json')
            
        Returns:
            Formatted report string
        """
        summary = self.get_summary()
        
        if not summary:
            return "No analytics data available yet."
        
        if format == "json":
            return json.dumps(summary, indent=2)
        
        if format == "markdown":
            return self._generate_markdown_report(summary)
        
        return self._generate_text_report(summary)
    
    def _generate_text_report(self, summary: dict) -> str:
        """Generate plain text report"""
        lines = []
        lines.append("=" * 70)
        lines.append("SECOND BRAIN AGENT - ANALYTICS REPORT")
        lines.append("=" * 70)
        lines.append(f"Generated: {summary['generated_at']}")
        lines.append("")
        
        lines.append("OVERALL STATISTICS")
        lines.append("-" * 70)
        lines.append(f"Total Projects Generated: {summary['total_projects']}")
        lines.append(f"Successful: {summary['successful_projects']}")
        lines.append(f"Failed: {summary['failed_projects']}")
        lines.append(f"Success Rate: {summary['success_rate']:.1%}")
        lines.append("")
        
        lines.append("PERFORMANCE METRICS")
        lines.append("-" * 70)
        avg = summary['averages']
        lines.append(f"Average Generation Time: {avg['duration_seconds']:.1f} seconds")
        lines.append(f"Average Tokens per Project: {avg['tokens_per_project']:.0f}")
        lines.append(f"Average Cost per Project: ${avg['cost_per_project']:.4f}")
        lines.append("")
        
        lines.append("COST ANALYSIS")
        lines.append("-" * 70)
        lines.append(f"Total Cost: ${summary['total_cost']:.2f}")
        lines.append(f"Total Tokens Used: {summary['total_tokens']:,}")
        lines.append(f"Total Duration: {summary['total_duration_hours']:.2f} hours")
        lines.append("")
        
        cache = summary['cache_statistics']
        lines.append("CACHE PERFORMANCE")
        lines.append("-" * 70)
        lines.append(f"Cache Hit Rate: {cache['cache_hit_rate']:.1%}")
        lines.append(f"Total Cache Hits: {cache['total_hits']}")
        lines.append(f"Total Cache Misses: {cache['total_misses']}")
        lines.append(f"Total LLM Requests: {cache['total_requests']}")
        lines.append("")
        
        recent = summary['recent_7_days']
        lines.append("LAST 7 DAYS")
        lines.append("-" * 70)
        lines.append(f"Projects Generated: {recent['total']}")
        lines.append(f"Successful: {recent['successful']}")
        lines.append(f"Average Duration: {recent['avg_duration']:.1f} seconds")
        lines.append(f"Total Cost: ${recent['total_cost']:.2f}")
        lines.append("")
        
        dist = summary['distributions']
        if dist['by_type']:
            lines.append("PROJECT TYPES")
            lines.append("-" * 70)
            for ptype, count in sorted(dist['by_type'].items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {ptype}: {count}")
            lines.append("")
        
        if dist['by_framework']:
            lines.append("FRAMEWORKS USED")
            lines.append("-" * 70)
            for framework, count in sorted(dist['by_framework'].items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {framework}: {count}")
            lines.append("")
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def _generate_markdown_report(self, summary: dict) -> str:
        """Generate Markdown report"""
        lines = []
        lines.append("# Second Brain Agent - Analytics Report")
        lines.append("")
        lines.append(f"**Generated:** {summary['generated_at']}")
        lines.append("")
        
        lines.append("## Overall Statistics")
        lines.append("")
        lines.append(f"- **Total Projects:** {summary['total_projects']}")
        lines.append(f"- **Successful:** {summary['successful_projects']}")
        lines.append(f"- **Failed:** {summary['failed_projects']}")
        lines.append(f"- **Success Rate:** {summary['success_rate']:.1%}")
        lines.append("")
        
        lines.append("## Performance Metrics")
        lines.append("")
        avg = summary['averages']
        lines.append(f"- **Average Generation Time:** {avg['duration_seconds']:.1f} seconds")
        lines.append(f"- **Average Tokens per Project:** {avg['tokens_per_project']:.0f}")
        lines.append(f"- **Average Cost per Project:** ${avg['cost_per_project']:.4f}")
        lines.append("")
        
        lines.append("## Cost Analysis")
        lines.append("")
        lines.append(f"- **Total Cost:** ${summary['total_cost']:.2f}")
        lines.append(f"- **Total Tokens Used:** {summary['total_tokens']:,}")
        lines.append(f"- **Total Duration:** {summary['total_duration_hours']:.2f} hours")
        lines.append("")
        
        cache = summary['cache_statistics']
        lines.append("## Cache Performance")
        lines.append("")
        lines.append(f"- **Cache Hit Rate:** {cache['cache_hit_rate']:.1%}")
        lines.append(f"- **Total Cache Hits:** {cache['total_hits']}")
        lines.append(f"- **Total Cache Misses:** {cache['total_misses']}")
        lines.append(f"- **Total LLM Requests:** {cache['total_requests']}")
        lines.append("")
        
        recent = summary['recent_7_days']
        lines.append("## Last 7 Days")
        lines.append("")
        lines.append(f"- **Projects Generated:** {recent['total']}")
        lines.append(f"- **Successful:** {recent['successful']}")
        lines.append(f"- **Average Duration:** {recent['avg_duration']:.1f} seconds")
        lines.append(f"- **Total Cost:** ${recent['total_cost']:.2f}")
        lines.append("")
        
        dist = summary['distributions']
        if dist['by_type']:
            lines.append("## Project Types Distribution")
            lines.append("")
            lines.append("| Project Type | Count |")
            lines.append("|--------------|-------|")
            for ptype, count in sorted(dist['by_type'].items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {ptype} | {count} |")
            lines.append("")
        
        if dist['by_framework']:
            lines.append("## Frameworks Distribution")
            lines.append("")
            lines.append("| Framework | Count |")
            lines.append("|-----------|-------|")
            for framework, count in sorted(dist['by_framework'].items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {framework} | {count} |")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_cost_insights(self) -> Dict[str, Any]:
        """
        Get cost optimization insights.
        
        Returns:
            Dictionary with cost insights and recommendations
        """
        summary = self.get_summary()
        
        if not summary or summary['total_projects'] == 0:
            return {
                'insights': [],
                'recommendations': ["Generate more projects to get cost insights"]
            }
        
        insights = []
        recommendations = []
        
        avg = summary['averages']
        cache = summary['cache_statistics']
        
        # High cost insight
        if avg['cost_per_project'] > 0.50:
            insights.append(
                f"Average cost per project (${avg['cost_per_project']:.2f}) is high. "
                "Consider optimizing prompts or using cheaper models."
            )
            recommendations.append("Use cached responses where possible")
            recommendations.append("Reduce max_tokens in prompts")
        
        # Low cache hit rate
        if cache['cache_hit_rate'] < 0.40:
            insights.append(
                f"Cache hit rate ({cache['cache_hit_rate']:.1%}) is low. "
                "You're missing optimization opportunities."
            )
            recommendations.append("Enable response caching")
            recommendations.append("Use templates for similar projects")
        
        # High token usage
        if avg['tokens_per_project'] > 5000:
            insights.append(
                f"Average token usage ({avg['tokens_per_project']:.0f}) is high. "
                "This directly impacts costs."
            )
            recommendations.append("Break down complex prompts")
            recommendations.append("Use more specific prompts")
        
        # Slow generation
        if avg['duration_seconds'] > 180:  # 3 minutes
            insights.append(
                f"Average generation time ({avg['duration_seconds']:.0f}s) is slow. "
                "Consider optimization."
            )
            recommendations.append("Enable async processing")
            recommendations.append("Use faster models for simple tasks")
        
        return {
            'insights': insights,
            'recommendations': recommendations,
            'metrics': {
                'avg_cost': avg['cost_per_project'],
                'cache_hit_rate': cache['cache_hit_rate'],
                'avg_tokens': avg['tokens_per_project'],
                'avg_duration': avg['duration_seconds']
            }
        }
    
    def export_metrics(self, output_file: Path, format: str = "csv"):
        """
        Export metrics to file.
        
        Args:
            output_file: Output file path
            format: Export format ('csv', 'json')
        """
        metrics = self._load_all_metrics()
        
        if not metrics:
            logger.warning("No metrics to export")
            return
        
        if format == "json":
            with open(output_file, 'w') as f:
                json.dump([m.to_dict() for m in metrics], f, indent=2)
        
        elif format == "csv":
            import csv
            with open(output_file, 'w', newline='') as f:
                if metrics:
                    fieldnames = list(metrics[0].to_dict().keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for m in metrics:
                        writer.writerow(m.to_dict())
        
        logger.info(f"Exported {len(metrics)} metrics to {output_file}")
    
    def clear_old_metrics(self, days: int = 90):
        """
        Clear metrics older than specified days.
        
        Args:
            days: Keep metrics from last N days
        """
        cutoff = datetime.now() - timedelta(days=days)
        metrics = self._load_all_metrics()
        
        # Filter recent metrics
        recent_metrics = [
            m for m in metrics
            if datetime.fromisoformat(m.timestamp) > cutoff
        ]
        
        removed = len(metrics) - len(recent_metrics)
        
        if removed > 0:
            # Rewrite file with recent metrics
            with open(self.metrics_file, 'w') as f:
                for m in recent_metrics:
                    f.write(json.dumps(m.to_dict()) + '\n')
            
            logger.info(f"Removed {removed} old metrics (older than {days} days)")
            
            # Update summary
            self._update_summary()
        else:
            logger.info("No old metrics to remove")


# Global analytics instance
_analytics_instance: Optional[ProjectAnalytics] = None


def get_analytics() -> ProjectAnalytics:
    """Get or create global analytics instance"""
    global _analytics_instance
    
    if _analytics_instance is None:
        _analytics_instance = ProjectAnalytics()
    
    return _analytics_instance


def reset_analytics():
    """Reset global analytics instance (for testing)"""
    global _analytics_instance
    _analytics_instance = None


if __name__ == "__main__":
    # Example usage
    analytics = ProjectAnalytics()
    
    # Track some sample generations
    analytics.track_generation(
        project_name="blog-api",
        duration_seconds=120.5,
        tokens_used=3500,
        estimated_cost=0.35,
        success=True,
        project_type="rest-api",
        framework="fastapi",
        cache_hits=5,
        cache_misses=3,
        llm_requests=8
    )
    
    # Generate report
    print(analytics.generate_report(format="text"))
    
    # Get insights
    insights = analytics.get_cost_insights()
    print("\nCost Insights:")
    for insight in insights['insights']:
        print(f"  - {insight}")
    
    print("\nRecommendations:")
    for rec in insights['recommendations']:
        print(f"  - {rec}")

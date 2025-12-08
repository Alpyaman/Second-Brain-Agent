"""
Unit tests for analytics module.

Tests the project analytics tracking, reporting, and insights functionality.
"""

import pytest
import json
from datetime import datetime, timedelta

from src.utils.analytics import (
    ProjectAnalytics,
    GenerationMetrics,
    get_analytics,
    reset_analytics
)


class TestGenerationMetrics:
    """Test GenerationMetrics dataclass"""
    
    def test_metrics_creation(self):
        """Test creating metrics object"""
        metrics = GenerationMetrics(
            project_name="test-project",
            timestamp="2024-01-01T12:00:00",
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
        
        assert metrics.project_name == "test-project"
        assert metrics.success is True
        assert metrics.tokens_used == 3500
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary"""
        metrics = GenerationMetrics(
            project_name="test",
            timestamp="2024-01-01T12:00:00",
            duration_seconds=120.0,
            tokens_used=3000,
            estimated_cost=0.30,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=5,
            cache_misses=3,
            llm_requests=8
        )
        
        data = metrics.to_dict()
        assert isinstance(data, dict)
        assert data['project_name'] == "test"
        assert data['tokens_used'] == 3000


class TestProjectAnalytics:
    """Test ProjectAnalytics class"""
    
    @pytest.fixture
    def temp_analytics_dir(self, tmp_path):
        """Create temporary analytics directory"""
        return tmp_path / "analytics"
    
    @pytest.fixture
    def analytics(self, temp_analytics_dir):
        """Create analytics instance with temp directory"""
        return ProjectAnalytics(analytics_dir=temp_analytics_dir)
    
    def test_initialization(self, analytics, temp_analytics_dir):
        """Test analytics initialization"""
        assert analytics.analytics_dir == temp_analytics_dir
        assert analytics.analytics_dir.exists()
        assert analytics.metrics_file.parent.exists()
    
    def test_track_generation(self, analytics):
        """Test tracking a generation"""
        analytics.track_generation(
            project_name="test-project",
            duration_seconds=120.0,
            tokens_used=3500,
            estimated_cost=0.35,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=5,
            cache_misses=3,
            llm_requests=8
        )
        
        # Check metrics file exists
        assert analytics.metrics_file.exists()
        
        # Check metrics were written
        with open(analytics.metrics_file, 'r') as f:
            line = f.readline()
            data = json.loads(line)
            assert data['project_name'] == "test-project"
            assert data['success'] is True
    
    def test_multiple_generations(self, analytics):
        """Test tracking multiple generations"""
        for i in range(5):
            analytics.track_generation(
                project_name=f"project-{i}",
                duration_seconds=100.0 + i * 10,
                tokens_used=3000 + i * 100,
                estimated_cost=0.30 + i * 0.01,
                success=i % 2 == 0,  # Alternate success/failure
                project_type="rest-api",
                framework="fastapi",
                cache_hits=5,
                cache_misses=3,
                llm_requests=8
            )
        
        metrics = analytics._load_all_metrics()
        assert len(metrics) == 5
        assert metrics[0].project_name == "project-0"
        assert metrics[4].project_name == "project-4"
    
    def test_get_summary(self, analytics):
        """Test getting summary"""
        # Track some generations
        analytics.track_generation(
            project_name="test-1",
            duration_seconds=120.0,
            tokens_used=3500,
            estimated_cost=0.35,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=5,
            cache_misses=3,
            llm_requests=8
        )
        
        analytics.track_generation(
            project_name="test-2",
            duration_seconds=150.0,
            tokens_used=4000,
            estimated_cost=0.40,
            success=False,
            project_type="fullstack",
            framework="react",
            cache_hits=3,
            cache_misses=5,
            llm_requests=8,
            error_message="Test error"
        )
        
        summary = analytics.get_summary()
        assert summary['total_projects'] == 2
        assert summary['successful_projects'] == 1
        assert summary['failed_projects'] == 1
        assert summary['success_rate'] == 0.5
    
    def test_generate_text_report(self, analytics):
        """Test generating text report"""
        analytics.track_generation(
            project_name="test",
            duration_seconds=120.0,
            tokens_used=3500,
            estimated_cost=0.35,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=5,
            cache_misses=3,
            llm_requests=8
        )
        
        report = analytics.generate_report(format="text")
        assert "ANALYTICS REPORT" in report
        assert "Total Projects Generated: 1" in report
        assert "Success Rate: 100.0%" in report
    
    def test_generate_markdown_report(self, analytics):
        """Test generating markdown report"""
        analytics.track_generation(
            project_name="test",
            duration_seconds=120.0,
            tokens_used=3500,
            estimated_cost=0.35,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=5,
            cache_misses=3,
            llm_requests=8
        )
        
        report = analytics.generate_report(format="markdown")
        assert "# Second Brain Agent" in report
        assert "## Overall Statistics" in report
        assert "- **Total Projects:** 1" in report
    
    def test_generate_json_report(self, analytics):
        """Test generating JSON report"""
        analytics.track_generation(
            project_name="test",
            duration_seconds=120.0,
            tokens_used=3500,
            estimated_cost=0.35,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=5,
            cache_misses=3,
            llm_requests=8
        )
        
        report = analytics.generate_report(format="json")
        data = json.loads(report)
        assert data['total_projects'] == 1
        assert 'averages' in data
    
    def test_cost_insights(self, analytics):
        """Test getting cost insights"""
        # High cost project
        analytics.track_generation(
            project_name="expensive",
            duration_seconds=300.0,
            tokens_used=10000,
            estimated_cost=1.50,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=1,
            cache_misses=20,
            llm_requests=21
        )
        
        insights = analytics.get_cost_insights()
        assert 'insights' in insights
        assert 'recommendations' in insights
        assert len(insights['insights']) > 0  # Should have insights
    
    def test_export_csv(self, analytics, tmp_path):
        """Test exporting metrics to CSV"""
        analytics.track_generation(
            project_name="test",
            duration_seconds=120.0,
            tokens_used=3500,
            estimated_cost=0.35,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=5,
            cache_misses=3,
            llm_requests=8
        )
        
        output_file = tmp_path / "metrics.csv"
        analytics.export_metrics(output_file, format="csv")
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "project_name" in content
        assert "test" in content
    
    def test_export_json(self, analytics, tmp_path):
        """Test exporting metrics to JSON"""
        analytics.track_generation(
            project_name="test",
            duration_seconds=120.0,
            tokens_used=3500,
            estimated_cost=0.35,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=5,
            cache_misses=3,
            llm_requests=8
        )
        
        output_file = tmp_path / "metrics.json"
        analytics.export_metrics(output_file, format="json")
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]['project_name'] == "test"
    
    def test_clear_old_metrics(self, analytics):
        """Test clearing old metrics"""
        # Add old metric (simulated)
        old_timestamp = (datetime.now() - timedelta(days=100)).isoformat()
        with open(analytics.metrics_file, 'a') as f:
            old_metric = GenerationMetrics(
                project_name="old-project",
                timestamp=old_timestamp,
                duration_seconds=100.0,
                tokens_used=3000,
                estimated_cost=0.30,
                success=True,
                project_type="rest-api",
                framework="fastapi",
                cache_hits=5,
                cache_misses=3,
                llm_requests=8
            )
            f.write(json.dumps(old_metric.to_dict()) + '\n')
        
        # Add recent metric
        analytics.track_generation(
            project_name="new-project",
            duration_seconds=120.0,
            tokens_used=3500,
            estimated_cost=0.35,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=5,
            cache_misses=3,
            llm_requests=8
        )
        
        # Clear old metrics (>90 days)
        analytics.clear_old_metrics(days=90)
        
        metrics = analytics._load_all_metrics()
        assert len(metrics) == 1
        assert metrics[0].project_name == "new-project"
    
    def test_cache_statistics(self, analytics):
        """Test cache statistics calculation"""
        analytics.track_generation(
            project_name="cached",
            duration_seconds=80.0,
            tokens_used=2000,
            estimated_cost=0.20,
            success=True,
            project_type="rest-api",
            framework="fastapi",
            cache_hits=7,
            cache_misses=3,
            llm_requests=10
        )
        
        summary = analytics.get_summary()
        cache = summary['cache_statistics']
        assert cache['total_hits'] == 7
        assert cache['total_misses'] == 3
        assert cache['cache_hit_rate'] == 0.7  # 7/10
    
    def test_project_type_distribution(self, analytics):
        """Test project type distribution"""
        analytics.track_generation("proj1", 100.0, 3000, 0.30, True, "rest-api", "fastapi", 5, 3, 8)
        analytics.track_generation("proj2", 100.0, 3000, 0.30, True, "rest-api", "django", 5, 3, 8)
        analytics.track_generation("proj3", 100.0, 3000, 0.30, True, "fullstack", "react", 5, 3, 8)
        
        summary = analytics.get_summary()
        dist = summary['distributions']['by_type']
        assert dist['rest-api'] == 2
        assert dist['fullstack'] == 1
    
    def test_framework_distribution(self, analytics):
        """Test framework distribution"""
        analytics.track_generation("proj1", 100.0, 3000, 0.30, True, "rest-api", "fastapi", 5, 3, 8)
        analytics.track_generation("proj2", 100.0, 3000, 0.30, True, "rest-api", "fastapi", 5, 3, 8)
        analytics.track_generation("proj3", 100.0, 3000, 0.30, True, "fullstack", "django", 5, 3, 8)
        
        summary = analytics.get_summary()
        dist = summary['distributions']['by_framework']
        assert dist['fastapi'] == 2
        assert dist['django'] == 1
    
    def test_empty_analytics(self, analytics):
        """Test analytics with no data"""
        summary = analytics.get_summary()
        assert summary == {}
        
        report = analytics.generate_report()
        assert "No analytics data" in report
        
        insights = analytics.get_cost_insights()
        assert len(insights['recommendations']) > 0


class TestGlobalAnalytics:
    """Test global analytics functions"""
    
    def test_get_analytics_singleton(self):
        """Test global analytics instance"""
        reset_analytics()
        
        analytics1 = get_analytics()
        analytics2 = get_analytics()
        
        assert analytics1 is analytics2  # Same instance
    
    def test_reset_analytics(self):
        """Test resetting global instance"""
        analytics1 = get_analytics()
        reset_analytics()
        analytics2 = get_analytics()
        
        assert analytics1 is not analytics2  # Different instances


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

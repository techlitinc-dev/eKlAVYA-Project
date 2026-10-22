"""
Batch Monitor Service for Gemini API - Mentor AI Platform

This module provides comprehensive monitoring and analytics for Gemini batch processing,
including cost tracking, performance metrics, and real-time dashboards.

Features:
- Real-time batch processing monitoring
- Comprehensive cost analysis and savings tracking
- Performance metrics and SLA monitoring
- Alert system for cost and performance issues
- Historical data analysis and trend reporting
- Dashboard integration and API endpoints
- Automated report generation
- Resource utilization monitoring

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.batch_monitor_service import BatchMonitorService
    >>> 
    >>> # Initialize monitor
    >>> monitor = BatchMonitorService()
    >>> 
    >>> # Track batch processing
    >>> monitor.track_batch_processing(batch_result)
    >>> 
    >>> # Get analytics
    >>> analytics = monitor.get_cost_analytics()
    >>> print(f"Total savings: ${analytics['total_savings']:.2f}")
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading

from services.gemini_batch_service import BatchResult
from services.batch_queue_manager import QueueMetrics

# Configure logging
logger = logging.getLogger(__name__)

# Monitoring configuration
DEFAULT_METRICS_RETENTION_HOURS = 24 * 7  # 1 week
DEFAULT_ALERT_THRESHOLDS = {
    "cost_per_hour": 10.0,  # $10/hour
    "batch_failure_rate": 0.1,  # 10%
    "average_wait_time": 300,  # 5 minutes
    "queue_utilization": 0.9,  # 90%
    "batch_size_efficiency": 0.5  # 50% of max batch size
}

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    COST = "cost"
    PERFORMANCE = "performance"
    QUEUE = "queue"
    ERROR = "error"
    UTILIZATION = "utilization"

@dataclass
class Alert:
    """Alert definition for monitoring thresholds."""
    alert_id: str
    level: AlertLevel
    metric_type: MetricType
    message: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class BatchMetrics:
    """Metrics for a single batch."""
    batch_id: str
    batch_size: int
    processing_time: float
    cost_individual: float
    cost_batch: float
    cost_savings: float
    tokens_saved: int
    success_rate: float
    request_types: Dict[str, int]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class CostAnalytics:
    """Cost analysis and savings metrics."""
    total_cost_individual: float
    total_cost_batch: float
    total_cost_savings: float
    savings_percentage: float
    cost_per_request: float
    cost_per_hour: float
    projected_monthly_savings: float
    roi_percentage: float
    breakdown_by_type: Dict[str, float]
    trend_data: List[Dict[str, Any]]

@dataclass
class PerformanceAnalytics:
    """Performance metrics and analysis."""
    average_batch_size: float
    average_processing_time: float
    throughput_per_hour: float
    success_rate: float
    failure_rate: float
    average_wait_time: float
    peak_throughput: float
    sla_compliance: Dict[str, float]
    bottlenecks: List[str]

class BatchMonitorService:
    """
    Comprehensive monitoring service for Gemini batch processing.
    
    This service tracks all aspects of batch processing including costs,
    performance, queue health, and generates alerts for issues.
    
    Attributes:
        metrics_history: Historical metrics storage
        alerts: Active and resolved alerts
        thresholds: Alert configuration thresholds
        real_time_metrics: Current processing metrics
        dashboard_data: Dashboard-ready data
    
    Example:
        >>> monitor = BatchMonitorService()
        >>> monitor.track_batch_processing(batch_result)
        >>> analytics = monitor.get_comprehensive_analytics()
    """
    
    def __init__(
        self,
        retention_hours: int = DEFAULT_METRICS_RETENTION_HOURS,
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        """
        Initialize Batch Monitor Service.
        
        Args:
            retention_hours: Hours to retain metrics data
            alert_thresholds: Custom alert thresholds
        """
        logger.info("Initializing BatchMonitorService")
        
        # Configuration
        self.retention_hours = retention_hours
        self.thresholds = alert_thresholds or DEFAULT_ALERT_THRESHOLDS
        
        # Metrics storage
        self.metrics_history = deque(maxlen=10000)  # Circular buffer
        self.cost_history = deque(maxlen=1000)
        self.performance_history = deque(maxlen=1000)
        self.queue_history = deque(maxlen=1000)
        
        # Alerts
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.alert_lock = threading.Lock()
        
        # Real-time metrics
        self.real_time_metrics = {
            "current_batch_size": 0,
            "current_processing_time": 0.0,
            "current_cost_savings": 0.0,
            "requests_per_second": 0.0,
            "queue_size": 0,
            "queue_utilization": 0.0
        }
        
        # Aggregated metrics
        self.aggregated_metrics = {
            "total_batches": 0,
            "total_requests": 0,
            "total_cost_savings": 0.0,
            "total_tokens_saved": 0,
            "average_batch_size": 0.0,
            "average_processing_time": 0.0,
            "success_rate": 1.0,
            "uptime_percentage": 100.0
        }
        
        # Background monitoring
        self.monitoring_active = True
        self.monitoring_thread = None
        
        # Start monitoring
        self._start_monitoring()
        
        logger.info(
            f"BatchMonitorService initialized (retention={retention_hours}h, "
            f"alerts_enabled=True)"
        )
    
    def track_batch_processing(self, batch_result: BatchResult):
        """
        Track metrics for a processed batch.
        
        Args:
            batch_result: Result of batch processing
        
        Example:
            >>> monitor.track_batch_processing(batch_result)
        """
        # Create batch metrics
        batch_metrics = BatchMetrics(
            batch_id=batch_result.batch_id,
            batch_size=len(batch_result.requests_processed),
            processing_time=batch_result.processing_time,
            cost_individual=batch_result.cost_individual,
            cost_batch=batch_result.cost_batch,
            cost_savings=batch_result.cost_savings,
            tokens_saved=batch_result.tokens_saved,
            success_rate=1.0 if batch_result.success else 0.0,
            request_types=self._extract_request_types(batch_result),
            timestamp=datetime.now()
        )
        
        # Store metrics
        self.metrics_history.append(batch_metrics)
        self.cost_history.append({
            "timestamp": batch_metrics.timestamp,
            "cost_savings": batch_metrics.cost_savings,
            "cost_individual": batch_metrics.cost_individual,
            "cost_batch": batch_metrics.cost_batch
        })
        self.performance_history.append({
            "timestamp": batch_metrics.timestamp,
            "batch_size": batch_metrics.batch_size,
            "processing_time": batch_metrics.processing_time,
            "success_rate": batch_metrics.success_rate
        })
        
        # Update real-time metrics
        self.real_time_metrics["current_batch_size"] = batch_metrics.batch_size
        self.real_time_metrics["current_processing_time"] = batch_metrics.processing_time
        self.real_time_metrics["current_cost_savings"] = batch_metrics.cost_savings
        
        # Update aggregated metrics
        self._update_aggregated_metrics(batch_metrics)
        
        # Check for alerts
        self._check_alerts(batch_metrics)
        
        logger.info(
            f"Tracked batch {batch_result.batch_id}: "
            f"{batch_metrics.batch_size} requests, ${batch_metrics.cost_savings:.4f} saved"
        )
    
    def track_queue_metrics(self, queue_metrics: QueueMetrics):
        """
        Track queue performance metrics.
        
        Args:
            queue_metrics: Current queue metrics
        
        Example:
            >>> monitor.track_queue_metrics(queue_metrics)
        """
        # Handle both QueueMetrics object and dict
        if hasattr(queue_metrics, 'current_queue_size'):
            # QueueMetrics object
            queue_data = {
                "timestamp": datetime.now(),
                "queue_size": queue_metrics.current_queue_size,
                "utilization": queue_metrics.queue_utilization,
                "average_wait_time": queue_metrics.average_wait_time,
                "total_enqueued": queue_metrics.total_enqueued,
                "total_processed": queue_metrics.total_processed
            }
        else:
            # Dict object
            queue_data = {
                "timestamp": datetime.now(),
                "queue_size": queue_metrics.get("current_queue_size", 0),
                "utilization": queue_metrics.get("queue_utilization", 0.0),
                "average_wait_time": queue_metrics.get("average_wait_time", 0.0),
                "total_enqueued": queue_metrics.get("total_enqueued", 0),
                "total_processed": queue_metrics.get("total_processed", 0)
            }
        
        self.queue_history.append(queue_data)
        
        # Update real-time metrics
        self.real_time_metrics["queue_size"] = queue_metrics.current_queue_size
        self.real_time_metrics["queue_utilization"] = queue_metrics.queue_utilization
        
        # Check queue alerts
        self._check_queue_alerts(queue_data)
    
    def get_cost_analytics(
        self, 
        time_window_hours: int = 24
    ) -> CostAnalytics:
        """
        Get comprehensive cost analytics.
        
        Args:
            time_window_hours: Hours of data to analyze
        
        Returns:
            CostAnalytics with detailed cost analysis
        
        Example:
            >>> analytics = monitor.get_cost_analytics(time_window_hours=24)
            >>> print(f"Savings: {analytics.savings_percentage:.1f}%")
        """
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        # Filter recent cost data
        recent_costs = [
            cost for cost in self.cost_history
            if cost["timestamp"] > cutoff_time
        ]
        
        if not recent_costs:
            return CostAnalytics(
                total_cost_individual=0.0,
                total_cost_batch=0.0,
                total_cost_savings=0.0,
                savings_percentage=0.0,
                cost_per_request=0.0,
                cost_per_hour=0.0,
                projected_monthly_savings=0.0,
                roi_percentage=0.0,
                breakdown_by_type={},
                trend_data=[]
            )
        
        # Calculate metrics
        total_individual = sum(c["cost_individual"] for c in recent_costs)
        total_batch = sum(c["cost_batch"] for c in recent_costs)
        total_savings = sum(c["cost_savings"] for c in recent_costs)
        
        savings_percentage = (total_savings / max(total_individual, 0.001)) * 100
        cost_per_hour = total_batch / max(time_window_hours, 1)
        
        # Project monthly savings
        daily_savings = total_savings / max(time_window_hours / 24, 1)
        projected_monthly_savings = daily_savings * 30
        
        # ROI calculation (assuming batch implementation cost)
        implementation_cost = 1000  # Estimated implementation cost
        monthly_savings = projected_monthly_savings
        roi_percentage = (monthly_savings * 12 / implementation_cost) * 100
        
        # Trend data
        trend_data = self._generate_cost_trend(recent_costs)
        
        return CostAnalytics(
            total_cost_individual=total_individual,
            total_cost_batch=total_batch,
            total_cost_savings=total_savings,
            savings_percentage=savings_percentage,
            cost_per_request=total_batch / max(len(recent_costs), 1),
            cost_per_hour=cost_per_hour,
            projected_monthly_savings=projected_monthly_savings,
            roi_percentage=roi_percentage,
            breakdown_by_type=self._get_cost_breakdown(recent_costs),
            trend_data=trend_data
        )
    
    def get_performance_analytics(
        self, 
        time_window_hours: int = 24
    ) -> PerformanceAnalytics:
        """
        Get comprehensive performance analytics.
        
        Args:
            time_window_hours: Hours of data to analyze
        
        Returns:
            PerformanceAnalytics with detailed performance analysis
        
        Example:
            >>> analytics = monitor.get_performance_analytics()
            >>> print(f"Throughput: {analytics.throughput_per_hour:.1f} req/hour")
        """
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        # Filter recent performance data
        recent_performance = [
            perf for perf in self.performance_history
            if perf["timestamp"] > cutoff_time
        ]
        
        if not recent_performance:
            return PerformanceAnalytics(
                average_batch_size=0.0,
                average_processing_time=0.0,
                throughput_per_hour=0.0,
                success_rate=0.0,
                failure_rate=0.0,
                average_wait_time=0.0,
                peak_throughput=0.0,
                sla_compliance={},
                bottlenecks=[]
            )
        
        # Calculate metrics
        batch_sizes = [p["batch_size"] for p in recent_performance]
        processing_times = [p["processing_time"] for p in recent_performance]
        success_rates = [p["success_rate"] for p in recent_performance]
        
        average_batch_size = sum(batch_sizes) / len(batch_sizes)
        average_processing_time = sum(processing_times) / len(processing_times)
        success_rate = sum(success_rates) / len(success_rates)
        failure_rate = 1.0 - success_rate
        
        # Throughput calculation
        total_requests = sum(batch_sizes)
        throughput_per_hour = total_requests / max(time_window_hours, 1)
        peak_throughput = max(batch_sizes) if batch_sizes else 0
        
        # Average wait time from queue metrics
        recent_queue = [
            q for q in self.queue_history
            if q["timestamp"] > cutoff_time
        ]
        average_wait_time = (
            sum(q["average_wait_time"] for q in recent_queue) / 
            max(len(recent_queue), 1)
        )
        
        # SLA compliance
        sla_compliance = {
            "processing_time_<60s": sum(1 for t in processing_times if t < 60) / len(processing_times),
            "success_rate_>95%": sum(1 for r in success_rates if r > 0.95) / len(success_rates),
            "batch_size_>5": sum(1 for s in batch_sizes if s >= 5) / len(batch_sizes)
        }
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(recent_performance, recent_queue)
        
        return PerformanceAnalytics(
            average_batch_size=average_batch_size,
            average_processing_time=average_processing_time,
            throughput_per_hour=throughput_per_hour,
            success_rate=success_rate,
            failure_rate=failure_rate,
            average_wait_time=average_wait_time,
            peak_throughput=peak_throughput,
            sla_compliance=sla_compliance,
            bottlenecks=bottlenecks
        )
    
    def get_real_time_dashboard(self) -> Dict[str, Any]:
        """
        Get real-time dashboard data.
        
        Returns:
            Dictionary with dashboard-ready data
        
        Example:
            >>> dashboard = monitor.get_real_time_dashboard()
            >>> print(f"Current savings: ${dashboard['current_savings']:.2f}")
        """
        # Get recent metrics for trend calculation
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 batches
        
        return {
            "timestamp": datetime.now().isoformat(),
            "real_time_metrics": self.real_time_metrics.copy(),
            "aggregated_metrics": self.aggregated_metrics.copy(),
            "active_alerts": len(self.active_alerts),
            "alert_summary": self._get_alert_summary(),
            "recent_trends": {
                "cost_savings_trend": self._calculate_trend(
                    [m.cost_savings for m in recent_metrics]
                ),
                "batch_size_trend": self._calculate_trend(
                    [m.batch_size for m in recent_metrics]
                ),
                "processing_time_trend": self._calculate_trend(
                    [m.processing_time for m in recent_metrics]
                )
            },
            "performance_indicators": {
                "status": self._get_overall_status(),
                "health_score": self._calculate_health_score(),
                "efficiency_score": self._calculate_efficiency_score()
            }
        }
    
    def get_alerts(
        self, 
        level: Optional[AlertLevel] = None,
        resolved: Optional[bool] = None
    ) -> List[Alert]:
        """
        Get alerts with optional filtering.
        
        Args:
            level: Filter by alert level
            resolved: Filter by resolved status
        
        Returns:
            List of matching alerts
        
        Example:
            >>> critical_alerts = monitor.get_alerts(level=AlertLevel.CRITICAL)
            >>> print(f"Found {len(critical_alerts)} critical alerts")
        """
        alerts = list(self.alert_history)
        
        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def create_alert(
        self,
        level: AlertLevel,
        metric_type: MetricType,
        message: str,
        value: float,
        threshold: float
    ) -> Alert:
        """
        Create a new alert.
        
        Args:
            level: Alert severity level
            metric_type: Type of metric that triggered alert
            message: Alert message
            value: Current metric value
            threshold: Threshold that was exceeded
        
        Returns:
            Created Alert object
        
        Example:
            >>> alert = monitor.create_alert(
            ...     AlertLevel.WARNING,
            ...     MetricType.COST,
            ...     "High cost per hour detected",
            ...     15.0,
            ...     10.0
            ... )
        """
        alert = Alert(
            alert_id=f"alert_{int(time.time())}_{len(self.alert_history)}",
            level=level,
            metric_type=metric_type,
            message=message,
            value=value,
            threshold=threshold
        )
        
        with self.alert_lock:
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)
        
        logger.warning(
            f"Alert created: {level.value} - {message} "
            f"(value: {value}, threshold: {threshold})"
        )
        
        return alert
    
    def resolve_alert(self, alert_id: str):
        """
        Resolve an active alert.
        
        Args:
            alert_id: ID of alert to resolve
        
        Example:
            >>> monitor.resolve_alert("alert_123456")
        """
        with self.alert_lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                
                # Move from active to history
                del self.active_alerts[alert_id]
                
                logger.info(f"Alert resolved: {alert_id}")
    
    def generate_report(
        self, 
        report_type: str = "comprehensive",
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Generate monitoring report.
        
        Args:
            report_type: Type of report (comprehensive, cost, performance)
            time_window_hours: Hours of data to include
        
        Returns:
            Dictionary with report data
        
        Example:
            >>> report = monitor.generate_report("comprehensive", 24)
            >>> print(f"Report generated with {len(report)} sections")
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "time_window_hours": time_window_hours,
            "report_type": report_type
        }
        
        if report_type in ["comprehensive", "cost"]:
            cost_analytics = self.get_cost_analytics(time_window_hours)
            report["cost_analytics"] = {
                "total_cost_individual": cost_analytics.total_cost_individual,
                "total_cost_batch": cost_analytics.total_cost_batch,
                "total_cost_savings": cost_analytics.total_cost_savings,
                "savings_percentage": cost_analytics.savings_percentage,
                "projected_monthly_savings": cost_analytics.projected_monthly_savings,
                "roi_percentage": cost_analytics.roi_percentage,
                "cost_breakdown": cost_analytics.breakdown_by_type,
                "trend_data": cost_analytics.trend_data
            }
        
        if report_type in ["comprehensive", "performance"]:
            performance_analytics = self.get_performance_analytics(time_window_hours)
            report["performance_analytics"] = {
                "average_batch_size": performance_analytics.average_batch_size,
                "average_processing_time": performance_analytics.average_processing_time,
                "throughput_per_hour": performance_analytics.throughput_per_hour,
                "success_rate": performance_analytics.success_rate,
                "failure_rate": performance_analytics.failure_rate,
                "average_wait_time": performance_analytics.average_wait_time,
                "peak_throughput": performance_analytics.peak_throughput,
                "sla_compliance": performance_analytics.sla_compliance,
                "bottlenecks": performance_analytics.bottlenecks
            }
        
        if report_type in ["comprehensive", "alerts"]:
            report["alerts"] = {
                "active_alerts": len(self.active_alerts),
                "total_alerts": len(self.alert_history),
                "alert_summary": self._get_alert_summary(),
                "recent_alerts": [
                    {
                        "id": a.alert_id,
                        "level": a.level.value,
                        "message": a.message,
                        "timestamp": a.timestamp.isoformat()
                    }
                    for a in list(self.alert_history)[-10:]
                ]
            }
        
        if report_type == "comprehensive":
            report["summary"] = {
                "overall_health": self._calculate_health_score(),
                "efficiency_score": self._calculate_efficiency_score(),
                "recommendations": self._generate_recommendations()
            }
        
        return report
    
    def _update_aggregated_metrics(self, batch_metrics: BatchMetrics):
        """Update aggregated metrics with new batch data."""
        self.aggregated_metrics["total_batches"] += 1
        self.aggregated_metrics["total_requests"] += batch_metrics.batch_size
        self.aggregated_metrics["total_cost_savings"] += batch_metrics.cost_savings
        self.aggregated_metrics["total_tokens_saved"] += batch_metrics.tokens_saved
        
        # Update averages
        total_batches = self.aggregated_metrics["total_batches"]
        total_requests = self.aggregated_metrics["total_requests"]
        
        self.aggregated_metrics["average_batch_size"] = total_requests / total_batches
        
        # Update success rate
        current_success_rate = self.aggregated_metrics["success_rate"]
        self.aggregated_metrics["success_rate"] = (
            (current_success_rate * (total_batches - 1) + batch_metrics.success_rate) / 
            total_batches
        )
    
    def _check_alerts(self, batch_metrics: BatchMetrics):
        """Check for alert conditions based on batch metrics."""
        # Cost per hour alert
        cost_per_hour = batch_metrics.cost_batch / max(batch_metrics.processing_time / 3600, 1)
        if cost_per_hour > self.thresholds["cost_per_hour"]:
            self.create_alert(
                AlertLevel.WARNING,
                MetricType.COST,
                f"High cost per hour: ${cost_per_hour:.2f}",
                cost_per_hour,
                self.thresholds["cost_per_hour"]
            )
        
        # Batch size efficiency alert
        max_batch_size = 20  # From batch service config
        efficiency = batch_metrics.batch_size / max_batch_size
        if efficiency < self.thresholds["batch_size_efficiency"]:
            self.create_alert(
                AlertLevel.INFO,
                MetricType.UTILIZATION,
                f"Low batch efficiency: {efficiency:.1%}",
                efficiency,
                self.thresholds["batch_size_efficiency"]
            )
        
        # Processing time alert
        if batch_metrics.processing_time > 60:  # 1 minute
            self.create_alert(
                AlertLevel.WARNING,
                MetricType.PERFORMANCE,
                f"Slow batch processing: {batch_metrics.processing_time:.1f}s",
                batch_metrics.processing_time,
                60.0
            )
    
    def _check_queue_alerts(self, queue_data: Dict[str, Any]):
        """Check for queue-related alerts."""
        # Queue utilization alert
        if queue_data["utilization"] > self.thresholds["queue_utilization"]:
            self.create_alert(
                AlertLevel.WARNING,
                MetricType.QUEUE,
                f"High queue utilization: {queue_data['utilization']:.1%}",
                queue_data["utilization"],
                self.thresholds["queue_utilization"]
            )
        
        # Wait time alert
        if queue_data["average_wait_time"] > self.thresholds["average_wait_time"]:
            self.create_alert(
                AlertLevel.WARNING,
                MetricType.PERFORMANCE,
                f"High average wait time: {queue_data['average_wait_time']:.1f}s",
                queue_data["average_wait_time"],
                self.thresholds["average_wait_time"]
            )
    
    def _extract_request_types(self, batch_result: BatchResult) -> Dict[str, int]:
        """Extract request type distribution from batch result."""
        # This would need to be implemented based on batch result structure
        return {"question_generation": len(batch_result.requests_processed)}
    
    def _generate_cost_trend(self, cost_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate cost trend data for charts."""
        return [
            {
                "timestamp": c["timestamp"].isoformat(),
                "cost_savings": c["cost_savings"],
                "cost_individual": c["cost_individual"],
                "cost_batch": c["cost_batch"]
            }
            for c in cost_data[-24:]  # Last 24 data points
        ]
    
    def _get_cost_breakdown(self, cost_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Get cost breakdown by request type."""
        breakdown = defaultdict(float)
        for cost in cost_data:
            # This would need actual request type data
            breakdown["question_generation"] += cost["cost_savings"]
        return dict(breakdown)
    
    def _identify_bottlenecks(
        self, 
        performance_data: List[Dict[str, Any]], 
        queue_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Check processing times
        processing_times = [p["processing_time"] for p in performance_data]
        if processing_times and max(processing_times) > 120:  # 2 minutes
            bottlenecks.append("Slow batch processing times detected")
        
        # Check batch sizes
        batch_sizes = [p["batch_size"] for p in performance_data]
        if batch_sizes and min(batch_sizes) < 3:
            bottlenecks.append("Small batch sizes reducing efficiency")
        
        # Check queue utilization
        if queue_data:
            max_utilization = max(q["utilization"] for q in queue_data)
            if max_utilization > 0.9:
                bottlenecks.append("High queue utilization causing delays")
        
        return bottlenecks
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values."""
        if len(values) < 2:
            return "stable"
        
        recent = values[-3:] if len(values) >= 3 else values
        if len(recent) < 2:
            return "stable"
        
        avg_first = sum(recent[:len(recent)//2]) / (len(recent)//2)
        avg_last = sum(recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
        
        change = (avg_last - avg_first) / max(avg_first, 0.001)
        
        if change > 0.1:
            return "increasing"
        elif change < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _get_overall_status(self) -> str:
        """Get overall system status."""
        if len(self.active_alerts) == 0:
            return "healthy"
        elif len(self.active_alerts) < 3:
            return "warning"
        else:
            return "critical"
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-100)."""
        score = 100.0
        
        # Deduct for active alerts
        critical_alerts = sum(1 for a in self.active_alerts.values() if a.level == AlertLevel.CRITICAL)
        warning_alerts = sum(1 for a in self.active_alerts.values() if a.level == AlertLevel.WARNING)
        
        score -= (critical_alerts * 20) + (warning_alerts * 10)
        
        # Deduct for low success rate
        if self.aggregated_metrics["success_rate"] < 0.95:
            score -= (0.95 - self.aggregated_metrics["success_rate"]) * 100
        
        return max(0.0, min(100.0, score))
    
    def _calculate_efficiency_score(self) -> float:
        """Calculate batch processing efficiency score (0-100)."""
        score = 100.0
        
        # Check batch size efficiency
        avg_batch_size = self.aggregated_metrics["average_batch_size"]
        if avg_batch_size < 5:
            score -= (5 - avg_batch_size) * 10
        
        # Check processing time efficiency
        avg_processing_time = self.aggregated_metrics["average_processing_time"]
        if avg_processing_time > 30:  # 30 seconds
            score -= (avg_processing_time - 30) * 2
        
        return max(0.0, min(100.0, score))
    
    def _get_alert_summary(self) -> Dict[str, int]:
        """Get summary of active alerts by level."""
        summary = {level.value: 0 for level in AlertLevel}
        for alert in self.active_alerts.values():
            summary[alert.level.value] += 1
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Cost recommendations
        if self.aggregated_metrics["average_batch_size"] < 5:
            recommendations.append("Consider increasing batch size for better cost efficiency")
        
        # Performance recommendations
        if self.aggregated_metrics["average_processing_time"] > 30:
            recommendations.append("Optimize prompt templates to reduce processing time")
        
        # Queue recommendations
        queue_util = self.real_time_metrics["queue_utilization"]
        if queue_util > 0.8:
            recommendations.append("Scale up batch processing capacity or optimize queue management")
        
        return recommendations
    
    def _start_monitoring(self):
        """Start background monitoring thread."""
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Cleanup old data
                    self._cleanup_old_data()
                    
                    # Update real-time metrics
                    self._update_real_time_metrics()
                    
                    time.sleep(60)  # Update every minute
                    
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(60)
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Background monitoring started")
    
    def _cleanup_old_data(self):
        """Remove data older than retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        # Clean metrics history
        self.metrics_history = deque(
            (m for m in self.metrics_history if m.timestamp > cutoff_time),
            maxlen=10000
        )
        
        # Clean cost history
        self.cost_history = deque(
            (c for c in self.cost_history if c["timestamp"] > cutoff_time),
            maxlen=1000
        )
        
        # Clean performance history
        self.performance_history = deque(
            (p for p in self.performance_history if p["timestamp"] > cutoff_time),
            maxlen=1000
        )
        
        # Clean queue history
        self.queue_history = deque(
            (q for q in self.queue_history if q["timestamp"] > cutoff_time),
            maxlen=1000
        )
        
        # Clean old alerts
        self.alert_history = deque(
            (a for a in self.alert_history if a.timestamp > cutoff_time),
            maxlen=1000
        )
    
    def _update_real_time_metrics(self):
        """Update real-time metrics calculations."""
        if len(self.metrics_history) > 0:
            recent_metrics = list(self.metrics_history)[-10:]
            
            # Calculate requests per second
            if len(recent_metrics) >= 2:
                time_diff = (recent_metrics[-1].timestamp - recent_metrics[0].timestamp).total_seconds()
                if time_diff > 0:
                    total_requests = sum(m.batch_size for m in recent_metrics)
                    self.real_time_metrics["requests_per_second"] = total_requests / time_diff

# Global monitor instance
_monitor_service_instance: Optional[BatchMonitorService] = None

def get_batch_monitor_service(**kwargs) -> BatchMonitorService:
    """
    Get or create singleton BatchMonitorService instance.
    
    Args:
        **kwargs: Arguments to pass to BatchMonitorService constructor
    
    Returns:
        BatchMonitorService instance
    
    Example:
        >>> monitor = get_batch_monitor_service(retention_hours=48)
        >>> monitor.track_batch_processing(batch_result)
    """
    global _monitor_service_instance
    
    if _monitor_service_instance is None:
        logger.info("Creating new BatchMonitorService singleton instance")
        _monitor_service_instance = BatchMonitorService(**kwargs)
    
    return _monitor_service_instance

# Module initialization
logger.info("Batch monitor service module loaded")
logger.info(f"Default retention: {DEFAULT_METRICS_RETENTION_HOURS} hours")
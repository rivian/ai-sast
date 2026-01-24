"""
Core modules for AI-SAST security scanner
"""

from .scanner import SecurityScanner
from .vertex import VertexAIClient
from .report import HTMLReportGenerator
from .config import PROJECT_ID, LOCATION

# Optional integrations
try:
    from ..integrations.jira import JiraClient
except ImportError:
    JiraClient = None

try:
    from ..integrations.databricks import DatabricksClient
except ImportError:
    DatabricksClient = None

try:
    from ..integrations.vector import VectorClient, log_security_event
except ImportError:
    VectorClient = None
    log_security_event = None

try:
    from ..integrations.notifications import WebhookClient as NotificationClient
except ImportError:
    NotificationClient = None

__all__ = [
    'SecurityScanner',
    'VertexAIClient', 
    'HTMLReportGenerator',
    'PROJECT_ID',
    'LOCATION',
    'JiraClient',
    'DatabricksClient',
    'VectorClient',
    'log_security_event',
    'NotificationClient'
]


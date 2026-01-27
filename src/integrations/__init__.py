"""
Optional integrations for AI-SAST

This package contains optional integrations with external systems:
- Feedback: Local SQLite database (default) or Databricks (enterprise) for historical feedback
- Jira: Fetch vulnerability context from Jira tickets
- Databricks: Store and retrieve historical feedback (enterprise option)
- Vector: Log security events to vector/log aggregation systems
- Notifications: Send notifications to Slack, Teams, Discord, or custom webhooks

All integrations are optional and only loaded if configured.
Built-in SQLite feedback system requires no configuration.
"""

__all__ = ['get_feedback_client', 'ScanDatabase', 'JiraClient', 'DatabricksClient', 'VectorClient', 'NotificationClient']

# Feedback system (always available - SQLite is built-in)
try:
    from .feedback import get_feedback_client
    from .scan_database import ScanDatabase
except ImportError:
    get_feedback_client = None
    ScanDatabase = None

# Optional imports - only available if configured
try:
    from .jira import JiraClient
except ImportError:
    JiraClient = None

try:
    from .databricks import DatabricksClient
except ImportError:
    DatabricksClient = None

try:
    from .vector import VectorClient, send_security_event
except ImportError:
    VectorClient = None
    send_security_event = None

try:
    from .notifications import WebhookClient as NotificationClient
except ImportError:
    NotificationClient = None


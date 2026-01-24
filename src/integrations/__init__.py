"""
Optional integrations for AI-SAST

This package contains optional integrations with external systems:
- Jira: Fetch vulnerability context from Jira tickets
- Databricks: Store and retrieve historical feedback
- Vector: Log security events to vector/log aggregation systems
- Notifications: Send notifications to Slack, Teams, Discord, or custom webhooks

All integrations are optional and only loaded if configured.
"""

__all__ = ['JiraClient', 'DatabricksClient', 'VectorClient', 'NotificationClient']

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
    from .vector import VectorClient, log_security_event
except ImportError:
    VectorClient = None
    log_security_event = None

try:
    from .notifications import WebhookClient as NotificationClient
except ImportError:
    NotificationClient = None


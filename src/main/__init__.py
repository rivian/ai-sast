"""
Main scanning modules for CI/CD integration
"""

from .full_scan import main as full_scan
from .pr_scan import main as pr_scan

__all__ = ['full_scan', 'pr_scan']


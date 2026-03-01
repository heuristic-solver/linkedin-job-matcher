"""
Matching module for job matching and analytics
"""
from .analytics import (
    calculate_resume_strength_score,
    analyze_skills_gap,
    extract_key_metrics
)

__all__ = [
    'calculate_resume_strength_score',
    'analyze_skills_gap',
    'extract_key_metrics'
]


"""
Market Intelligence Module
Provides job market insights and trends
"""
from typing import Dict, List
import random
from datetime import datetime, timedelta

def get_salary_insights(job_title: str, location: str, experience_level: str = "mid") -> Dict:
    """
    Get salary insights for a job role
    Note: In production, this would connect to real salary APIs
    """
    # Base salary ranges by role type (simplified - would use real data in production)
    base_salaries = {
        'ai engineer': {'entry': (60000, 90000), 'mid': (90000, 130000), 'senior': (130000, 180000)},
        'data scientist': {'entry': (65000, 95000), 'mid': (95000, 140000), 'senior': (140000, 190000)},
        'software engineer': {'entry': (55000, 85000), 'mid': (85000, 120000), 'senior': (120000, 170000)},
        'machine learning': {'entry': (70000, 100000), 'mid': (100000, 150000), 'senior': (150000, 200000)},
        'data analyst': {'entry': (50000, 75000), 'mid': (75000, 110000), 'senior': (110000, 150000)},
    }
    
    job_lower = job_title.lower()
    role_type = 'software engineer'  # default
    
    for role, _ in base_salaries.items():
        if role in job_lower:
            role_type = role
            break
    
    salary_range = base_salaries.get(role_type, base_salaries['software engineer']).get(
        experience_level.lower(), base_salaries['software engineer']['mid']
    )
    
    # Location adjustments (simplified)
    location_multipliers = {
        'san francisco': 1.4,
        'new york': 1.3,
        'seattle': 1.2,
        'boston': 1.15,
        'london': 1.1,
        'mumbai': 0.3,
        'bangalore': 0.3,
        'delhi': 0.3,
        'india': 0.3,
        'hyderabad': 0.3,
    }
    
    location_lower = location.lower()
    multiplier = 1.0
    for loc, mult in location_multipliers.items():
        if loc in location_lower:
            multiplier = mult
            break
    
    adjusted_min = int(salary_range[0] * multiplier)
    adjusted_max = int(salary_range[1] * multiplier)
    
    return {
        'role': role_type,
        'location': location,
        'experience_level': experience_level,
        'salary_range': {
            'min': adjusted_min,
            'max': adjusted_max,
            'currency': 'USD' if multiplier >= 0.8 else 'INR' if multiplier <= 0.4 else 'USD'
        },
        'market_average': int((adjusted_min + adjusted_max) / 2),
        'insights': [
            f"Average salary range for {job_title} in {location}",
            f"Expected range: {adjusted_min:,} - {adjusted_max:,} per year",
            "Salaries vary based on company size, industry, and specific skills"
        ]
    }


def get_market_demand_trends(job_title: str, skills: List[str]) -> Dict:
    """
    Get market demand trends for skills and roles
    """
    # High demand skills (would be from real-time data in production)
    high_demand_skills = [
        'python', 'machine learning', 'artificial intelligence', 'cloud computing',
        'aws', 'docker', 'kubernetes', 'react', 'javascript', 'data science',
        'tensorflow', 'pytorch', 'sql', 'api development', 'microservices'
    ]
    
    # Growing skills
    growing_skills = [
        'generative ai', 'llm', 'langchain', 'openai', 'mlops', 'data engineering',
        'devops', 'terraform', 'graphql', 'typescript', 'vue.js'
    ]
    
    # Declining skills (relatively)
    stable_skills = [
        'jquery', 'php', 'perl', 'visual basic', 'cobol'
    ]
    
    job_lower = job_title.lower()
    skills_lower = [s.lower() for s in skills]
    
    # Analyze skills
    skills_analysis = []
    high_demand_count = 0
    growing_count = 0
    
    for skill in skills_lower:
        if any(hd in skill for hd in high_demand_skills):
            skills_analysis.append({
                'skill': skill,
                'demand': 'high',
                'trend': 'stable'
            })
            high_demand_count += 1
        elif any(gs in skill for gs in growing_skills):
            skills_analysis.append({
                'skill': skill,
                'demand': 'high',
                'trend': 'growing'
            })
            growing_count += 1
        else:
            skills_analysis.append({
                'skill': skill,
                'demand': 'medium',
                'trend': 'stable'
            })
    
    # Overall market demand for the role
    if any(term in job_lower for term in ['ai', 'machine learning', 'data science', 'ml engineer']):
        role_demand = 'very_high'
        demand_score = 95
        trend = 'growing'
    elif any(term in job_lower for term in ['software engineer', 'developer', 'full stack']):
        role_demand = 'high'
        demand_score = 85
        trend = 'stable'
    else:
        role_demand = 'medium'
        demand_score = 70
        trend = 'stable'
    
    recommendations = []
    if high_demand_count == 0:
        recommendations.append("Consider learning high-demand skills like Python, ML, or Cloud technologies")
    elif high_demand_count < 3:
        recommendations.append(f"You have {high_demand_count} high-demand skills - consider adding more")
    else:
        recommendations.append("Great! You have strong high-demand skills in your profile")
    
    if growing_count > 0:
        recommendations.append(f"You have {growing_count} growing/emerging skills - excellent for future-proofing")
    
    return {
        'role_demand': role_demand,
        'demand_score': demand_score,
        'trend': trend,
        'skills_analysis': skills_analysis[:10],  # Limit to top 10
        'high_demand_skills_count': high_demand_count,
        'growing_skills_count': growing_count,
        'recommendations': recommendations,
        'market_insights': [
            f"Overall demand for {job_title} roles: {role_demand.replace('_', ' ').title()}",
            f"Market trend: {trend.title()}",
            f"Your profile has {high_demand_count} high-demand skills"
        ]
    }


def get_competition_analysis(job_title: str, location: str) -> Dict:
    """
    Estimate competition level for job applications
    """
    # Competition levels (would use real data in production)
    competition_levels = {
        'entry': {'low': (1, 50), 'medium': (50, 200), 'high': (200, 500), 'very_high': (500, 1000)},
        'mid': {'low': (1, 30), 'medium': (30, 100), 'high': (100, 300), 'very_high': (300, 800)},
        'senior': {'low': (1, 20), 'medium': (20, 80), 'high': (80, 200), 'very_high': (200, 500)}
    }
    
    # Estimate based on role and location
    job_lower = job_title.lower()
    
    # High competition roles
    if any(term in job_lower for term in ['data scientist', 'ai engineer', 'ml engineer']):
        base_competition = 'high'
        applicants_range = random.randint(150, 400)
    elif any(term in job_lower for term in ['software engineer', 'developer']):
        base_competition = 'medium'
        applicants_range = random.randint(80, 200)
    else:
        base_competition = 'medium'
        applicants_range = random.randint(50, 150)
    
    # Location adjustments
    location_lower = location.lower()
    if any(city in location_lower for city in ['san francisco', 'new york', 'seattle', 'london']):
        applicants_range = int(applicants_range * 1.5)
        base_competition = 'high' if applicants_range > 200 else 'medium'
    elif 'remote' in location_lower:
        applicants_range = int(applicants_range * 2.0)
        base_competition = 'very_high' if applicants_range > 300 else 'high'
    
    if applicants_range > 300:
        competition_level = 'very_high'
    elif applicants_range > 150:
        competition_level = 'high'
    elif applicants_range > 50:
        competition_level = 'medium'
    else:
        competition_level = 'low'
    
    tips = []
    if competition_level == 'very_high':
        tips.extend([
            "Competition is very high - ensure your resume is perfectly tailored",
            "Consider reaching out to employees for referrals",
            "Highlight unique projects or achievements",
            "Apply early - many roles get hundreds of applicants"
        ])
    elif competition_level == 'high':
        tips.extend([
            "Competition is high - make your application stand out",
            "Customize your resume for each application",
            "Write a compelling cover letter",
            "Network with people in the company"
        ])
    else:
        tips.extend([
            "Moderate competition level",
            "Focus on showcasing your relevant skills",
            "Prepare well for interviews"
        ])
    
    return {
        'competition_level': competition_level,
        'estimated_applicants': f"{applicants_range - 20}-{applicants_range + 50}",
        'applicants_range': applicants_range,
        'tips': tips,
        'insights': [
            f"Estimated competition for {job_title} in {location}: {competition_level.replace('_', ' ').title()}",
            f"Typically receives {applicants_range - 20}-{applicants_range + 50} applicants per posting",
            "Standing out requires a strong, tailored application"
        ]
    }


def get_industry_insights(job_title: str) -> Dict:
    """
    Get industry insights and growth projections
    """
    job_lower = job_title.lower()
    
    insights_map = {
        'ai': {
            'industry': 'Artificial Intelligence',
            'growth_rate': 'High (25-30% annually)',
            'trending_skills': ['LLM', 'Generative AI', 'MLOps', 'Deep Learning', 'NLP'],
            'outlook': 'Very Positive - AI is one of the fastest-growing tech sectors',
            'key_companies': ['OpenAI', 'Google', 'Microsoft', 'Meta', 'Anthropic']
        },
        'machine learning': {
            'industry': 'Machine Learning',
            'growth_rate': 'High (20-25% annually)',
            'trending_skills': ['TensorFlow', 'PyTorch', 'MLOps', 'ML Engineering'],
            'outlook': 'Very Positive - High demand across all industries',
            'key_companies': ['Google', 'Amazon', 'Microsoft', 'Apple', 'Netflix']
        },
        'data science': {
            'industry': 'Data Science',
            'growth_rate': 'High (15-20% annually)',
            'trending_skills': ['Python', 'SQL', 'Statistics', 'Data Visualization', 'Cloud'],
            'outlook': 'Positive - Growing demand for data-driven insights',
            'key_companies': ['Amazon', 'Google', 'Microsoft', 'IBM', 'Salesforce']
        },
        'software engineer': {
            'industry': 'Software Development',
            'growth_rate': 'Steady (10-15% annually)',
            'trending_skills': ['Cloud Computing', 'DevOps', 'Microservices', 'React', 'Node.js'],
            'outlook': 'Stable - Consistent demand with evolving technologies',
            'key_companies': ['Google', 'Microsoft', 'Amazon', 'Meta', 'Apple']
        }
    }
    
    # Match job title to industry
    industry_info = insights_map.get('software engineer')  # default
    for key, info in insights_map.items():
        if key in job_lower:
            industry_info = info
            break
    
    return {
        'industry': industry_info['industry'],
        'growth_rate': industry_info['growth_rate'],
        'trending_skills': industry_info['trending_skills'],
        'outlook': industry_info['outlook'],
        'key_companies': industry_info['key_companies'],
        'recommendations': [
            f"Focus on trending skills: {', '.join(industry_info['trending_skills'][:3])}",
            f"Industry growth: {industry_info['growth_rate']}",
            f"Outlook: {industry_info['outlook']}"
        ]
    }


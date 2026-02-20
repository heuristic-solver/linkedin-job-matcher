"""
Lightweight smoke checks for resume parsing + ATS scoring.
Run: python -m tests.resume_parsing_smoke
"""
from extraction.structured_extractor import StructuredResumeExtractor
from matching.analytics import calculate_resume_strength_score


def run_case(name: str, resume_text: str, expect_min_years: float, expected_skills: list, expect_education: bool):
    extractor = StructuredResumeExtractor()
    parsed = extractor.extract_all(resume_text)
    ats = calculate_resume_strength_score(parsed)

    missing_expected = [s for s in expected_skills if not any(s.lower() in ps.lower() for ps in parsed.get("skills", []))]
    years = parsed.get("experience", [])
    total_years = sum(exp.get("years", 0) for exp in years if isinstance(exp, dict))

    assert total_years >= expect_min_years, f"{name}: expected at least {expect_min_years} years, got {total_years}"
    assert not missing_expected, f"{name}: missing expected skills {missing_expected}; got {parsed.get('skills')}"
    if expect_education:
        assert parsed.get("education"), f"{name}: expected education entries"

    print(f"[PASS] {name}: skills={len(parsed.get('skills', []))}, yrs={total_years}, ats_overall={ats['scores']['overall']}")


def main():
    cases = [
        {
            "name": "Chronological_MMYYYY",
            "text": """
John Doe
Email: john@example.com | Phone: 555-123-4567

SKILLS
Python, SQL, Flask, AWS, Docker

EXPERIENCE
Software Engineer, Acme Corp
02/2019 - 07/2023
Built APIs with Flask and deployed to AWS using Docker.

Senior Engineer at Beta Systems
08/2023 - Present
Leading a team building Python services.

EDUCATION
B.Tech in Computer Science, Example University, 2018
            """,
            "expect_min_years": 4.0,
            "expected_skills": ["Python", "AWS", "SQL"],
            "expect_education": True,
        },
        {
            "name": "Uppercase_Headings_NoColon",
            "text": """
JANE SMITH
Email jane.smith@example.com | Phone +1 222-333-4444

TECHNICAL SKILLS
JavaScript • ReactJS • NodeJS • PostgreSQL • GCP

PROFESSIONAL EXPERIENCE
Full Stack Developer @ StartUp XYZ
March 2020 – Current
- Built React frontends and Node APIs
- Deployed services on GCP with PostgreSQL

Bachelor of Engineering in Information Technology
State University 2019
            """,
            "expect_min_years": 3.0,
            "expected_skills": ["JavaScript", "React", "Node.js", "PostgreSQL"],
            "expect_education": True,
        },
        {
            "name": "ShortYear_and_Bullets",
            "text": """
ALAN T.

Skills: Go; Kubernetes; Terraform; CI/CD; Linux

Experience:
DevOps Engineer - CloudCo
Feb'20 - Present
Managed Kubernetes clusters and automated infra with Terraform.

Education
MCA, Tech Institute, 2020
            """,
            "expect_min_years": 4.0,
            "expected_skills": ["Go", "Kubernetes", "Terraform"],
            "expect_education": True,
        },
    ]

    for case in cases:
        run_case(
            name=case["name"],
            resume_text=case["text"],
            expect_min_years=case["expect_min_years"],
            expected_skills=case["expected_skills"],
            expect_education=case["expect_education"],
        )


if __name__ == "__main__":
    main()


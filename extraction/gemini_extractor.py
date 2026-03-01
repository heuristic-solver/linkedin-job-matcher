
import os
import json
import re
import requests

class GeminiResumeExtractor:
    """
    Resume extractor using Google Gemini API.
    Uses the REST API directly so it works with either google-generativeai or google.genai.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Use the Gemini 2.0 Flash model - fast and cheap
        self.model = "gemini-2.0-flash"
        self.api_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

    def _clean_text(self, text: str) -> str:
        """Clean common PDF encoding artifacts before passing to LLM."""
        # Replace known mangled chars
        replacements = {
            '\xfb': '-', 'û': '-', 'Æ': "'", 'Ö': '-', '§': '-',
            '\x96': '-', '\x97': '-',  # en/em dashes
            '\x91': "'", '\x92': "'",  # smart quotes
            '\x93': '"', '\x94': '"',  # smart double quotes
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text

    def extract_all(self, text: str) -> dict:
        """Send resume text to Gemini and get structured JSON back."""
        text = self._clean_text(text)

        prompt = f"""
You are a precise resume parser. Analyze the resume text below and extract structured information.

Return ONLY a valid JSON object with this exact structure (no extra text, no markdown, no code blocks):
{{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "Phone Number",
    "summary": "Professional summary/bio sentence(s)",
    "skills": ["Skill1", "Skill2", "Skill3"],
    "education": [
        {{
            "degree": "Full degree name e.g. Bachelor of Technology",
            "institution": "Full university/college name",
            "field": "Major or specialization",
            "year": "Year or date range e.g. 2022 - 2026",
            "gpa": "GPA if stated"
        }}
    ],
    "experience": [
        {{
            "role": "Job Title",
            "company": "Company Name",
            "location": "City, Country or null",
            "duration": "Month Year - Month Year e.g. December 2025 - January 2026",
            "years": 0.5
        }}
    ]
}}

Rules:
- Extract ALL skills explicitly mentioned (languages, frameworks, tools, platforms, certifications)
- Extract ALL experience entries (internships count as experience)
- If a field is missing, use null or empty string - do not fabricate data
- For "years" in experience: calculate the float value of the duration (e.g. 2 months = 0.17)

Resume Text:
\"\"\"
{text}
\"\"\"
"""

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json"
            }
        }

        try:
            print(f"[Gemini] Analyzing resume with {self.model}...")
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            candidates = result.get("candidates", [])
            if not candidates:
                print("[Gemini] No candidates in response.")
                return {}
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                print("[Gemini] No parts in response content.")
                return {}
            
            raw_text = parts[0].get("text", "")
            
            # Try to strip any accidental markdown fences
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_text, re.DOTALL)
            if json_match:
                raw_text = json_match.group(1)
            
            extracted = json.loads(raw_text.strip())
            print(f"[Gemini] Extraction successful: {len(extracted.get('skills', []))} skills, "
                  f"{len(extracted.get('experience', []))} experience entries.")
            return extracted

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print("[Gemini] Rate limit / quota exceeded. Falling back.")
            elif response.status_code == 400:
                print(f"[Gemini] Bad request: {response.text[:300]}")
            else:
                print(f"[Gemini] HTTP error {response.status_code}: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"[Gemini] JSON parse error: {e}. Raw: {raw_text[:300]}")
            return {}
        except Exception as e:
            print(f"[Gemini] Error: {e}")
            return {}


import requests
import json
import re
from typing import Dict, List

import os

class OllamaResumeExtractor:
    def __init__(self, model: str = None):
        self.model = model or os.getenv('OLLAMA_MODEL', "gemma3:12b")
        self.api_url = os.getenv('OLLAMA_API_URL', "http://localhost:11434/api/generate")

    def extract_all(self, text: str) -> Dict:
        # Clean text of common PDF mangled characters
        text = text.replace('û', '-').replace('Æ', "'").replace('Ö', '-').replace('§', '-')
        
        prompt = f"""
        Analyze and extract structured information from the following resume text. 
        Mangled characters like 'û' often represent dashes or bullets.
        
        Return ONLY a JSON object with the following structure:
        {{
            "name": "Full Name",
            "email": "email@example.com",
            "phone": "Phone Number",
            "summary": "Professional summary or bio",
            "skills": ["Skill 1", "Skill 2"],
            "education": [
                {{
                    "degree": "Full degree name",
                    "institution": "Full university/college name",
                    "field": "Major or field of study",
                    "year": "Graduation year or date range",
                    "gpa": "GPA value"
                }}
            ],
            "experience": [
                {{
                    "role": "Job Title",
                    "company": "Company Name",
                    "location": "Job Location",
                    "duration": "Start Date - End Date",
                    "years": duration_in_years_as_float
                }}
            ]
        }}

        Resume Text:
        \"\"\"
        {text}
        \"\"\"
        """

        try:
            print(f"[Ollama] Analyzing resume with {self.model} (this may take a minute)...")
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 2048
                    }
                },
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "{}")
            
            # Extract JSON if it's wrapped in markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            extracted_data = json.loads(response_text)
            print(f"[Ollama] Extraction successful.")
            return extracted_data
        except Exception as e:
            print(f"[Ollama] Error: {e}")
            return {}

if __name__ == "__main__":
    # Test with sample text
    extractor = OllamaResumeExtractor()
    sample_text = "Joel Alex John | +91-8089232301 | Christ University Bengaluru | B.Tech in AI & ML | GPA 9.3"
    print(json.dumps(extractor.extract_all(sample_text), indent=2))

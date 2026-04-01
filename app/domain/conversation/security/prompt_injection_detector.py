import re
from typing import Dict, List

class PromptInjectionDetector:
    def __init__(self):
        self.patterns = [
            {
                "name": "ignore_instructions",
                "pattern": re.compile(r"(ignore|disregard|forget|bypass|override)\s+(all|previous|given)\s+instructions", re.IGNORECASE),
                "risk": 90
            },
            {
                "name": "role_play",
                "pattern": re.compile(r"pretend\s+to\s+be|act\s+as|you\s+are\s+now", re.IGNORECASE),
                "risk": 70
            },
            {
                "name": "jailbreak",
                "pattern": re.compile(r"jailbreak|escape|break\s+free|override\s+security", re.IGNORECASE),
                "risk": 100
            },
            {
                "name": "system_prompt",
                "pattern": re.compile(r"system\s*:|system\s*prompt", re.IGNORECASE),
                "risk": 80
            }
        ]

    def detect(self, text: str) -> int:
        max_risk = 0
        for pattern_info in self.patterns:
            if pattern_info["pattern"].search(text):
                max_risk = max(max_risk, pattern_info["risk"])
        return max_risk

    def get_detected_patterns(self, text: str) -> List[str]:
        detected = []
        for pattern_info in self.patterns:
            if pattern_info["pattern"].search(text):
                detected.append(pattern_info["name"])
        return detected

    def is_high_risk(self, text: str) -> bool:
        return self.detect(text) > 80
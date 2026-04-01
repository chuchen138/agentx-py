import re
from typing import List

class SensitiveWordFilter:
    def __init__(self):
        self.sensitive_words = [
            "敏感词1",
            "敏感词2",
            "敏感词3"
        ]
        self.pattern = re.compile('|'.join(re.escape(word) for word in self.sensitive_words), re.IGNORECASE)

    def filter(self, text: str) -> str:
        return self.pattern.sub('***', text)

    def detect(self, text: str) -> bool:
        return bool(self.pattern.search(text))

    def get_filtered_words(self, text: str) -> List[str]:
        matches = self.pattern.findall(text)
        return list(set(matches))
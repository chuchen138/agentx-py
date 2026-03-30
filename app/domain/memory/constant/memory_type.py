from enum import Enum

class MemoryType(Enum):
    PROFILE = "PROFILE"
    TASK = "TASK"
    FACT = "FACT"
    EPISODIC = "EPISODIC"
    
    @classmethod
    def fromCode(cls, code):
        for type_enum in cls:
            if type_enum.value == code:
                return type_enum
        raise ValueError(f"Unknown memory type: {code}")
    
    def getCode(self):
        return self.value
    
    def getDescription(self):
        descriptions = {
            self.PROFILE: "用户偏好，稳定的偏好、人格特质或固定的格式要求",
            self.TASK: "目标任务，明确的中长期目标或持续性计划",
            self.FACT: "稳定事实，与用户身份或工作环境相关的稳定不变的事实",
            self.EPISODIC: "情景信息，未来3-5轮交互内明显有帮助的情节性信息"
        }
        return descriptions[self]

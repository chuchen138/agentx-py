from enum import Enum
from typing import Dict, List

class AuditStatus(Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

# 状态转换规则
STATUS_TRANSITIONS: Dict[AuditStatus, List[AuditStatus]] = {
    AuditStatus.PENDING: [AuditStatus.IN_REVIEW, AuditStatus.CANCELLED],
    AuditStatus.IN_REVIEW: [AuditStatus.APPROVED, AuditStatus.REJECTED],
    AuditStatus.APPROVED: [],  # 已批准状态不能再转换
    AuditStatus.REJECTED: [],  # 已拒绝状态不能再转换
    AuditStatus.CANCELLED: [],  # 已取消状态不能再转换
}

# 状态流转记录
def validate_status_transition(current_status: AuditStatus, new_status: AuditStatus) -> bool:
    """
    验证状态转换是否合法
    """
    if current_status not in STATUS_TRANSITIONS:
        return False
    return new_status in STATUS_TRANSITIONS[current_status]

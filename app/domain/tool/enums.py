from enum import Enum


class ToolType(Enum):
    MCP = "MCP"


class UploadType(Enum):
    GITHUB = "GITHUB"
    ZIP = "ZIP"


class ToolStatus(Enum):
    WAITING_REVIEW = "WAITING_REVIEW"
    FETCHING_TOOLS = "FETCHING_TOOLS"
    GITHUB_URL_VALIDATION = "GITHUB_URL_VALIDATION"
    DEPLOYING = "DEPLOYING"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"


class ToolVersionStatus(Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
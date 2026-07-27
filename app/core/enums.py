from enum import StrEnum


class ResumeStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PARSED_UNCONFIRMED = "PARSED_UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    SUPERSEDED = "SUPERSEDED"
    FAILED = "FAILED"


class SourceType(StrEnum):
    PDF = "pdf"
    TEXT = "text"
    LATEX = "latex"


class ExtractionMethod(StrEnum):
    PDF_TEXT = "pdf_text"
    PLAIN_TEXT = "plain_text"
    LATEX_STATIC = "latex_static"


class BlockType(StrEnum):
    HEADING = "heading"
    ENTRY_HEADER = "entry_header"
    PARAGRAPH = "paragraph"
    BULLET = "bullet"
    CONTACT = "contact"
    UNKNOWN = "unknown"


class ClaimType(StrEnum):
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    ALGORITHM = "algorithm"
    PERFORMANCE = "performance"
    RESEARCH = "research"
    LEADERSHIP = "leadership"
    RESULT = "result"
    SKILL = "skill"


class ExpectedLevel(StrEnum):
    KNOW = "know"
    USE = "use"
    IMPLEMENT = "implement"
    DESIGN = "design"
    PRODUCTION = "production"


class VerificationCategory(StrEnum):
    BACKGROUND = "background"
    IMPLEMENTATION = "implementation"
    DATA_STRUCTURE = "data_structure"
    PRINCIPLE = "principle"
    DEBUGGING = "debugging"
    TRADEOFF = "tradeoff"
    PRODUCTION = "production"
    PERSONAL_CONTRIBUTION = "personal_contribution"
    RESULT = "result"


class InterviewMode(StrEnum):
    SIMULATION = "simulation"
    PRACTICE = "practice"
    ASSESSMENT = "assessment"


class ClaimStatusEnum(StrEnum):
    UNTOUCHED = "UNTOUCHED"
    IN_PROGRESS = "IN_PROGRESS"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    VERIFIED = "VERIFIED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTORY = "CONTRADICTORY"
    SKIPPED = "SKIPPED"


class NextAction(StrEnum):
    FOLLOW_UP = "follow_up"
    CLARIFY = "clarify"
    INCREASE_DIFFICULTY = "increase_difficulty"
    SWITCH_CLAIM = "switch_claim"
    SWITCH_TOPIC = "switch_topic"
    COACHING = "coaching"
    FINISH = "finish"

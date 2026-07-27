import uuid


def new_id(prefix: str = "") -> str:
    """Generate a short unique ID with optional prefix."""
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}_{uid}" if prefix else uid


def new_resume_id() -> str:
    return new_id("res")


def new_revision_id() -> str:
    return new_id("rev")


def new_claim_id() -> str:
    return new_id("clm")


def new_interview_id() -> str:
    return new_id("int")


def new_question_id() -> str:
    return new_id("q")


def new_answer_id() -> str:
    return new_id("ans")


def new_evidence_id() -> str:
    return new_id("ev")


def new_thread_id() -> str:
    return uuid.uuid4().hex

class AppError(Exception):
    """Base application error."""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ResumeError(AppError):
    pass


class ParseError(AppError):
    pass


class InterviewError(AppError):
    pass


class LLMError(AppError):
    def __init__(self, code: str, message: str, status_code: int = 502):
        super().__init__(code, message, status_code)


class PermissionDeniedError(AppError):
    """Raised when user lacks permission to access a resource (M2.6)."""
    def __init__(self, message: str = "Permission denied"):
        super().__init__("PERMISSION_DENIED", message, status_code=403)


# Error codes
RESUME_EMPTY = "RESUME_EMPTY"
RESUME_TOO_LARGE = "RESUME_TOO_LARGE"
RESUME_UNSUPPORTED_TYPE = "RESUME_UNSUPPORTED_TYPE"
RESUME_TYPE_MISMATCH = "RESUME_TYPE_MISMATCH"
PDF_ENCRYPTED = "PDF_ENCRYPTED"
PDF_NO_TEXT = "PDF_NO_TEXT"
PDF_TOO_MANY_PAGES = "PDF_TOO_MANY_PAGES"
TEXT_ENCODING_FAILED = "TEXT_ENCODING_FAILED"
LATEX_MULTI_FILE_NOT_SUPPORTED = "LATEX_MULTI_FILE_NOT_SUPPORTED"
LATEX_PARSE_FAILED = "LATEX_PARSE_FAILED"
PARSE_QUALITY_TOO_LOW = "PARSE_QUALITY_TOO_LOW"

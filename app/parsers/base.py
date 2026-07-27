from abc import ABC, abstractmethod
from app.parsers.schemas import ParseInput, ResumeDocument


class ResumeParser(ABC):
    @abstractmethod
    async def parse(self, parse_input: ParseInput) -> ResumeDocument:
        raise NotImplementedError

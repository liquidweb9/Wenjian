"""Answer diff and retry analysis.

M2.5: Detects differences between answer versions and distinguishes new evidence from coaching repetition.
"""

import hashlib
from typing import Any


class AnswerDiffer:
    """Analyze differences between answer versions."""

    def compute_diff(
        self,
        original_text: str,
        revised_text: str,
    ) -> dict[str, Any]:
        """Compute difference between two answer versions.

        Args:
            original_text: Original answer text
            revised_text: Revised answer text

        Returns:
            Diff summary with token changes, evidence detection, coaching flags
        """
        # Tokenize (simple word-based)
        original_tokens = set(self._tokenize(original_text))
        revised_tokens = set(self._tokenize(revised_text))

        # Calculate token changes
        added_tokens = revised_tokens - original_tokens
        removed_tokens = original_tokens - revised_tokens
        common_tokens = original_tokens & revised_tokens

        # Token counts
        total_original = len(original_tokens)
        total_revised = len(revised_tokens)
        total_added = len(added_tokens)
        total_removed = len(removed_tokens)
        total_common = len(common_tokens)

        # Change metrics
        if total_original > 0:
            change_ratio = (total_added + total_removed) / (total_original + total_revised)
        else:
            change_ratio = 1.0

        # Detect new evidence indicators
        new_evidence_detected = self._detect_new_evidence(
            added_tokens=added_tokens,
            original_text=original_text,
            revised_text=revised_text,
        )

        # Detect coaching repetition (parroting feedback)
        coaching_repetition = self._detect_coaching_repetition(
            added_tokens=added_tokens,
            change_ratio=change_ratio,
        )

        # Determine if substantive change
        is_substantive = self._is_substantive_change(
            change_ratio=change_ratio,
            new_evidence_detected=new_evidence_detected,
            coaching_repetition=coaching_repetition,
        )

        return {
            "added_tokens": list(added_tokens)[:50],  # Limit for storage
            "removed_tokens": list(removed_tokens)[:50],
            "total_added": total_added,
            "total_removed": total_removed,
            "total_common": total_common,
            "change_ratio": round(change_ratio, 3),
            "new_evidence": new_evidence_detected,
            "coaching_repetition": coaching_repetition,
            "is_substantive_change": is_substantive,
            "original_hash": self._hash_text(original_text),
            "revised_hash": self._hash_text(revised_text),
        }

    def _tokenize(self, text: str) -> list[str]:
        """Simple word tokenization.

        Args:
            text: Input text

        Returns:
            List of tokens (lowercase words)
        """
        # Split on whitespace and common punctuation
        import re
        # Keep alphanumeric sequences (English/digits) and individual Chinese characters
        tokens = []

        # First split by whitespace and punctuation
        parts = re.findall(r'[a-zA-Z0-9]+|[一-鿿]', text.lower())

        return parts

    def _detect_new_evidence(
        self,
        added_tokens: set[str],
        original_text: str,
        revised_text: str,
    ) -> bool:
        """Detect if revision contains new evidence.

        New evidence indicators:
        - Numbers/metrics (QPS, latency, percentage, dates)
        - Technical terms not in original
        - Specific project details (names, technologies)

        Args:
            added_tokens: Tokens added in revision
            original_text: Original answer
            revised_text: Revised answer

        Returns:
            True if new evidence detected
        """
        # Evidence indicator 1: New numbers
        original_has_numbers = any(char.isdigit() for char in original_text)
        revised_has_numbers = any(char.isdigit() for char in revised_text)

        if revised_has_numbers and not original_has_numbers:
            return True

        # Evidence indicator 2: Technical keywords in added tokens
        technical_keywords = {
            "api", "database", "cache", "redis", "mysql", "kafka", "nginx",
            "docker", "kubernetes", "microservice", "架构", "设计", "实现",
            "优化", "部署", "监控", "日志", "异常", "性能", "并发", "分布式",
        }

        technical_additions = added_tokens & technical_keywords
        if len(technical_additions) >= 2:
            return True

        # Evidence indicator 3: Substantial length increase (>30%)
        len_increase = len(revised_text) - len(original_text)
        if len_increase > len(original_text) * 0.3:
            return True

        return False

    def _detect_coaching_repetition(
        self,
        added_tokens: set[str],
        change_ratio: float,
    ) -> bool:
        """Detect if revision just parrots coaching feedback.

        Coaching repetition indicators:
        - Minimal change (<15% change ratio)
        - Generic filler words added
        - No substantive new content

        Args:
            added_tokens: Tokens added in revision
            change_ratio: Ratio of changes to total tokens

        Returns:
            True if likely coaching repetition
        """
        # Low change ratio suggests minimal effort
        if change_ratio < 0.15:
            return True

        # Check for generic filler phrases (in Chinese or English)
        filler_phrases = {
            "具", "体", "来", "说", "也", "就", "是", "换", "句", "话",
            "总", "的", "简", "单", "我", "认", "为", "觉", "得", "想",
            "们", "这", "个", "那",
            "basically", "actually", "essentially", "generally", "specifically",
        }

        filler_count = len(added_tokens & filler_phrases)
        if filler_count >= 3 and len(added_tokens) < 20:
            return True

        return False

    def _is_substantive_change(
        self,
        change_ratio: float,
        new_evidence_detected: bool,
        coaching_repetition: bool,
    ) -> bool:
        """Determine if change is substantive.

        Args:
            change_ratio: Ratio of changes
            new_evidence_detected: Whether new evidence found
            coaching_repetition: Whether likely coaching repetition

        Returns:
            True if substantive change
        """
        # Substantive if new evidence OR significant rewrite
        if new_evidence_detected:
            return True

        # Not substantive if coaching repetition
        if coaching_repetition:
            return False

        # Substantive if significant changes (>20%)
        if change_ratio > 0.2:
            return True

        return False

    def _hash_text(self, text: str) -> str:
        """Generate SHA256 hash of text.

        Args:
            text: Input text

        Returns:
            Hex digest of SHA256 hash
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AnswerVersionManager:
    """Manage answer versions and retries."""

    def __init__(self) -> None:
        """Initialize version manager."""
        self.differ = AnswerDiffer()

    def create_version(
        self,
        answer_id: str,
        version_number: int,
        answer_text: str,
        previous_text: str | None = None,
    ) -> dict[str, Any]:
        """Create a new answer version record.

        Args:
            answer_id: Answer ID
            version_number: Version number (1, 2, 3...)
            answer_text: Current answer text
            previous_text: Previous version text (if exists)

        Returns:
            Version record dict
        """
        answer_hash = self.differ._hash_text(answer_text)

        # Compute diff if previous version exists
        if previous_text and version_number > 1:
            diff_summary = self.differ.compute_diff(
                original_text=previous_text,
                revised_text=answer_text,
            )
            is_substantive = diff_summary["is_substantive_change"]
        else:
            diff_summary = None
            is_substantive = True  # First version is always substantive

        return {
            "answer_id": answer_id,
            "version_number": version_number,
            "answer_text": answer_text,
            "answer_hash": answer_hash,
            "diff_summary": diff_summary,
            "is_substantive_change": is_substantive,
        }

    def should_suggest_switch_question(
        self,
        version_count: int,
        last_diff: dict[str, Any] | None,
    ) -> bool:
        """Determine if system should suggest switching questions.

        Suggest switching if:
        - User has retried 3+ times
        - Last retry was not substantive (coaching repetition)

        Args:
            version_count: Number of versions
            last_diff: Last diff summary

        Returns:
            True if should suggest switching
        """
        if version_count >= 3:
            if last_diff and not last_diff.get("is_substantive_change", True):
                return True

        return False

"""Tests for log sanitization.

M2.6: Tests PII masking and log safety.
"""

import pytest
from app.observability.sanitizer import (
    mask_email,
    mask_phone,
    mask_id_card,
    mask_credit_card,
    mask_chinese_name,
    sanitize_text,
    sanitize_dict,
    safe_log_dict,
    truncate_for_logging,
)


class TestEmailMasking:
    """Test email address masking."""

    def test_mask_single_email(self):
        """Test masking a single email."""
        text = "Contact me at user@example.com for details"
        result = mask_email(text)
        assert "user@example.com" not in result
        assert "u***@example.com" in result

    def test_mask_multiple_emails(self):
        """Test masking multiple emails."""
        text = "Email alice@company.com or bob@company.com"
        result = mask_email(text)
        assert "alice@company.com" not in result
        assert "bob@company.com" not in result
        assert "a***@company.com" in result
        assert "b***@company.com" in result

    def test_mask_email_with_numbers(self):
        """Test masking emails with numbers."""
        text = "Contact user123@test.org"
        result = mask_email(text)
        assert "user123@test.org" not in result
        assert "u***@test.org" in result

    def test_no_email_in_text(self):
        """Test text without emails."""
        text = "This text has no emails"
        result = mask_email(text)
        assert result == text


class TestPhoneMasking:
    """Test phone number masking."""

    def test_mask_phone_with_dashes(self):
        """Test masking phone with dashes."""
        text = "Call me at 123-456-7890"
        result = mask_phone(text)
        assert "123-456-7890" not in result
        assert "***-***-****" in result

    def test_mask_phone_with_spaces(self):
        """Test masking phone with spaces."""
        text = "Phone: 123 456 7890"
        result = mask_phone(text)
        assert "123 456 7890" not in result

    def test_mask_phone_with_country_code(self):
        """Test masking phone with country code."""
        text = "Mobile: +1 (123) 456-7890"
        result = mask_phone(text)
        assert "+1 (123) 456-7890" not in result

    def test_no_phone_in_text(self):
        """Test text without phone numbers."""
        text = "No phone numbers here"
        result = mask_phone(text)
        assert result == text


class TestIDCardMasking:
    """Test ID card masking."""

    def test_mask_chinese_id_card(self):
        """Test masking Chinese 18-digit ID."""
        text = "My ID is 110101199001011234"
        result = mask_id_card(text)
        assert "110101199001011234" not in result
        assert "**************1234" in result

    def test_mask_id_with_x(self):
        """Test masking ID ending with X."""
        text = "ID: 11010119900101123X"
        result = mask_id_card(text)
        assert "11010119900101123X" not in result
        assert "**************123X" in result

    def test_no_id_in_text(self):
        """Test text without ID cards."""
        text = "Random numbers 12345"
        result = mask_id_card(text)
        assert result == text


class TestCreditCardMasking:
    """Test credit card masking."""

    def test_mask_credit_card_with_spaces(self):
        """Test masking credit card with spaces."""
        text = "Card: 1234 5678 9012 3456"
        result = mask_credit_card(text)
        assert "1234 5678 9012 3456" not in result
        assert "3456" in result
        assert "1234" not in result

    def test_mask_credit_card_with_dashes(self):
        """Test masking credit card with dashes."""
        text = "Card: 1234-5678-9012-3456"
        result = mask_credit_card(text)
        assert "1234-5678-9012-3456" not in result
        assert "3456" in result

    def test_mask_credit_card_no_separators(self):
        """Test masking credit card without separators."""
        text = "Card: 1234567890123456"
        result = mask_credit_card(text)
        assert "1234567890123456" not in result
        assert "3456" in result


class TestChineseNameMasking:
    """Test Chinese name masking."""

    def test_mask_two_character_name(self):
        """Test masking 2-character Chinese name."""
        text = "张三是一名工程师"
        result = mask_chinese_name(text, "张三")
        assert "张三" not in result
        assert "张*" in result

    def test_mask_three_character_name(self):
        """Test masking 3-character Chinese name."""
        text = "李小明负责后端开发"
        result = mask_chinese_name(text, "李小明")
        assert "李小明" not in result
        assert "李**" in result

    def test_mask_four_character_name(self):
        """Test masking 4-character compound name."""
        text = "欧阳娜娜是歌手"
        result = mask_chinese_name(text, "欧阳娜娜")
        assert "欧阳娜娜" not in result
        assert "欧***" in result

    def test_mask_name_multiple_occurrences(self):
        """Test masking name that appears multiple times."""
        text = "张三和张三的朋友"
        result = mask_chinese_name(text, "张三")
        assert "张三" not in result
        assert result.count("张*") == 2

    def test_empty_name(self):
        """Test with empty name."""
        text = "Some text"
        result = mask_chinese_name(text, "")
        assert result == text

    def test_single_character_name(self):
        """Test with single character (should not mask)."""
        text = "王是姓氏"
        result = mask_chinese_name(text, "王")
        assert result == text  # Single char names not masked


class TestSanitizeText:
    """Test comprehensive text sanitization."""

    def test_sanitize_mixed_pii(self):
        """Test sanitizing text with multiple PII types."""
        text = "张三的邮箱是zhangsan@example.com，电话123-456-7890"
        result = sanitize_text(text, known_names=["张三"])

        # Name should be masked
        assert "张三" not in result
        assert "张*" in result

        # Email username should be masked (check that full username is gone)
        assert "zhangsan" not in result or "z***" in result

        # Domain should remain
        assert "@example.com" in result

        # Phone should be masked
        assert "123-456-7890" not in result

    def test_sanitize_with_no_pii(self):
        """Test sanitizing text with no PII."""
        text = "这是一段普通的技术描述，没有个人信息"
        result = sanitize_text(text)
        assert result == text

    def test_sanitize_empty_text(self):
        """Test sanitizing empty text."""
        result = sanitize_text("")
        assert result == ""

    def test_sanitize_none(self):
        """Test sanitizing None."""
        result = sanitize_text(None)
        assert result is None


class TestSanitizeDict:
    """Test dictionary sanitization."""

    def test_sanitize_sensitive_keys(self):
        """Test sanitizing dict with sensitive keys."""
        data = {
            "user_id": "123",
            "name": "张三",
            "email": "user@example.com",
            "phone": "123-456-7890",
            "score": 85,
        }

        result = sanitize_dict(data)

        assert result["user_id"] == "123"  # Not sensitive
        assert result["name"] == "***MASKED***"
        assert result["email"] == "***MASKED***"
        assert result["phone"] == "***MASKED***"
        assert result["score"] == 85  # Not sensitive

    def test_sanitize_nested_dict(self):
        """Test sanitizing nested dictionary."""
        data = {
            "interview_id": "int1",
            "user": {
                "name": "李四",
                "email": "lisi@example.com",
            },
            "score": 90,
        }

        result = sanitize_dict(data)

        assert result["interview_id"] == "int1"
        assert result["user"]["name"] == "***MASKED***"
        assert result["user"]["email"] == "***MASKED***"
        assert result["score"] == 90

    def test_sanitize_list_of_dicts(self):
        """Test sanitizing list containing dicts."""
        data = {
            "users": [
                {"name": "User1", "email": "u1@test.com"},
                {"name": "User2", "email": "u2@test.com"},
            ]
        }

        result = sanitize_dict(data)

        assert result["users"][0]["name"] == "***MASKED***"
        assert result["users"][1]["name"] == "***MASKED***"

    def test_sanitize_answer_text(self):
        """Test that answer_text is masked."""
        data = {
            "question_id": "q1",
            "answer_text": "我在阿里巴巴工作，负责分布式系统",
            "score": 85,
        }

        result = sanitize_dict(data)

        assert result["question_id"] == "q1"
        assert result["answer_text"] == "***MASKED***"
        assert result["score"] == 85

    def test_sanitize_raw_text(self):
        """Test that raw_text (resume content) is masked."""
        data = {
            "resume_id": "res1",
            "raw_text": "张三\n软件工程师\nemail: zhangsan@company.com",
            "quality": 0.9,
        }

        result = sanitize_dict(data)

        assert result["resume_id"] == "res1"
        assert result["raw_text"] == "***MASKED***"
        assert result["quality"] == 0.9

    def test_sanitize_custom_keys(self):
        """Test sanitization with custom sensitive keys."""
        data = {
            "public_data": "visible",
            "internal_secret": "should_mask",
        }

        result = sanitize_dict(data, sensitive_keys={"internal_secret"})

        assert result["public_data"] == "visible"
        assert result["internal_secret"] == "***MASKED***"

    def test_sanitize_numeric_sensitive_value(self):
        """Test that numeric sensitive values are zeroed."""
        data = {
            "salary": 100000,
            "bonus": 20000,
        }

        result = sanitize_dict(data, sensitive_keys={"salary", "bonus"})

        assert result["salary"] == 0
        assert result["bonus"] == 0


class TestSafeLogDict:
    """Test safe_log_dict convenience function."""

    def test_safe_log_dict_basic(self):
        """Test basic safe_log_dict usage."""
        data = {
            "action": "login",
            "user_id": "123",
            "email": "user@test.com",
        }

        result = safe_log_dict(data)

        assert result["action"] == "login"
        assert result["user_id"] == "123"
        assert result["email"] == "***MASKED***"


class TestTruncateForLogging:
    """Test truncation with sanitization."""

    def test_truncate_short_text(self):
        """Test truncating text shorter than max."""
        text = "Short text"
        result = truncate_for_logging(text, max_length=200)
        assert result == "Short text"

    def test_truncate_long_text(self):
        """Test truncating text longer than max."""
        text = "A" * 300
        result = truncate_for_logging(text, max_length=200)
        assert len(result) == 203  # 200 + "..."
        assert result.endswith("...")

    def test_truncate_with_pii(self):
        """Test truncating text with PII."""
        text = "Email: user@test.com. " + "A" * 300
        result = truncate_for_logging(text, max_length=50)

        assert "user@test.com" not in result
        assert len(result) <= 53  # 50 + "..."

    def test_truncate_exactly_max_length(self):
        """Test text exactly at max length."""
        text = "A" * 200
        result = truncate_for_logging(text, max_length=200)
        assert result == text
        assert not result.endswith("...")


class TestPIIPatternEdgeCases:
    """Test edge cases in PII pattern matching."""

    def test_email_without_tld(self):
        """Test that emails without proper TLD are not masked."""
        text = "user@localhost"
        result = mask_email(text)
        # localhost doesn't have TLD (.com, .org, etc), so not masked by pattern
        assert result == text

    def test_phone_with_extension(self):
        """Test phone number with extension."""
        text = "Call 123-456-7890 ext 123"
        result = mask_phone(text)
        assert "123-456-7890" not in result

    def test_partial_credit_card(self):
        """Test that partial card numbers are not masked."""
        text = "Last 4 digits: 1234"
        result = mask_credit_card(text)
        assert "1234" in result  # Too short, not masked

    def test_multiple_pii_types_in_sentence(self):
        """Test sentence with multiple PII types."""
        text = "张三 (zhangsan@company.com, 123-456-7890) 身份证: 110101199001011234"
        result = sanitize_text(text, known_names=["张三"])

        # All PII should be masked
        assert "张三" not in result
        assert "zhangsan@company.com" not in result
        assert "123-456-7890" not in result
        assert "110101199001011234" not in result

        # Domain should remain
        assert "@company.com" in result

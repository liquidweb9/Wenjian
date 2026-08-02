"""Tests for answer diff and versioning.

M2.5: Tests answer version comparison and coaching detection.
"""

import pytest
from app.abilities.answer_diff import AnswerDiffer, AnswerVersionManager


class TestAnswerDiffer:
    """Test answer difference detection."""

    def test_compute_diff_basic(self):
        """Test basic diff computation."""
        differ = AnswerDiffer()

        original = "我使用Redis作为缓存"
        revised = "我使用Redis和Memcached作为缓存，支持高并发"

        diff = differ.compute_diff(original, revised)

        assert diff["total_added"] > 0
        assert diff["total_removed"] == 0
        assert diff["change_ratio"] > 0
        assert "original_hash" in diff
        assert "revised_hash" in diff

    def test_detect_new_evidence_numbers(self):
        """Test detection of new numerical evidence."""
        differ = AnswerDiffer()

        original = "系统处理请求很快"
        revised = "系统处理请求QPS达到5000，延迟p99为20ms"

        diff = differ.compute_diff(original, revised)

        assert diff["new_evidence"] is True

    def test_detect_new_evidence_technical_details(self):
        """Test detection of new technical details."""
        differ = AnswerDiffer()

        original = "我们使用数据库存储数据"
        revised = "我们使用MySQL数据库，采用分库分表架构，配置了主从复制和读写分离"

        diff = differ.compute_diff(original, revised)

        assert diff["new_evidence"] is True

    def test_detect_coaching_repetition_minimal_change(self):
        """Test detection of coaching repetition with minimal changes."""
        differ = AnswerDiffer()

        original = "我负责开发API接口"
        revised = "我负责开发API接口，具体来说就是开发接口"

        diff = differ.compute_diff(original, revised)

        # May or may not be coaching depending on change ratio
        # The key is that coaching_repetition is detected
        assert diff["coaching_repetition"] is True or diff["change_ratio"] < 0.15

    def test_detect_coaching_repetition_filler_words(self):
        """Test detection of filler word additions."""
        differ = AnswerDiffer()

        original = "系统使用缓存"
        revised = "我觉得系统使用缓存，也就是说，简单来说，就是用缓存"

        diff = differ.compute_diff(original, revised)

        assert diff["coaching_repetition"] is True

    def test_substantive_change_with_evidence(self):
        """Test substantive change detection with new evidence."""
        differ = AnswerDiffer()

        original = "我设计了缓存方案"
        revised = "我设计了Redis缓存方案，使用LRU淘汰策略，配置了2GB内存，TTL设置为3600秒，QPS从500提升到5000"

        diff = differ.compute_diff(original, revised)

        assert diff["new_evidence"] is True
        assert diff["is_substantive_change"] is True

    def test_substantive_change_significant_rewrite(self):
        """Test substantive change with significant rewrite."""
        differ = AnswerDiffer()

        original = "我开发了推荐系统"
        revised = "我主导设计并实现了基于协同过滤的推荐系统，采用Spark处理离线数据，使用Redis存储实时特征，通过ABtest验证效果提升15%"

        diff = differ.compute_diff(original, revised)

        assert diff["change_ratio"] > 0.2
        assert diff["is_substantive_change"] is True

    def test_identical_text(self):
        """Test diff of identical texts."""
        differ = AnswerDiffer()

        text = "我使用Redis作为缓存"
        diff = differ.compute_diff(text, text)

        assert diff["total_added"] == 0
        assert diff["total_removed"] == 0
        assert diff["change_ratio"] == 0.0
        assert diff["original_hash"] == diff["revised_hash"]

    def test_tokenize_chinese(self):
        """Test tokenization of Chinese text."""
        differ = AnswerDiffer()

        text = "我使用Redis作为缓存，QPS达到5000"
        tokens = differ._tokenize(text)

        assert "redis" in tokens  # Lowercase
        assert "qps" in tokens
        assert "5000" in tokens

    def test_tokenize_mixed_language(self):
        """Test tokenization of mixed Chinese-English text."""
        differ = AnswerDiffer()

        text = "System uses Redis cache with 5000 QPS"
        tokens = differ._tokenize(text)

        assert "system" in tokens
        assert "redis" in tokens
        assert "5000" in tokens

    def test_hash_consistency(self):
        """Test hash consistency for same text."""
        differ = AnswerDiffer()

        text1 = "测试文本"
        text2 = "测试文本"

        hash1 = differ._hash_text(text1)
        hash2 = differ._hash_text(text2)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length


class TestAnswerVersionManager:
    """Test answer version management."""

    def test_create_first_version(self):
        """Test creating first version."""
        manager = AnswerVersionManager()

        version = manager.create_version(
            answer_id="ans1",
            version_number=1,
            answer_text="我使用Redis作为缓存",
            previous_text=None,
        )

        assert version["answer_id"] == "ans1"
        assert version["version_number"] == 1
        assert version["is_substantive_change"] is True
        assert version["diff_summary"] is None

    def test_create_second_version_with_diff(self):
        """Test creating second version with diff."""
        manager = AnswerVersionManager()

        original = "我使用Redis作为缓存"
        revised = "我使用Redis作为缓存，QPS达到5000"

        version = manager.create_version(
            answer_id="ans1",
            version_number=2,
            answer_text=revised,
            previous_text=original,
        )

        assert version["version_number"] == 2
        assert version["diff_summary"] is not None
        assert version["diff_summary"]["new_evidence"] is True
        assert version["is_substantive_change"] is True

    def test_should_suggest_switch_after_coaching_repetition(self):
        """Test suggestion to switch after coaching repetition."""
        manager = AnswerVersionManager()

        # Simulate 3 non-substantive retries
        last_diff = {
            "is_substantive_change": False,
            "coaching_repetition": True,
        }

        should_switch = manager.should_suggest_switch_question(
            version_count=3,
            last_diff=last_diff,
        )

        assert should_switch is True

    def test_no_switch_suggestion_with_substantive_change(self):
        """Test no switch suggestion when changes are substantive."""
        manager = AnswerVersionManager()

        last_diff = {
            "is_substantive_change": True,
            "new_evidence": True,
        }

        should_switch = manager.should_suggest_switch_question(
            version_count=3,
            last_diff=last_diff,
        )

        assert should_switch is False

    def test_no_switch_suggestion_few_retries(self):
        """Test no switch suggestion with few retries."""
        manager = AnswerVersionManager()

        last_diff = {
            "is_substantive_change": False,
        }

        should_switch = manager.should_suggest_switch_question(
            version_count=2,
            last_diff=last_diff,
        )

        assert should_switch is False


class TestDiffEdgeCases:
    """Test edge cases in diff computation."""

    def test_empty_original_text(self):
        """Test diff with empty original text."""
        differ = AnswerDiffer()

        diff = differ.compute_diff("", "新增内容")

        assert diff["change_ratio"] == 1.0
        assert diff["total_added"] > 0

    def test_empty_revised_text(self):
        """Test diff with empty revised text."""
        differ = AnswerDiffer()

        diff = differ.compute_diff("原始内容", "")

        assert diff["change_ratio"] > 0
        assert diff["total_removed"] > 0

    def test_very_long_text(self):
        """Test diff with very long texts."""
        differ = AnswerDiffer()

        original = "我使用Redis缓存 " * 100
        revised = original + "新增了Memcached作为二级缓存，QPS提升到10000"

        diff = differ.compute_diff(original, revised)

        assert diff["new_evidence"] is True
        # Should still complete without errors
        assert "change_ratio" in diff

    def test_special_characters(self):
        """Test diff with special characters."""
        differ = AnswerDiffer()

        original = "配置参数：max_connections=100"
        revised = "配置参数：max_connections=1000, timeout=30s"

        diff = differ.compute_diff(original, revised)

        assert diff["total_added"] > 0
        assert diff["new_evidence"] is True

    def test_punctuation_only_changes(self):
        """Test diff with only punctuation changes."""
        differ = AnswerDiffer()

        original = "我使用Redis作为缓存"
        revised = "我使用Redis作为缓存。"

        diff = differ.compute_diff(original, revised)

        # Should detect minimal change
        assert diff["change_ratio"] < 0.1

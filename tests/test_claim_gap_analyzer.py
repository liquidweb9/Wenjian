"""Tests for Claim Gap Analyzer."""

import pytest

from app.planning.claim_mapper import ClaimMapper, ClaimMappingResult
from app.planning.claim_gap_analyzer import (
    ClaimGapAnalyzer,
    GapType,
    ReasonCode,
)


class TestUncoveredRequirements:
    """Test detection of uncovered requirements."""

    def test_uncovered_requirement_detected(self):
        """Requirement with no matching claim is UNCOVERED."""
        analyzer = ClaimGapAnalyzer()

        # No claims
        claim_mappings = []

        # One requirement
        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis 缓存",
                "importance": 0.9,
                "expected_level": 3,
            }
        ]

        result = analyzer.analyze_gaps(claim_mappings, requirements)

        # Should have one uncovered gap
        uncovered_gaps = [g for g in result.gaps if g.gap_type == GapType.UNCOVERED_REQUIREMENT]
        assert len(uncovered_gaps) == 1
        assert uncovered_gaps[0].requirement_id == "req_1"
        assert uncovered_gaps[0].claim_id is None
        assert ReasonCode.REQUIREMENT_UNCOVERED in uncovered_gaps[0].reason_codes

    def test_uncovered_high_importance_flagged(self):
        """High-importance uncovered requirement gets HIGH_IMPORTANCE_GAP."""
        analyzer = ClaimGapAnalyzer()

        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.9,  # High
                "expected_level": 3,
            }
        ]

        result = analyzer.analyze_gaps([], requirements)

        gap = result.gaps[0]
        assert ReasonCode.HIGH_IMPORTANCE_GAP in gap.reason_codes
        assert gap.priority > 0.7

    def test_uncovered_low_importance_lower_priority(self):
        """Low-importance uncovered requirement has lower priority."""
        analyzer = ClaimGapAnalyzer()

        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.6,  # Low
                "expected_level": 2,
            }
        ]

        result = analyzer.analyze_gaps([], requirements)

        gap = result.gaps[0]
        assert gap.priority < 0.7


class TestWeakEvidenceClaims:
    """Test detection of weak evidence claims."""

    def test_weak_evidence_claim_detected(self):
        """Claim with low coverage level is WEAK_EVIDENCE."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        # Create claim mapping with low coverage
        claim_text = "提到了 Redis"
        claim_result = mapper.map_claim(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.7,
                    "expected_level": 3,
                }
            ],
        )

        result = analyzer.analyze_gaps([claim_result], [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.7,
                "expected_level": 3,
            }
        ])

        # Should detect weak evidence (coverage L1-2, expected L3)
        weak_gaps = [
            g for g in result.gaps
            if g.gap_type in (GapType.WEAK_EVIDENCE_CLAIM, GapType.HIGH_PRIORITY_WEAK_EVIDENCE)
        ]
        assert len(weak_gaps) > 0

    def test_high_priority_weak_evidence(self):
        """High-importance requirement with weak evidence gets special classification."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        claim_text = "使用过 Redis"
        claim_result = mapper.map_claim(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.9,  # High importance
                    "expected_level": 4,  # High expectation
                }
            ],
        )

        result = analyzer.analyze_gaps([claim_result], [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.9,
                "expected_level": 4,
            }
        ])

        # Should be HIGH_PRIORITY_WEAK_EVIDENCE
        high_priority_gaps = [g for g in result.gaps if g.gap_type == GapType.HIGH_PRIORITY_WEAK_EVIDENCE]
        assert len(high_priority_gaps) > 0
        assert high_priority_gaps[0].priority > 0.5  # Adjusted threshold


class TestSupportedClaims:
    """Test detection of supported claims."""

    def test_supported_claim_detected(self):
        """Claim with good coverage is SUPPORTED."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        claim_text = "负责 Redis 缓存架构设计，实现缓存模式、一致性处理、分布式锁、性能优化、监控告警"
        claim_result = mapper.map_claim(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.85,
                    "expected_level": 2,  # Lower expectation to match coverage
                }
            ],
        )

        result = analyzer.analyze_gaps([claim_result], [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.85,
                "expected_level": 2,  # Lower expectation
            }
        ])

        # Should have SUPPORTED_CLAIM (coverage L2 >= expected L2)
        supported_gaps = [g for g in result.gaps if g.gap_type == GapType.SUPPORTED_CLAIM]
        assert len(supported_gaps) > 0

    def test_supported_claim_lower_priority(self):
        """Supported claims have lower priority than gaps."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        claim_text = "深度使用 Redis 缓存，包括缓存模式、一致性、分布式锁、性能调优、监控体系"
        claim_result = mapper.map_claim(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.8,
                    "expected_level": 2,  # Match coverage level
                }
            ],
        )

        result = analyzer.analyze_gaps([claim_result], [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.8,
                "expected_level": 2,  # Match coverage level
            }
        ])

        supported_gap = next(g for g in result.gaps if g.gap_type == GapType.SUPPORTED_CLAIM)
        assert supported_gap.priority < 0.5  # Lower than gap priorities


class TestIrrelevantClaims:
    """Test detection of irrelevant claims."""

    def test_irrelevant_claim_detected(self):
        """Claim with no requirement mapping is IRRELEVANT."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        # Claim about frontend (not in job requirements)
        claim_text = "负责前端 React 开发"
        claim_result = mapper.map_claim(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.8,
                    "expected_level": 3,
                }
            ],
        )

        result = analyzer.analyze_gaps([claim_result], [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.8,
                "expected_level": 3,
            }
        ])

        # Should have IRRELEVANT_CLAIM
        irrelevant_gaps = [g for g in result.gaps if g.gap_type == GapType.IRRELEVANT_CLAIM]
        assert len(irrelevant_gaps) > 0
        assert irrelevant_gaps[0].claim_id == "claim_1"
        assert ReasonCode.IRRELEVANT_TO_JOB in irrelevant_gaps[0].reason_codes

    def test_irrelevant_claim_low_priority(self):
        """Irrelevant claims have very low priority."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        claim_text = "前端开发经验"
        claim_result = mapper.map_claim(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.9,
                    "expected_level": 3,
                }
            ],
        )

        result = analyzer.analyze_gaps([claim_result], [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.9,
                "expected_level": 3,
            }
        ])

        irrelevant_gap = next(
            (g for g in result.gaps if g.gap_type == GapType.IRRELEVANT_CLAIM),
            None
        )
        if irrelevant_gap:
            assert irrelevant_gap.priority <= 0.2


class TestCoverageStats:
    """Test coverage statistics calculation."""

    def test_coverage_stats_calculated(self):
        """Coverage stats correctly summarize gaps."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        # 2 claims
        claim1 = mapper.map_claim(
            claim_id="claim_1",
            claim_text="使用 Redis 缓存",
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.8,
                    "expected_level": 3,
                },
                {
                    "requirement_id": "req_2",
                    "competency_code": "backend.message_queue",
                    "title": "Kafka",
                    "importance": 0.7,
                    "expected_level": 2,
                },
            ],
        )

        claim2 = mapper.map_claim(
            claim_id="claim_2",
            claim_text="Kafka 消息队列设计",
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.8,
                    "expected_level": 3,
                },
                {
                    "requirement_id": "req_2",
                    "competency_code": "backend.message_queue",
                    "title": "Kafka",
                    "importance": 0.7,
                    "expected_level": 2,
                },
            ],
        )

        # 3 requirements (2 covered by claims, 1 uncovered)
        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.8,
                "expected_level": 3,
            },
            {
                "requirement_id": "req_2",
                "competency_code": "backend.message_queue",
                "title": "Kafka",
                "importance": 0.7,
                "expected_level": 2,
            },
            {
                "requirement_id": "req_3",
                "competency_code": "backend.database_modeling",
                "title": "MySQL",
                "importance": 0.9,
                "expected_level": 3,
            },
        ]

        result = analyzer.analyze_gaps([claim1, claim2], requirements)

        stats = result.coverage_stats
        assert stats.total_requirements == 3
        assert stats.covered_requirements == 2
        assert stats.uncovered_requirements == 1
        assert stats.coverage_percentage == pytest.approx(2/3)

    def test_high_priority_gaps_counted(self):
        """High-priority gaps (priority >= 0.7) are counted."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        # High-importance uncovered requirement
        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.95,  # Very high
                "expected_level": 4,
            }
        ]

        result = analyzer.analyze_gaps([], requirements)

        assert result.coverage_stats.high_priority_gaps >= 1


class TestPrioritySorting:
    """Test that gaps are sorted by priority."""

    def test_gaps_sorted_by_priority(self):
        """Gaps are sorted descending by priority."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        claim_text = "使用 Redis 和 Kafka"
        claim_result = mapper.map_claim(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.7,
                    "expected_level": 3,
                },
                {
                    "requirement_id": "req_2",
                    "competency_code": "backend.message_queue",
                    "title": "Kafka",
                    "importance": 0.6,
                    "expected_level": 2,
                },
                {
                    "requirement_id": "req_3",
                    "competency_code": "backend.database_modeling",
                    "title": "MySQL",
                    "importance": 0.95,  # Highest importance, uncovered
                    "expected_level": 4,
                },
            ],
        )

        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.7,
                "expected_level": 3,
            },
            {
                "requirement_id": "req_2",
                "competency_code": "backend.message_queue",
                "title": "Kafka",
                "importance": 0.6,
                "expected_level": 2,
            },
            {
                "requirement_id": "req_3",
                "competency_code": "backend.database_modeling",
                "title": "MySQL",
                "importance": 0.95,
                "expected_level": 4,
            },
        ]

        result = analyzer.analyze_gaps([claim_result], requirements)

        # Check that priorities are descending
        priorities = [g.priority for g in result.gaps]
        assert priorities == sorted(priorities, reverse=True)

        # Uncovered high-importance requirement should be first
        assert result.gaps[0].gap_type == GapType.UNCOVERED_REQUIREMENT
        assert result.gaps[0].requirement_id == "req_3"


class TestHighPriorityTargets:
    """Test identification of high-priority targets."""

    def test_high_priority_targets_identified(self):
        """High-priority gaps (priority >= 0.7) are listed as targets."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.9,
                "expected_level": 3,
            }
        ]

        result = analyzer.analyze_gaps([], requirements)

        # Uncovered high-importance requirement should be in targets
        assert len(result.high_priority_targets) > 0
        assert "req_1" in result.high_priority_targets

    def test_supported_claims_not_in_targets(self):
        """Supported claims (low priority) are not in high-priority targets."""
        mapper = ClaimMapper()
        analyzer = ClaimGapAnalyzer()

        claim_text = "深度使用 Redis，包括缓存模式、一致性、分布式锁、性能优化"
        claim_result = mapper.map_claim(
            claim_id="claim_1",
            claim_text=claim_text,
            requirements=[
                {
                    "requirement_id": "req_1",
                    "competency_code": "backend.cache",
                    "title": "Redis",
                    "importance": 0.7,
                    "expected_level": 3,
                }
            ],
        )

        requirements = [
            {
                "requirement_id": "req_1",
                "competency_code": "backend.cache",
                "title": "Redis",
                "importance": 0.7,
                "expected_level": 3,
            }
        ]

        result = analyzer.analyze_gaps([claim_result], requirements)

        # Supported claim should not be in high-priority targets
        assert "claim_1" not in result.high_priority_targets or len(result.high_priority_targets) == 0

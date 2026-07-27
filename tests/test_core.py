"""Tests for core modules."""

import pytest
from app.core.ids import new_id, new_resume_id, new_interview_id
from app.core.enums import ResumeStatus, SourceType, ClaimStatusEnum
from app.core.security import sanitize_filename


class TestIDs:
    def test_new_id_with_prefix(self):
        uid = new_id("test")
        assert uid.startswith("test_")
        assert len(uid) > 5

    def test_new_id_no_prefix(self):
        uid = new_id()
        assert len(uid) == 12

    def test_resume_id(self):
        assert new_resume_id().startswith("res_")

    def test_interview_id(self):
        assert new_interview_id().startswith("int_")


class TestEnums:
    def test_resume_status_values(self):
        assert ResumeStatus.UPLOADED.value == "UPLOADED"
        assert ResumeStatus.CONFIRMED.value == "CONFIRMED"

    def test_source_type_values(self):
        assert SourceType.PDF.value == "pdf"

    def test_claim_status_values(self):
        assert ClaimStatusEnum.UNTOUCHED.value == "UNTOUCHED"
        assert ClaimStatusEnum.VERIFIED.value == "VERIFIED"


class TestSecurity:
    def test_sanitize_simple(self):
        assert sanitize_filename("resume.pdf") == "resume.pdf"

    def test_sanitize_path_traversal(self):
        assert sanitize_filename("../../etc/passwd") == "passwd"

    def test_sanitize_special_chars(self):
        result = sanitize_filename("my<resume>.pdf")
        assert "/" not in result

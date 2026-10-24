"""Tests for the carbon-credit certificate PDF renderer."""

from services.audit.certificate_pdf import build_certificate_pdf


def _data():
    return {
        "project": {"name": "پروژه جنگل‌کاری", "ref": "PRJ-001", "country": "ایران"},
        "credit": {"tonnes": 12.5, "standard": "VCS", "serial": "SER-001"},
        "owner": {"name": "مالک گواهی"},
        "meta": {"issued": "2026-10-19", "valid_until": "2027-10-19"},
    }


class TestCertificatePdf:
    """Tests for the PDF renderer."""

    def test_it_produces_a_pdf(self):
        pdf = build_certificate_pdf(_data())
        assert isinstance(pdf, bytes)
        assert len(pdf) > 0

    def test_the_document_starts_with_the_pdf_magic(self):
        pdf = build_certificate_pdf(_data())
        assert pdf.startswith(b"%PDF")

    def test_the_document_ends_with_the_eof_marker(self):
        pdf = build_certificate_pdf(_data())
        assert b"%%EOF" in pdf[-1024:]

    def test_an_empty_payload_still_renders(self):
        """A missing field must not crash the renderer."""
        pdf = build_certificate_pdf({})
        assert pdf.startswith(b"%PDF")

    def test_a_missing_project_still_renders(self):
        pdf = build_certificate_pdf({"credit": {"tonnes": 1.0}})
        assert pdf.startswith(b"%PDF")

    def test_the_payload_is_not_mutated(self):
        data = _data()
        before = dict(data)
        build_certificate_pdf(data)
        assert data == before

import pytest
from src.report_generator import report_generator

def test_pdf_generation():
    pdf_buffer = report_generator.generate_pdf_report()
    assert pdf_buffer is not None
    content = pdf_buffer.getvalue()
    assert len(content) > 1000
    assert content.startswith(b"%PDF")

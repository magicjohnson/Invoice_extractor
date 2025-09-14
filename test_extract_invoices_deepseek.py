import json

import pytest
from unittest.mock import patch, MagicMock
from extract_invoices_deepseek import DeepSeekInvoiceExtractor

# Mock sample PDF text
SAMPLE_PDF_TEXT = """
===== Page 1 =====
Invoice Number: INV12345
Vendor Name: Example Vendor
Invoice Date: 2025-09-01
Total Amount: $1000.00
"""

# Mock extracted data
SAMPLE_EXTRACTED_DATA = [{
    "Vendor Name": "Example Vendor",
    "Invoice Number": "INV12345",
    "Invoice Date": "2025-09-01",
    "Due Date": "2025-10-01",
    "PO Number": "PO67890",
    "Total Amount": "$1000.00",
    "Description": "Consulting Services",
    "Bill To": "Oaks at Creekside",
    "Payment Terms": "Net 30",
    "Payment Instructions": "Wire transfer to account XYZ"
}]

@pytest.fixture
def extractor():
    """Fixture to create a DeepSeekInvoiceExtractor instance with a mock API key."""
    return DeepSeekInvoiceExtractor(api_key="mock_api_key")

def test_extract_text_from_pdf(extractor):
    """Test OCR-based PDF text extraction."""
    with patch("extract_invoices_deepseek.convert_from_bytes", return_value=[MagicMock()]):
        with patch("extract_invoices_deepseek.pytesseract.image_to_string", return_value="Invoice Number: INV12345"):
            result = extractor.extract_text_from_pdf(b"mock_pdf_content")
            assert "===== Page 1 =====" in result
            assert "Invoice Number: INV12345" in result

def test_extract_text_from_pdf1(extractor):
    """Test PyPDF2-based PDF text extraction."""
    mock_pdf_reader = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Invoice Number: INV12345"
    mock_pdf_reader.pages = [mock_page]
    
    with patch("extract_invoices_deepseek.PyPDF2.PdfReader", return_value=mock_pdf_reader):
        with patch("extract_invoices_deepseek.io.BytesIO"):
            result = extractor.extract_text_from_pdf1(b"mock_pdf_content")
            assert "===== Page 1 =====" in result
            assert "Invoice Number: INV12345" in result

def test_extract_text_from_pdf_fitz(extractor):
    """Test PyMuPDF-based PDF text extraction."""
    mock_pdf_document = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Invoice Number: INV12345"
    mock_pdf_document.load_page.return_value = mock_page
    mock_pdf_document.__len__.return_value = 1
    
    with patch("extract_invoices_deepseek.fitz.open", return_value=mock_pdf_document):
        result = extractor.extract_text_from_pdf_fitz(b"mock_pdf_content")
        assert "===== Page 1 =====" in result
        assert "Invoice Number: INV12345" in result

def test_split_text_into_chunks(extractor):
    """Test text chunking logic."""
    text = """
    ===== Page 1 =====
    Invoice Number: INV12345
    ===== Page 2 =====
    Vendor Name: Example Vendor
    """
    chunks = extractor.split_text_into_chunks(text, max_tokens=10)
    assert len(chunks) == 2
    assert "Invoice Number: INV12345" in chunks[0]
    assert "Vendor Name: Example Vendor" in chunks[1]

def test_extract_invoice_data_from_chunk(extractor):
    """Test invoice data extraction from a text chunk."""
    with patch("extract_invoices_deepseek.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(SAMPLE_EXTRACTED_DATA)}}]
        }
        mock_post.return_value = mock_response
        
        result = extractor.extract_invoice_data_from_chunk(SAMPLE_PDF_TEXT)
        assert result == SAMPLE_EXTRACTED_DATA
        assert mock_post.called
        assert result[0]["Invoice Number"] == "INV12345"
        assert result[0]["Vendor Name"] == "Example Vendor"

def test_extract_invoice_data_from_chunk_error(extractor):
    """Test handling of API error in chunk processing."""
    with patch("extract_invoices_deepseek.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        result = extractor.extract_invoice_data_from_chunk(SAMPLE_PDF_TEXT)
        assert result == []

def test_extract_invoice_data_from_chunk_invalid_json(extractor):
    """Test handling of invalid JSON in chunk processing."""
    with patch("extract_invoices_deepseek.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Invalid JSON"}}]
        }
        mock_post.return_value = mock_response
        
        result = extractor.extract_invoice_data_from_chunk(SAMPLE_PDF_TEXT)
        assert result == []

def test_extract_invoice_data(extractor):
    """Test the main invoice data extraction pipeline."""
    with patch.object(extractor, "extract_text_from_pdf", return_value=SAMPLE_PDF_TEXT):
        with patch.object(extractor, "split_text_into_chunks", return_value=[SAMPLE_PDF_TEXT]):
            with patch.object(extractor, "extract_invoice_data_from_chunk", return_value=SAMPLE_EXTRACTED_DATA):
                result = extractor.extract_invoice_data(b"mock_pdf_content")
                assert len(result) == 1
                assert result[0]["Invoice Number"] == "INV12345"
                assert result[0]["Vendor Name"] == "Example Vendor"

def test_extract_invoice_data_duplicate_handling(extractor):
    """Test duplicate invoice removal."""
    duplicate_data = SAMPLE_EXTRACTED_DATA + SAMPLE_EXTRACTED_DATA
    with patch.object(extractor, "extract_text_from_pdf", return_value=SAMPLE_PDF_TEXT):
        with patch.object(extractor, "split_text_into_chunks", return_value=[SAMPLE_PDF_TEXT]):
            with patch.object(extractor, "extract_invoice_data_from_chunk", return_value=duplicate_data):
                result = extractor.extract_invoice_data(b"mock_pdf_content")
                assert len(result) == 1  # Duplicates removed
                assert result[0]["Invoice Number"] == "INV12345"

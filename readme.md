

# Invoice Extractor

A Python application for extracting structured invoice data from PDF files using multiple AI models (DeepSeek, OpenAI, Mistral) with OCR and exporting results to Excel.

## Features

- **PDF Text Extraction**: Extracts text using PyPDF2, PyMuPDF, and OCR (Tesseract via pdf2image).
- **Multi-Model Support**: Extracts structured invoice data using DeepSeek, OpenAI, or Mistral APIs.
- **Chunk Processing**: Splits large PDFs into chunks for efficient processing.
- **Excel Export**: Exports data to formatted Excel files using pandas and openpyxl.
- **Duplicate Handling**: Removes duplicate invoices based on vendor name and invoice number.

## Prerequisites

- Python 3.8+
- Tesseract OCR installed ([Tesseract Installation](https://tesseract-ocr.github.io/tessdoc/Installation.html))
- API keys for DeepSeek, OpenAI, and/or Mistral (set in `.env` file)
- Poetry for dependency management

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/magicjohnson/invoice-extractor.git
   cd invoice-extractor
   ```

2. Install Poetry:
   ```bash
   pip install poetry
   ```

3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

4. Create a `.env` file in the project root and add your API keys:
   ```env
   DEEPSEEK_API_KEY=your_deepseek_key
   OPENAI_API_KEY=your_openai_key
   MISTRAL_API_KEY=your_mistral_key
   ```

## Dependencies

Managed via Poetry (`pyproject.toml`):
- `PyPDF2`
- `pdf2image`
- `pytesseract`
- `PyMuPDF`
- `pandas`
- `openpyxl`
- `requests`
- `python-dotenv`

## Usage

1. Place your PDF invoice file (e.g., `invoices_example.pdf`) in the project directory.
2. Activate the Poetry virtual environment:
   ```bash
   poetry shell
   ```
3. Run the desired extraction script:
   ```bash
   python extract_invoices_deepseek.py  # For DeepSeek
   python extract_invoices_openai.py    # For OpenAI
   python extract_invoices_mistral.py   # For Mistral
   ```
4. The script will:
   - Extract text from the PDF using OCR.
   - Process text with the chosen AI model to extract structured invoice data.
   - Export results to `extracted_invoice_data.xlsx`.
   - Print extracted data to the console.

## Example Output

The extracted data is saved in `extracted_invoice_data.xlsx` with columns:
- Vendor Name
- Invoice Number
- Invoice Date
- Due Date
- PO Number
- Total Amount
- Description
- Bill To
- Payment Terms
- Payment Instructions

Console output example:
```
Extracted Invoice Data:
Invoice 1:
  Vendor Name: Example Vendor
  Invoice Number: INV12345
  Invoice Date: 2025-09-01
  Due Date: 2025-10-01
  PO Number: PO67890
  Total Amount: $1000.00
  Description: Consulting Services
  Bill To: Oaks at Creekside
  Payment Terms: Net 30
  Payment Instructions: Wire transfer to account XYZ
```

## Project Structure

```
invoice-extractor/
├── extract_invoices_deepseek.py  # DeepSeek-based extraction script
├── extract_invoices_openai.py    # OpenAI-based extraction script
├── extract_invoices_mistral.py   # Mistral-based extraction script
├── invoices_example.pdf          # Sample invoice PDF
├── pyproject.toml                # Poetry configuration
├── poetry.lock                   # Poetry lock file
├── .env                         # Environment variables (not tracked)
└── README.md                    # This file
```

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- DeepSeek, OpenAI, and Mistral APIs for structured data extraction
- Tesseract OCR for text extraction
- PyMuPDF and PyPDF2 for PDF processing
- Poetry for dependency management


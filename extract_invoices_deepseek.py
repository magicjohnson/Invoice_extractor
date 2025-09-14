import json
import os

import PyPDF2
import io
import re

import pandas as pd
import requests
from dotenv import load_dotenv
from openpyxl.styles import Font, PatternFill
import pytesseract
from pdf2image import convert_from_bytes
import fitz  # pymupdf


class DeepSeekInvoiceExtractor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def extract_text_from_pdf_fitz(self, pdf_content):
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += f"===== Page {page_num + 1} =====\n"
            text += page.get_text() + "\n\n"
        return text

    def extract_text_from_pdf(self, pdf_content):
        """Extract text from PDF using OCR"""
        print("Converting PDF to images...")
        images = convert_from_bytes(pdf_content)

        text = ""
        for i, image in enumerate(images):
            print(f"Processing page {i + 1}/{len(images)} with OCR...")
            page_text = pytesseract.image_to_string(image)
            text += f"===== Page {i + 1} =====\n"
            text += page_text + "\n\n"

        return text

    def extract_text_from_pdf1(self, pdf_content):
        """Extract text from PDF content"""
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += f"===== Page {page_num + 1} =====\n"
            text += page.extract_text() + "\n\n"

        return text

    def split_text_into_chunks(self, text, max_tokens=100000):
        """Split text into chunks based on approximate token count"""
        # Simple token estimation (1 token ≈ 4 characters)
        max_chars = max_tokens * 4

        # Split by pages to maintain context
        pages = re.split(r'===== Page \d+ =====', text)
        pages = [page for page in pages if page.strip()]

        chunks = []
        current_chunk = ""

        for page in pages:
            if len(current_chunk) + len(page) > max_chars:
                chunks.append(current_chunk)
                current_chunk = page
            else:
                current_chunk += f"\n===== Page =====\n{page}"

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def extract_invoice_data_from_chunk(self, text_chunk):
        """Extract invoice data from a text chunk"""
        prompt = """
        Analyze this partial document which contains invoices for Oaks at Creekside.
        Extract all invoice data and return it as a structured JSON array.

        For each invoice, extract these fields:
        - Vendor Name
        - Invoice Number
        - Invoice Date
        - Due Date
        - PO Number (if available)
        - Total Amount
        - Description of Services/Goods
        - Bill To / Property Name
        - Payment Terms
        - Remit To / Payment Instructions

        Return ONLY valid JSON in this format:
        [
          {
            "Vendor Name": "Vendor Name",
            "Invoice Number": "Number",
            "Invoice Date": "Date",
            "Due Date": "Date",
            "PO Number": "Number or empty",
            "Total Amount": "Amount",
            "Description": "Description",
            "Bill To": "Name",
            "Payment Terms": "Terms",
            "Payment Instructions": "Instructions"
          },
          ...
        ]
        """

        # Prepare the request payload
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at extracting structured data from invoices. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nDocument Text: {text_chunk}"
                }
            ],
            "temperature": 0.1
        }

        # Make the API request
        response = requests.post(self.api_url, headers=self.headers, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']

            # Extract JSON from the response
            try:
                # Find JSON start and end positions
                json_start = content.find('[')
                json_end = content.rfind(']') + 1

                if json_start == -1 or json_end == 0:
                    return []

                json_str = content[json_start:json_end]

                # Parse the JSON
                invoice_data = json.loads(json_str)
                return invoice_data
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing JSON: {e}")
                print(f"Response content: {content}")
                return []
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return []

    def export_to_excel(self, invoice_data, filename="invoice_data.xlsx"):
        # Create a DataFrame from the invoice data
        df = pd.DataFrame(invoice_data)

        # Create Excel writer
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Invoices', index=False)

            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Invoices']

            # Apply formatting
            header_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            header_font = Font(bold=True)

            # Format headers
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font

            # Adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f"Invoice data exported to {filename}")

    def extract_invoice_data(self, pdf_content):
        """Main method to extract invoice data from PDF"""
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_content)

        # Split text into chunks
        chunks = self.split_text_into_chunks(text)

        # Process each chunk
        all_invoices = []
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i + 1}/{len(chunks)}...")
            chunk_invoices = self.extract_invoice_data_from_chunk(chunk)
            all_invoices.extend(chunk_invoices)

        # Remove duplicates based on invoice number
        unique_invoices = {}
        for invoice in all_invoices:
            invoice_id = f"{invoice.get('Vendor Name', '')}-{invoice.get('Invoice Number', '')}"
            if invoice_id not in unique_invoices:
                unique_invoices[invoice_id] = invoice

        return list(unique_invoices.values())


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv('DEEPSEEK_API_KEY')
    extractor = DeepSeekInvoiceExtractor(api_key)

    pdf_path = "invoices_example.pdf"
    with open(pdf_path, "rb") as file:
        pdf_content = file.read()

    # Extract invoice data
    invoice_data = extractor.extract_invoice_data(pdf_content)

    if invoice_data:
        extractor.export_to_excel(invoice_data, "extracted_invoice_data.xlsx")

        print("Extracted Invoice Data:")
        for i, invoice in enumerate(invoice_data, 1):
            print(f"\nInvoice {i}:")
            for key, value in invoice.items():
                print(f"  {key}: {value}")
    else:
        print("Failed to extract invoice data.")

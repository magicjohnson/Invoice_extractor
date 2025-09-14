import pdfplumber
import pandas as pd
import json
import re
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables (for API key)
load_dotenv()


class InvoiceExtractor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.system_prompt = """
        You are an expert at extracting structured data from invoices. Extract the following fields from the invoice text:
        - vendor_name
        - invoice_number
        - invoice_date
        - due_date
        - total_amount
        - description
        - bill_to
        - po_number (if available)
        - payment_terms

        Return the data as a valid JSON object. If a field is not found, set it to null.
        """

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF using pdfplumber"""
        full_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
        return full_text

    def clean_text(self, text):
        """Basic text cleaning"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_invoice_data_with_llm(self, text):
        """Use LLM to extract structured invoice data"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Extract invoice data from this text:\n\n{text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            result = response.choices[0].message.content
            return json.loads(result)
        except Exception as e:
            print(f"Error extracting data with LLM: {e}")
            return None

    def process_pdf(self, pdf_path):
        """Process a PDF file and extract invoice data"""
        print(f"Processing {pdf_path}...")

        # Extract text from PDF
        raw_text = self.extract_text_from_pdf(pdf_path)
        if not raw_text:
            print(f"Could not extract text from {pdf_path}")
            return None

        # Clean text
        cleaned_text = self.clean_text(raw_text)

        # Use LLM to extract structured data
        invoice_data = self.extract_invoice_data_with_llm(cleaned_text)

        return invoice_data

    def process_multiple_invoices(self, pdf_paths):
        """Process multiple PDF files"""
        all_invoices = []

        for pdf_path in pdf_paths:
            invoice_data = self.process_pdf(pdf_path)
            if invoice_data:
                all_invoices.append(invoice_data)

        return all_invoices

    def export_to_excel(self, invoices_data, output_path):
        """Export extracted data to Excel"""
        if not invoices_data:
            print("No data to export")
            return False

        df = pd.DataFrame(invoices_data)

        # Reorder columns for better readability
        column_order = [
            'vendor_name', 'invoice_number', 'invoice_date', 'due_date',
            'total_amount', 'description', 'bill_to', 'po_number', 'payment_terms'
        ]

        # Only include columns that exist in the data
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]

        df.to_excel(output_path, index=False)
        print(f"Data exported to {output_path}")
        return True


if __name__ == "__main__":
    extractor = InvoiceExtractor()

    pdf_files = ["invoices_example.pdf"]  # Add more files as needed

    invoices_data = extractor.process_multiple_invoices(pdf_files)

    if invoices_data:
        extractor.export_to_excel(invoices_data, "extracted_invoices.xlsx")

        print(f"Successfully processed {len(invoices_data)} invoices")
        for i, invoice in enumerate(invoices_data, 1):
            print(f"Invoice {i}: {invoice.get('vendor_name', 'Unknown')} - ${invoice.get('total_amount', 0)}")
    else:
        print("No invoice data was extracted")

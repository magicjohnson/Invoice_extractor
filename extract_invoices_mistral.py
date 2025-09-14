import pymupdf4llm
from transformers import pipeline
import pandas as pd

md_text = pymupdf4llm.to_markdown("invoices_example.pdf")
md_text_chunks = pymupdf4llm.to_markdown("invoices_example.pdf", page_chunks=True)

# Process chunks into a DataFrame
data = [{"page": i, "text": chunk} for i, chunk in enumerate(md_text_chunks)]
df = pd.DataFrame(data)
df.to_excel("invoices_output.xlsx")

nlp = pipeline("text-generation", model="mistralai/Mixtral-8x7B-Instruct-v0.1")
prompt = f"Extract invoice number, date, and total from: {md_text}"
result = nlp(prompt, max_length=200)

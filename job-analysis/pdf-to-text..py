import pdfplumber

pdf_path = 'job-analysis\CV1.pdf'
def pdf_to_text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text

text = pdf_to_text(pdf_path)
print(text)
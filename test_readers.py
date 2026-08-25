from parser.pdf_reader import extract_text_from_pdf
from parser.docx_reader import extract_text_from_docx

pdf_text = extract_text_from_pdf("data/resumes/resume_ananya_rao.pdf")
print("----- PDF TEXT -----")
print(pdf_text)

docx_text = extract_text_from_docx("data/resumes/resume_rahul_mehta.docx")
print("----- DOCX TEXT -----")
print(docx_text)
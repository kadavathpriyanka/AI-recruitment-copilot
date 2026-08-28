from parser.pdf_reader import extract_text_from_pdf
from parser.docx_reader import extract_text_from_docx
from parser.info_extractor import extract_candidate_info

pdf_text = extract_text_from_pdf("data/resumes/resume_ananya_rao.pdf")
print("----- PDF CANDIDATE INFO -----")
print(extract_candidate_info(pdf_text))

docx_text = extract_text_from_docx("data/resumes/resume_rahul_mehta.docx")
print("----- DOCX CANDIDATE INFO -----")
print(extract_candidate_info(docx_text))
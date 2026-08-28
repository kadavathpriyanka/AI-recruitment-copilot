import pandas as pd
from parser.pdf_reader import extract_text_from_pdf
from parser.docx_reader import extract_text_from_docx
from parser.info_extractor import extract_candidate_info

def generate_profile(candidate):
    df = pd.DataFrame([candidate])
    return df

def process_resume(file_path):
    if file_path.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format")

    candidate_info = extract_candidate_info(text)
    profile = generate_profile(candidate_info)
    return profile

if __name__ == "__main__":
    import os

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)

    resume_folder = "data/resumes"
    all_profiles = []

    for filename in os.listdir(resume_folder):
        file_path = os.path.join(resume_folder, filename)
        if filename.endswith(".pdf") or filename.endswith(".docx"):
            profile = process_resume(file_path)
            all_profiles.append(profile)

    all_candidates_df = pd.concat(all_profiles, ignore_index=True)
    print(all_candidates_df)

    all_candidates_df.to_csv("data/candidate_profiles.csv", index=False)
    print("\nSaved to data/candidate_profiles.csv")
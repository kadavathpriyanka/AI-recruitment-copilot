import os
from app import process_resume

resume_folder = "data/resumes"

# Fields we expect every resume to have something for
fields_to_check = ["name", "email", "phone", "education", "skills"]

def is_field_populated(value):
    if value is None:
        return False
    if isinstance(value, list):
        return len(value) > 0
    return True

def run_accuracy_check():
    results = []
    field_totals = {field: 0 for field in fields_to_check}
    total_resumes = 0

    for filename in os.listdir(resume_folder):
        if not (filename.endswith(".pdf") or filename.endswith(".docx")):
            continue

        file_path = os.path.join(resume_folder, filename)
        profile_df = process_resume(file_path)
        candidate = profile_df.iloc[0].to_dict()

        total_resumes += 1
        populated_count = 0

        for field in fields_to_check:
            if is_field_populated(candidate.get(field)):
                field_totals[field] += 1
                populated_count += 1

        accuracy = (populated_count / len(fields_to_check)) * 100
        results.append({"file": filename, "accuracy": round(accuracy, 1)})
        print(f"{filename}: {round(accuracy, 1)}% fields populated")

    print("\n--- Per-field extraction rate ---")
    for field, count in field_totals.items():
        rate = (count / total_resumes) * 100 if total_resumes else 0
        print(f"{field}: {round(rate, 1)}% ({count}/{total_resumes} resumes)")

    overall = sum(r["accuracy"] for r in results) / len(results) if results else 0
    print(f"\nOverall extraction accuracy: {round(overall, 1)}%")
    return round(overall, 1)

if __name__ == "__main__":
    run_accuracy_check()
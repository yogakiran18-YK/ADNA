"""
ADNA Raw Dataset Downloader
Fetches official datasets for all 5 ADNA agents.
Uses Kaggle Bearer Token for Kaggle datasets, direct HTTPS for UCI/ONET, and GitHub/HF for SkillSpan.
"""

import os
import sys
import zipfile
import shutil
import requests
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw")

# Kaggle Token
KAGGLE_TOKEN = "KGAT_52120226f125dc6f6768e2dc990af3fc"
KAGGLE_HEADERS = {"Authorization": f"Bearer {KAGGLE_TOKEN}"}

def download_file(url, target_path, headers=None, stream=True):
    print(f"Downloading from {url} -> {target_path}...")
    resp = requests.get(url, headers=headers, stream=stream, timeout=120)
    resp.raise_for_status()
    with open(target_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
    size_mb = os.path.getsize(target_path) / (1024 * 1024)
    print(f"Downloaded: {size_mb:.2f} MB")
    return target_path

def download_kaggle_dataset(dataset_ref, dest_dir, filename_prefix=""):
    print(f"\n--- Fetching Kaggle Dataset: {dataset_ref} ---")
    url = f"https://www.kaggle.com/api/v1/datasets/download/{dataset_ref}"
    zip_path = os.path.join(dest_dir, f"{filename_prefix or 'dataset'}_temp.zip")
    download_file(url, zip_path, headers=KAGGLE_HEADERS)
    
    print(f"Extracting {zip_path} into {dest_dir}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)
    os.remove(zip_path)
    print(f"Successfully extracted {dataset_ref}")

def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. CURRICULUM AGENT
    # -------------------------------------------------------------
    curr_dir = os.path.join(RAW_DIR, "curriculum_agent")
    os.makedirs(curr_dir, exist_ok=True)
    
    # Placeholder for university syllabus PDFs
    pdf_dir = os.path.join(curr_dir, "university_syllabus_pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_readme = os.path.join(pdf_dir, "README.md")
    if not os.path.exists(pdf_readme):
        with open(pdf_readme, "w") as f:
            f.write("# University Syllabus PDFs Placeholder\n\nDrop departmental syllabus PDF files here for prerequisite & course extraction by the Curriculum Agent.\nSupported formats: .pdf, .docx, .txt.\n")
            
    # Coursera Courses Dataset
    coursera_dest = os.path.join(curr_dir, "coursera")
    os.makedirs(coursera_dest, exist_ok=True)
    if not os.path.exists(os.path.join(coursera_dest, "Coursera.csv")):
        download_kaggle_dataset("khusheekapoor/coursera-courses-dataset-2021", coursera_dest, "coursera")
        
    # MIT OpenCourseWare Video/Course Data
    mit_dest = os.path.join(curr_dir, "mit_ocw")
    os.makedirs(mit_dest, exist_ok=True)
    if not os.path.exists(os.path.join(mit_dest, "mit_ocw.csv")):
        download_kaggle_dataset("jorgoose/mit-opencourseware-youtube-course-data", mit_dest, "mit_ocw")

    # -------------------------------------------------------------
    # 2. MARKET TRENDS AGENT
    # -------------------------------------------------------------
    market_dir = os.path.join(RAW_DIR, "market_trends_agent")
    os.makedirs(market_dir, exist_ok=True)
    
    # Job Postings with Skills
    jobs_dest = os.path.join(market_dir, "job_postings")
    os.makedirs(jobs_dest, exist_ok=True)
    if not os.path.exists(os.path.join(jobs_dest, "data_science_job_postings.csv")):
        download_kaggle_dataset("asaniczka/data-science-job-postings-and-skills", jobs_dest, "jobs")
        
    # O*NET 28.0 Database (Official US Dept of Labor)
    onet_dest = os.path.join(market_dir, "onet")
    os.makedirs(onet_dest, exist_ok=True)
    onet_zip = os.path.join(onet_dest, "onet_28_0.zip")
    if not any(f.endswith(".txt") for f in os.listdir(onet_dest)):
        download_file("https://www.onetcenter.org/dl_files/database/db_28_0_text.zip", onet_zip)
        with zipfile.ZipFile(onet_zip, 'r') as zf:
            zf.extractall(onet_dest)
        if os.path.exists(onet_zip):
            os.remove(onet_zip)
            
    # ESCO Skills Taxonomy
    esco_dest = os.path.join(market_dir, "esco")
    os.makedirs(esco_dest, exist_ok=True)
    if not os.path.exists(os.path.join(esco_dest, "esco_skills.csv")):
        download_kaggle_dataset("thenoob69/esco-skills", esco_dest, "esco")

    # -------------------------------------------------------------
    # 3. SKILL GAP / SKILL EXTRACTION AGENT
    # -------------------------------------------------------------
    skill_dir = os.path.join(RAW_DIR, "skill_gap_agent")
    os.makedirs(skill_dir, exist_ok=True)
    
    # SkillSpan dataset directly from official repository
    skillspan_dest = os.path.join(skill_dir, "skillspan")
    os.makedirs(skillspan_dest, exist_ok=True)
    skillspan_files = {
        "train.conll": "https://raw.githubusercontent.com/kris927b/SkillSpan/main/data/conll/train.conll",
        "dev.conll": "https://raw.githubusercontent.com/kris927b/SkillSpan/main/data/conll/dev.conll",
        "test.conll": "https://raw.githubusercontent.com/kris927b/SkillSpan/main/data/conll/test.conll",
    }
    for fname, url in skillspan_files.items():
        fpath = os.path.join(skillspan_dest, fname)
        if not os.path.exists(fpath):
            try:
                download_file(url, fpath)
            except Exception as e:
                print(f"Notice: SkillSpan file {fname} error: {e}")

    # -------------------------------------------------------------
    # 4. STUDENT PROFILING AGENT
    # -------------------------------------------------------------
    stu_dir = os.path.join(RAW_DIR, "student_profiling_agent")
    os.makedirs(stu_dir, exist_ok=True)
    
    # UCI Student Performance
    uci_dest = os.path.join(stu_dir, "uci_student_performance")
    os.makedirs(uci_dest, exist_ok=True)
    uci_zip = os.path.join(uci_dest, "student_performance.zip")
    if not os.path.exists(os.path.join(uci_dest, "student-mat.csv")):
        download_file("https://archive.ics.uci.edu/static/public/320/student+performance.zip", uci_zip)
        with zipfile.ZipFile(uci_zip, 'r') as zf:
            zf.extractall(uci_dest)
        # Inner student.zip if present
        inner_zip = os.path.join(uci_dest, "student.zip")
        if os.path.exists(inner_zip):
            with zipfile.ZipFile(inner_zip, 'r') as zf:
                zf.extractall(uci_dest)
            os.remove(inner_zip)
        if os.path.exists(uci_zip):
            os.remove(uci_zip)

    # OULAD Dataset (Open University Learning Analytics Dataset)
    oulad_dest = os.path.join(stu_dir, "oulad")
    os.makedirs(oulad_dest, exist_ok=True)
    if not os.path.exists(os.path.join(oulad_dest, "studentInfo.csv")):
        download_kaggle_dataset("anlgrbz/student-demographics-online-education-dataoulad", oulad_dest, "oulad")

    # -------------------------------------------------------------
    # 5. CAREER SIMULATOR AGENT
    # -------------------------------------------------------------
    career_dir = os.path.join(RAW_DIR, "career_simulator_agent")
    os.makedirs(career_dir, exist_ok=True)
    
    # Campus Placement Dataset
    placement_dest = os.path.join(career_dir, "placement")
    os.makedirs(placement_dest, exist_ok=True)
    if not os.path.exists(os.path.join(placement_dest, "Placement_Data_Full_Class.csv")):
        try:
            download_kaggle_dataset("benroshan/factors-affecting-campus-placement", placement_dest, "placement")
        except Exception:
            download_kaggle_dataset("likithagedipudi/campus-placement-prediction", placement_dest, "placement")

    # Resume to Role Dataset
    resume_dest = os.path.join(career_dir, "resume_dataset")
    os.makedirs(resume_dest, exist_ok=True)
    if not os.path.exists(os.path.join(resume_dest, "UpdatedResumeDataSet.csv")):
        download_kaggle_dataset("jillanisofttech/updated-resume-dataset", resume_dest, "resume")

    print("\n==========================================")
    print("ALL RAW DATASETS DOWNLOADED AND EXTRACTED!")
    print("==========================================")

if __name__ == "__main__":
    main()

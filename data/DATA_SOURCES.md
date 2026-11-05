# ADNA Data Sources, Provenance & Suitability Registry

This document provides a verified, reproducible registry of all datasets present in the Autonomous Degree Navigator Agent (ADNA) repository. It specifies exact record counts verified on disk, active recommendation integration status, suitability assessments for unintegrated datasets, mathematical decay calculations, and fallback mechanisms.

---

## 1. Verified Dataset Registry

All record counts below are verified against the physical raw files in `data/raw/` using `data/kaggle_connector.py`:

| Dataset Key | Dataset Name & Kaggle Source | Verified Records | Integration Status | Role in Recommendation System |
| :--- | :--- | :--- | :--- | :--- |
| **`market_jobs`** | Data Science Job Postings (`asaniczka/data-science-job-postings-and-skills`) | **12,218 postings** (and 12,218 skills records) | **Connected & Active** | Primary market input for skill demand frequencies and exponential recency decay scoring in `SkillGapAgent` and `MarketTrendsAgent`. |
| **`coursera_courses`** | Coursera Course Dataset (`khusheekapoor/coursera-courses-dataset-2021`) | **3,532 records** | **Reference Catalog** | External MOOC catalog for skill-course keyword mapping. Not used for university degree roadmaps due to lack of academic prerequisite DAG structure. |
| **`mit_ocw`** | MIT OpenCourseWare Catalog (`jorgoose/mit-opencourseware-youtube-course-data`) | **5,288 records** | **Reference Archive** | Catalog of open lecture modules. Lacks degree credit units, letter grading, and multi-semester prerequisite sequencing. |
| **`esco_skills`** | European Skills/Competences (`thenoob69/esco-skills`) | **13,893 records** | **Taxonomy Reference** | Hierarchical skill taxonomy. Provides standard naming but lacks real-time labor market frequency and posting recency signals. |
| **`oulad_students`** | Open University Learning Analytics (`anlgrbz/.../studentInfo.csv`) | **32,593 records** | **Not Suitable** (Documented Below) | Virtual learning environment (VLE) modular clickstream and retention data; lacks technical CS course progressions and degree trajectories. |
| **`campus_placement`** | Factors Affecting Campus Placement (`benroshan/factors-affecting-campus-placement`) | **215 records** | **Not Suitable** (Documented Below) | Single-batch MBA placement demographic records (salary, degree %, MBA specialization). Completely unsuitable for CS/AI engineering career simulation. |
| **`resume_dataset`** | Updated Resume Dataset (`jillanisofttech/updated-resume-dataset`) | **962 records** | **Not Suitable** (Documented Below) | Short unlabeled text classification snippets across 25 career tags. Lacks transcripts, grades, semester sequences, and longitudinal career outcomes. |

---

## 2. Reproducible Verification Method

The verified record counts and schema health can be reproduced at any time via the CLI:

```bash
python -c "from data.kaggle_connector import check_dataset_status; s = check_dataset_status(); [print(f'{k}: {v[\"total_records\"]} records, connected={v[\"connected\"]}, suitable={v[\"suitability_assessment\"]}') for k, v in s.items()]"
```

Or by executing the API endpoint:
```http
GET /api/v1/market/kaggle/status
```

---

## 3. Dataset Suitability Analysis

### Why `market_jobs` is Suitable and Integrated
The 12,218 LinkedIn and job-board postings contain parsed job titles, company data, posting dates (`posted_date`), and extracted technical skill tags (`job_skills.csv`). When ingested via `data/kaggle_connector.py`, each posting is stored in SQLite `market_postings`. `MarketTrendsAgent` and `SkillGapAgent` aggregate skill frequencies and apply exponential recency decay to compute grounded market demand scores $D(s)$.

### Why `campus_placement` (215 records) is Unsuitable
The campus placement dataset contains 215 rows from an MBA cohort with fields like `gender`, `ssc_p` (10th grade %), `hsc_p` (12th grade %), `degree_t` (Commerce & Mgmt), and `specialisation` (Mkt&HR, Mkt&Fin). It contains zero engineering courses, zero computer science prerequisites, and zero technical skill assessments. Training a technical employability model on this dataset would result in severe model invalidity. It is excluded from the recommendation path.

### Why `resume_dataset` (962 records) is Unsuitable
The dataset consists of 962 raw text resume blurbs tagged into broad category labels (e.g., `Java Developer`, `HR`). It does not contain student transcripts, university course credit histories, or validated employability ground truth. Using it as a predictive career model constitutes false precision; instead, ADNA uses a transparent rule-based heuristic career fit estimate based on actual completed university coursework.

### Why `oulad_students` (32,593 records) is Unsuitable
OULAD tracks online distance-education virtual learning environment (VLE) clicks (e.g., `date_unregistration`, `num_of_prev_attempts`, daily click counts). It does not follow undergraduate university CS curriculum semester DAG structures or industry technical skill acquisitions.

---

## 4. Mathematical Formulas & Scoring Definitions

### 4.1 Exponential Recency Decay & Timezone Date Policy
For any job posting with posting timestamp $t$ evaluated against an explicit reference timestamp $t_{\text{as\_of}}$:
$$\Delta t = \max(0.0, (t_{\text{as\_of}} - t)_{\text{days}})$$
$$R(s) = e^{-\lambda \cdot \Delta t}$$
where $\lambda = 0.05$ (configurable in `app.config.Settings.RECENCY_DECAY_LAMBDA`).

**Date Policy**:
- Scoring references default to current UTC date (`datetime.now(timezone.utc)`).
- Explicit `as_of` parameters are strictly validated against `YYYY-MM-DD`. Malformed dates raise `ValueError` (HTTP 400).
- Postings with invalid or unparseable dates are rejected and logged in `rejection_reasons['invalid_posting_date']`; they are never silently converted to today's date.
- Postings dated in the future relative to `as_of` have $\Delta t$ clamped to $0.0$, producing $R(s) = 1.0$ (decay score strictly bounded in $[0.0, 1.0]$).

### 4.2 Role-Aware Skill Gap Score $G(s, u)$
$$\text{MarketWeight}(s) = w_1 \cdot D(s) + w_2 \cdot R(s)$$
$$G(s, u) = \text{MarketWeight}(s) \cdot \left[1 - \text{clamp}(S_{\text{sim}}(E_u, E_s), -1.0, 1.0)\right] \cdot \left[1 - \text{clamp}(C_{\text{mastery}}(u, s), 0.0, 1.0)\right]$$
where $w_1 = 0.6, w_2 = 0.4$, $E_u$ is student profile vector, $E_s$ is market skill vector, and $C_{\text{mastery}}$ is grade-point mastery factor.

**Role Partitioning**:
- Rather than scoring all skills indiscriminately, `/api/v1/skills/gap-analysis/{student_id}` accepts a `target_role_id`.
- The system resolves role definitions via `resolve_target_role()`, partition gaps into `role_required_gaps` (prioritized), `broader_market_gaps` (general market skills), and `unmapped_skills` (skills without reliable taxonomy mapping).
- Unsupported or unknown role IDs raise `ValueError` (HTTP 400).

### 4.3 Multi-Criteria Planner Objective $J(X)$
For candidate selection and final roadmap scoring over remaining semesters:
$$J(X) = w_g \cdot \text{GapClosure}(X) + w_m \cdot \text{MarketAlignment}(X) + w_p \cdot \text{FeasibilityScore}(X) - w_w \cdot \text{WorkloadPenalty}(X)$$
Default configured weights in `app.config.Settings`:
- $w_g = 0.40$ (`WEIGHT_GAP_CLOSURE`)
- $w_m = 0.30$ (`WEIGHT_MARKET_ALIGNMENT`)
- $w_p = 0.20$ (`WEIGHT_FEASIBILITY`)
- $w_w = 0.10$ (`WEIGHT_WORKLOAD_PENALTY`)

---

## 5. Fallback Modes, Provenance Transparency & Curriculum Separation

1. **Deterministic Lexical Vector Fallback**:
   - If the local HuggingFace `SentenceTransformer` (`sentence-transformers/all-MiniLM-L6-v2`) cannot be loaded or is offline, ChromaDB / `vector_store` automatically activates a deterministic lexical SHA-256 token frequency hashing vectorizer.
   - It sets `is_fallback: True` and `vector_mode: "deterministic_lexical_fallback"` in system logs.
   - It **never** returns pseudo-random vectors (`np.random.randn`) disguised as semantic similarity.

2. **Sample Data & Provenance Transparency**:
   - If no real job postings have been ingested into SQLite, the system populates standard curated baseline skills with `is_sample_data: True` and `data_source: "sample_synthesized_baseline"`.
   - The UI and API responses prominently flag `is_sample_data: True` to prevent mistaking sample defaults for ingested Kaggle data.
   - The UI renders actual API demand values or an explicit "Not Available" badge; hardcoded fallbacks such as `0.75` are strictly eliminated.

3. **Curriculum Source Separation & Infeasibility**:
   - The planner interacts with the backing graph via `Neo4jGraphManager` methods (`get_all_courses()`, `get_prerequisites_for()`, `get_course_skills_map()`, `detect_cycles()`).
   - `curriculum_source` explicitly distinguishes `"ingested"` (institution-approved curriculum ingested via `CurriculumAgent`) from `"seeded_demo"`. Seed demo courses are never merged into user-ingested curriculum.
   - When curriculum is empty or prerequisite cycles occur, the planner returns an actionable `infeasible` response explaining the violation instead of silently selecting unrelated courses.

4. **Truthful Academic Records & Estimation Disclosures**:
   - Completed courses capture actual student-reported grades and semesters. If unrecorded, they are tracked as `None` / `UNKNOWN`.
   - GPA is calculated strictly across courses with known grades; if no grades are known, `gpa = None`.
   - When estimates are made, the response flags `gpa_estimated: True` or `credits_estimated: True` and lists specific fields in `estimated_fields`.

5. **Career Simulation Transparency**:
   - Simulated career match scores are returned with `is_estimate: True` and `model_type: "transparent_heuristic_estimate"`.
   - Categorical match tiers represent academic alignment rather than guaranteed employment outcomes.


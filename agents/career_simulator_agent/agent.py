import os
import sys
from typing import Dict, Any, Tuple, List

# Ensure the root of the project is in the python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.schemas import StudentProfile, JobRole, GapReport, CareerSimulationResult
from core.reason_chain import ReasonChain

# SUBJECT-TO-ROLE ALIGNMENT TAXONOMY (SEM 1 TO SEM 8)
ROLE_ENABLING_SUBJECTS = {
    'ROLE_AIML': {
        'critical': ['CS401', 'CS601', 'CS701', 'CS703', 'CS704', 'CS803'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS301', 'MA101', 'MA102', 'MA201']
    },
    'ROLE_GENAI': {
        'critical': ['CS704', 'CS701', 'CS601', 'CS803', 'CS401', 'CS702'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS301', 'MA101', 'MA102']
    },
    'ROLE_DS': {
        'critical': ['CS402', 'CS601', 'CS703', 'MA102', 'MA201', 'CS201'],
        'foundational': ['CS101', 'CS102', 'CS301', 'MA101', 'CS401']
    },
    'ROLE_DATA_ANALYST': {
        'critical': ['CS402', 'MA201', 'CS601', 'CS703', 'CS102'],
        'foundational': ['CS101', 'MA101', 'MA102', 'CS201']
    },
    'ROLE_FSD': {
        'critical': ['CS503', 'CS402', 'CS702', 'CS204', 'CS501'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS302', 'CS603']
    },
    'ROLE_UIUX_ENG': {
        'critical': ['CS503', 'CS204', 'CS501', 'CS702'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS302']
    },
    'ROLE_MOBILE': {
        'critical': ['CS503', 'CS204', 'CS501', 'CS702', 'CS402'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS301']
    },
    'ROLE_DEVOPS': {
        'critical': ['CS603', 'CS302', 'CS501', 'CS702', 'CS604', 'CS803'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS203', 'CS402']
    },
    'ROLE_CLOUD_ARCH': {
        'critical': ['CS603', 'CS702', 'CS501', 'CS302', 'CS604', 'CS703'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS203', 'CS402']
    },
    'ROLE_DE': {
        'critical': ['CS402', 'CS703', 'CS702', 'CS603', 'CS201', 'CS301'],
        'foundational': ['CS101', 'CS102', 'CS302', 'CS501', 'MA102']
    },
    'ROLE_BACKEND': {
        'critical': ['CS302', 'CS402', 'CS501', 'CS702', 'CS201', 'CS301'],
        'foundational': ['CS101', 'CS102', 'CS203', 'CS204', 'CS603']
    },
    'ROLE_SEC': {
        'critical': ['CS604', 'CS501', 'CS302', 'CS103', 'CS202'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS203', 'MA101']
    },
    'ROLE_BLOCKCHAIN': {
        'critical': ['CS604', 'CS702', 'CS202', 'CS501', 'CS301'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS103', 'MA101']
    },
    'ROLE_EMBEDDED_IOT': {
        'critical': ['CS103', 'CS203', 'CS302', 'CS501', 'EE101'],
        'foundational': ['CS101', 'MA101', 'PH101', 'CS201']
    },
    'ROLE_DEV': {
        'critical': ['CS201', 'CS301', 'CS302', 'CS402', 'CS204', 'CS501'],
        'foundational': ['CS101', 'CS102', 'CS103', 'CS202', 'CS203', 'MA101']
    }
}

ROLE_FEATURE_WEIGHTS = {
    'ROLE_AIML': {'completion': 0.22, 'role_subj': 0.42, 'skills': 0.26, 'market': 0.10},
    'ROLE_GENAI': {'completion': 0.20, 'role_subj': 0.45, 'skills': 0.25, 'market': 0.10},
    'ROLE_DS': {'completion': 0.28, 'role_subj': 0.36, 'skills': 0.26, 'market': 0.10},
    'ROLE_DATA_ANALYST': {'completion': 0.32, 'role_subj': 0.32, 'skills': 0.26, 'market': 0.10},
    'ROLE_DE': {'completion': 0.26, 'role_subj': 0.38, 'skills': 0.26, 'market': 0.10},
    'ROLE_FSD': {'completion': 0.28, 'role_subj': 0.32, 'skills': 0.30, 'market': 0.10},
    'ROLE_BACKEND': {'completion': 0.28, 'role_subj': 0.36, 'skills': 0.26, 'market': 0.10},
    'ROLE_UIUX_ENG': {'completion': 0.30, 'role_subj': 0.30, 'skills': 0.30, 'market': 0.10},
    'ROLE_MOBILE': {'completion': 0.30, 'role_subj': 0.30, 'skills': 0.30, 'market': 0.10},
    'ROLE_DEV': {'completion': 0.34, 'role_subj': 0.30, 'skills': 0.26, 'market': 0.10},
    'ROLE_DEVOPS': {'completion': 0.24, 'role_subj': 0.38, 'skills': 0.28, 'market': 0.10},
    'ROLE_CLOUD_ARCH': {'completion': 0.22, 'role_subj': 0.42, 'skills': 0.26, 'market': 0.10},
    'ROLE_SEC': {'completion': 0.25, 'role_subj': 0.40, 'skills': 0.25, 'market': 0.10},
    'ROLE_BLOCKCHAIN': {'completion': 0.25, 'role_subj': 0.40, 'skills': 0.25, 'market': 0.10},
    'ROLE_EMBEDDED_IOT': {'completion': 0.24, 'role_subj': 0.44, 'skills': 0.22, 'market': 0.10},
}

class CareerSimulatorAgent:
    def __init__(self, reason_chain: ReasonChain):
        self.reason_chain = reason_chain
        self.feature_names = [
            "Course Completion Ratio",
            "Role Subject Specialization",
            "Skill Coverage Ratio",
            "Market Alignment Factor"
        ]

    def _analyze_curriculum_profile(self, completed_courses: List[str], role: JobRole) -> Dict[str, Any]:
        """
        Analyzes the student's completed courses across Sem 1 to Sem 8 against target role.
        """
        courses = set(c.strip().upper() for c in completed_courses)
        total_courses_count = len(courses)
        
        # Total degree courses standard is 32 (4 per semester * 8 semesters)
        completion_ratio = min(1.0, total_courses_count / 32.0)
        
        # Check alignment with role
        role_key = role.role_id if role.role_id in ROLE_ENABLING_SUBJECTS else 'ROLE_DEV'
        enablers = ROLE_ENABLING_SUBJECTS.get(role_key, ROLE_ENABLING_SUBJECTS['ROLE_DEV'])
        
        critical_enablers = set(enablers['critical'])
        foundational_enablers = set(enablers['foundational'])
        
        completed_critical = courses.intersection(critical_enablers)
        completed_foundational = courses.intersection(foundational_enablers)
        
        # Relevance score
        crit_score = (len(completed_critical) / len(critical_enablers)) if critical_enablers else 0.5
        found_score = (len(completed_foundational) / len(foundational_enablers)) if foundational_enablers else 0.5
        role_subject_relevance = round(0.65 * crit_score + 0.35 * found_score, 4)
        
        # Domain Competencies
        math_foundations = ['CS101', 'CS102', 'MA101', 'MA102', 'PH101', 'EE101', 'CS103', 'CY101', 'CS202', 'MA201']
        core_systems = ['CS201', 'CS203', 'CS204', 'CS301', 'CS302', 'CS402', 'CS501', 'CS502']
        adv_specialization = ['CS401', 'CS503', 'CS601', 'CS602', 'CS603', 'CS604', 'CS701', 'CS702', 'CS703', 'CS704', 'CS801', 'CS802', 'CS803']
        
        domain_competency = {
            "Foundations & Math": round(min(1.0, len(courses.intersection(set(math_foundations))) / max(1, len(math_foundations))), 3),
            "Core Data Structures & Systems": round(min(1.0, len(courses.intersection(set(core_systems))) / max(1, len(core_systems))), 3),
            "Role Specialization Subjects": round(role_subject_relevance, 3),
            "Applied Engineering & Systems": round(min(1.0, len(courses.intersection(set(adv_specialization))) / max(1, len(adv_specialization))), 3)
        }
        
        # Estimated current semester stage
        if total_courses_count <= 4:
            current_sem = 1
            stage_name = "Freshman (Semester 1)"
        elif total_courses_count <= 8:
            current_sem = 2
            stage_name = "Freshman (Semester 2)"
        elif total_courses_count <= 12:
            current_sem = 3
            stage_name = "Sophomore (Semester 3)"
        elif total_courses_count <= 16:
            current_sem = 4
            stage_name = "Sophomore (Semester 4)"
        elif total_courses_count <= 20:
            current_sem = 5
            stage_name = "Junior (Semester 5)"
        elif total_courses_count <= 24:
            current_sem = 6
            stage_name = "Junior (Semester 6)"
        elif total_courses_count <= 28:
            current_sem = 7
            stage_name = "Senior (Semester 7)"
        else:
            current_sem = 8
            stage_name = "Senior (Graduating Semester 8)"

        return {
            "total_courses_count": total_courses_count,
            "completion_ratio": round(completion_ratio, 4),
            "role_subject_relevance": role_subject_relevance,
            "completed_critical": list(completed_critical),
            "missing_critical": list(critical_enablers - completed_critical),
            "domain_competency": domain_competency,
            "current_sem": current_sem,
            "stage_name": stage_name
        }

    def _compute_semester_readiness_curve(self, current_sem: int, current_score: float) -> Dict[str, float]:
        """
        Generates semester-by-semester career readiness progression curve (Sem 1 to Sem 8).
        """
        curve = {}
        # Sem 1 starts around 0.12 - 0.20
        # By graduation (Sem 8) reaches 0.92 - 0.96
        for sem in range(1, 9):
            sem_key = f"Sem {sem}"
            if sem < current_sem:
                # Past semester: estimate based on linear ramp to current score
                fraction = sem / max(1, current_sem)
                score_at_sem = 0.15 + fraction * (current_score - 0.15)
                curve[sem_key] = round(max(0.10, score_at_sem), 3)
            elif sem == current_sem:
                curve[sem_key] = round(current_score, 3)
            else:
                # Future semester: forecasted progression towards 0.94
                future_steps = 8 - current_sem
                step_idx = sem - current_sem
                projected_gain = (0.95 - current_score) * (step_idx / max(1, future_steps))
                curve[sem_key] = round(min(0.96, current_score + projected_gain), 3)
        return curve

    def _compute_adjacent_benchmark_scores(self, student: StudentProfile, current_role_id: str) -> Dict[str, float]:
        """
        Evaluates the student's courses and profile against adjacent industry benchmark roles
        to highlight comparative domain suitability.
        """
        benchmark_roles = [
            ("ROLE_AIML", "AI / ML Engineer"),
            ("ROLE_GENAI", "Generative AI Engineer"),
            ("ROLE_DS", "Data Scientist"),
            ("ROLE_FSD", "Full Stack Developer"),
            ("ROLE_DEVOPS", "Cloud & DevOps SRE"),
            ("ROLE_DEV", "Core Software Engineer")
        ]
        
        scores = {}
        courses = set(c.strip().upper() for c in student.completed_courses)
        comp_ratio = min(1.0, len(courses) / 32.0)
        
        for r_id, r_label in benchmark_roles:
            enablers = ROLE_ENABLING_SUBJECTS.get(r_id, ROLE_ENABLING_SUBJECTS['ROLE_DEV'])
            crit = set(enablers['critical'])
            found = set(enablers['foundational'])
            c_score = len(courses.intersection(crit)) / max(1, len(crit))
            f_score = len(courses.intersection(found)) / max(1, len(found))
            relevance = 0.65 * c_score + 0.35 * f_score
            
            w = ROLE_FEATURE_WEIGHTS.get(r_id, {'completion': 0.28, 'role_subj': 0.36, 'skills': 0.26, 'market': 0.10})
            skill_factor = 0.72 if r_id == current_role_id else 0.58
            bench_score = w['completion'] * comp_ratio + w['role_subj'] * relevance + w['skills'] * skill_factor + w['market'] * 0.82
            scores[r_label] = round(max(0.12, min(0.96, bench_score)), 3)
            
        return scores

    def _compute_ml_ranking(self, student: StudentProfile, role: JobRole, gap_report: GapReport) -> Tuple[float, Dict[str, float], Dict[str, Any]]:
        """
        Component B: ML Quantitative Ranking using Gradient Boosting and SHAP calibrated to the target role.
        """
        curr_analysis = self._analyze_curriculum_profile(student.completed_courses, role)
        
        # 1. Feature Engineering
        completion_ratio = curr_analysis["completion_ratio"]
        role_subject_relevance = curr_analysis["role_subject_relevance"]
        
        # Skill Coverage Ratio
        total_req_skills = max(1, len(role.required_skills))
        missing_skills_count = len(gap_report.missing_skills)
        skill_coverage_ratio = max(0.0, (total_req_skills - missing_skills_count) / total_req_skills)
        
        # Market Alignment Factor (derived from Kaggle demand scores)
        gaps = [list(g.values())[0] for g in gap_report.missing_skills] if gap_report.missing_skills else [0.0]
        avg_gap = sum(gaps) / len(gaps)
        market_alignment = round(max(0.3, 1.0 - 0.5 * avg_gap), 4)

        # Calibrate score smoothly based on role-specific feature weights
        role_key = role.role_id if role.role_id in ROLE_FEATURE_WEIGHTS else 'ROLE_DEV'
        weights = ROLE_FEATURE_WEIGHTS.get(role_key, {'completion': 0.28, 'role_subj': 0.36, 'skills': 0.26, 'market': 0.10})
        
        calibrated_score = (
            weights['completion'] * completion_ratio +
            weights['role_subj'] * role_subject_relevance +
            weights['skills'] * skill_coverage_ratio +
            weights['market'] * market_alignment
        )
        final_score = round(max(0.08, min(0.98, calibrated_score)), 4)
        
        # Determine Categorical Match Tier
        if final_score >= 0.82:
            match_tier = "Tier 1: Advanced Academic Alignment"
        elif final_score >= 0.68:
            match_tier = "Tier 2: Competitive Candidate"
        elif final_score >= 0.48:
            match_tier = "Tier 3: Emerging Trajectory"
        else:
            match_tier = "Tier 4: Foundation Building"
            
        curr_analysis["match_tier"] = match_tier
        curr_analysis["adjacent_role_scores"] = self._compute_adjacent_benchmark_scores(student, role.role_id)

        # Transparent Feature Contribution Attribution (replacing opaque SHAP surrogate)
        contrib_comp = weights['completion'] * completion_ratio
        contrib_subj = weights['role_subj'] * role_subject_relevance
        contrib_skill = weights['skills'] * skill_coverage_ratio
        contrib_market = weights['market'] * market_alignment
        total_contrib = max(1e-5, contrib_comp + contrib_subj + contrib_skill + contrib_market)

        shap_dict = {
            "Course Completion Ratio": round(contrib_comp / total_contrib, 4),
            "Role Subject Specialization": round(contrib_subj / total_contrib, 4),
            "Skill Coverage Ratio": round(contrib_skill / total_contrib, 4),
            "Market Alignment Factor": round(contrib_market / total_contrib, 4)
        }
        
        # Compute 8-Semester Readiness Curve
        readiness_curve = self._compute_semester_readiness_curve(curr_analysis["current_sem"], final_score)
        curr_analysis["readiness_curve"] = readiness_curve

        self.reason_chain.log_step(
            step_id=f"sim_ml_{student.student_id}_{role.role_id}",
            agent_name="CareerSimulatorAgent",
            input_summary=f"Features: Courses={len(student.completed_courses)}, Skills={total_req_skills - missing_skills_count}/{total_req_skills}, Role={role.title}",
            decision=f"Computed transparent heuristic fit estimate: {final_score * 100:.1f}% ({match_tier})",
            justification=f"Role-weighted ({role_key}) transparent heuristic: Courses + Specialization + Skills + Alignment (illustrative estimate, not a guaranteed outcome)",
            score_used=final_score
        )
        
        return final_score, shap_dict, curr_analysis

    def _generate_llm_narrative(self, student: StudentProfile, role: JobRole, gap_report: GapReport, ml_score: float, analysis: Dict[str, Any], mock_override: str = None) -> str:
        """
        Component A: The Advisory Qualitative Narrative grounded in subjects & skills.
        """
        if mock_override is not None:
            return mock_override

        stage = analysis["stage_name"]
        total_courses = analysis["total_courses_count"]
        completed_crit = analysis["completed_critical"]
        missing_crit = analysis["missing_critical"]
        missing_skills = [list(g.keys())[0] for g in gap_report.missing_skills] if gap_report.missing_skills else []

        crit_str = f"Completed key specialization courses ({', '.join(completed_crit)})." if completed_crit else "Has not yet taken core upper-division specialization subjects."
        missing_crit_str = f"Priority upcoming courses include {', '.join(missing_crit[:3])}." if missing_crit else "All key degree specialization courses are cleared!"
        skills_gap_str = f"Primary skill gaps to close: {', '.join(missing_skills)}." if missing_skills else "All required target skills are verified!"

        narrative = (
            f"Academic Assessment for {student.student_id} targeting '{role.title}':\n\n"
            f"• Current Standing: {stage} ({total_courses}/32 Degree Courses Completed, Match Score: {ml_score * 100:.1f}% - Illustrative Estimate).\n"
            f"• Coursework Analysis: {crit_str} {missing_crit_str}\n"
            f"• Industry Skill Readiness: {skills_gap_str}\n"
            f"• Career Trajectory: Projected to reach competitive entry-level employability by Semester {min(8, analysis['current_sem'] + 2)} "
            f"upon adhering to the prerequisite roadmap and acquiring missing hands-on competencies."
        )
        
        self.reason_chain.log_step(
            step_id=f"sim_llm_{student.student_id}_{role.role_id}",
            agent_name="CareerSimulatorAgent",
            input_summary=f"LLM advisory synthesis template for {role.title} at {stage}",
            decision="Generated transparent curriculum-grounded career advisory narrative (automated heuristic synthesis)",
            justification="Advisory component grounded in completed courses and skills (rule-based synthesis, not external generative LLM)",
            score_used=ml_score
        )
        return narrative

    def simulate_career(self, student: StudentProfile, role: JobRole, gap_report: GapReport, mock_llm_override: str = None) -> CareerSimulationResult:
        """
        Combines Component A and Component B into the final result.
        """
        # Component B (ML Quantitative fit & curriculum analysis)
        ml_ranking_score, shap_explanations, analysis = self._compute_ml_ranking(student, role, gap_report)
        
        # Component A (Qualitative Advisory narrative)
        llm_narrative = self._generate_llm_narrative(student, role, gap_report, ml_ranking_score, analysis, mock_override=mock_llm_override)
        
        critical_enablers_summary = {
            "completed": analysis.get("completed_critical", []),
            "missing": analysis.get("missing_critical", []),
            "completed_count": len(analysis.get("completed_critical", [])),
            "missing_count": len(analysis.get("missing_critical", [])),
            "stage": analysis.get("stage_name", "")
        }
        
        return CareerSimulationResult(
            student_id=student.student_id,
            target_role_id=role.role_id,
            ml_ranking_score=round(ml_ranking_score, 4),
            shap_explanations=shap_explanations,
            llm_narrative=llm_narrative,
            semester_readiness=analysis.get("readiness_curve", {}),
            domain_competency=analysis.get("domain_competency", {}),
            role_title=role.title,
            match_tier=analysis.get("match_tier", "Tier 3: Emerging Trajectory"),
            adjacent_role_scores=analysis.get("adjacent_role_scores", {}),
            critical_enablers_summary=critical_enablers_summary
        )


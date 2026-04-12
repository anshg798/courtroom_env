# -*- coding: utf-8 -*-
import uuid
import re
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import CourtAction, CourtObservation, CourtState


# ── CASE FILES ────────────────────────────────────────────────────────────────

CASES = {
    "easy": {
        "title": "State vs Rajan Mehta — Theft Case",
        "case_summary": (
            "Accused Rajan Mehta, 34, was caught on CCTV removing a mobile phone "
            "worth Rs.15,000 from an unattended bag at Bangalore City Railway Station on 12 Jan 2026. "
            "Two eyewitnesses confirm the act. The phone was recovered from the accused. "
            "Accused claims he mistook it for his own phone."
        ),
        "applicable_laws": (
            "IPC Section 378 (Theft): Whoever intending to take dishonestly any moveable property "
            "out of the possession of any person without that person's consent, moves that property. "
            "IPC Section 379: Punishment for theft — imprisonment up to 3 years or fine or both."
        ),
        "rounds": [
            {
                "round": "opening",
                "opposing_argument": (
                    "Defense: My client is an honest citizen. The similarity in phone models "
                    "caused genuine confusion. There was no dishonest intention whatsoever."
                ),
            },
            {
                "round": "argument",
                "opposing_argument": (
                    "Defense: CCTV footage is inconclusive in poor lighting. "
                    "Eyewitnesses were 15 meters away and cannot confirm identity beyond doubt."
                ),
            },
            {
                "round": "rebuttal",
                "opposing_argument": (
                    "Defense: My client cooperated fully with police. "
                    "A guilty man would have fled. This shows innocent intent."
                ),
            },
            {
                "round": "closing",
                "opposing_argument": (
                    "Defense: Benefit of doubt must go to the accused. "
                    "The prosecution has not proven dishonest intent beyond reasonable doubt."
                ),
            },
        ],
        "key_facts": ["cctv", "eyewitness", "recovered", "mobile phone", "railway station"],
        "key_laws": ["section 378", "section 379", "dishonest", "intention", "ipc"],
        "winning_side": "prosecution",
    },
    "medium": {
        "title": "Sharma vs TechCorp Pvt Ltd — Wrongful Termination",
        "case_summary": (
            "Plaintiff Sunita Sharma, a senior software engineer, was terminated by TechCorp "
            "on 3 March 2026 via email with 2 hours notice, citing 'performance issues'. "
            "Her last 3 annual reviews rated her 'Exceeds Expectations'. No performance "
            "improvement plan (PIP) was ever issued. She had raised an internal harassment "
            "complaint against her manager 2 weeks before termination. "
            "Her employment contract requires 60 days written notice for termination."
        ),
        "applicable_laws": (
            "Industrial Disputes Act 1947 Section 25F: No workman can be retrenched without "
            "one month notice or wages in lieu. "
            "The Sexual Harassment of Women at Workplace Act 2013: Employer cannot retaliate "
            "against complainants. "
            "Contract Law: Breach of contractual notice period entitles damages."
        ),
        "rounds": [
            {
                "round": "opening",
                "opposing_argument": (
                    "Defense (TechCorp): The termination was a legitimate business decision "
                    "based on a recent performance review cycle. The company followed its HR policies."
                ),
            },
            {
                "round": "argument",
                "opposing_argument": (
                    "Defense: Performance issues are documented in internal systems. "
                    "The harassment complaint and termination are coincidental in timing."
                ),
            },
            {
                "round": "rebuttal",
                "opposing_argument": (
                    "Defense: The company offered a severance package which was refused. "
                    "This shows good faith on the employer's part."
                ),
            },
            {
                "round": "closing",
                "opposing_argument": (
                    "Defense: Employment decisions are management prerogative. "
                    "Courts should not interfere in business operations."
                ),
            },
        ],
        "key_facts": ["harassment complaint", "60 days notice", "performance review", "retaliation", "pip"],
        "key_laws": ["industrial disputes act", "section 25f", "posh act", "breach of contract", "retrenchment"],
        "winning_side": "plaintiff",
    },
    "hard": {
        "title": "Citizen Rights Forum vs Union of India — Right to Privacy",
        "case_summary": (
            "The government passed the National Surveillance Act 2025 allowing mass interception "
            "of all digital communications without individual warrants, citing national security. "
            "The Act gives a single ministry official the power to authorize bulk surveillance. "
            "Petitioner argues this violates the fundamental right to privacy established in "
            "Justice K.S. Puttaswamy vs Union of India (2017) and Article 21 of the Constitution. "
            "Government argues national security is a reasonable restriction under Article 19(2)."
        ),
        "applicable_laws": (
            "Article 21 (Constitution): No person shall be deprived of life or personal liberty "
            "except according to procedure established by law. "
            "Puttaswamy Judgment 2017: Privacy is a fundamental right. Any restriction must satisfy "
            "the triple test: legality, legitimate aim, proportionality. "
            "Article 19(2): Reasonable restrictions on free speech for national security are permitted. "
            "IT Act Section 69: Government may intercept communications with procedural safeguards."
        ),
        "rounds": [
            {
                "round": "opening",
                "opposing_argument": (
                    "Government: National security threats are existential. "
                    "The Act is a necessary and proportionate response to modern terrorism."
                ),
            },
            {
                "round": "argument",
                "opposing_argument": (
                    "Government: Parliament has sovereign authority to legislate on security. "
                    "Judicial review should not second-guess security assessments."
                ),
            },
            {
                "round": "rebuttal",
                "opposing_argument": (
                    "Government: Other democracies including the US and UK have similar bulk "
                    "surveillance programs. India is not unique in this approach."
                ),
            },
            {
                "round": "closing",
                "opposing_argument": (
                    "Government: The Act has internal oversight mechanisms. "
                    "The petitioner has not demonstrated actual harm from surveillance."
                ),
            },
        ],
        "key_facts": ["mass surveillance", "no warrant", "bulk interception", "single official", "national security"],
        "key_laws": ["article 21", "puttaswamy", "proportionality", "triple test", "article 19", "legality"],
        "winning_side": "petitioner",
    },
}

MAX_ROUNDS = 4


# ── JUDGE GRADER ──────────────────────────────────────────────────────────────

def judge_score(task_id: str, role: str, argument: str,
                evidence_cited: str, round_name: str, attempt: int) -> tuple[float, str]:
    """
    Scores the agent's argument 0.0–1.0.
    Partial credit at every component — rich training signal.
    """
    case = CASES[task_id]
    text = argument.lower()
    evidence_text = (evidence_cited or "").lower()
    combined = text + " " + evidence_text

    score = 0.0
    feedback = []

    # 1. RELEVANCE TO CASE FACTS (30 points)
    fact_hits = sum(1 for f in case["key_facts"] if f.lower() in combined)
    fact_score = min(0.30, fact_hits * 0.08)
    score += fact_score
    if fact_hits == 0:
        feedback.append("WEAK: argument doesn't reference case facts")
    else:
        feedback.append(f"facts cited: {fact_hits}/{len(case['key_facts'])} (+{fact_score:.2f})")

    # 2. LEGAL CITATION QUALITY (35 points)
    law_hits = sum(1 for l in case["key_laws"] if l.lower() in combined)
    law_score = min(0.35, law_hits * 0.10)
    score += law_score
    if law_hits == 0:
        feedback.append("WEAK: no applicable law cited")
    else:
        feedback.append(f"laws cited: {law_hits}/{len(case['key_laws'])} (+{law_score:.2f})")

    # 3. ARGUMENT STRUCTURE (20 points)
    structure_score = 0.0
    if len(argument.split()) >= 40:
        structure_score += 0.10
        feedback.append("length adequate (+0.10)")
    else:
        feedback.append(f"too brief: {len(argument.split())} words (need 40+)")

    # Check for logical connectors
    connectors = ["therefore", "because", "consequently", "furthermore",
                  "however", "evidence shows", "this proves", "accordingly",
                  "it follows", "hence", "thus", "moreover"]
    connector_hits = sum(1 for c in connectors if c in text)
    if connector_hits >= 2:
        structure_score += 0.10
        feedback.append("logical structure present (+0.10)")
    score += structure_score

    # 4. ROUND-SPECIFIC QUALITY (15 points)
    round_score = 0.0
    if round_name == "rebuttal":
        rebuttal_words = ["however", "contrary to", "the defense claims", "this is incorrect",
                          "in fact", "the evidence shows otherwise", "despite"]
        if any(w in text for w in rebuttal_words):
            round_score = 0.15
            feedback.append("rebuttal framing correct (+0.15)")
        else:
            feedback.append("rebuttal should directly counter opposing argument")
    elif round_name == "closing":
        closing_words = ["in conclusion", "therefore", "the evidence clearly", "we urge",
                         "the court should", "it is established", "beyond doubt"]
        if any(w in text for w in closing_words):
            round_score = 0.15
            feedback.append("closing structure correct (+0.15)")
        else:
            feedback.append("closing should summarize and urge a verdict")
    else:
        round_score = 0.10  # baseline for opening/argument rounds
        feedback.append("round baseline (+0.10)")
    score += round_score

    # Attempt penalty for repeated weak attempts
    if attempt > 2:
        penalty = 0.05 * (attempt - 2)
        score = max(0.0, score - penalty)
        feedback.append(f"attempt penalty (-{penalty:.2f})")

    return round(min(1.0, score), 3), " | ".join(feedback)


# ── ENVIRONMENT ───────────────────────────────────────────────────────────────

class CourtroomEnvEnvironment(Environment):

    def __init__(self):
        self._task_id = "easy"
        self._role = "prosecution"
        self._round_idx = 0
        self._attempt = 0
        self._argument_history = []
        self._state = CourtState(episode_id=str(uuid.uuid4()), step_count=0)

    def reset(self, task_id: str = "easy", role: str = "prosecution") -> CourtObservation:
        task_id = task_id if task_id in CASES else "easy"
        role = role if role in ("prosecution", "defense", "petitioner", "respondent") else "prosecution"

        self._task_id = task_id
        self._role = role
        self._round_idx = 0
        self._attempt = 0
        self._argument_history = []
        self._state = CourtState(
            episode_id=str(uuid.uuid4()),
            step_count=0,
            task_id=task_id,
            role=role,
        )

        case = CASES[task_id]
        first_round = case["rounds"][0]

        return CourtObservation(
            task_id=task_id,
            role=role,
            case_summary=case["case_summary"],
            current_round=first_round["round"],
            opposing_argument=first_round["opposing_argument"],
            judge_feedback="Case opened. Present your opening argument.",
            hint="",
            applicable_laws=case["applicable_laws"],
            attempt_number=0,
            max_attempts=MAX_ROUNDS,
            reward=0.0,
            done=False,
            success=False,
        )

    def step(self, action: CourtAction) -> CourtObservation:
        self._attempt += 1
        self._state.step_count += 1

        case = CASES[self._task_id]
        current_round = case["rounds"][min(self._round_idx, MAX_ROUNDS - 1)]
        # Store full argument with key evidence
        self._argument_history.append(
            f"[Round {self._attempt} - {current_round['round']}]: {action.argument[:200]}"
            + (f" [Evidence: {action.evidence_cited}]" if action.evidence_cited else "")
        )
        # Keep all rounds, not just last 3
        history_summary = "\n".join(self._argument_history)

        reward, feedback = judge_score(
            self._task_id,
            self._role,
            action.argument,
            action.evidence_cited or "",
            current_round["round"],
            self._attempt,
        )

        self._state.cumulative_score = reward
        self._round_idx += 1
        done = self._round_idx >= MAX_ROUNDS

        # Move to next round's opposing argument
        if not done:
            next_round = case["rounds"][self._round_idx]
            next_opposing = next_round["opposing_argument"]
            next_round_name = next_round["round"]
        else:
            next_opposing = "The court thanks both sides. Judgment reserved."
            next_round_name = "concluded"

        hint = ""
        if reward < 0.4 and self._attempt >= 2:
            hint = f"Hint: cite these laws — {', '.join(case['key_laws'][:3])}"

        return CourtObservation(
            task_id=self._task_id,
            role=self._role,
            case_summary=case["case_summary"],
            current_round=next_round_name,
            opposing_argument=next_opposing,
            judge_feedback=feedback,
            hint=hint,
            applicable_laws=case["applicable_laws"],
            attempt_number=self._attempt,
            max_attempts=MAX_ROUNDS,
            argument_history=history_summary,
            reward=reward,
            done=done,
            success=reward >= 0.75,
        )

    @property
    def state(self) -> CourtState:
        return self._state
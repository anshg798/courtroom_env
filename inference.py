# inference.py — ROOT of courtroom_env/
import os, json
from openai import OpenAI
from client import CourtroomEnv
from models import CourtAction

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "llama-3.1-8b-instant")
HF_TOKEN     = os.environ.get("HF_TOKEN", "")
ENV_URL      = os.environ.get("ENV_URL", "https://sihuser-courtroom-env.hf.space")

llm = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

SYSTEM_PROMPT = """You are an experienced courtroom lawyer in India.
You will receive a case file with specific facts, applicable laws, and the opposing argument.
Your argument MUST:
1. Reference at least 3 specific facts from the case summary by name (dates, people, amounts, events)
2. Cite at least 2 specific laws by their exact name or section number
3. Directly counter the opposing argument in rebuttal rounds
4. Use logical connectors: therefore, consequently, furthermore, however, this proves
5. Be 60-120 words minimum
6. In REBUTTAL rounds: start with "However," or "Contrary to the defense's claim,"
7. In CLOSING rounds: start with "In conclusion," and summarize ALL laws cited in previous rounds
8. NEVER repeat the same opening phrase you used in a previous round

YOUR PREVIOUS ARGUMENTS ARE YOUR MEMORY - build on them, never contradict them, 
and in closing rounds CITE EVERY LAW you mentioned across all previous rounds.

DO NOT write generic arguments. ALWAYS anchor to the specific facts given."""


def call_llm(obs) -> CourtAction:
    # Extract key facts reminder for later rounds
    facts_reminder = ""
    if obs.attempt_number >= 2:
        facts_reminder = f"\nCRITICAL: You MUST reference these specific facts in your argument: {', '.join(obs.case_summary.split('.')[:2])}"

    user_msg = f"""CASE: {obs.case_summary}

YOUR ROLE: {obs.role}
CURRENT ROUND: {obs.current_round}
APPLICABLE LAWS: {obs.applicable_laws}

YOUR PREVIOUS ARGUMENTS THIS EPISODE:
{obs.argument_history if obs.argument_history else "None yet"}

OPPOSING ARGUMENT:
{obs.opposing_argument}

JUDGE'S LAST FEEDBACK: {obs.judge_feedback}
{f"HINT: {obs.hint}" if obs.hint else ""}
{facts_reminder}

Write your {obs.current_round} argument. Reference specific facts AND laws:"""

    resp = llm.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=300,
        temperature=0.3,
    )
    text = resp.choices[0].message.content.strip()
    # Extract any law citation for evidence_cited field
    law_match = None
    for kw in ["Section", "Article", "Act", "IPC", "CrPC"]:
        if kw in text:
            law_match = kw
            break
    return CourtAction(argument=text, evidence_cited=law_match)


def run_task(task_id: str, role: str = "prosecution") -> float:
    env = CourtroomEnv(base_url=ENV_URL).sync()
    total_reward = 0.0
    step_count = 0

    with env:
        reset_result = env.reset(task_id=task_id, role=role)
        # reset() returns a StepResult — observation is inside .observation
        obs = reset_result.observation

        # ── [START] — exact format ──
        print(json.dumps({
            "type":        "[START]",
            "task_id":     task_id,
            "role":        role,
            "observation": obs.case_summary[:200],
        }), flush=True)

        while not obs.done:
            action = call_llm(obs)
            step_result = env.step(action)
            obs = step_result.observation
            total_reward = obs.reward
            step_count += 1

            # ── [STEP] — exact format ──
            print(json.dumps({
                "type":        "[STEP]",
                "task_id":     task_id,
                "step":        step_count,
                "round":       obs.current_round,
                "action":      action.argument[:150],
                "reward":      obs.reward,
                "observation": obs.judge_feedback,
                "done":        obs.done,
            }), flush=True)

        # ── [END] — exact format ──
        print(json.dumps({
            "type":         "[END]",
            "task_id":      task_id,
            "total_reward": total_reward,
            "success":      obs.success,
        }), flush=True)

    return total_reward


if __name__ == "__main__":
    results = {}

    # Run all 3 tasks — prosecution side
    for task_id in ["easy", "medium", "hard"]:
        results[task_id] = run_task(task_id, role="prosecution")

    # Final summary [END]
    print(json.dumps({
        "type":    "[END]",
        "summary": results,
        "average": round(sum(results.values()) / 3, 3),
    }), flush=True)

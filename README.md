---
title: Courtroom Env
emoji: ⚖️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# CourtRoom RL Environment

An OpenEnv environment where an LLM agent acts as a courtroom lawyer,
arguing real Indian legal cases across 4 structured rounds.
The environment's judge grader scores each argument on fact citation,
law citation, logical structure, and round-specific quality — providing
a rich partial reward signal at every step.

---

## Environment Description

The agent receives a real case file (facts, applicable laws, opposing argument)
and must submit a legal argument each round. The judge grader evaluates the
argument programmatically and returns a reward between 0.0 and 1.0.

The environment simulates the full arc of a courtroom proceeding:
opening -> argument -> rebuttal -> closing.

This is a real-world task with immediate practical value — training LLMs
to reason about law, cite statutes correctly, and adapt arguments based
on feedback mirrors exactly what legal AI tools need to do.

---

## Tasks

| Task   | Case                                              | Difficulty | Domain                  |
|--------|---------------------------------------------------|------------|-------------------------|
| easy   | State vs Rajan Mehta — Theft at Railway Station   | Easy       | Criminal Law (IPC)      |
| medium | Sharma vs TechCorp — Wrongful Termination         | Medium     | Employment Law          |
| hard   | Citizen Rights Forum vs Union of India — Privacy  | Hard       | Constitutional Law      |

Each task runs for 4 rounds: opening, argument, rebuttal, closing.

---

## Action Space

The agent submits a CourtAction at each step:

| Field          | Type   | Required | Description                            |
|----------------|--------|----------|----------------------------------------|
| argument       | string | Yes      | The legal argument text (60-120 words) |
| evidence_cited | string | No       | Specific law or evidence being cited   |
| objection      | string | No       | Objection to the opposing argument     |

---

## Observation Space

The agent receives a CourtObservation after each step:

| Field             | Type   | Description                                      |
|-------------------|--------|--------------------------------------------------|
| task_id           | string | "easy", "medium", or "hard"                      |
| role              | string | "prosecution" or "defense"                       |
| case_summary      | string | Full case facts                                  |
| current_round     | string | "opening", "argument", "rebuttal", "closing"     |
| opposing_argument | string | What the opposing side just argued               |
| judge_feedback    | string | Grader feedback from the last step               |
| hint              | string | Appears after 2 weak arguments                   |
| applicable_laws   | string | Laws relevant to this case                       |
| attempt_number    | int    | Current round number                             |
| max_attempts      | int    | Total rounds (4)                                 |
| reward            | float  | Score for this step (0.0-1.0)                    |
| done              | bool   | True when all rounds are complete                |
| success           | bool   | True when reward >= 0.75                         |

---

## Reward Function

Partial credit is awarded at every step — the agent always gets a training signal.

| Component              | Max Points | Condition                                         |
|------------------------|------------|---------------------------------------------------|
| Case fact citation     | 0.30       | Each key fact mentioned from the case summary     |
| Law citation           | 0.35       | Each applicable statute or case law cited         |
| Argument length        | 0.10       | Argument is >= 40 words                           |
| Logical structure      | 0.10       | Uses connectors: therefore, consequently, etc.    |
| Round-specific quality | 0.15       | Rebuttal counters opposing; closing urges verdict |
| Attempt penalty        | -0.05/step | Applied from attempt 3 onwards                    |

Maximum score per step: 1.0
Success threshold: >= 0.75

---

## Baseline Scores

Scores achieved by llama-3.1-8b-instant via Groq API:

| Task    | Score | Success |
|---------|-------|---------|
| easy    | 0.80  | Yes     |
| medium  | 0.61  | No      |
| hard    | 0.51  | No      |
| average | 0.64  |         |

---

## API Endpoints

| Endpoint | Method | Description                        |
|----------|--------|------------------------------------|
| /reset   | POST   | Start a new episode                |
| /step    | POST   | Submit an argument, get reward     |
| /state   | GET    | Get current episode state          |
| /health  | GET    | Health check - returns 200 if live |
| /schema  | GET    | Action and observation schemas     |
| /docs    | GET    | Auto-generated Swagger UI          |

---

## Quick Start

```python
from client import CourtroomEnv
from models import CourtAction

with CourtroomEnv(base_url="https://YOUR_USERNAME-courtroom-env.hf.space").sync() as env:
    result = env.reset(task_id="easy", role="prosecution")
    obs = result.observation
    print(obs.case_summary)

    result = env.step(CourtAction(
        argument="Under IPC Section 378, the accused's dishonest intention is proven "
                 "by the CCTV footage and recovery of the stolen phone.",
        evidence_cited="IPC Section 378"
    ))
    print(result.reward)
    print(result.observation.judge_feedback)
```

---

## Setup and Local Development

### Requirements

- Python 3.10, 3.11, or 3.12
- Docker Desktop
- Hugging Face account and CLI

### Install dependencies

```bash
pip install openenv-core fastapi uvicorn pydantic openai
```

### Run the server locally

```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

### Test the server

```bash
curl http://localhost:7860/health
```

### Run the inference script

```bash
set API_BASE_URL=https://api.groq.com/openai/v1
set MODEL_NAME=llama3-8b-8192
set HF_TOKEN=your_groq_api_key_here
set ENV_URL=http://localhost:7860
python inference.py
```

### Docker

```bash
docker build -t courtroom-env .
docker run -p 7860:7860 courtroom-env
```

---

## Environment Variables

| Variable     | Description                    |
|--------------|--------------------------------|
| API_BASE_URL | LLM API endpoint               |
| MODEL_NAME   | Model identifier for inference |
| HF_TOKEN     | Your Hugging Face / API key    |
| ENV_URL      | Environment server URL         |

---

## Project Structure

```
courtroom_env/
├── inference.py          # Baseline LLM agent (submission entry point)
├── models.py             # Pydantic: CourtAction, CourtObservation, CourtState
├── client.py             # WebSocket client for training code
├── openenv.yaml          # OpenEnv spec configuration
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Package metadata
├── README.md             # This file
└── server/
    ├── app.py                        # FastAPI server
    ├── courtroom_env_environment.py  # Core logic: cases, grader, rewards
    ├── requirements.txt              # Server dependencies
    └── Dockerfile                    # Container definition
```

---

## Links

- OpenEnv GitHub: https://github.com/meta-pytorch/OpenEnv
- OpenEnv Hub: https://huggingface.co/openenv
- Hackathon: https://www.scaler.com/school-of-technology/meta-pytorch-hackathon

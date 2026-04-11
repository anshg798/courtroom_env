from pydantic import BaseModel
from typing import Optional, List
from openenv.core.env_server.types import State


class CourtAction(BaseModel):
    """The agent lawyer's argument submission."""
    argument: str                        # the legal argument text
    evidence_cited: Optional[str] = None # evidence or law the agent cites
    objection: Optional[str] = None      # if objecting to opposing argument


class CourtObservation(BaseModel):
    """What the agent sees at each step."""
    task_id: str                         # "easy", "medium", "hard"
    role: str                            # "prosecution" or "defense"
    case_summary: str                    # the full case facts
    current_round: str                   # "opening" / "argument" / "rebuttal" / "closing"
    opposing_argument: str               # what the other side just said
    judge_feedback: str                  # judge's score feedback from last step
    hint: str                            # appears after 2 weak arguments
    applicable_laws: str                 # laws relevant to this case
    attempt_number: int
    max_attempts: int
    reward: float = 0.0
    done: bool = False
    success: bool


class CourtState(State):
    task_id: str = "easy"
    role: str = "prosecution"
    round_number: int = 0
    cumulative_score: float = 0.0
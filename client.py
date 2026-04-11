from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from models import CourtAction, CourtObservation, CourtState


class CourtroomEnv(EnvClient[CourtAction, CourtObservation, CourtState]):

    def _step_payload(self, action: CourtAction) -> dict:
        return {
            "argument": action.argument,
            "evidence_cited": action.evidence_cited,
            "objection": action.objection,
        }

    def _parse_result(self, payload: dict) -> StepResult[CourtObservation]:
        # server wraps observation inside "observation" key
        obs_data = payload.get("observation", payload)
        # inject reward and done from outer payload if not in obs_data
        obs_data.setdefault("reward", payload.get("reward", 0.0))
        obs_data.setdefault("done", payload.get("done", False))
        obs_data.setdefault("success", payload.get("success", False))
        obs = CourtObservation(**obs_data)
        return StepResult(
            observation=obs,
            reward=obs.reward,
            done=obs.done,
        )

    def _parse_state(self, payload: dict) -> CourtState:
        return CourtState(
            episode_id=payload.get("episode_id", ""),
            step_count=payload.get("step_count", 0),
            task_id=payload.get("task_id", "easy"),
            role=payload.get("role", "prosecution"),
        )
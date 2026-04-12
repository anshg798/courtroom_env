import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from openenv.core.env_server import create_app
except Exception as e:
    raise ImportError("openenv is required.") from e

try:
    from models import CourtAction, CourtObservation
    from server.courtroom_env_environment import CourtroomEnvEnvironment
except ModuleNotFoundError:
    from ..models import CourtAction, CourtObservation
    from .courtroom_env_environment import CourtroomEnvEnvironment

# Create the core openenv app
_openenv_app = create_app(
    CourtroomEnvEnvironment,
    CourtAction,
    CourtObservation,
    env_name="courtroom_env",
    max_concurrent_envs=1,
)

TASKS_RESPONSE = json.dumps({
    "tasks": [
        {"task_id": "easy",   "difficulty": "easy",   "domain": "Criminal Law (IPC)"},
        {"task_id": "medium", "difficulty": "medium",  "domain": "Employment Law"},
        {"task_id": "hard",   "difficulty": "hard",    "domain": "Constitutional Law"},
    ]
}).encode()


class CustomRoutesASGI:
    """Pure ASGI wrapper that intercepts custom routes before openenv."""

    def __init__(self, openenv_app):
        self._app = openenv_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            method = scope.get("method", "")

            if path == "/tasks" and method == "GET":
                await self._send_json(scope, send, TASKS_RESPONSE)
                return

            if path == "/grader" and method == "GET":
                query = scope.get("query_string", b"").decode()
                params = dict(p.split("=") for p in query.split("&") if "=" in p)
                task_id = params.get("task_id", "easy")
                argument = params.get("argument", "test")
                try:
                    from server.courtroom_env_environment import judge_score
                except ModuleNotFoundError:
                    from .courtroom_env_environment import judge_score
                reward, feedback = judge_score(
                    task_id, "prosecution", argument, "", "argument", 1
                )
                body = json.dumps({
                    "task_id": task_id,
                    "reward": reward,
                    "feedback": feedback
                }).encode()
                await self._send_json(scope, send, body)
                return

        await self._app(scope, receive, send)

    async def _send_json(self, scope, send, body: bytes):
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body)).encode()],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })


# This is what uvicorn serves
app = CustomRoutesASGI(_openenv_app)


def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run("server.app:app", host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main()

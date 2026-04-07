"""
Baseline Inference Script for Intercompany Dispute Environment
==============================================================

Environment Variables (mandatory):
    API_BASE_URL   LLM API endpoint
    MODEL_NAME     Model identifier
    HF_TOKEN       API key (also accepts API_KEY or GROQ_API_KEY)

STDOUT FORMAT (required by hackathon):
    [START] task=<task_name> env=<env_name> model=<model_name>
    [STEP] step=<n> action=<action> reward=<0.00> done=<true|false> error=<msg|null>
    [END] success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import json
import os
import sys
from pathlib import Path

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from openai import OpenAI

from agent import (
    SYSTEM_PROMPT,
    EpisodeTracker,
    build_user_prompt,
    extract_initial_context,
    extract_tool_result,
    format_tool_schema,
    log_end,
    log_start,
    log_step,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
ENV_NAME = "intercompany_dispute_env"

TASKS = [
    {"task_id": "easy_batch_matching", "scenario_id": "smoke", "max_steps": 20},
    {"task_id": "medium_fx_variance", "scenario_id": "smoke", "max_steps": 25},
    {"task_id": "hard_liability_dispute", "scenario_id": "smoke", "max_steps": 15},
]

SUCCESS_THRESHOLD = 0.10


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------


def parse_tool_call(text: str) -> tuple[str, dict]:
    """Extract {tool_name, arguments} JSON from LLM response text."""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start:end])
            name = data.get("tool_name", "")
            args = data.get("arguments", {})
            if name:
                return name, args
        except json.JSONDecodeError:
            pass
    return "query_open_items", {}


# ---------------------------------------------------------------------------
# Run one task in-process
# ---------------------------------------------------------------------------


def run_task(llm_client: OpenAI, task_config: dict) -> dict:
    """Run a single task episode against the env class (no HTTP needed)."""
    from openenv.core.env_server.mcp_types import CallToolAction, ListToolsAction
    from server.environment import IntercompanyDisputeEnvironment

    task_id = task_config["task_id"]
    scenario_id = task_config["scenario_id"]
    max_steps = task_config["max_steps"]

    log_start(task=task_id, env=ENV_NAME, model=MODEL_NAME)

    env = IntercompanyDisputeEnvironment()
    obs = env.reset(task_id=task_id, scenario_id=scenario_id)

    # Tool schemas (compact, one line each)
    tools_obs = env.step(ListToolsAction())
    tools_info = "\n".join(format_tool_schema(t) for t in (tools_obs.tools or []))

    # Initial context kept alive for the whole episode
    initial_ctx = extract_initial_context(obs.metadata or {})
    tracker = EpisodeTracker(initial_ctx)

    history: list[str] = []
    rewards: list[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    last_result = "(none — call query_open_items first)"

    for step_n in range(1, max_steps + 1):
        if env._done:
            break

        user_msg = build_user_prompt(
            step=step_n,
            max_steps=max_steps,
            initial_context=initial_ctx,
            tools_info=tools_info,
            last_result=last_result,
            history=history,
            directives=tracker.build_directives(),
        )

        try:
            completion = llm_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=300,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as e:
            response_text = '{"tool_name": "query_open_items", "arguments": {}}'
            print(f"[DEBUG] LLM error step {step_n}: {e}", file=sys.stderr)

        tool_name, arguments = parse_tool_call(response_text)

        # Execute action
        step_obs = env.step(CallToolAction(tool_name=tool_name, arguments=arguments))
        reward = step_obs.reward or 0.0
        done = step_obs.done

        error_msg = None
        step_meta = step_obs.metadata or {}
        if "error" in step_meta:
            error_msg = str(step_meta["error"])[:100]

        # Extract result for next prompt and tracker
        last_result = extract_tool_result(step_obs)
        if error_msg:
            last_result = f"ERROR: {error_msg}\n{last_result}"

        tracker.update(tool_name, arguments, reward, last_result)

        rewards.append(reward)
        steps_taken = step_n
        action_str = f"{tool_name}({json.dumps(arguments)[:80]})"

        log_step(step=step_n, action=action_str, reward=reward, done=done, error=error_msg)
        history.append(f"Step {step_n}: {action_str} -> reward={reward:+.2f}")

        if done:
            score = float(step_meta.get("terminal_task_score", 0.0))
            success = score >= SUCCESS_THRESHOLD
            break

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    return {"task_id": task_id, "success": success, "steps": steps_taken,
            "score": score, "rewards": rewards}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    if not API_KEY:
        print("ERROR: Set HF_TOKEN, API_KEY, or GROQ_API_KEY", flush=True)
        sys.exit(1)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    results = []
    for task_cfg in TASKS:
        result = run_task(client, task_cfg)
        results.append(result)
        print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"  {r['task_id']}: score={r['score']:.2f} "
              f"steps={r['steps']} success={r['success']}")


if __name__ == "__main__":
    main()

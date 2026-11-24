"""Run the full baseline once per output directory, resuming after restart."""

import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent


def notify(webhook: str | None, message: str) -> None:
    print(message, flush=True)
    if not webhook:
        return
    payload = json.dumps({"content": message, "allowed_mentions": {"parse": []}})
    try:
        request = Request(
            webhook, data=payload.encode(),
            headers={"Content-Type": "application/json", "User-Agent": "MMDL-Baseline/1.0"},
        )
        with urlopen(request, timeout=5):
            pass
    except (OSError, URLError, ValueError) as exc:
        print(f"Discord notification failed ({type(exc).__name__}).", file=sys.stderr, flush=True)


def write_state(path: Path, state: str) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(state + "\n", encoding="utf-8")
    temporary.replace(path)


def run(run_dir: Path, webhook: str | None, lock_fd: int) -> int:
    state_path = run_dir / "supervisor.state"
    previous = state_path.read_text(encoding="utf-8").strip() if state_path.exists() else ""
    if previous == "completed":
        print(f"Evaluation already completed in {run_dir}.", flush=True)
        return 0

    child = None
    stop_signal = None
    stop_time = None

    def stop(signum, _frame):
        nonlocal stop_signal, stop_time
        if stop_signal is None:
            stop_signal = signum
            stop_time = time.monotonic()
            if child is not None:
                signal_child(signum)

    def signal_child(signum):
        try:
            os.killpg(child.pid, signum)
        except ProcessLookupError:
            pass

    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, stop)

    write_state(state_path, "running")
    name = run_dir.name
    if previous == "running":
        notify(webhook, f"⏸️ {name}: previous run ended unexpectedly.")
    checkpoint_count = len(list((run_dir / "per_subject").glob("*.jsonl")))
    action = f"resuming with {checkpoint_count} saved subject files" if checkpoint_count else "starting"
    notify(webhook, f"▶️ {name}: {action}.")

    try:
        if stop_signal is None:
            with (run_dir / "run.log").open("a", encoding="utf-8") as log:
                child = subprocess.Popen(
                    ["bash", str(ROOT / "run_test.sh"), "--resume"],
                    env={**os.environ, "RUN_DIR": str(run_dir)},
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    pass_fds=(lock_fd,),
                )
                if stop_signal is not None:
                    signal_child(stop_signal)
                while child.poll() is None:
                    if stop_time is not None and time.monotonic() - stop_time >= 10:
                        signal_child(signal.SIGKILL)
                    time.sleep(0.2)

        if stop_signal is not None:
            write_state(state_path, "interrupted")
            notify(webhook, f"⏸️ {name}: interrupted by {signal.Signals(stop_signal).name}.")
            return 128 + stop_signal
        if child.returncode:
            raise RuntimeError(f"runner exit code {child.returncode}")

        with (run_dir / "metrics.json").open(encoding="utf-8") as file:
            metrics = json.load(file)
        if (metrics["status"], metrics["split"], metrics["num_results"]) != ("completed", "test", 10_500):
            raise RuntimeError("full MMMU test metrics check failed")
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        write_state(state_path, "failed")
        notify(webhook, f"❌ {name}: {exc}. See run.log.")
        return 1

    write_state(state_path, "completed")
    errors = metrics.get("generation", {}).get("errors", 0)
    if errors:
        notify(webhook, f"⚠️ {name}: {errors} question-level inference errors. See run.log.")
    notify(webhook, f"✅ {name}: completed 10,500 questions. Macro accuracy {metrics['overall_percent']:.2f}%.")
    return 0


def main() -> int:
    configured = os.environ.get("RUN_DIR", "runs/baseline_modelcard_v1_mmmu_test_98e6")
    run_dir = (ROOT / configured).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "supervisor.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"Evaluation is already running in {run_dir}.", flush=True)
            return 0
        webhook = os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook:
            secret = Path("/shared_dir/.mmmu_discord_webhook")
            try:
                webhook = secret.read_text(encoding="utf-8").strip()
            except FileNotFoundError:
                pass
            except OSError:
                print(f"Cannot read Discord webhook from {secret}.", file=sys.stderr)
        return run(run_dir, webhook, lock.fileno())


if __name__ == "__main__":
    sys.exit(main())

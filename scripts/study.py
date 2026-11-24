#!/usr/bin/env python3
"""Run the pinned public OSS Verify tools; no work happens on import."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache"
DEPS = CACHE / "pydeps"
PROOFS = ROOT / "oss-verify-proofs"


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def config():
    data = json.loads((ROOT / "VERSIONS.json").read_text())
    if not re.fullmatch(r"ghcr\.io/theorem-labs/oss-fuzz-theorems-checker@sha256:[0-9a-f]{64}", data["checker_image"]):
        raise SystemExit("VERSIONS.json must name the official checker by its SHA-256 digest.")
    return data


def versions():
    result = {}
    for name, spec in config()["repositories"].items():
        repo = ROOT / name
        if not (repo / ".git").exists():
            raise SystemExit("Missing submodule; run git submodule update --init --recursive.")
        head = output("git", "-C", str(repo), "rev-parse", "HEAD")
        result[name] = {"commit": head, "expected": spec["commit"],
                        "status": output("git", "-C", str(repo), "status", "--porcelain")}
        if head != spec["commit"]:
            raise SystemExit(f"{name} is at {head}, not the pinned {spec['commit']}.")
    return result


def docker(command, repo=PROOFS, *, network=False, deps=DEPS, extra=()):
    if not shutil.which("docker"):
        raise SystemExit("Docker is required. Install it and make its daemon accessible first.")
    jobs = os.environ.get("OFT_JOBS", "4")
    if not jobs.isdecimal() or int(jobs) < 1:
        raise SystemExit("OFT_JOBS must be a positive integer.")
    args = ["docker", "run", "--rm", "--platform", "linux/amd64", "--user", f"{os.getuid()}:{os.getgid()}",
            "--cpus", jobs, "--ulimit", "stack=-1:-1"]
    if not network:
        args += ["--network", "none"]
    args += ["-e", "HOME=/tmp", "-e", "PYTHONPATH=/pydeps", "-e", "DUNE_CACHE=disabled",
             "-e", f"OFT_JOBS={jobs}", "-v", f"{repo}:/work", "-v", f"{deps}:/pydeps:ro",
             "-w", "/work", *extra, config()["checker_image"], *command]
    return args


def requirements_hash():
    return hashlib.sha256((PROOFS / "tools/oft/requirements.txt").read_bytes()).hexdigest()


def require_prepared():
    marker = CACHE / "prepared.json"
    expected = {"checker_image": config()["checker_image"], "requirements_sha256": requirements_hash()}
    if not DEPS.is_dir() or not marker.exists() or json.loads(marker.read_text()) != expected:
        raise SystemExit("Run prepare first; dependency receipt is missing or does not match the pins.")
    return expected


def prepare():
    versions()
    if platform.system() != "Linux" or platform.machine() != "x86_64" or sys.version_info[:2] != (3, 12):
        raise SystemExit("Prepare requires Linux x86-64 and Python 3.12, matching the checker Python ABI.")
    if not shutil.which("docker"):
        raise SystemExit("Docker is required for prepare.")
    subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["docker", "pull", config()["checker_image"]], check=True)
    expected = {"checker_image": config()["checker_image"], "requirements_sha256": requirements_hash()}
    marker = CACHE / "prepared.json"
    if DEPS.exists():
        require_prepared()
    else:
        CACHE.mkdir(exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix="pydeps-", dir=CACHE))
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--require-hashes", "--no-deps",
                            "--only-binary=:all:", "--target", str(stage), "-r",
                            str(PROOFS / "tools/oft/requirements.txt")], check=True)
            subprocess.run(docker(["python3", "-c", "import yaml; print(yaml.__version__)"], deps=stage), check=True)
            stage.rename(DEPS)
            marker.write_text(json.dumps(expected, indent=2) + "\n")
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    subprocess.run(docker(["rocq", "--version"]), check=True)


def validate_name(value, harness=False):
    part = r"[A-Za-z0-9_][A-Za-z0-9_.-]*"
    if not re.fullmatch(part + ("/" + part if harness else ""), value):
        raise SystemExit("Expected PROJECT/HARNESS." if harness else "Expected one project name.")
    return value


def verify(unit):
    import fcntl  # Linux host required by this workflow.
    validate_name(unit, harness=True)
    pins = versions()
    receipt = require_prepared()
    if not (PROOFS / "projects" / unit / "harness.yaml").is_file():
        raise SystemExit("Unknown harness in the pinned repository: " + unit)
    lock = (CACHE / "verify.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("Another proof replay is using this checkout; wait for it to finish.")
    runs = ROOT / "runs"
    runs.mkdir(exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex[:8]
    base = runs / (unit.replace("/", "__") + "-" + stamp)
    command = docker(["./oft", "check", unit, "--parts", "statements,proofs", "--proof-jobs", "1"])
    record = {"unit": unit, "status": "running", "started_at": stamp, "repositories": pins,
              **receipt, "oft_jobs": os.environ.get("OFT_JOBS", "4"), "command": command,
              "scope": "Binary hashes, statements, published proofs, typed wrappers and allowed-axiom audit; excludes optional rocqchk."}
    diff = subprocess.check_output(["git", "-C", str(PROOFS), "diff", "HEAD", "--binary"])
    record["tracked_diff_sha256"] = hashlib.sha256(diff).hexdigest()
    result, log_path = Path(str(base) + ".json"), Path(str(base) + ".log")
    result.write_text(json.dumps(record, indent=2) + "\n")
    print("Checking; progress log:", log_path, flush=True)
    start = time.monotonic()
    with log_path.open("x") as log:
        code = subprocess.call(command, stdout=log, stderr=subprocess.STDOUT)
    record.update(status="passed" if code == 0 else "failed", exit_code=code,
                  elapsed_seconds=round(time.monotonic() - start, 2), finished_at=dt.datetime.now(dt.timezone.utc).isoformat())
    result.write_text(json.dumps(record, indent=2) + "\n")
    print(record["status"], result)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["versions", "prepare", "smoke"]:
        sub.add_parser(name)
    sub.add_parser("verify").add_argument("unit")
    sub.add_parser("fetch").add_argument("project")
    args = parser.parse_args()
    if args.command == "versions":
        print(json.dumps(versions(), indent=2))
    elif args.command == "prepare":
        prepare()
    elif args.command == "verify":
        return verify(args.unit)
    else:
        versions()
        require_prepared()
        if args.command == "fetch":
            command = docker(["./oft", "fetch", validate_name(args.project)], network=True)
        else:
            source = ROOT / "examples/ModelSmoke.v"
            if not source.is_file():
                raise SystemExit("Missing examples/ModelSmoke.v.")
            # Compile a temporary copy inside the container, leaving the checkout clean.
            command = docker(["bash", "-c", "cp /example.v /tmp/ModelSmoke.v && cd /tmp && rocq compile ModelSmoke.v"],
                             extra=["-v", f"{source}:/example.v:ro"])
        subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, subprocess.CalledProcessError, KeyError, ValueError) as error:
        sys.exit(str(error))

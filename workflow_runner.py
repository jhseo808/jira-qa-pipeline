#!/usr/bin/env python3
"""
QA Automation Workflow Orchestrator

Usage:
  python workflow_runner.py --ticket PA-21 --step all --url https://melon.com/chart
  python workflow_runner.py --ticket PA-21 --step plan
  python workflow_runner.py --ticket PA-21 --step all --from-step testcases
  python workflow_runner.py --ticket PA-21 --schedule
  python workflow_runner.py --daily
  python workflow_runner.py --ticket PA-21 --step all --dry-run
"""

import argparse
import os
import sys
from pathlib import Path

# Windows UTF-8 stdout / stderr
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import load_config
from lib.state import create_state, list_active_tickets, load_state, save_state

STEP_ORDER = [
    "plan",
    "testcases",
    "playwright",
    "run",
    "report",
    "bugs",
    "dashboard",
    "sideeffects",
]

STEP_MODULES = {
    "plan": "steps.step1_plan_generator",
    "testcases": "steps.step2_testcase_generator",
    "playwright": "steps.step3_playwright_generator",
    "run": "steps.step4_test_runner",
    "report": "steps.step5_report_generator",
    "bugs": "steps.step6_bug_creator",
    "dashboard": "steps.step7_dashboard",
    "sideeffects": "steps.step8_sideeffect_detector",
}


def get_step_module(step_name: str):
    import importlib

    return importlib.import_module(STEP_MODULES[step_name])


def run_step(step_name: str, state: dict, config: dict) -> dict:
    module = get_step_module(step_name)
    return module.run(state, config)


def run_pipeline(
    ticket: str,
    steps_to_run: list,
    config: dict,
    target_url: str = "",
    from_step: str = None,
) -> None:
    output_base = config["output"]["base_dir"]
    project_key = ticket.split("-")[0]

    # Load or create pipeline state
    state = load_state(ticket, output_base)
    if state is None:
        state = create_state(ticket, project_key, output_base, target_url)
        save_state(state, output_base)
        print(f"[Runner] Created new pipeline state for {ticket}")
    else:
        print(f"[Runner] Loaded existing pipeline state for {ticket}")
        if target_url:
            state["target_url"] = target_url

    # When --from-step is given, filter steps_to_run to those at or after that index
    if from_step and from_step in STEP_ORDER:
        from_idx = STEP_ORDER.index(from_step)
        steps_to_run = [s for s in steps_to_run if STEP_ORDER.index(s) >= from_idx]

    print(f"[Runner] Steps to run: {steps_to_run}")

    for step in steps_to_run:
        # Skip already-completed steps unless we're resuming from a specific step
        if step in state.get("steps_completed", []) and from_step is None:
            print(f"[Runner] Skipping already completed step: {step}")
            continue
        print(f"\n{'=' * 60}")
        print(f"[Runner] Running step: {step}")
        print(f"{'=' * 60}")
        try:
            state = run_step(step, state, config)
        except Exception as exc:
            print(f"[Runner] ERROR in step '{step}': {exc}")
            raise

    print(f"\n[Runner] Pipeline complete for {ticket}")


def main():
    parser = argparse.ArgumentParser(
        description="QA Automation Workflow Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Check environment/config (acli, node/npm/npx, output dir) and exit",
    )
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate config paths (acli.path, output.base_dir) and exit",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Create local config templates (.env, config.local.yaml) without overwriting",
    )
    parser.add_argument("--ticket", help="Jira ticket key (e.g., PA-21)")
    parser.add_argument(
        "--step",
        default="all",
        choices=STEP_ORDER + ["all"],
        help="Step to run (default: all)",
    )
    parser.add_argument("--url", default="", help="Target URL for Playwright tests")
    parser.add_argument(
        "--from-step",
        dest="from_step",
        default=None,
        choices=STEP_ORDER,
        help="Resume pipeline from this step (re-runs even if already completed)",
    )
    parser.add_argument(
        "--daily",
        action="store_true",
        help="Run dashboard+sideeffects for all active tickets",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config.yaml (default: config.yaml in project root)",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Register Windows Task Scheduler daily tasks for the ticket",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without executing any steps",
    )

    args = parser.parse_args()

    # Ensure cwd is the project root so relative imports work correctly
    os.chdir(Path(__file__).parent)

    if args.init:
        from lib.init_project import init_project, print_init_results

        raise SystemExit(print_init_results(init_project(Path(__file__).parent.resolve())))

    config = load_config(args.config, project_root=Path(__file__).parent)

    if args.validate_config or args.doctor:
        exit_code = 0
        if args.validate_config:
            from lib.validate_config import print_validation, validate_config

            exit_code = max(exit_code, print_validation(validate_config(config)))
        if args.doctor:
            from lib.doctor import print_doctor, run_doctor

            exit_code = max(exit_code, print_doctor(run_doctor(config)))
        raise SystemExit(exit_code)

    # ── Daily maintenance mode ─────────────────────────────────────────────
    if args.daily:
        tickets = list_active_tickets(config["output"]["base_dir"])
        if not tickets:
            print("[Runner] No active tickets found.")
            return
        for ticket in tickets:
            print(f"\n[Daily] Processing {ticket}...")
            try:
                run_pipeline(ticket, ["dashboard", "sideeffects"], config)
            except Exception as exc:
                print(f"[Daily] ERROR processing {ticket}: {exc}")
        return

    if not args.ticket:
        parser.error(
            "--ticket is required (unless --daily, --doctor, --validate-config, or --init)"
        )

    # ── Schedule registration mode ─────────────────────────────────────────
    if args.schedule:
        from lib.scheduler import DailyScheduler

        scheduler = DailyScheduler()
        scheduler.register(args.ticket)
        return

    # ── Dry run ────────────────────────────────────────────────────────────
    steps = STEP_ORDER if args.step == "all" else [args.step]
    if args.dry_run:
        print(f"[DryRun] Ticket:      {args.ticket}")
        print(f"[DryRun] Steps:       {steps}")
        print(f"[DryRun] From step:   {args.from_step}")
        print(f"[DryRun] Target URL:  {args.url}")
        print(f"[DryRun] Config:      {args.config}")
        return

    # ── Normal pipeline run ────────────────────────────────────────────────
    run_pipeline(args.ticket, steps, config, args.url, args.from_step)


if __name__ == "__main__":
    main()

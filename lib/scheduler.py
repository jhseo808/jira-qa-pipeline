"""
Windows Task Scheduler integration for daily QA automation.
"""

import subprocess
import sys
from pathlib import Path


class DailyScheduler:
    def __init__(self, runner_path: Path = None):
        self.runner_path = runner_path or Path(__file__).parent.parent / "workflow_runner.py"
        self.python_exe = sys.executable

    def register(self, ticket: str) -> None:
        """Register daily weekday tasks for dashboard refresh and side-effect detection."""
        for step, hour, task_name in [
            ("dashboard", "09:00", f"QA_Dashboard_{ticket}"),
            ("sideeffects", "18:00", f"QA_SideEffects_{ticket}"),
        ]:
            cmd = [
                "schtasks",
                "/create",
                "/tn",
                task_name,
                "/tr",
                f'"{self.python_exe}" "{self.runner_path}" --ticket {ticket} --step {step}',
                "/sc",
                "WEEKLY",
                "/d",
                "MON,TUE,WED,THU,FRI",
                "/st",
                hour,
                "/f",
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"[Scheduler] Registered task: {task_name} at {hour}")
            except subprocess.CalledProcessError as e:
                print(f"[Scheduler] Warning: Could not register {task_name}: {e}")

    def unregister(self, ticket: str) -> None:
        """Remove scheduled tasks for the given ticket."""
        for task_name in [f"QA_Dashboard_{ticket}", f"QA_SideEffects_{ticket}"]:
            subprocess.run(
                ["schtasks", "/delete", "/tn", task_name, "/f"],
                capture_output=True,
            )
            print(f"[Scheduler] Removed task: {task_name}")

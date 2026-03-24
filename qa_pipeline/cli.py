from __future__ import annotations


def main() -> None:
    """
    Console entrypoint.

    Keeps backward compatibility by delegating to workflow_runner.main().
    """
    from workflow_runner import main as runner_main

    runner_main()

# Changelog

All notable changes to this project will be documented in this file.

The format is based on *Keep a Changelog*, and this project follows *Semantic Versioning*.

## [Unreleased]

### Added

### Changed

### Fixed

## [0.1.0] - 2026-03-24

### Added

- Initial public version of the QA automation pipeline:
  - Config portability (`config.yaml` + `config.local.yaml` + env overrides)
  - 8-step orchestrator (`workflow_runner.py`)
  - Jira integration via `acli.exe`
  - Playwright execution and result parsing
  - Bug dashboard generator
  - Side-effect detector
  - CI (pytest + ruff)


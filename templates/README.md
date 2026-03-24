# QA 산출물 템플릿

파이프라인에서 **Claude Code 또는 작성자가 채워 넣는 문서**의 기준 형식입니다.  
실제 티켓 산출물은 `output/{ticket}/` 아래에 생성됩니다.

전체 워크플로우 안내는 루트 [`CLAUDE.md`](../CLAUDE.md) 및 [`docs/claude/common.md`](../docs/claude/common.md) 를 본다.

| 항목 | 경로 | 용도 |
|------|------|------|
| QA 계획서 | [qa_plan.md](qa_plan.md) | Step 1 → `output/{ticket}/qa_plan.md` |
| 테스트케이스 | [test_cases.md](test_cases.md) | Step 2 → `output/{ticket}/test_cases.md` |
| QA 결과서 | [qa_report.md](qa_report.md) | Step 5 → `output/{ticket}/qa_report.md` |
| 버그 대시보드 | [dashboard/](dashboard/) | 스펙·구현 연결 (HTML은 `generate_dashboard.py`가 생성) |

루트의 `qa_plan_template.md`는 하위 호환용으로 `templates/qa_plan.md`를 가리킵니다.

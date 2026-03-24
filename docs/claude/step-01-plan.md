# Step 1: QA 계획서 (plan)

[← 공통](common.md) · [인덱스](README.md)

## 스크립트

- `steps/step1_plan_generator.py`
- Jira 티켓 fetch → state 캐시, 출력 경로 안내

## Claude Code

- `output/{ticket}/qa_plan.md` 를 직접 작성한다.

## 마스터 템플릿

- [`templates/qa_plan.md`](../../templates/qa_plan.md)
- 13섹션 구조 요약은 [common.md](common.md) 표를 참고한다.

## 실행

```bash
python workflow_runner.py --ticket PA-21 --step plan
```

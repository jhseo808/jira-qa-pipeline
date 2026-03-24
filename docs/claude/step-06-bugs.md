# Step 6: Jira 버그 생성 (bugs)

[← 공통](common.md) · [인덱스](README.md)

## 스크립트

- `steps/step6_bug_creator.py`
- 테스트 실패 등에 따라 acli로 Jira 버그 티켓 생성 → `created_bugs.json`

## Claude Code

- 없음

## 선행 조건

- Step 4 결과(`test_results.json`)가 있어야 한다.

## 실패 0건일 때

- **자동화 실패가 없으면** Jira 버그를 **생성하지 않는다** (`created_bugs.json`은 `[]`).
- 스크립트는 그대로 **한 번 실행**해 두면 `bugs` 단계가 완료 처리되어 Step 7·8과 파이프라인 상태가 맞는다. (명령을 “안 돌린다”가 아니라, **돌려도 버그 티켓은 0건**인 셈.)

## 실행

```bash
python workflow_runner.py --ticket PA-21 --step bugs
```

Jira 연결 정보는 [common.md](common.md) 의 Jira Connection을 따른다.

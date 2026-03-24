# Step 8: 사이드이펙트 감지 (sideeffects)

[← 공통](common.md) · [인덱스](README.md)

## 스크립트

- `steps/step8_sideeffect_detector.py`
- 최근 7일 버그를 Jira에서 fetch
- **버그가 0건이 아닐 때도** `side_effects.md` 초안을 쓰고 `sideeffects` 단계를 완료 처리한다 (이전에는 버그가 있으면 산출물 없이 단계가 끊길 수 있었음).

## Claude Code

- 필요 시 초안을 보강하고, `append_testcases`로 테스트케이스 추가 반영

## 실행

```bash
python workflow_runner.py --ticket PA-21 --step sideeffects
```

## 일일 배치

- `workflow_runner.py --daily` 에 포함될 수 있다 ([common.md](common.md) 참고).

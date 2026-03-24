# Step 5: QA 결과서 (report)

[← 공통](common.md) · [인덱스](README.md)

## 스크립트

- `steps/step5_report_generator.py`
- `test_results.json` 로드 후 보고서 작성 안내

## Claude Code

- `output/{ticket}/qa_report.md` 를 직접 작성한다.

## 마스터 템플릿

- [`templates/qa_report.md`](../../templates/qa_report.md)

## 선행 조건

- Step 4 완료 (`test_results.json`)

## 실행

```bash
python workflow_runner.py --ticket PA-21 --step report
```

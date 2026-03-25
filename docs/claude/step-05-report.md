# Step 5: QA 결과서 (report)

[← 공통](common.md) · [인덱스](README.md)

## 스크립트

- `steps/step5_report_generator.py`
- `test_results.json`(+ 선택: `test_results_rerun.json`) 로드 후 `qa_report.md` 자동 생성

## Claude Code

- 없음 (스크립트가 `output/{ticket}/qa_report.md`를 자동 생성)

## 마스터 템플릿

- [`templates/qa_report.md`](../../templates/qa_report.md)

## 생성 내용

- **실패 요약 표에 TC 컬럼 포함**
- **히스토리 섹션 포함**
  - 8.1: 1차 실행(전체) 실패 원인 분석(초안)
  - 8.2: 2차 재테스트(실패 케이스만 1회) 결과 + 버그 등록 판단/근거

## 선행 조건

- Step 4 완료 (`test_results.json`)
- (권장) 실패 케이스만 1회 재실행 완료 (`test_results_rerun.json`)

## 실행

```bash
python workflow_runner.py --ticket PA-21 --step report
```

## 재생성 (권장)

이미 Step 5가 완료된 티켓이라도, 보고서를 다시 생성하려면:

```bash
python workflow_runner.py --ticket PA-21 --step report --from-step report
```

보고 일자를 고정하려면(선택):

```bash
QA_PIPELINE_REPORT_DATE=YYYY-MM-DD python workflow_runner.py --ticket PA-21 --step report --from-step report
```

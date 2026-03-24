# Step 7: 버그 트래킹 대시보드 (dashboard)

[← 공통](common.md) · [인덱스](README.md)

## 스크립트

- `steps/step7_dashboard.py`
- `generate_dashboard.py` 재사용 → 보통 `output/{ticket}/dashboard.html`

## Claude Code

- 없음

## 설정 (`config.yaml`)

- `dashboard.bug_summary_contains`: 예) `"멜론"` — Step 7이 `AND summary ~ "멜론"`을 붙이고, 상세 조회 후에도 제목에 해당 문자열이 있는 이슈만 남긴다. 다른 제품/전체 버그만 볼 때는 빈 문자열 또는 키 생략.
- `dashboard.bug_jql_suffix`: 고급용. 비어 있으면 위 키워드로 JQL 접미사를 자동 생성한다. 직접 JQL 조각을 쓸 때만 지정.

## 독립 실행 (기존 방식 유지)

```bash
python generate_dashboard.py

python generate_dashboard.py \
    --jql "project = PA AND issuetype = 버그 AND summary ~ \"멜론\""

python generate_dashboard.py \
    --qa-ticket CCS-5 --project "제품명" --version v2.0.0 \
    --period-start 2026-04-14 --period-end 2026-04-25
```

## 대시보드 스펙 (고정)

- 레이아웃·색·차트: [`templates/dashboard/dashboard_spec.md`](../../templates/dashboard/dashboard_spec.md)
- 구현·실행 안내: [`templates/dashboard/README.md`](../../templates/dashboard/README.md)

## 오케스트레이터

```bash
python workflow_runner.py --ticket PA-21 --step dashboard
```

이미 Step 7을 완료한 뒤 HTML만 다시 뽑을 때는 `--from-step dashboard`를 함께 쓴다.

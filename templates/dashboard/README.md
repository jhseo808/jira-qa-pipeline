# QA Bug Tracking Dashboard (템플릿 역할)

이 항목은 **HTML UI**가 아니라, 대시보드의 **고정 스펙**과 **구현 위치**를 한곳에 묶어 둔 것입니다.

- **생성 코드**: 저장소 루트의 `generate_dashboard.py`  
  - Jira(acli)에서 데이터를 가져와 HTML 파일을 출력합니다.
- **레이아웃·색·차트 구성**: [dashboard_spec.md](dashboard_spec.md)

Step 7 실행 시 산출물은 보통 `output/{ticket}/dashboard.html` 입니다.

`workflow_runner`로 돌릴 때는 루트 `config.yaml`의 `dashboard` 섹션(제목 필터 등)이 적용됩니다. 검증 기간·날짜별 누적 차트는 `generate_dashboard.py`가 `qa_plan.md`의 `총 검증 기간` 줄과 이슈 등록일을 조합해 축을 만든다.

### 독립 실행 예

```bash
python generate_dashboard.py
```

자세한 CLI 옵션은 `generate_dashboard.py` 상단 docstring을 참고합니다.

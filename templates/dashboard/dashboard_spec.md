# Dashboard 구성 스펙 (고정)

`generate_dashboard.py`가 생성하는 HTML이 따르는 **레이아웃·시각 규칙**입니다.  
코드 변경 시 이 문서와 불일치를 없애는 것을 권장합니다.

## 상단 카드

- 전체 건수
- 잔여 건수
- 해결 건수
- 해결률

## 심각도 칩

Critical / Major / Medium / Minor

## 차트

- 심각도 도넛
- 영역 스택 바
- 레이블 수평 바
- 누적 추이 라인
- 교차 바

## 디자인 토큰 (색상)

| 용도 | Hex |
|------|-----|
| Critical | `#ff4d6d` |
| Major | `#ff9f43` |
| Medium | `#54a0ff` |
| Minor | `#1dd1a1` |
| 해결 | `#26de81` |

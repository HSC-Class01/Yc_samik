# 🔗 대시보드 바로가기

[![Dashboard](https://img.shields.io/badge/DART_Dashboard-Live_View-2563eb?style=for-the-badge&logo=github)](https://hsc-class01.github.io/Yc_samik/)

> **삼익제약(014950) DART 자동 수집 · 재무분석 · GitHub Pages 대시보드**

## 1. 프로젝트 개요
DART Open API를 이용해 삼익제약의 정기보고서 재무정보를 자동 수집하고, 주요 재무제표 항목과 재무비율을 계산하여 GitHub Pages 대시보드로 제공합니다.

- 대상 기업: 삼익제약(014950)
- 보고서: 사업보고서 / 반기보고서 / 1분기보고서 / 3분기보고서
- 목표 수집기간: 2010년~현재
- OpenDART 재무정보 API 제공기간: **2015년 이후**
- 자동 업데이트: 매월 1일 00:00 UTC (한국시간 09:00)
- 데이터 원본: DART Open API
- 대시보드: GitHub Pages `/docs`

## 2. 분석 지표
### 성장
매출액, 매출증가율, 영업이익, 영업이익 증가율, 당기순이익, 당기순이익 증가율

### 수익성
매출총이익, 매출총이익률, 영업이익률, 순이익률, ROIC, ROE, ROA, EPS

### 현금흐름
영업활동현금흐름(CFO), CFO/순이익, CAPEX, FCF

### 재무안정성
총자산, 총부채, 자본, 부채비율, 순차입금, 순차입금/영업이익, 이자보상배율

### 운전자본
DSO, DIO, DPO, CCC

> 비율은 DART 공시 계정과목을 기반으로 계산합니다. ROIC·순차입금 등 일부 지표는 계정과목 가용성에 따라 `—`로 표시될 수 있습니다.

## 3. 데이터 구조
- `data/financial_data.json`: 분석용 통합 데이터
- `data/raw/YYYY/*.json`: 연도·보고서별 DART 원자료
- `docs/index.html`: GitHub Pages
- `docs/dashboard.js`: 시각화 및 표 렌더링
- `docs/data.json`: Pages에서 읽는 최신 분석자료
- `scripts/fetch_dart.py`: DART 수집·정규화·비율계산 agent
- `.github/workflows/update_data.yml`: 월간 자동화

## 4. 2010~2014년 데이터에 대한 주의
OpenDART의 정기보고서 재무정보 API는 공식적으로 **2015년 이후** 정보를 제공합니다. 따라서 2010~2014년은 API가 제공하지 않는 값을 추정하거나 임의 생성하지 않습니다. 해당 기간의 historical financial statements가 별도 확보되는 경우 `data/raw/legacy/`에 검증된 자료로 추가할 수 있도록 구조를 열어두었습니다.

## 5. 국내 Peer Firms

| 기업명 | 종목코드 | 비교 목적 |
|---|---:|---|
| **삼익제약** | 014950 | 기준기업 |
| 동구바이오제약 | 006620 | 피부과·비뇨기과 중심 전문의약품 |
| 신일제약 | 012790 | 국내 중소형 제약기업 비교군 |
| 진양제약 | 007370 | 제네릭·CMO 및 순환기·소화기·당뇨 관련 의약품 |

## 6. GitHub Actions 설정
Repository Secrets에 `DART_API_KEY`를 등록해야 합니다. 등록 후 **Actions → Monthly DART Financial Data Agent → Run workflow**로 최초 수집을 실행하면 이후 매월 1일 자동 실행됩니다.

## 7. Dashboard
[🔗 삼익제약 재무분석 대시보드](https://hsc-class01.github.io/Yc_samik/)

# 🌏 관광-환율 연관 분석 대시보드

한국관광공사의 관광 통계와 한국수출입은행 환율 정보를 기반으로  
**관광객 수와 환율 간의 상관관계**를 분석하고 시각화한 Streamlit 대시보드 프로젝트입니다.

---

# 📌 프로젝트 설명

본 프로젝트는 **관광(방한/출국) 데이터와 환율 데이터의 상관관계를 분석**하고,  
이를 Streamlit 기반 대시보드로 시각화하여 누구나 쉽게 확인할 수 있도록 만드는 것을 목표로 합니다.

---

# 🎯 프로젝트 주제

**관광객 수(출국∙방한)**와 **주요 국가 환율(USD, JPY, EUR, CNY)** 간의  
상관관계를 분석하고 대시보드 형태로 시각화

---

# 💡 주제 선택 이유

- 환율 변동은 해외여행 및 방한 관광에 직접적인 영향을 미치는 핵심 요인
- 팬데믹 이후 여행 수요 회복 흐름을 환율과 함께 분석하면 의미 있는 결과 도출 가능
- 실무형 데이터 분석 과정 전체를 경험하기 위한 적합한 주제
  - 데이터 수집 → 정제 & ETL → EDA → 분석 모델링 → 시각화
- 팀 단위 협업 프로젝트로 역할 분담 및 Git 기반 협업 경험 확보

---

# 📊 데이터 분석 내용

## 1) 데이터 수집

- **한국관광데이터랩** 월별 관광객 통계 (xls)

  https://datalab.visitkorea.or.kr/site/portal/ex/bbs/View.do?cbIdx=1127&bcIdx=309616&pageIndex=1&cateCont=spt04

- **관광지식정보시스템** 국적별 입국 월별 통계 (xls)

  https://know.tour.go.kr/stat/entryTourStatDis19Re.do

- **SMB 서울외환중개** 월평균 매매기준율 (xls)

  http://www.smbs.biz/ExRate/MonAvgStdExRate.jsp

## 2) 데이터 정제 & ETL

ETL 파이프라인을 구축하여 다음 작업 자동화:

- 결측치 처리
- 날짜 포맷 통일
- 국가명 정규화 (영문 매핑)
- 중복 컬럼 제거
- 월별 기준 리샘플링
- CSV → Parquet 변환

### 🔧 디렉토리 구조

```text
root/
├── app.py                  # Streamlit 메인 애플리케이션
├── utils.py                # 데이터 로더 및 공통 유틸리티
├── data/ ## 📂 Data Directory 설명
        자세한 내용은 아래 문서를 참고하세요:
```

➡ ️ [data/README.md](data/README.md)

```text
└── views/                  # 대시보드 페이지별 뷰 모듈
    ├── dashboard.py        # 메인 현황판
    ├── inbound.py          # 입국 분석
    ├── outbound.py         # 출국 분석
    ├── exchange.py         # 환율 분석
    └── correlation.py      # 상관관계 분석
```

## 3) 주요 분석 기능

### 🏠 메인 대시보드

- 최신 출입국 관광객 수 KPI
- USD / JPY / EUR / CNY 환율 표시
- 월별 출입국자 흐름 그래프

### 📈 환율–관광객 상관분석

- Pearson Correlation 계산
- 국가별 상관도 비교
- 관광객 수(막대) + 환율(선) 이중축 그래프

### 🛫 출국지별 분석

- 인천/김해/제주 등 공항/항만별 출국자 분석

### 🌏 방한 관광(인바운드) 분석

---

# 🎬 시연 동영상

📺 **[YouTube 시연 영상 보러가기](https://youtube.com/)**  
_(추후 실제 영상 업로드 예정)_

---

# 🌐 Streamlit 대시보드 URL

👉 **http://223.194.169.161:8501**

---

# 👥 팀원 소개

| 팀원       | 역할 | 담당                                    |
| ---------- | ---- | --------------------------------------- |
| **한준탁** | 팀장 | 데이터 수집, 대시보드 구성, GitHub 작성 |
| **신동수** | 팀원 | 데이터 분석, 전체 코드 정리             |
| **임성은** | 팀원 | 자료 조사, README 정리                  |
| **유건희** | 팀원 | 자료 조사, 대시보드 구성 보조           |

---

# 🧰 기술 스택

- **Python**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib
- **Framework**: Streamlit
- **API**: 한국수출입은행 환율 API (사용X)
- **Deployment**: Streamlit Cloud
- **Version Control**: Git / GitHub

---

## 🚀 프로젝트 실행 방법

<details>
<summary>**설치 및 실행 방법**</summary>
이 프로젝트는 Python 가상 환경(.venv)을 사용하며,  
아래 3단계만 그대로 실행하면 누구나 바로 구동할 수 있습니다.

---

# 1️⃣ 가상 환경 설정 및 라이브러리 설치

### ■ 1) 프로젝트 폴더 이동

cd Bigdata_HW

### ■ 2) 가상환경 생성 (필요한 경우)

python -m venv .venv

### ■ 3) 가상환경 활성화

Windows:
.venv\Scripts\activate

macOS / Linux:
source .venv/bin/activate

### ■ 4) 패키지 설치

pip install -r requirements.txt

---

# 2️⃣ 데이터 파이프라인 실행 (ETL)

원본 CSV/XLS 데이터를 자동으로 정제하여  
`cleaned_data/*.parquet` 파일을 생성합니다.

python data/main.py

**이 명령어 1번으로 다음이 모두 자동 수행됩니다:**

- Inbound/Outbound/Exchange 모듈 실행
- 컬럼명 정규화
- 월별로 환율 resample
- Parquet 파일 최종 저장

---

# 3️⃣ Streamlit 대시보드 실행

ETL이 완료되면 아래 명령어로 웹 대시보드를 실행합니다:

streamlit run app.py

브라우저 자동 실행 주소:
http://localhost:8501

---

## 📌 전체 실행 흐름 요약

(1) 가상환경 활성화  
(2) pip install -r requirements.txt  
(3) python data/main.py ← ETL 자동 처리  
(4) streamlit run app.py ← 대시보드 실행

</details>

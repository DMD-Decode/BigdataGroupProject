import pandas as pd
import streamlit as st
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import plotly.io as pio

# Plotly 기본 템플릿 설정 (전역 설정)
pio.templates.default = "plotly_white"


@st.cache_data(ttl=3600)  # 1시간 동안 메모리에 캐시 유지
def load_data():
    """
    Parquet 파일에서 데이터를 로드합니다. (CSV보다 10배 이상 빠름)
    """
    base_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "cleaned_data"
    )

    data = {}
    # 파일명 매핑 (.parquet 확장자 확인)
    files = {
        "inbound": "cleaned_inbound_tourism.parquet",
        "outbound": "cleaned_outbound_tourism.parquet",
        "exchange": "cleaned_exchange_rates.parquet",
    }

    for key, filename in files.items():
        path = os.path.join(base_path, filename)
        if os.path.exists(path):
            try:
                # Parquet 로드 (훨씬 빠름)
                data[key] = pd.read_parquet(path)
            except Exception as e:
                st.error(f"데이터 로드 오류: {e}")
                data[key] = pd.DataFrame()
        else:
            # Parquet 파일이 없으면 CSV로 폴백(Fallback) 시도
            csv_path = path.replace(".parquet", ".csv")
            if os.path.exists(csv_path):
                data[key] = pd.read_csv(csv_path, index_col="Date", parse_dates=True)
            else:
                st.warning(f"파일을 찾을 수 없습니다: {filename}")
                data[key] = pd.DataFrame()

    return data


@st.cache_resource  # 리소스(설정)는 이 데코레이터로 캐싱해야 함
def init_korean_font():
    """
    한글 폰트 설정을 캐싱하여 매번 실행되지 않도록 함
    """
    system_name = platform.system()
    font_path = None

    if system_name == "Windows":
        # 윈도우: 맑은 고딕
        font_name = "Malgun Gothic"
    elif system_name == "Darwin":
        # 맥: 애플고딕
        font_name = "AppleGothic"
    else:
        # 리눅스(Streamlit Cloud 등): 나눔고딕 설치 가정
        font_name = "NanumGothic"

    plt.rc("font", family=font_name)
    plt.rc("axes", unicode_minus=False)
    return font_name


def filter_date_range(df, start_date, end_date):
    if df.empty:
        return df
    # 인덱스가 날짜형인지 확인 후 슬라이싱
    return df.loc[start_date:end_date]

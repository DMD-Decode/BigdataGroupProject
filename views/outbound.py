# views/outbound.py
import streamlit as st
import plotly.express as px
import utils
import pandas as pd

# Matplotlib/Seaborn 관련 라이브러리 제거 (Plotly로 대체)
# import seaborn as sns
# import matplotlib.pyplot as plt


def show():
    st.title("🛫 출국 상세 분석 (Outbound Analysis)")

    data = utils.load_data()
    df_out = data["outbound"]

    if df_out.empty:
        st.error("출국 데이터가 없습니다.")
        return

    # --- 데이터 필터링 설정 ---
    st.sidebar.header("🔍 분석 필터")

    # 국가 목록 추출 (Total 제외)
    exclude_cols = ["Total Outbound"]
    country_options = [c for c in df_out.columns if c not in exclude_cols]

    selected_countries = st.sidebar.multiselect(
        "비교할 목적지 국가 선택 (최대 5개 권장)",
        options=country_options,
        default=["Japan", "United States", "Thailand", "Vietnam"],
    )

    min_date = df_out.index.min().date()
    max_date = df_out.index.max().date()
    start_date, end_date = st.sidebar.slider(
        "조회 기간", min_date, max_date, (min_date, max_date)
    )

    df_filtered = utils.filter_date_range(df_out, start_date, end_date)

    if not selected_countries:
        st.info("좌측 사이드바에서 국가를 선택해주세요.")
        return

    # --- 4가지 핵심 분석 섹션 ---

    # 1. 국가별 추이 비교 (시계열)
    st.subheader("1. 국가별 출국 추이 비교")
    fig_line = px.line(
        df_filtered,
        x=df_filtered.index,
        y=selected_countries,
        labels={"value": "출국자 수 (명)", "variable": "목적지", "Date": "날짜"},
        markers=True,
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # 2. 대륙별 점유율 & Top 10 국가
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("2. 대륙별 점유율")

        # 임시 대륙 합계 그룹핑 (Outbound 데이터는 국가만 있으므로 수동 그룹핑)
        continent_groups = {
            "아시아": [
                "Japan",
                "China",
                "Thailand",
                "Vietnam",
                "Philippines",
                "Hong Kong",
                "Taiwan",
                "Macau",
                "Singapore",
                "Malaysia",
                "Indonesia",
                "Cambodia",
                "Laos",
                "India",
                "Mongolia",
                "Myanmar",
                "Israel",
                "Maldives",
                "Sri Lanka",
                "Cyprus",
                "Bhutan",
                "Jordan",
                "Nepal",
                "Yemen",
                "Turkiye",
            ],
            "미주": [
                "United States",
                "Canada",
                "Brazil",
                "Mexico",
                "Chile",
                "Argentina",
                "Colombia",
                "Peru",
                "Venezuela",
                "Ecuador",
                "Cuba",
                "Dominican Republic",
                "Jamaica",
                "Guatemala",
                "Costa Rica",
                "Panama",
            ],
            "유럽": [
                "Germany",
                "UK",
                "France",
                "Italy",
                "Spain",
                "Russia",
                "Austria",
                "Slovenia",
                "Finland",
                "Slovakia",
                "Poland",
                "Denmark",
                "Greece",
                "Switzerland",
                "Norway",
                "Romania",
                "Belgium",
                "Bulgaria",
                "Ukraine",
            ],
            "대양주": [
                "Australia",
                "New Zealand",
                "Fiji",
                "Northern Mariana Islands",
                "Palau",
                "Guam",
            ],
            "아프리카": [
                "South Africa",
                "Mauritius",
                "Eswatini",
                "Seychelles",
                "Zimbabwe",
                "Uganda",
                "Sierra Leone",
                "Nigeria",
                "Egypt",
            ],
        }

        # 필터링된 데이터에서 유효한 국가만 포함하여 대륙별 합계 계산
        continent_shares = {}
        for continent, countries in continent_groups.items():
            valid_countries = [c for c in countries if c in df_filtered.columns]
            if valid_countries:
                continent_shares[continent] = (
                    df_filtered[valid_countries].sum(axis=1).mean()
                )

        avg_data = pd.Series(continent_shares).sort_values(ascending=False)

        fig_pie = px.pie(
            values=avg_data.values,
            names=avg_data.index,
            title="목적지 대륙별 출국자 평균 비중",
            hole=0.4,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader(f"3. 누적 출국자 Top 10")
        # 기간 내 합계 기준 정렬
        top_countries = (
            df_filtered[country_options].sum().sort_values(ascending=False).head(10)
        )

        fig_bar = px.bar(
            x=top_countries.values,
            y=top_countries.index,
            orientation="h",
            labels={"x": "누적 출국자 수", "y": "목적지"},
            color=top_countries.values,
            color_continuous_scale="Reds",
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_bar, use_container_width=True)

    # 4. 전년 대비 성장률 (YoY Heatmap) - Plotly로 변경
    st.subheader("4. 전년 대비 출국 성장률 (YoY Heatmap)")

    # YoY 계산 (전년 동월 대비 증감률)
    df_yoy = df_filtered[selected_countries].pct_change(periods=12) * 100
    df_heatmap = df_yoy.tail(12).transpose()

    # [Plotly] 히트맵 그리기
    if not df_heatmap.empty and not df_heatmap.isna().all().all():
        # 색상 범위 설정: 0을 중심으로 대칭되도록 최대 절대값 계산
        max_abs = df_heatmap.abs().max().max()
        if pd.isna(max_abs) or max_abs == 0:
            max_val = 1
        else:
            max_val = max_abs

        # Plotly Heatmap (다크 테마 및 깔끔한 레이블 적용)
        fig_heat = px.imshow(
            df_heatmap,
            x=df_heatmap.columns,
            y=df_heatmap.index,
            color_continuous_scale="RdBu",  # RdBu는 증가(파랑)/감소(빨강) -> RdBu_r은 증가(빨강)/감소(파랑)
            zmin=-max_val,
            zmax=max_val,
            aspect="auto",
            title="전년 동월 대비 출국자 성장률 (%)",
            labels=dict(color="YoY Growth (%)", x="기간", y="목적지"),
        )

        # 다크 테마 적용 및 레이아웃 조정
        fig_heat.update_layout(
            template="plotly_dark",
            height=400,  # 차트 크기 조정
            margin=dict(t=50, b=20, l=10, r=10),
            xaxis=dict(
                side="top", tickangle=45, tickfont=dict(size=10)
            ),  # X축을 위로 이동
            yaxis=dict(side="left"),
        )

        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption(
            "* 빨간색: 성장(증가), 파란색: 역성장(감소), 흰색: 변화 없음 (0% 중심)"
        )
    else:
        st.info("선택한 기간에 YoY 성장률을 계산할 수 있는 데이터가 부족합니다.")

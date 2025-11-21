import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import utils


def show():
    st.title("📊 메인 대시보드 (Main Overview)")
    st.markdown(
        "관광객 수와 환율 변동을 **사용자가 직접 선택하여 비교**할 수 있는 대시보드입니다."
    )

    # 데이터 로드
    data = utils.load_data()
    df_in = data["inbound"]
    df_out = data["outbound"]
    df_fx = data["exchange"]

    if df_in.empty:
        st.error("데이터 로드에 실패했습니다. data 폴더를 확인해주세요.")
        return

    # --- 1. 컨트롤 패널 (사이드바) ---
    st.sidebar.header("📅 기간 및 데이터 선택")

    # 날짜 범위 슬라이더
    min_date = df_in.index.min().date()
    max_date = df_in.index.max().date()

    start_date, end_date = st.sidebar.slider(
        "조회 기간 설정",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM",
    )

    # 데이터 필터링
    df_in_filtered = utils.filter_date_range(df_in, start_date, end_date)
    df_out_filtered = utils.filter_date_range(df_out, start_date, end_date)
    df_fx_filtered = utils.filter_date_range(df_fx, start_date, end_date)

    # --- 2. KPI Metrics (주요 지표) ---
    st.subheader(f"📌 주요 지표 요약 ({end_date.strftime('%Y-%m')} 기준)")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    # 최신 데이터 (필터링된 기간의 마지막 날짜 기준)
    try:
        last_in = df_in_filtered["Total"].iloc[-1]
        last_in_prev = df_in_filtered["Total"].iloc[-2]

        last_out = df_out_filtered["Total Outbound"].dropna().iloc[-1]
        last_out_prev = df_out_filtered["Total Outbound"].dropna().iloc[-2]

        last_usd = df_fx_filtered["USD"].iloc[-1]
        last_usd_prev = df_fx_filtered["USD"].iloc[-2]

        last_jpy = df_fx_filtered["JPY"].iloc[-1]
        last_jpy_prev = df_fx_filtered["JPY"].iloc[-2]

        kpi1.metric(
            "총 입국자 (Inbound)", f"{last_in:,.0f}명", f"{last_in - last_in_prev:,.0f}"
        )
        kpi2.metric(
            "총 출국자 (Outbound)",
            f"{last_out:,.0f}명",
            f"{last_out - last_out_prev:,.0f}",
        )
        kpi3.metric(
            "환율 (USD)", f"{last_usd:,.2f}원", f"{last_usd - last_usd_prev:,.2f}"
        )
        kpi4.metric(
            "환율 (JPY 100)", f"{last_jpy:,.2f}원", f"{last_jpy - last_jpy_prev:,.2f}"
        )
    except IndexError:
        st.warning("선택한 기간에 데이터가 충분하지 않습니다.")

    st.divider()

    # --- 3. 사용자 정의 통합 그래프 ---
    st.subheader("📈 통합 데이터 시각화 (Custom Chart)")

    # 그래프 선택 옵션
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("##### **보고 싶은 데이터 선택**")
        show_inbound = st.checkbox("입국자 수 (Total)", value=True)
        show_outbound = st.checkbox("출국자 수 (Total Outbound)", value=True)

        st.markdown("##### **환율 오버레이 (보조축)**")
        selected_fx = st.multiselect(
            "환율 선택", ["USD", "JPY", "EUR", "CNH"], default=["USD"]
        )

    with col2:
        # Plotly 이중축 차트 생성
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # 1) 관광객 데이터 (좌측 Y축 - Bar/Area)
        if show_inbound:
            fig.add_trace(
                go.Scatter(
                    x=df_in_filtered.index,
                    y=df_in_filtered["Total"],
                    name="입국 (Inbound)",
                    fill="tozeroy",
                    line=dict(color="#3498db", width=1),
                ),
                secondary_y=False,
            )

        if show_outbound:
            fig.add_trace(
                go.Scatter(
                    x=df_out_filtered.index,
                    y=df_out_filtered["Total Outbound"],
                    name="출국 (Outbound)",
                    line=dict(color="#e74c3c", width=3),
                ),
                secondary_y=False,
            )

        # 2) 환율 데이터 (우측 Y축 - Line)
        colors = {"USD": "green", "JPY": "orange", "EUR": "purple", "CNH": "brown"}
        for currency in selected_fx:
            fig.add_trace(
                go.Scatter(
                    x=df_fx_filtered.index,
                    y=df_fx_filtered[currency],
                    name=f"환율 ({currency})",
                    line=dict(color=colors.get(currency, "black"), dash="dot"),
                ),
                secondary_y=True,
            )

        # 레이아웃 설정
        fig.update_layout(
            title="관광객 및 환율 통합 추이",
            hovermode="x unified",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            height=500,
        )
        fig.update_yaxes(title_text="관광객 수 (명)", secondary_y=False, showgrid=False)
        fig.update_yaxes(title_text="환율 (원)", secondary_y=True, showgrid=False)

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- 4. [수정됨] 데이터 출처 및 참고 문헌 (페이지 맨 하단) ---
    st.markdown("## 📚 데이터 출처 및 참고 문헌")

    st.info(
        """
**📊 데이터 출처 (Data Sources)**

- **한국관광데이터랩** 월별 관광객 통계 (xls)
  [바로가기](https://datalab.visitkorea.or.kr/site/portal/ex/bbs/View.do?cbIdx=1127&bcIdx=309616&pageIndex=1&cateCont=spt04)

- **관광지식정보시스템** 국적별 입국 월별 통계 (xls)
  [바로가기](https://know.tour.go.kr/stat/entryTourStatDis19Re.do)

- **SMB 서울외환중개** 월평균 매매기준율 (xls)
  [바로가기](http://www.smbs.biz/ExRate/MonAvgStdExRate.jsp)
"""
    )

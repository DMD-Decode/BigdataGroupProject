# views/exchange.py
import streamlit as st
import plotly.express as px
import pandas as pd
import utils
from datetime import datetime, timedelta

# --- 🔍 환율 변동 심층 분석 데이터 ---
CURRENCY_EVENTS = {
    "USD": [
        {
            "period": "2008.09 ~ 2009.03",
            "title": "📉 글로벌 금융위기",
            "desc": "리먼 브라더스 사태로 안전자산(달러) 수요 폭증.",
        },
        {
            "period": "2014.06 ~ 2015.12",
            "title": "🏦 미 연준 테이퍼링",
            "desc": "양적완화 축소로 인한 슈퍼 달러 현상 재현.",
        },
        {
            "period": "2020.03",
            "title": "🦠 코로나19 초기 쇼크",
            "desc": "공포 심리로 인한 일시적 달러 확보 전쟁.",
        },
        {
            "period": "2022.01 ~ 2023.10",
            "title": "👑 킹달러 & 고금리",
            "desc": "미 연준의 공격적 금리 인상(자이언트 스텝).",
        },
    ],
    "JPY": [
        {
            "period": "2008 ~ 2011",
            "title": "🚀 슈퍼 엔고",
            "desc": "엔캐리 트레이드 청산으로 안전자산 엔화 급등.",
        },
        {
            "period": "2012.12 ~ 2015",
            "title": "📉 아베노믹스",
            "desc": "무제한 양적완화로 인위적 엔저 유도.",
        },
        {
            "period": "2022 ~ 2024",
            "title": "💸 역대급 슈퍼 엔저",
            "desc": "미-일 금리차 확대로 엔화 매도세 지속.",
        },
    ],
    "EUR": [
        {
            "period": "2010 ~ 2012",
            "title": "🇬🇷 유로존 재정위기",
            "desc": "남유럽 국가 부도 위기로 유로화 가치 급락.",
        },
        {
            "period": "2022",
            "title": "⚔️ 우크라이나 전쟁",
            "desc": "에너지 위기로 유로-달러 패리티 붕괴.",
        },
    ],
    "CNH": [
        {
            "period": "2015.08",
            "title": "📉 위안화 기습 절하",
            "desc": "경기 둔화 방어를 위한 인민은행의 인위적 절하.",
        },
        {
            "period": "2018 ~ 2019",
            "title": "🥊 미-중 무역전쟁",
            "desc": "관세 폭탄 방어를 위해 위안화 약세 용인.",
        },
        {
            "period": "2023 ~ 2024",
            "title": "🏗️ 부동산 위기",
            "desc": "내수 부진과 외국인 자본 이탈로 약세 지속.",
        },
    ],
}


def parse_period(period_str):
    """
    '2008.09 ~ 2009.03' 또는 '2022' 형식의 문자열을
    (start_date, end_date) 문자열 튜플로 변환
    """
    try:
        period_str = period_str.replace(" ", "")
        if "~" in period_str:
            start, end = period_str.split("~")
        else:
            start = period_str
            end = period_str

        # 포맷 정규화 (YYYY.MM -> YYYY-MM-01)
        def fmt(d):
            parts = d.split(".")
            if len(parts) == 1:
                return f"{parts[0]}-01-01", f"{parts[0]}-12-31"  # 연도만 있는 경우
            return f"{parts[0]}-{parts[1].zfill(2)}-01"

        start_date = fmt(start)
        if len(start.split(".")) == 1:  # 연도만 있는 경우 튜플 반환됨
            start_date, end_date = start_date
        else:
            start_date = fmt(start)
            # 종료일은 해당 월의 마지막 날 근처로 대략 설정 (다음달 1일)
            end_parts = end.split(".")
            if len(end_parts) == 2:
                y, m = int(end_parts[0]), int(end_parts[1])
                if m == 12:
                    end_date = f"{y+1}-01-01"
                else:
                    end_date = f"{y}-{str(m+1).zfill(2)}-01"
            else:
                end_date = fmt(end)

        return start_date, end_date
    except:
        return None, None


def show():
    st.title("💱 환율 상세 분석 (Exchange Rate Deep Dive)")
    utils.init_korean_font()

    # Session State 초기화 (강조할 기간 저장용)
    if "highlight_period" not in st.session_state:
        st.session_state["highlight_period"] = (
            None  # {'start': ..., 'end': ..., 'label': ...}
        )

    # 데이터 로드
    data = utils.load_data()
    df_fx = data["exchange"]

    if df_fx.empty:
        return

    # --- 1. 옵션 설정 ---
    st.sidebar.header("환율 분석 옵션")
    currencies = df_fx.columns.tolist()
    selected_currencies = st.sidebar.multiselect(
        "비교할 통화 선택", options=currencies, default=["USD", "JPY"]
    )

    min_date = df_fx.index.min().date()
    max_date = df_fx.index.max().date()
    start_date, end_date = st.sidebar.slider(
        "조회 기간", min_date, max_date, (min_date, max_date)
    )

    df_filtered = utils.filter_date_range(df_fx, start_date, end_date)

    if not selected_currencies:
        st.warning("통화를 선택해주세요.")
        return

    # --- 2. KPI ---
    st.subheader(f"📌 환율 요약 ({end_date.strftime('%Y-%m')})")
    cols = st.columns(len(selected_currencies))
    for i, currency in enumerate(selected_currencies):
        with cols[i % 4]:
            curr_val = df_filtered[currency].iloc[-1]
            prev_val = df_filtered[currency].iloc[-2]
            st.metric(
                label=currency,
                value=f"{curr_val:,.2f}원",
                delta=f"{curr_val - prev_val:+.2f}원",
            )

    # --- 3. 환율 추세 그래프 (하이라이트 기능 적용) ---
    st.subheader("📈 환율 변동 추세 및 주요 사건")

    # 하이라이트 초기화 버튼
    if st.session_state["highlight_period"]:
        if st.button("🔄 강조 해제 (Reset Chart)"):
            st.session_state["highlight_period"] = None
            st.rerun()

    tab1, tab2 = st.tabs(["절대값 추이", "변동률 비교 (Index=100)"])

    with tab1:
        fig_raw = px.line(
            df_filtered,
            y=selected_currencies,
            title="주요 통화 환율 추이",
            labels={"value": "환율(원)", "Date": "날짜"},
        )
        fig_raw.update_yaxes(autorange=True)

        # [핵심] 세션에 저장된 기간이 있으면 차트에 사각형 그리기
        hp = st.session_state["highlight_period"]
        if hp:
            fig_raw.add_vrect(
                x0=hp["start"],
                x1=hp["end"],
                fillcolor="red",
                opacity=0.15,
                layer="below",
                line_width=0,
                annotation_text=hp["label"],
                annotation_position="top left",
            )
        st.plotly_chart(fig_raw, use_container_width=True)

    with tab2:
        df_rebased = df_filtered[selected_currencies].apply(
            lambda x: x / x.iloc[0] * 100
        )
        fig_rebased = px.line(
            df_rebased, y=selected_currencies, title="통화별 가치 변동률 (시작일=100)"
        )
        fig_rebased.add_hline(y=100, line_dash="dot")

        # 변동률 차트에도 동일하게 적용
        if hp:
            fig_rebased.add_vrect(
                x0=hp["start"],
                x1=hp["end"],
                fillcolor="red",
                opacity=0.15,
                layer="below",
                line_width=0,
                annotation_text=hp["label"],
                annotation_position="top left",
            )
        st.plotly_chart(fig_rebased, use_container_width=True)

    st.divider()

    # --- 5. 통계 요약 ---
    st.subheader("📊 기간 내 통계")
    stats = df_filtered[selected_currencies].describe().T[["mean", "min", "max", "std"]]
    stats.columns = ["평균", "최저", "최고", "변동성"]
    st.dataframe(stats.style.format("{:,.2f}"), use_container_width=True)
    st.divider()
    # --- 4. 사건 기반 분석 (버튼 클릭 시 차트 강조) ---
    st.subheader("🧐 환율 변동 원인 (Click to Highlight)")
    st.markdown(
        "아래 사건의 **'📊 차트에서 보기'** 버튼을 누르면 해당 기간이 위 그래프에 강조됩니다."
    )

    for currency in selected_currencies:
        if currency in CURRENCY_EVENTS:
            with st.expander(f"📘 **{currency}** 주요 변동 이슈 리스트", expanded=True):
                for idx, event in enumerate(CURRENCY_EVENTS[currency]):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{event['period']} : {event['title']}**")
                        st.caption(event["desc"])
                    with c2:
                        # 버튼 클릭 시 세션 상태 업데이트 및 리런
                        if st.button("📊 강조", key=f"btn_{currency}_{idx}"):
                            s_date, e_date = parse_period(event["period"])
                            if s_date and e_date:
                                st.session_state["highlight_period"] = {
                                    "start": s_date,
                                    "end": e_date,
                                    "label": event["title"],
                                }
                                st.rerun()  # 앱 다시 실행하여 차트 업데이트
        else:
            st.info(f"{currency} 관련 데이터 없음")

    st.divider()

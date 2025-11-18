import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# (★추가★) 이중 축 차트 및 상관관계 계산을 위한 import
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np  # 상관관계 계산 시 NaN 값 처리용

# -------------------------------
# 1. 기본 설정
# -------------------------------
st.set_page_config(
    page_title="관광-환율 연관 분석 대시보드", page_icon="🌏", layout="wide"
)


# -------------------------------
# 2. (★추가★) 환율 API 함수
# -------------------------------
@st.cache_data(ttl=600)
def get_exchange_rates(api_key, search_date):
    url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
    params = {"authkey": api_key, "searchdate": search_date, "data": "AP01"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data or (isinstance(data, list) and data[0].get("result") in [3, 4]):
            return None
        return data
    except requests.exceptions.RequestException:
        return None
    except requests.exceptions.JSONDecodeError:
        return None


@st.cache_data(ttl=3600)
def get_historical_data(api_key, start_date, end_date):
    all_dfs = []
    current_date = datetime.combine(start_date, datetime.min.time())
    end_date_dt = datetime.combine(end_date, datetime.min.time())

    while current_date <= end_date_dt:
        date_str = current_date.strftime("%Y%m%d")
        raw_data = get_exchange_rates(api_key, date_str)
        if raw_data:
            df_daily = pd.DataFrame(raw_data)
            df_daily["date"] = pd.to_datetime(date_str)
            all_dfs.append(df_daily)
        current_date += timedelta(days=1)

    if not all_dfs:
        return pd.DataFrame()

    df_historical = pd.concat(all_dfs, ignore_index=True)
    cols_to_numeric = ["deal_bas_r", "tts", "ttb"]
    for col in cols_to_numeric:
        df_historical[col] = pd.to_numeric(
            df_historical[col].str.replace(",", ""), errors="coerce"
        )
    df_historical = df_historical.set_index("date")
    return df_historical


# -------------------------------
# 3. 관광 데이터 불러오기
# -------------------------------
@st.cache_data
def load_outbound():
    try:
        return pd.read_csv(
            "한국관광공사_국민 해외관광객 월별 상세 집계.csv", encoding="cp949"
        )
    except FileNotFoundError:
        st.error(
            "파일을 찾을 수 없습니다: '한국관광공사_국민 해외관광객 월별 상세 집계.csv'"
        )
        return pd.DataFrame()


@st.cache_data
def load_inbound():
    try:
        return pd.read_csv(
            "한국관광공사_방한 외래관광객 상세 월별 집계.csv", encoding="cp949"
        )
    except FileNotFoundError:
        st.error(
            "파일을 찾을 수 없습니다: '한국관광공사_방한 외래관광객 상세 월별 집계.csv'"
        )
        return pd.DataFrame()


out_df = load_outbound()
in_df = load_inbound()

# -------------------------------
# 4. 데이터 전처리
# -------------------------------
# 아웃바운드 (out_df) 전처리
if not out_df.empty:
    out_df["기준연월"] = pd.to_datetime(out_df["기준연월"])
    # '기준연월'을 제외한 모든 숫자 컬럼을 합산하여 총출국자수 계산
    numeric_cols = out_df.select_dtypes(include=np.number).columns
    out_df["총출국자수"] = out_df[numeric_cols].sum(axis=1)

# 인바운드 (in_df) 전처리
if not in_df.empty:
    in_df["기준연월"] = pd.to_datetime(in_df["기준연월"])
    in_df["인원수"] = pd.to_numeric(in_df["인원수"], errors="coerce")
    in_df = in_df.dropna(subset=["인원수"])

# -------------------------------
# 5. 사이드바 메뉴
# -------------------------------
st.sidebar.title("데이터 대시보드")
st.sidebar.markdown("---")

# (★추가★) API 키 관리
try:
    api_key = st.secrets.api_keys.exim_bank
except (AttributeError, KeyError):
    api_key = None

if not api_key:
    st.sidebar.header("🔑 API 키 설정")
    st.sidebar.warning("`.streamlit/secrets.toml`에 API 키가 없습니다.")
    api_key = st.sidebar.text_input(
        "수출입은행 API 키를 수동으로 입력하세요.", type="password"
    )
else:
    st.sidebar.success("API 키가 `secrets.toml`에서 로드되었습니다.")

st.sidebar.markdown("---")

# 메뉴 선택
menu_options = [
    "🏠 메인 대시보드",
    "📈 환율-관광객 연관 분석",
    "👨‍👩‍👧‍👦 성별·연령별 분석",
    "🛫 출국지별 분석",
    "🌏 방한관광(인바운드) 분석",
]
menu = st.sidebar.radio("📑 메뉴 선택", menu_options)

# -------------------------------
# 6. 메뉴별 화면 구현
# -------------------------------

# -------------------------------
# 1️⃣ 메인 대시보드
# -------------------------------
if menu == "🏠 메인 대시보드":
    st.title("🌏 국민·방한 관광 월별 통계 대시보드")
    st.markdown(
        "한국관광공사 공개데이터 및 수출입은행 환율 데이터를 기반으로 통계를 시각화합니다."
    )

    # 최근 월 기준 주요 지표 (관광)
    col1, col2 = st.columns(2)
    if not out_df.empty:
        latest_month = out_df["기준연월"].max()
        latest_out = out_df[out_df["기준연월"] == latest_month]["총출국자수"].sum()
        col1.metric("🛫 최근 월 해외 출국자 수", f"{latest_out:,.0f} 명")

    if not in_df.empty:
        latest_month_in = in_df["기준연월"].max()
        latest_in = in_df[in_df["기준연월"] == latest_month_in]["인원수"].sum()
        col2.metric("🌏 최근 월 방한 관광객 수", f"{latest_in:,.0f} 명")

    st.divider()

    # (★추가★) 최근 환율 정보
    st.subheader("📊 최근 주요 환율 (매매기준율)")
    if not api_key:
        st.warning("환율 정보를 보려면 사이드바에서 API 키를 입력하세요.")
    else:
        raw_data_today = None
        search_date_str = None
        for days_back in range(3):
            target_date = datetime.now() - timedelta(days=days_back)
            search_date_str = target_date.strftime("%Y%m%d")
            raw_data_today = get_exchange_rates(api_key, search_date_str)
            if raw_data_today:
                break

        if raw_data_today:
            df_today = pd.DataFrame(raw_data_today)
            df_today["deal_bas_r"] = pd.to_numeric(
                df_today["deal_bas_r"].str.replace(",", ""), errors="coerce"
            )
            target_currencies = ["USD", "JPY(100)", "EUR", "CNY"]
            cols = st.columns(len(target_currencies))
            metrics_data = {row["cur_unit"]: row for _, row in df_today.iterrows()}

            for i, unit in enumerate(target_currencies):
                if unit in metrics_data:
                    row = metrics_data[unit]
                    cols[i].metric(
                        label=f"{row['cur_nm']} ({row['cur_unit']})",
                        value=f"{row['deal_bas_r']:,.2f} KRW",
                        help=f"{search_date_str} 기준",
                    )
                else:
                    cols[i].metric(label=f"{unit} 환율", value="조회 불가")
        else:
            st.warning("최근 3일간의 환율 데이터를 가져오지 못했습니다.")

    st.divider()

    # 월별 추이 비교
    st.subheader("📈 월별 총 출입국자 비교 추이")
    if not out_df.empty and not in_df.empty:
        out_line = (
            out_df.groupby("기준연월")["총출국자수"]
            .sum()
            .reset_index(name="국민 해외여행")
        )
        in_line = (
            in_df.groupby("기준연월")["인원수"].sum().reset_index(name="방한 외래관광")
        )
        merged = pd.merge(out_line, in_line, on="기준연월", how="outer").sort_values(
            "기준연월"
        )

        # Melt_df for better plotly visualization
        melted_df = merged.melt(
            id_vars="기준연월", var_name="구분", value_name="관광객 수"
        )

        fig = px.line(
            melted_df,
            x="기준연월",
            y="관광객 수",
            color="구분",
            markers=True,
            title="월별 출국 vs 방한 관광객 비교",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("관광 데이터를 불러오지 못해 차트를 표시할 수 없습니다.")


# -------------------------------
# 2️⃣ (★신규★) 환율-관광객 연관 분석
# -------------------------------
elif menu == "📈 환율-관광객 연관 분석":
    st.title("📈 환율-관광객 연관 분석")
    st.markdown(
        """
    **환율 변동**이 **관광객 수(인바운드/아웃바운드)**에 미치는 영향을 분석합니다.
    - **알고리즘:** 두 변수(환율, 관광객 수) 간의 **피어슨 상관관계 계수(Pearson Correlation Coefficient)**를 계산합니다.
    - **데이터 처리:** 일별 환율 데이터는 **월별 평균**으로 집계하여 월별 관광객 데이터와 병합합니다.
    """
    )

    st.info(
        "⚠️ **데이터 한계**: 현재 로드된 CSV 파일에는 '국가별' 데이터가 없습니다. 따라서 **전체 관광객 수**와 선택한 환율 간의 관계를 분석합니다."
    )

    if not api_key:
        st.error("분석을 위해 사이드바에서 수출입은행 API 키를 입력해야 합니다.")
    elif out_df.empty or in_df.empty:
        st.error("관광 데이터 파일(CSV)을 찾을 수 없습니다.")
    else:
        # --- 1. 분석 옵션 선택 ---
        col1, col2 = st.columns(2)
        with col1:
            analysis_type = st.radio(
                "분석 대상 선택",
                ["🛫 국민 해외 관광 (Outbound)", "🌏 방한 외래 관광 (Inbound)"],
            )
        with col2:
            currency_options = ["USD", "JPY(100)", "EUR", "CNY"]
            currency = st.selectbox("비교할 환율 선택", currency_options)

        # 기간 설정 (관광 데이터의 최대/최소 날짜 기준)
        min_date = max(out_df["기준연월"].min(), in_df["기준연월"].min()).date()
        max_date = min(out_df["기준연월"].max(), in_df["기준연월"].max()).date()

        st.write(f"**분석 가능 기간:** `{min_date}` ~ `{max_date}`")

        start_date = st.date_input(
            "분석 시작일", value=min_date, min_value=min_date, max_value=max_date
        )
        end_date = st.date_input(
            "분석 종료일", value=max_date, min_value=start_date, max_value=max_date
        )

        # --- 2. 데이터 처리 (알고리즘) ---

        # 2-1. 관광객 데이터 (월별)
        if analysis_type == "🛫 국민 해외 관광 (Outbound)":
            df_tourism = out_df.groupby("기준연월")["총출국자수"].sum().reset_index()
            tourism_col = "총출국자수"
            tourism_name = "국민 해외 관광객"
        else:  # "🌏 방한 외래 관광 (Inbound)"
            df_tourism = in_df.groupby("기준연월")["인원수"].sum().reset_index()
            tourism_col = "인원수"
            tourism_name = "방한 외래 관광객"

        df_tourism["Month"] = df_tourism["기준연월"].dt.to_period("M")

        # 2-2. 환율 데이터 (일별 -> 월별 평균)
        df_fx_raw = get_historical_data(api_key, start_date, end_date)

        if df_fx_raw.empty:
            st.warning("선택한 기간의 환율 데이터를 가져오지 못했습니다.")
        else:
            df_fx_filtered = df_fx_raw[df_fx_raw["cur_unit"] == currency]

            # 'MS' = Month Start (매월 1일 기준)
            df_fx_monthly = (
                df_fx_filtered["deal_bas_r"].resample("MS").mean().reset_index()
            )
            df_fx_monthly["Month"] = df_fx_monthly["date"].dt.to_period("M")
            df_fx_monthly = df_fx_monthly.rename(
                columns={"deal_bas_r": f"{currency}_환율"}
            )

            # 2-3. 데이터 병합
            merged_df = pd.merge(df_tourism, df_fx_monthly, on="Month", how="inner")
            merged_df = merged_df.dropna()  # NaN 값 제거

            if merged_df.empty:
                st.error("데이터 병합에 실패했거나, 해당 기간에 데이터가 없습니다.")
            else:
                # --- 3. 상관관계 분석 (알고리즘) ---
                st.subheader(f"📊 {tourism_name} vs. {currency} 환율 상관관계 분석")

                # 피어슨 상관계수 계산
                correlation = merged_df[tourism_col].corr(merged_df[f"{currency}_환율"])

                # 상관관계 해석
                if correlation > 0.7:
                    corr_desc = "강한 양의 상관관계"
                elif correlation > 0.3:
                    corr_desc = "약한 양의 상관관계"
                elif correlation < -0.7:
                    corr_desc = "강한 음의 상관관계"
                elif correlation < -0.3:
                    corr_desc = "약한 음의 상관관계"
                else:
                    corr_desc = "상관관계 거의 없음"

                st.metric(f"피어슨 상관계수 (r)", f"{correlation:.4f}", f"{corr_desc}")

                if analysis_type == "🛫 국민 해외 관광 (Outbound)":
                    st.markdown(
                        f"- **해석:** {corr_desc} ({correlation:.4f})가 나타납니다. 일반적으로 {currency} 환율이 오르면(원화 가치 하락), 해외여행 경비가 비싸져 출국자 수가 **감소**하는 **음의 상관관계**가 예상됩니다."
                    )
                else:
                    st.markdown(
                        f"- **해석:** {corr_desc} ({correlation:.4f})가 나타납니다. 일반적으로 {currency} 환율이 오르면(원화 가치 하락), 외국인에게 한국 여행이 저렴해져 방한 관광객이 **증가**하는 **양의 상관관계**가 예상됩니다."
                    )

                # --- 4. 시각화 (이중 축 차트) ---
                fig = make_subplots(specs=[[{"secondary_y": True}]])

                # 관광객 수 (막대 차트)
                fig.add_trace(
                    go.Bar(
                        x=merged_df["기준연월"],
                        y=merged_df[tourism_col],
                        name=tourism_name,
                    ),
                    secondary_y=False,
                )

                # 환율 (선 차트)
                fig.add_trace(
                    go.Scatter(
                        x=merged_df["기준연월"],
                        y=merged_df[f"{currency}_환율"],
                        name=f"{currency} 환율 (월평균)",
                        mode="lines+markers",
                    ),
                    secondary_y=True,
                )

                # 차트 제목 및 축 레이블
                fig.update_layout(
                    title_text=f"월별 {tourism_name}과 {currency} 환율 변동 비교",
                    xaxis_title="기준연월",
                )
                fig.update_yaxes(
                    title_text=f"<b>{tourism_name}</b> (명)", secondary_y=False
                )
                fig.update_yaxes(
                    title_text=f"<b>{currency} 환율</b> (KRW)", secondary_y=True
                )

                st.plotly_chart(fig, use_container_width=True)


# -------------------------------
# 3️⃣ 성별·연령별 분석 (아웃바운드)
# -------------------------------
elif menu == "👨‍👩‍👧‍👦 성별·연령별 분석":
    st.title("👨‍👩‍👧‍👦 해외 출국자 - 성별·연령별 분석")
    if out_df.empty:
        st.warning("아웃바운드 관광 데이터를 불러오지 못했습니다.")
    else:
        try:
            gender = st.selectbox("성별 선택", ["남성", "여성"])
            age_groups = sorted(
                list(
                    set(
                        [
                            c.split("_")[1]
                            for c in out_df.columns
                            if c.startswith(gender)
                        ]
                    )
                )
            )
            if not age_groups:
                st.error(
                    "선택한 성별의 연령대 데이터를 찾을 수 없습니다. (CSV 컬럼명 확인 필요: '남성_20세이하_...')"
                )
            else:
                selected_age = st.selectbox("연령대 선택", age_groups)

                # 해당 성별/연령대에 속하는 모든 컬럼 (e.g., 남성_20세이하_일본, 남성_20세이하_미국...)
                age_cols = [
                    c
                    for c in out_df.columns
                    if c.startswith(f"{gender}_{selected_age}")
                ]
                if not age_cols:
                    st.error(
                        f"'{gender}_{selected_age}'로 시작하는 컬럼을 찾을 수 없습니다."
                    )
                else:
                    out_df[f"{gender}_{selected_age}_총합"] = out_df[age_cols].sum(
                        axis=1
                    )

                    st.subheader(f"📊 {gender} {selected_age} 출국자 월별 추이")
                    fig = px.line(
                        out_df,
                        x="기준연월",
                        y=f"{gender}_{selected_age}_총합",
                        markers=True,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # 히트맵
                    st.subheader("🔥 연도별 분포 Heatmap")
                    temp = out_df.copy()
                    temp["연도"] = out_df["기준연월"].dt.year
                    temp["월"] = out_df["기준연월"].dt.month
                    pivot = temp.pivot_table(
                        index="연도",
                        columns="월",
                        values=f"{gender}_{selected_age}_총합",
                        aggfunc="sum",
                    )

                    fig2, ax = plt.subplots(figsize=(10, 5))  # fig, ax 분리
                    sns.heatmap(
                        pivot,
                        annot=True,
                        fmt=",.0f",
                        annot_kws={"size": 8},
                        cmap="viridis",
                        linewidths=0.5,
                        cbar_kws={"label": "출국자 수"},
                        ax=ax,
                    )
                    ax.set_title(
                        f"{gender} {selected_age} 연도별 월별 출국자수 Heatmap",
                        fontsize=13,
                    )
                    ax.set_xlabel("월")
                    ax.set_ylabel("연도")
                    st.pyplot(fig2)

        except Exception as e:
            st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
            st.write(
                "CSV 컬럼명 형식이 예상과 다를 수 있습니다. (예: '남성_20세이하_일본')"
            )


# -------------------------------
# 4️⃣ 출국지별 분석
# -------------------------------
elif menu == "🛫 출국지별 분석":
    st.title("🛫 출국지별 출국자 분석")
    st.info("여기서 '출국지'는 인천공항, 김해공항 등 출국한 공항/항만입니다.")
    if out_df.empty:
        st.warning("아웃바운드 관광 데이터를 불러오지 못했습니다.")
    else:
        try:
            # '기준연월', '총출국자수' 및 성별/연령 컬럼 제외
            non_port_cols = ["기준연월", "총출국자수"] + [
                c
                for c in out_df.columns
                if c.startswith("남성_") or c.startswith("여성_")
            ]
            # 순수 출국지 컬럼명 추출
            ports = sorted(
                list(set(out_df.drop(columns=non_port_cols, errors="ignore").columns))
            )

            if not ports:
                st.error("출국지 데이터를 찾을 수 없습니다. (CSV 컬럼명 확인 필요)")
            else:
                selected_port = st.selectbox("출국지 선택", ports)

                fig = px.line(
                    out_df,
                    x="기준연월",
                    y=selected_port,
                    markers=True,
                    title=f"{selected_port} 출국자 추이",
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
            st.write("CSV 컬럼명 형식이 예상과 다를 수 있습니다.")


# -------------------------------
# 5️⃣ 방한관광(인바운드) 분석
# -------------------------------
elif menu == "🌏 방한관광(인바운드) 분석":
    st.title("🌏 방한 외래관광객 분석 (상세 필터)")
    if in_df.empty:
        st.warning("인바운드 관광 데이터를 불러오지 못했습니다.")
    else:
        # 필터 선택
        gender_list = sorted(in_df["성별"].unique())
        age_list = sorted(in_df["연령별"].unique())
        purpose_list = sorted(in_df["목적별"].unique())
        transport_list = sorted(in_df["교통수단별"].unique())

        col1, col2 = st.columns(2)
        with col1:
            sel_gender = st.selectbox("성별", gender_list)
            sel_purpose = st.selectbox("방문 목적", purpose_list)
        with col2:
            sel_age = st.selectbox("연령대", age_list)
            sel_transport = st.selectbox("교통수단", transport_list)

        filtered = (
            in_df.query(
                "성별 == @sel_gender and 연령별 == @sel_age and 목적별 == @sel_purpose and 교통수단별 == @sel_transport"
            )
            .groupby("기준연월", as_index=False)["인원수"]
            .sum()
        )

        st.subheader(
            f"📈 {sel_gender} · {sel_age} · {sel_purpose} · {sel_transport} 방한 관광객 추이"
        )

        if filtered.empty:
            st.warning("선택한 조건에 맞는 데이터가 없습니다.")
        else:
            fig_in = px.line(
                filtered,
                x="기준연월",
                y="인원수",
                markers=True,
                title=f"{sel_gender} {sel_age} {sel_purpose} ({sel_transport}) 월별 추이",
            )
            st.plotly_chart(fig_in, use_container_width=True)

        # 월별 총합 비교
        st.subheader("📊 전체 월별 총 방한 관광객 추이")
        total_in = in_df.groupby("기준연월", as_index=False)["인원수"].sum()
        fig_total = px.line(
            total_in,
            x="기준연월",
            y="인원수",
            markers=True,
            title="전체 월별 방한 관광객수 변화",
        )
        st.plotly_chart(fig_total, use_container_width=True)

# -------------------------------
# 7. (★신규★) 데이터 출처 및 API 정보
# -------------------------------
st.markdown("---")
st.subheader("🔗 데이터 출처 및 정보")
st.markdown(
    """
    **본 대시보드는 아래 공공 데이터를 기반으로 작성되었습니다.**

    ### 1. 관광객 통계 데이터
    * **출처:** 한국관광공사
    * **사용 파일:** `한국관광공사_국민 해외관광객 월별 상세 집계.csv`, `한국관광공사_방한 외래관광객 상세 월별 집계.csv`
    * **[한국관광 데이터랩 바로가기]** (https://datalab.visitkorea.or.kr/main/index.do)

    ### 2. 환율 데이터
    * **출처:** 기획재정부, e-나라지표 등 공공 통계 자료 (한국수출입은행 API 대체)
    * **사용 파일:** `환율_20251111161825.xlsx - 환율(e-나라지표).csv`, `기획재정부_환율_20250820.csv`
    * **이전 API 출처:** 한국수출입은행 환율 정보 Open API (https://www.koreaexim.go.kr/ir/HPHKIR020M01?apino=2&viewtype=C&searchselect=&searchword=)
    * **[e-나라지표 환율 통계 바로가기]** (https://www.index.go.kr/unity/potal/main/EachIndexPage.do?idx_cd=2749)
    """
)

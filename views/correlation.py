# views/correlation.py
import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import utils
import statsmodels.api as sm


def analyze_correlation(country_name, currency_name, r_in, r_out):
    """상관계수 값을 바탕으로 자동 분석 텍스트를 생성하는 함수"""

    # 1. 출국 (Outbound) 분석
    if pd.isna(r_out):
        out_stat = "⚠️ **분석 불가**"
        out_desc = "데이터 부족 또는 변동성 부족으로 상관계수를 계산할 수 없습니다."
    elif r_out <= -0.5:
        out_stat = "📉 **강한 음의 상관관계**"
        out_desc = f"환율이 오르면 {country_name} 여행객이 **확실하게 줄어드는** 경향이 있습니다. 환율 민감도가 높습니다."
    elif -0.5 < r_out <= -0.2:
        out_stat = "↘️ **약한 음의 상관관계**"
        out_desc = (
            f"환율이 오르면 {country_name} 여행객이 **다소 줄어드는** 경향이 보입니다."
        )
    elif r_out >= 0.5:
        out_stat = "📈 **강한 양의 상관관계 (특이)**"
        out_desc = f"환율이 올라도 {country_name} 여행객이 오히려 **증가**하는 특이한 패턴입니다. (여행 수요가 환율보다 다른 요인에 더 큼)"
    else:
        out_stat = "⏺️ **상관관계 없음**"
        out_desc = f"환율 변동이 {country_name} 여행 수요에 큰 영향을 미치지 않는 것으로 보입니다."

    # 2. 입국 (Inbound) 분석
    if pd.isna(r_in):
        in_stat = "⚠️ **분석 불가**"
        in_desc = "데이터 부족으로 상관계수를 계산할 수 없습니다."
    elif r_in >= 0.5:
        in_stat = "📈 **강한 양의 상관관계**"
        in_desc = f"환율 상승(원화 가치 하락) 시 {country_name} 관광객의 방한이 **뚜렷하게 증가**합니다. (가격 경쟁력 상승)"
    elif 0.2 <= r_in < 0.5:
        in_stat = "↗️ **약한 양의 상관관계**"
        in_desc = f"환율이 오르면 방한 관광객이 **소폭 증가**하는 경향이 있습니다."
    elif r_in <= -0.3:
        in_stat = "📉 **음의 상관관계 (특이)**"
        in_desc = f"환율 상승에도 불구하고 방한 관광객이 줄어드는 경향이 있습니다."
    else:
        in_stat = "⏺️ **상관관계 없음**"
        in_desc = "환율과 방한 관광객 수 사이에 뚜렷한 연관성이 없습니다."

    return out_stat, out_desc, in_stat, in_desc


def show():
    st.title("📈 통합 상관관계 분석 (Correlation Analysis)")
    utils.init_korean_font()

    # 1. 알고리즘 설명
    with st.expander("ℹ️ 분석 기준 및 알고리즘 설명 (Analysis Methodology)"):
        st.markdown(
            """
        ### 1. 피어슨 상관계수 (Pearson Correlation, $r$)
        - **+1**: 완벽한 양의 상관관계 (함께 증가)
        - **-1**: 완벽한 음의 상관관계 (반대로 움직임)
        - **0**: 관계 없음
        
        > **경제학적 해석:**
        > - **환율 상승 (▲)** ➔ 해외 여행 비용 증가 ➔ **출국자 감소 (▼)** (음의 상관관계 예상)
        > - **환율 상승 (▲)** ➔ 한국 여행 비용 절감 ➔ **입국자 증가 (▲)** (양의 상관관계 예상)
        """
        )

    data = utils.load_data()
    df_in = data["inbound"]
    df_out = data["outbound"]
    df_fx = data["exchange"]

    merged_df = pd.concat(
        [
            df_in[["Total"]].rename(columns={"Total": "총 입국자 수"}),
            df_out[["Total Outbound"]].rename(
                columns={"Total Outbound": "총 출국자 수"}
            ),
            df_fx,
        ],
        axis=1,
    ).dropna()

    st.divider()

    # --- 2. 주요 3개국 심층 비교 분석 ---
    st.subheader("🏆 주요 3개국(미·일·중) 환율 민감도 비교 분석")

    countries = {"United States": "USD", "Japan": "JPY", "China": "CNH"}
    summary_data = []

    for country, currency in countries.items():
        # 데이터 병합 (결측치 제거 전)
        temp_df_raw = pd.concat(
            [
                df_in[country].rename("Inbound"),
                df_out[country].rename("Outbound"),
                df_fx[currency].rename("Rate"),
            ],
            axis=1,
        )

        # 결측치 제거 (상관관계 계산용)
        temp_df = temp_df_raw.dropna()

        if not temp_df.empty:
            corr_in = temp_df["Rate"].corr(temp_df["Inbound"])
            corr_out = temp_df["Rate"].corr(temp_df["Outbound"])
            out_stat, out_desc, in_stat, in_desc = analyze_correlation(
                country, currency, corr_in, corr_out
            )

            summary_data.append(
                {
                    "국가": country,
                    "통화": currency,
                    "출국-환율 상관계수": corr_out,
                    "출국 분석": out_stat,
                    "출국 상세": out_desc,
                    "입국-환율 상관계수": corr_in,
                    "입국 분석": in_stat,
                    "입국 상세": in_desc,
                }
            )

    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(
            summary_df[
                [
                    "국가",
                    "통화",
                    "출국-환율 상관계수",
                    "출국 분석",
                    "입국-환율 상관계수",
                    "입국 분석",
                ]
            ]
            .style.format(
                {"출국-환율 상관계수": "{:.3f}", "입국-환율 상관계수": "{:.3f}"},
                na_rep="N/A",
            )
            .background_gradient(
                cmap="coolwarm",
                subset=["출국-환율 상관계수", "입국-환율 상관계수"],
                vmin=-1,
                vmax=1,
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### 📝 국가별 상세 분석 리포트")
        tabs = st.tabs([f"🇺🇸 미국 (USD)", f"🇯🇵 일본 (JPY)", f"🇨🇳 중국 (CNH)"])

        for i, row in enumerate(summary_data):
            with tabs[i]:
                country_name = row["국가"]
                currency_name = row["통화"]

                # [추가됨] 중국 데이터 이슈 안내
                if country_name == "China":
                    st.warning(
                        """
                    📢 **데이터 주의 (Data Notice):** 중국행 출국자 통계는 중국 정부의 통계 발표 정책 변화(2020년 이후) 및 집계 중단으로 인해 
                    **상당 기간 데이터가 누락(NaN)되거나 0으로 집계**된 구간이 존재합니다.
                    이로 인해 상관계수가 왜곡되거나 낮게 나타날 수 있습니다.
                    """
                    )

                # 해당 국가의 데이터 다시 추출 (그래프용)
                temp_df = pd.concat(
                    [
                        df_in[country_name].rename("Inbound"),
                        df_out[country_name].rename("Outbound"),
                        df_fx[currency_name].rename("Rate"),
                    ],
                    axis=1,
                ).dropna()

                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"🛫 **출국 (한국인 ➔ {country_name})**")

                    if pd.isna(row["출국-환율 상관계수"]):
                        st.write("**상관계수:** 계산 불가")
                    else:
                        st.write(f"**상관계수:** {row['출국-환율 상관계수']:.3f}")

                    st.markdown(f"**결론:** {row['출국 상세']}")

                    # 국가별 그래프 (출국)
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(
                        go.Scatter(
                            x=temp_df.index,
                            y=temp_df["Outbound"],
                            name="출국자",
                            line=dict(color="#e74c3c"),
                        ),
                        secondary_y=False,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=temp_df.index,
                            y=temp_df["Rate"],
                            name=f"환율({currency_name})",
                            line=dict(color="#2ecc71", dash="dot"),
                        ),
                        secondary_y=True,
                    )
                    fig.update_layout(
                        title=f"{country_name} 출국자 vs 환율",
                        height=300,
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="h", y=1.1),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with c2:
                    st.success(f"🛬 **입국 ({country_name} ➔ 한국)**")

                    if pd.isna(row["입국-환율 상관계수"]):
                        st.write("**상관계수:** 계산 불가")
                    else:
                        st.write(f"**상관계수:** {row['입국-환율 상관계수']:.3f}")

                    st.markdown(f"**결론:** {row['입국 상세']}")

                    # 국가별 그래프 (입국)
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    fig.add_trace(
                        go.Scatter(
                            x=temp_df.index,
                            y=temp_df["Inbound"],
                            name="입국자",
                            line=dict(color="#3498db"),
                        ),
                        secondary_y=False,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=temp_df.index,
                            y=temp_df["Rate"],
                            name=f"환율({currency_name})",
                            line=dict(color="#2ecc71", dash="dot"),
                        ),
                        secondary_y=True,
                    )
                    fig.update_layout(
                        title=f"{country_name} 입국자 vs 환율",
                        height=300,
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="h", y=1.1),
                    )
                    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- 3. 사용자 자유 선택형 상세 분석 ---
    st.subheader("🔍 사용자 자유 선택 분석 (히트맵 & 산점도)")
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.markdown("##### 🔥 전체 지표 상관관계 (Heatmap)")
        fig_heatmap, ax = plt.subplots(figsize=(8, 8))
        sns.heatmap(
            merged_df.corr(),
            annot=True,
            cmap="coolwarm",
            fmt=".2f",
            linewidths=0.5,
            ax=ax,
            cbar=False,
        )
        st.pyplot(fig_heatmap)
        st.caption("※ 빨간색: 정비례, 파란색: 반비례 관계")

    with col_right:
        st.markdown("##### 🔍 변수 간 상세 관계 (Scatter Plot)")
        cols = merged_df.columns.tolist()

        c1, c2 = st.columns(2)
        with c1:
            x_axis = st.selectbox(
                "X축 (원인)", cols, index=cols.index("USD") if "USD" in cols else 0
            )
        with c2:
            y_axis = st.selectbox(
                "Y축 (결과)",
                cols,
                index=cols.index("총 출국자 수") if "총 출국자 수" in cols else 1,
            )

        if x_axis == y_axis:
            st.warning("⚠️ 서로 다른 변수를 선택해주세요.")
        else:
            fig_scatter = px.scatter(
                merged_df,
                x=x_axis,
                y=y_axis,
                trendline="ols",
                hover_data=[merged_df.index],
                opacity=0.6,
                title=f"{x_axis} vs {y_axis}",
                labels={x_axis: f"{x_axis} (값)", y_axis: f"{y_axis} (값)"},
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

            try:
                results = px.get_trendline_results(fig_scatter)
                model = results.px_fit_results.iloc[0]
                r_val = merged_df[x_axis].corr(merged_df[y_axis])
                p_val = model.pvalues[1]

                msg = "유의함 ✅" if p_val < 0.05 else "유의하지 않음 ❌"
                st.info(
                    f"📊 **통계 요약:** 상관계수 **{r_val:.3f}** / P-value **{p_val:.4f}** ({msg})"
                )
            except:
                pass

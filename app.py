import streamlit as st
from views import dashboard, inbound, outbound, correlation, exchange

# 페이지 기본 설정 (가장 먼저 실행되어야 함)
st.set_page_config(
    page_title="여행과 환율 분석 대시보드",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 스타일 커스텀 (선택 사항)
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    # 사이드바 네비게이션
    with st.sidebar:
        st.title("🧭 Navigation")

        # [수정] 메뉴 항목에 이모티콘 추가
        menu = st.radio(
            "분석 메뉴 선택",
            [
                "🏠 1. 메인 대시보드",
                "🛬 2. 입국 상세 분석",
                "🛫 3. 출국 상세 분석",
                "💱 4. 환율 상세 분석",
                "🔗 5. 통합 상관관계 분석",
            ],
        )

        st.markdown("---")
        st.info("데이터 출처 및 참고 문헌은 '메인 대시보드' 섹션을 확인해 주세요.")

    # 페이지 라우팅
    if "메인" in menu:
        dashboard.show()
    elif "입국" in menu:
        inbound.show()
    elif "출국" in menu:
        outbound.show()
    elif "환율" in menu:
        exchange.show()
    elif "통합" in menu:
        correlation.show()


if __name__ == "__main__":
    main()

# data/main.py
import os
import sys
import pandas as pd
import numpy as np  # 추가: NaN 처리를 위해 필요

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processors import inbound, outbound, exchange, common


def convert_to_parquet():
    """
    최종 생성된 CSV 파일들을 Parquet 포맷으로 변환합니다. (속도 최적화)
    """
    print("-" * 60)
    print("🔄 [Optimization] CSV -> Parquet 변환 시작...")

    files = {
        "inbound": "cleaned_inbound_tourism.csv",
        "outbound": "cleaned_outbound_tourism.csv",
        "exchange": "cleaned_exchange_rates.csv",
    }

    for key, filename in files.items():
        csv_path = os.path.join(common.CLEAN_DIR, filename)
        parquet_path = csv_path.replace(".csv", ".parquet")

        if os.path.exists(csv_path):
            try:
                # CSV 읽기
                df = pd.read_csv(csv_path, index_col="Date", parse_dates=True)

                # Outbound 데이터의 경우, 0값을 NaN으로 치환 (여기서 한 번 더 확실하게 처리)
                if key == "outbound" and "Total Outbound" in df.columns:
                    # Total Outbound가 0인 행은 전체가 미래 데이터일 가능성이 높음
                    mask = df["Total Outbound"] == 0
                    df.loc[mask, :] = np.nan
                    # 모든 컬럼이 NaN인 행 제거 (완전한 미래 데이터 삭제)
                    df.dropna(how="all", inplace=True)

                # Parquet 저장 (snappy 압축 사용 - 빠르고 용량 작음)
                df.to_parquet(parquet_path, engine="pyarrow", compression="snappy")
                print(f"  ✅ 변환 완료: {filename} -> {os.path.basename(parquet_path)}")
            except Exception as e:
                print(f"  ❌ 변환 실패 ({filename}): {e}")
        else:
            print(f"  ⚠️ 파일 없음 (Skipping): {filename}")


def main():
    print("🚀 [BIGDATA_HW Data Pipeline] 데이터 팩토리를 가동합니다...")

    # 0. 폴더 생성 (안전장치)
    os.makedirs(common.CLEAN_DIR, exist_ok=True)

    # 1. 데이터별 프로세서 실행 (CSV 생성)
    print("-" * 60)
    inbound.process()

    print("-" * 60)
    outbound.process()

    print("-" * 60)
    exchange.process()

    # 2. Parquet 변환 (속도 최적화 단계 추가)
    convert_to_parquet()

    print("-" * 60)
    print(f"🏁 모든 작업 완료! 결과물: {common.CLEAN_DIR}")


if __name__ == "__main__":
    main()

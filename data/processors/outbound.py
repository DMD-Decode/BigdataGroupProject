# data/processors/outbound.py
import pandas as pd
import glob
import os
import re
import numpy as np
from . import common


def process():
    search_path = os.path.join(common.RAW_OUTBOUND_DIR, "*.csv")
    files = glob.glob(search_path)

    if not files:
        print(f"⚠️ [Outbound] 파일이 없습니다: {common.RAW_OUTBOUND_DIR}")
        return

    print(f"🔄 [Outbound] {len(files)}개 파일 처리 중...")
    all_dfs = []

    for file in files:
        try:
            try:
                df_raw = pd.read_csv(file, encoding="utf-8-sig", header=None)
            except:
                df_raw = pd.read_csv(file, encoding="cp949", header=None)

            # 1. '명수' 행(Header Row) 찾기 (좌표 기반 추출을 위해)
            header_idx = -1
            for i, row in df_raw.iterrows():
                row_str = " ".join(row.astype(str).values)
                if "명수" in row_str:
                    header_idx = i
                    break

            if header_idx == -1:
                print(f"  ⏩ Skip (No Data): {os.path.basename(file)}")
                continue

            # 2. 메타데이터 행 확보
            metric_row = df_raw.iloc[header_idx]
            country_row = df_raw.iloc[header_idx - 1]  # 명수 바로 윗줄이 국가명

            # 3. 데이터 영역 확보
            data_part = df_raw.iloc[header_idx + 1 :].copy()

            # 4. 날짜 파싱 (0열:년, 1열:월)
            # Series로 확실하게 변환 후 스트링 처리
            year_series = (
                data_part.iloc[:, 0].astype(str).str.replace(r"\D", "", regex=True)
            )
            year_series = year_series.replace("", pd.NA).ffill()

            month_series = (
                data_part.iloc[:, 1]
                .astype(str)
                .str.replace(r"\D", "", regex=True)
                .str.zfill(2)
            )

            # 유효 날짜 마스크 생성
            valid_months = [str(i).zfill(2) for i in range(1, 13)]
            valid_mask = (year_series.str.len() == 4) & (
                month_series.isin(valid_months)
            )

            if not valid_mask.any():
                continue

            # 날짜 인덱스 생성
            dates = pd.to_datetime(
                year_series[valid_mask] + "-" + month_series[valid_mask] + "-01",
                errors="coerce",
            )

            # 5. 데이터 추출 (좌표 기반)
            # '명수'가 적힌 컬럼 인덱스들을 찾음
            count_cols_indices = [
                i for i, val in enumerate(metric_row) if "명수" in str(val)
            ]

            extracted_data = {}

            for col_idx in count_cols_indices:
                raw_country = str(country_row.iloc[col_idx]).strip()
                clean_country_key = raw_country.replace(" ", "")  # 공백 제거

                # 매핑 (공백 제거된 키 사용)
                if clean_country_key in ["nan", "None", ""]:
                    continue
                mapped_country = common.COUNTRY_MAP.get(
                    clean_country_key, clean_country_key
                )

                # 값 추출
                vals = data_part.iloc[:, col_idx][valid_mask].astype(str)
                vals = vals.str.replace(",", "").str.replace("-", "0")
                vals = pd.to_numeric(vals, errors="coerce").fillna(0)

                extracted_data[mapped_country] = vals.values

            if extracted_data:
                df_clean = pd.DataFrame(extracted_data, index=dates)
                df_clean.index.name = "Date"
                # 중복 날짜 제거
                df_clean = df_clean.groupby(df_clean.index).last()
                all_dfs.append(df_clean)

        except Exception as e:
            print(f"❌ [Outbound] Error {os.path.basename(file)}: {e}")

    if all_dfs:
        final_df = pd.concat(all_dfs, axis=1)
        final_df = final_df.loc[:, ~final_df.columns.duplicated()]

        # 최종 정리: 한글 컬럼 제거
        final_df.columns = final_df.columns.astype(str)
        final_df = final_df.loc[:, ~final_df.columns.str.contains(r"[가-힣]", na=False)]

        # 0만 있는 미래 데이터 NaN 처리 (선택사항, 시각화 품질 위해 추천)
        # 'Total Outbound'가 있으면 그걸 기준으로, 없으면 전체 0인 행
        if "Total Outbound" in final_df.columns:
            mask = final_df["Total Outbound"] == 0
            final_df.loc[mask, :] = np.nan

        final_df = final_df.dropna(how="all")  # 전체가 NaN인 행 제거
        final_df.sort_index(inplace=True)

        save_path = os.path.join(common.CLEAN_DIR, "cleaned_outbound_tourism.csv")
        final_df.to_csv(save_path, encoding="utf-8-sig")
        print(" ✅ [Outbound] 완료")
    else:
        print("⚠️ [Outbound] 결과 데이터가 없습니다.")

# data/processors/inbound.py
import pandas as pd
import glob
import os
import re
from . import common


def process():
    search_path = os.path.join(common.RAW_INBOUND_DIR, "*.csv")
    files = glob.glob(search_path)

    if not files:
        print(f"⚠️ [Inbound] 파일이 없습니다: {common.RAW_INBOUND_DIR}")
        return

    print(f"🔄 [Inbound] {len(files)}개 파일 처리 중...")
    all_dfs = []

    for file in files:
        try:
            try:
                df_raw = pd.read_csv(file, encoding="cp949", header=None)
            except:
                df_raw = pd.read_csv(file, encoding="utf-8-sig", header=None)

            # 1. 헤더 찾기
            header_idx = -1
            for i, row in df_raw.iterrows():
                if "국적" in " ".join(row.astype(str).values):
                    header_idx = i
                    break
            if header_idx == -1:
                continue

            df = df_raw.iloc[header_idx:].copy()
            df.columns = df.iloc[0]
            df = df.iloc[1:]

            # 인덱스 설정
            country_col = next(
                (c for c in df.columns if "국적" in str(c)), df.columns[0]
            )
            df = df.set_index(country_col)

            # 2. Transpose
            df_t = df.T

            # 3. 날짜 파싱
            idx_series = df_t.index.astype(str).to_series()
            # "YYYY년 M월" 또는 숫자형태 추출
            date_matches = idx_series.str.extract(r"(\d{4})[^\d]*(\d{1,2})")

            valid_indices = date_matches.dropna(subset=[0, 1]).index
            df_t = df_t.loc[valid_indices].copy()
            date_matches = date_matches.loc[valid_indices]

            years = date_matches[0]
            months = date_matches[1].str.zfill(2)
            df_t.index = pd.to_datetime(years + "-" + months + "-01", errors="coerce")
            df_t.index.name = "Date"

            # 4. 컬럼 정제 및 영문 매핑
            column_rename_map = {}
            columns_to_drop = []

            for col in df_t.columns:
                k_name = str(col).strip()
                k_name_clean = k_name.replace(" ", "")  # 공백 제거

                # 삭제 조건
                if k_name_clean in [
                    "nan",
                    "0.0",
                    "성별",
                    "전년동기",
                    "성장률",
                    "구성비",
                    "인원(명)",
                ]:
                    columns_to_drop.append(col)
                    continue

                # 매핑 (공백 제거된 키로 검색)
                e_name = common.COUNTRY_MAP.get(k_name_clean, k_name_clean)
                column_rename_map[col] = e_name

            df_t = df_t.drop(columns=columns_to_drop, errors="ignore").rename(
                columns=column_rename_map
            )

            # 5. 숫자 변환
            for col in df_t.columns:
                df_t[col] = pd.to_numeric(
                    df_t[col].astype(str).str.replace(",", "").str.replace("-", "0"),
                    errors="coerce",
                ).fillna(0)

            all_dfs.append(df_t)
        except Exception as e:
            print(f"❌ [Inbound] Error {os.path.basename(file)}: {e}")

    if all_dfs:
        final_df = pd.concat(all_dfs).sort_index()
        final_df = final_df[~final_df.index.duplicated(keep="last")]

        # 최종적으로 한글이 포함된 컬럼 제거 (매핑 안 된 잔여물)
        final_df.columns = final_df.columns.astype(str)
        final_df = final_df.loc[:, ~final_df.columns.str.contains(r"[가-힣]", na=False)]

        # nan 컬럼 제거
        final_df = final_df.loc[:, ~final_df.columns.str.lower().isin(["nan", "none"])]

        save_path = os.path.join(common.CLEAN_DIR, "cleaned_inbound_tourism.csv")
        final_df.to_csv(save_path, encoding="utf-8-sig")
        print(" ✅ [Inbound] 완료")
    else:
        print("⚠️ [Inbound] 결과 데이터가 없습니다.")

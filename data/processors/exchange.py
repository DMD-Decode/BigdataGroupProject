import pandas as pd
import glob
import os
import re
from . import common


def process():
    search_path = os.path.join(common.RAW_EXCHANGE_DIR, "*.csv")
    files = glob.glob(search_path)

    if not files:
        print(f"⚠️ [Exchange] 파일이 없습니다: {common.RAW_EXCHANGE_DIR}")
        return

    print(f"🔄 [Exchange] {len(files)}개 파일 처리 중...")
    final_df = pd.DataFrame()

    # 날짜 패턴: 20xx.xx 또는 20xx/xx 또는 20xx-xx
    date_pattern = re.compile(r"20\d{2}[\.\-/]\d{1,2}")

    for file in files:
        try:
            # 통화 코드 추출
            filename = os.path.basename(file).upper()
            currency = "UNKNOWN"
            for code in ["USD", "JPY", "EUR", "CNH", "GBP"]:
                if code in filename:
                    currency = code
                    break
            if currency == "UNKNOWN":
                continue

            try:
                df = pd.read_csv(file, encoding="utf-8-sig", header=None)
            except:
                df = pd.read_csv(file, encoding="cp949", header=None)

            # 데이터 시작 행 찾기 (수정된 부분)
            start_row = -1
            for i, row in df.iterrows():
                # 첫 번째 열이 날짜 형태인지 확인
                val = str(row[0]).strip()
                if date_pattern.match(val):
                    start_row = i
                    break

            if start_row == -1:
                print(f"⚠️ [Exchange] 날짜 패턴을 찾을 수 없음: {filename}")
                continue

            # 데이터 정제
            data = df.iloc[start_row:].copy()
            # 날짜 포맷 통일 (2014/03 -> 2014-03-01)
            dates = data[0].astype(str).str.replace(".", "-").str.replace("/", "-")
            dates = dates.apply(lambda x: x + "-01" if len(x) <= 7 else x)

            data.index = pd.to_datetime(dates, errors="coerce")
            data.index.name = "Date"
            data = data[~data.index.isna()]  # 유효하지 않은 날짜 제거

            # 마지막 컬럼을 환율 값으로 가정
            vals = pd.to_numeric(
                data.iloc[:, -1].astype(str).str.replace(",", ""), errors="coerce"
            )

            # 월 단위로 리샘플링 (일별 데이터일 경우 대비)
            vals = vals.resample("MS").mean()

            temp_df = pd.DataFrame({currency: vals})

            if final_df.empty:
                final_df = temp_df
            else:
                final_df = final_df.join(temp_df, how="outer")

        except Exception as e:
            print(f"❌ [Exchange] Error {os.path.basename(file)}: {e}")

    if not final_df.empty:
        final_df.sort_index().to_csv(
            os.path.join(common.CLEAN_DIR, "cleaned_exchange_rates.csv"),
            encoding="utf-8-sig",
        )
        print(" ✅ [Exchange] 완료")
    else:
        print("⚠️ [Exchange] 결과 데이터가 없습니다.")

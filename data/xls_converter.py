# data/xls_converter.py
import pandas as pd
import glob
import os
import warnings
from processors import common

warnings.filterwarnings("ignore")


def run():
    print(f"\n[2/3] 🔄 Excel -> CSV 포맷 변환 시작 (Target: {common.RAW_ROOT})...")

    # original_data 폴더 하위의 모든 xls, xlsx 탐색 (recursive=True)
    extensions = ["*.xls", "*.xlsx"]
    files = []
    for ext in extensions:
        files.extend(
            glob.glob(os.path.join(common.RAW_ROOT, "**", ext), recursive=True)
        )

    if not files:
        print("  ℹ️ 변환할 Excel 파일이 없습니다.")
        return

    count = 0
    for file in files:
        try:
            # 변환된 파일명 (.xls -> .csv)
            base_name = os.path.splitext(file)[0]
            output_csv = f"{base_name}.csv"

            # 이미 CSV가 존재하면 스킵 (중복 변환 방지)
            if os.path.exists(output_csv):
                continue

            df = None
            # 1. HTML 포맷 엑셀 (공공데이터 구형 파일) 파싱 시도
            try:
                dfs = pd.read_html(file, encoding="cp949")
                df = max(dfs, key=len)  # 가장 데이터가 많은 표 선택
            except:
                try:
                    dfs = pd.read_html(file, encoding="utf-8")
                    df = max(dfs, key=len)
                except:
                    # 2. 일반 엑셀 파싱 시도
                    try:
                        df = pd.read_excel(file)  # openpyxl or xlrd
                    except:
                        pass

            if df is not None:
                # UTF-8-SIG (엑셀 호환)로 저장
                df.to_csv(output_csv, index=False, encoding="utf-8-sig")
                print(f"  └─ 🔨 변환 성공: {os.path.basename(file)} -> CSV")
                count += 1

                # (선택) 원본 엑셀 파일 삭제하고 싶으면 아래 주석 해제
                # os.remove(file)
            else:
                print(f"  ⚠️ 변환 실패 (포맷 확인 필요): {os.path.basename(file)}")

        except Exception as e:
            print(f"  ❌ 에러 발생 ({os.path.basename(file)}): {e}")

    print(f"  ✨ 총 {count}개 파일 변환 완료.")

# data/file_organizer.py
import os
import shutil
import glob
from processors import common  # 공통 경로 설정 가져오기


def run():
    print(f"\n[1/3] 🧹 파일 자동 분류 및 정리 시작...")

    # 1. 타겟 폴더들 확인 및 생성
    targets = {
        "inbound": common.RAW_INBOUND_DIR,
        "outbound": common.RAW_OUTBOUND_DIR,
        "exchange": common.RAW_EXCHANGE_DIR,
    }
    for path in targets.values():
        os.makedirs(path, exist_ok=True)

    # 2. 현재 폴더(data/)의 파일 탐색 (이미 정리된 폴더 제외)
    # 정리 대상 확장자
    extensions = ["*.xls", "*.xlsx", "*.csv"]
    base_dir = os.path.dirname(os.path.abspath(__file__))

    move_count = 0

    for ext in extensions:
        # data/ 폴더 바로 아래 있는 파일만 검색
        files = glob.glob(os.path.join(base_dir, ext))

        for file_path in files:
            filename = os.path.basename(file_path)

            # 이미 정리된 파일이나 스크립트, 결과 파일은 건너뜀
            if "cleaned_" in filename or filename.startswith("result_"):
                continue

            destination = None

            # 3. 키워드 기반 분류 로직
            if any(keyword in filename for keyword in ["국적별", "입국", "방한"]):
                destination = targets["inbound"]
            elif any(keyword in filename for keyword in ["환율", "ExRate", "MonAvg"]):
                destination = targets["exchange"]
            # Outbound는 보통 대륙명(Asia, Europe 등)이나 '국민' 키워드
            elif any(
                keyword in filename
                for keyword in [
                    "Asia",
                    "Europe",
                    "Africa",
                    "Oceania",
                    "America",
                    "국민",
                    "해외",
                ]
            ):
                destination = targets["outbound"]

            # 4. 이동 실행
            if destination:
                try:
                    dest_path = os.path.join(destination, filename)
                    shutil.move(file_path, dest_path)
                    print(
                        f"  └─ 🚚 이동: {filename} -> {os.path.basename(destination)}/"
                    )
                    move_count += 1
                except Exception as e:
                    print(f"  ⚠️ 이동 실패 ({filename}): {e}")
            else:
                # 분류 기준에 안 맞으면 스킵 (혹은 수동 확인 유도)
                # print(f"  ❓ 분류 불가 (Skip): {filename}")
                pass

    if move_count == 0:
        print("  ℹ️ 정리할 새로운 파일이 없습니다.")
    else:
        print(f"  ✨ 총 {move_count}개 파일 분류 완료.")

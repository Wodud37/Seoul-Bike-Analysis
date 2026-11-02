"""따릉이 일별 원본(대여소·연령대별로 쪼개진 파일)을 날짜별 합계로 줄이고, 서울 날씨와 합친다."""
import glob
import sys

import pandas as pd

UP = sys.argv[1]
OUT = sys.argv[2]

bike_files = sorted(f for f in glob.glob(f"{UP}/서울특별시_공공자전거_이용정보_일별__26*.csv") if not f.endswith("_1.csv"))

parts, by_type, by_age = [], [], []
for f in bike_files:
    df = pd.read_csv(f, encoding="cp949", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    for c in ["이용건수", "이동거리(M)", "이용시간(분)"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["대여일자"] = pd.to_datetime(df["대여일자"])
    agg = {"이용건수": "sum", "이동거리(M)": "sum", "이용시간(분)": "sum"}
    parts.append(df.groupby("대여일자").agg(agg))
    by_type.append(df.groupby(["대여일자", "대여구분코드"])["이용건수"].sum())
    by_age.append(df.groupby(["대여일자", "연령대"])["이용건수"].sum())
    print(f, len(df))

daily = pd.concat(parts).groupby(level=0).sum()
daily.columns = ["이용건수", "이동거리_m", "이용시간_분"]

w = pd.read_csv(glob.glob(f"{UP}/95828c65-OBS_ASOS_DD_*.csv")[0], encoding="cp949")
w = w.rename(columns={"일시": "대여일자", "평균기온(°C)": "평균기온", "최저기온(°C)": "최저기온",
                      "최고기온(°C)": "최고기온", "일강수량(mm)": "강수량_mm",
                      "평균 풍속(m/s)": "평균풍속", "평균 상대습도(%)": "평균습도"})
w["대여일자"] = pd.to_datetime(w["대여일자"])
w = w[["대여일자", "평균기온", "최저기온", "최고기온", "강수량_mm", "평균풍속", "평균습도"]]
w["강수량_mm"] = w["강수량_mm"].fillna(0)  # 기상청 자료에서 빈칸 = 비 안 옴

merged = daily.reset_index().merge(w, on="대여일자", how="left")
merged["요일"] = merged["대여일자"].dt.day_name()
merged.to_csv(f"{OUT}/daily_bike_weather.csv", index=False, encoding="utf-8-sig")

pd.concat(by_type).groupby(level=[0, 1]).sum().unstack(fill_value=0).to_csv(
    f"{OUT}/daily_by_ticket.csv", encoding="utf-8-sig")
pd.concat(by_age).groupby(level=[0, 1]).sum().unstack(fill_value=0).to_csv(
    f"{OUT}/daily_by_age.csv", encoding="utf-8-sig")
print(merged.shape)

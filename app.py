from pathlib import Path
import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="따릉이 이용 분석", layout="wide")

HOLIDAYS = pd.to_datetime([
    '2026-01-01', '2026-02-16', '2026-02-17', '2026-02-18',
    '2026-03-02', '2026-05-05', '2026-05-25', '2026-05-01', '2026-06-03'
])
DAYS = {'Monday': '월', 'Tuesday': '화', 'Wednesday': '수', 'Thursday': '목',
        'Friday': '금', 'Saturday': '토', 'Sunday': '일'}
DAY_ORDER = list(DAYS.values())
RAIN_ORDER = ['0mm', '0~5mm', '5~20mm', '20mm+']

@st.cache_data
def load():
    df = pd.read_csv(Path(__file__).parent / 'data' / 'daily_bike_weather.csv',
                     parse_dates=['대여일자'])
    df['월'] = df['대여일자'].dt.month
    df['휴일'] = df['대여일자'].isin(HOLIDAYS) | df['요일'].isin(['Saturday', 'Sunday'])
    df['상대이용'] = df['이용건수'] / df.groupby(['월', '휴일'])['이용건수'].transform('mean')
    df['강수구간'] = pd.cut(df['강수량_mm'], bins=[-0.1, 0, 5, 20, 1000], labels=RAIN_ORDER)
    df['요일한글'] = df['요일'].map(DAYS)
    return df

df = load()

st.title("🚲 서울 따릉이 이용량과 날씨 (2026년 1~6월)")
st.caption("데이터: 서울 열린데이터광장 공공자전거 이용정보, 기상청 ASOS 서울(108)")

lo, hi = df['대여일자'].min().date(), df['대여일자'].max().date()
start, end = st.slider("기간 선택", min_value=lo, max_value=hi, value=(lo, hi))
d = df[(df['대여일자'].dt.date >= start) & (df['대여일자'].dt.date <= end)]

c1, c2, c3 = st.columns(3)
c1.metric("총 이용건수", f"{d['이용건수'].sum():,}건")
c2.metric("일평균 이용건수", f"{d['이용건수'].mean():,.0f}건")
c3.metric("비 온 날", f"{(d['강수량_mm'] > 0).sum()}일 / {len(d)}일")

# 1. 일별 이용건수 + 비 온 날 표시
st.subheader("일별 이용건수")
tip = [alt.Tooltip('대여일자:T', format='%Y-%m-%d'), '이용건수:Q', '강수량_mm:Q', '평균기온:Q']
line = alt.Chart(d).mark_line().encode(
    x=alt.X('대여일자:T', title=None),
    y=alt.Y('이용건수:Q', title='이용건수'),
    tooltip=tip
)
rain = alt.Chart(d[d['강수량_mm'] > 0]).mark_circle(color='crimson', size=45).encode(
    x='대여일자:T', y='이용건수:Q', tooltip=tip
)
st.altair_chart(line + rain, use_container_width=True)
st.caption("빨간 점: 비 온 날 (강수량 > 0mm)")

left, right = st.columns(2)

# 2. 기온 vs 이용건수
with left:
    st.subheader("평균기온 vs 이용건수")
    scatter = alt.Chart(d).mark_circle(size=50).encode(
        x=alt.X('평균기온:Q', title='평균기온(℃)'),
        y=alt.Y('이용건수:Q'),
        color=alt.Color('월:O', scale=alt.Scale(scheme='viridis'), title='월'),
        tooltip=tip
    )
    st.altair_chart(scatter, use_container_width=True)

# 3. 강수구간별 상대 이용량
with right:
    st.subheader("강수량 구간별 상대 이용량")
    r = (d.groupby('강수구간', observed=True)['상대이용']
          .agg(['mean', 'count']).reset_index())
    bars = alt.Chart(r).mark_bar().encode(
        x=alt.X('강수구간:N', sort=RAIN_ORDER, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('mean:Q', title='상대 이용량'),
        tooltip=['강수구간', alt.Tooltip('mean:Q', format='.2f'), alt.Tooltip('count:Q', title='일수')]
    )
    st.altair_chart(bars, use_container_width=True)
    st.caption("같은 달·평일/휴일 평균을 1.0으로 둔 비율. 20mm+는 표본 2일.")

# 4. 요일별
st.subheader("요일별 일평균 이용건수")
w = d.groupby('요일한글')['이용건수'].mean().reset_index()
wbars = alt.Chart(w).mark_bar().encode(
    x=alt.X('요일한글:N', sort=DAY_ORDER, title=None, axis=alt.Axis(labelAngle=0)),
    y=alt.Y('이용건수:Q', title='일평균 이용건수'),
    tooltip=['요일한글', alt.Tooltip('이용건수:Q', format=',.0f')]
)
st.altair_chart(wbars, use_container_width=True)
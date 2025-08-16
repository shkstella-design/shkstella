# 설치 방법 (가상환경 권장)
# pip install --upgrade pip
# pip install streamlit pandas altair
# 실행: streamlit run app.py

import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

st.set_page_config(page_title='월별 매출 대시보드', layout='wide')

# ========== 사이드바 ==========
st.sidebar.header('설정')
uploaded = st.sidebar.file_uploader('CSV 업로드 (열: 월, 매출액, 전년동월, 증감률)', type=['csv'])
st.sidebar.write('')
annual_goal = st.sidebar.number_input('연간 매출 목표(원)', min_value=0, step=1_000_000, value=0, format='%d')
st.sidebar.markdown('<span style="color:#6b7280;font-size:12px;">※ 헤더명은 반드시 <b>월, 매출액, 전년동월, 증감률</b> 을 사용하세요.</span>', unsafe_allow_html=True)

# ========== 데이터 로드 ==========
def load_data(file):
    if file is None:
        # 예시 데이터 (12개월 채움)
        rows = [
            ('2024-01', 12000000, 10500000, 14.3),
            ('2024-02', 13500000, 11200000, 20.5),
            ('2024-03', 11000000, 12800000, -14.1),
            ('2024-04', 18000000, 15200000, 18.4),
            ('2024-05', 21000000, 18500000, 13.5),
            ('2024-06', 19500000, 17000000, 14.7),
            ('2024-07', 23000000, 20000000, 15.0),
            ('2024-08', 22000000, 19800000, 11.1),
            ('2024-09', 17500000, 15400000, 13.6),
            ('2024-10', 25000000, 22000000, 13.6),
            ('2024-11', 26500000, 23500000, 12.8),
            ('2024-12', 28000000, 24700000, 13.4),
        ]
        df = pd.DataFrame(rows, columns=['월','매출액','전년동월','증감률'])
    else:
        df = pd.read_csv(file)
        expected = {'월','매출액','전년동월','증감률'}
        if not expected.issubset(df.columns):
            st.warning('CSV에 필요한 컬럼이 없습니다. 예시 데이터로 표시합니다.')
            return load_data(None)
    # 전처리
    df = df.copy()
    df['월'] = pd.to_datetime(df['월'], errors='coerce')
    df = df.dropna(subset=['월']).sort_values('월')
    df['매출액'] = pd.to_numeric(df['매출액'], errors='coerce')
    df['전년동월'] = pd.to_numeric(df['전년동월'], errors='coerce')
    df['증감률'] = pd.to_numeric(df['증감률'], errors='coerce')
    # 3개월 이동평균
    df['이동평균_3M'] = df['매출액'].rolling(3, min_periods=1).mean()
    return df

df = load_data(uploaded)

# ========== 헤더 ==========
st.markdown('<h1 style="margin:4px 0 8px;">월별 매출 대시보드</h1>', unsafe_allow_html=True)

# ========== KPI ==========
ytd = int(df['매출액'].sum())
avg_yoy = float(df['증감률'].mean()) if not df['증감률'].isna().all() else 0.0
max_idx = int(df['매출액'].idxmax())
min_idx = int(df['매출액'].idxmin())
max_month = df.loc[max_idx, '월']
min_month = df.loc[min_idx, '월']
max_value = int(df.loc[max_idx, '매출액'])
min_value = int(df.loc[min_idx, '매출액'])

c1, c2, c3, c4 = st.columns([1,1,1,1])
c1.metric('YTD 누적 매출', f"{ytd:,} 원")
c2.metric('YTD 전년대비 증감률', f"{avg_yoy:,.1f} %")
c3.metric('최고 매출 월', f"{max_month.strftime('%Y-%m')} · {max_value:,}")
c4.metric('최저 매출 월', f"{min_month.strftime('%Y-%m')} · {min_value:,}")

if annual_goal and annual_goal > 0:
    progress = min(1.0, ytd / annual_goal)
    st.progress(progress, text=f"연간 목표 대비 {progress*100:,.1f}%")

st.markdown("<hr style='margin:8px 0 14px;'>", unsafe_allow_html=True)

# ========== ① 매출 추세 & 3M 이동평균 ==========
st.markdown('<h3>① 매출 추세 & 3M 이동평균</h3>', unsafe_allow_html=True)
base = alt.Chart(df).encode(x=alt.X('월:T', title='월'))
line_sales = base.mark_line(point=True).encode(
    y=alt.Y('매출액:Q', title='원'),
    color=alt.value('#2563eb')
)
line_ma = base.mark_line(strokeDash=[6,6]).encode(
    y=alt.Y('이동평균_3M:Q', title=''),
    color=alt.value('#60a5fa')
)
legend = alt.Chart(pd.DataFrame({'name':['매출액','3M 이동평균']})).mark_point(filled=True).encode(
    x=alt.value(0), y=alt.value(0), color=alt.Color('name:N', scale=alt.Scale(range=['#2563eb','#60a5fa']))
).properties(width=0, height=0)
chart1 = (line_sales + line_ma).properties(height=340).resolve_scale(y='shared')
st.altair_chart(chart1, use_container_width=True)

# ========== ② 전년동월 대비 ==========
st.markdown('<h3>② 전년동월 대비</h3>', unsafe_allow_html=True)
df_yoy = df.copy()
df_yoy['증감률_label'] = df_yoy['증감률'].map(lambda v: f"{v:.1f}%")
bar = alt.Chart(df_yoy).mark_bar().encode(
    x=alt.X('월:T', title='월'),
    y=alt.Y('증감률:Q', title='증감률(%)'),
    color=alt.condition(alt.datum.증감률 < 0, alt.value('#ef4444'), alt.value('#2563eb')),
    tooltip=['월','증감률']
).properties(height=260)
st.altair_chart(bar, use_container_width=True)

# ========== ③ (선택) 누적 매출 & 목표선 ==========
with st.expander('누적 매출 추이 보기'):
    df_cum = df.copy()
    df_cum['누적매출'] = df_cum['매출액'].cumsum()
    base2 = alt.Chart(df_cum).encode(x=alt.X('월:T', title='월'))
    area = base2.mark_area(opacity=0.2).encode(y=alt.Y('누적매출:Q', title='누적 매출'))
    line_cum = base2.mark_line().encode(y='누적매출:Q', color=alt.value('#2563eb'))
    layers = area + line_cum
    if annual_goal and annual_goal > 0:
        goal_per_month = annual_goal
        rule = alt.Chart(pd.DataFrame({'y':[goal_per_month]})).mark_rule(strokeDash=[6,3], color='#10b981').encode(y='y:Q')
        layers = layers + rule
    st.altair_chart(layers.properties(height=260), use_container_width=True)

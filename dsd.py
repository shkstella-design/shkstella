import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
from datetime import datetime

# =====================
# 브랜드 컬러 팔레트
# =====================
BRAND_BG = "#EDF6F2"   # 배경
BRAND_DARK = "#231413" # 텍스트/포인트 다크
BRAND_MAIN = "#116741" # 메인 그린
BRAND_A = "#82BEA4"    # 서브 라이트
BRAND_B = "#86B4A2"    # 서브 라이트2

# Altair 테마 등록
def brand_theme():
    return {
        "config": {
            "view": {"continuousWidth": 400, "continuousHeight": 300, "stroke": None},
            "background": "transparent",
            "axis": {
                "labelColor": BRAND_DARK,
                "titleColor": BRAND_DARK,
                "gridColor": "#e5efe9",
            },
            "legend": {
                "labelColor": BRAND_DARK,
                "titleColor": BRAND_DARK,
            },
            "range": {
                "category": [BRAND_MAIN, BRAND_A, BRAND_B, BRAND_DARK, "#9CA3AF"],
            },
        }
    }

alt.themes.register("brand", brand_theme)
alt.themes.enable("brand")

st.set_page_config(page_title="월별 매출 대시보드", layout="wide")

# =====================
# 글로벌 스타일
# =====================
st.markdown(
    f"""
    <style>
    .main {{ background: {BRAND_BG}; }}
    section[data-testid="stSidebar"] {{ background: white; border-right: 1px solid #e5efe9; }}
    h1, h2, h3, h4, h5, h6 {{ color: {BRAND_DARK}; }}
    .metric-card {{
        background: white; border: 1px solid #e5efe9; border-radius: 14px; padding: 14px 16px; box-shadow: 0 1px 2px rgba(0,0,0,.04);
    }}
    .metric-title {{ font-size: 13px; color: #4B5563; margin-bottom: 6px; }}
    .metric-value {{ font-weight: 700; color: {BRAND_DARK}; font-size: 22px; }}
    .metric-delta.up {{ color: {BRAND_MAIN}; font-weight: 600; }}
    .metric-delta.down {{ color: #ef4444; font-weight: 600; }}
    .sep {{ margin: 10px 0 16px; border-top: 1px solid #e5efe9; }}
    .hint {{ color:#6b7280;font-size:12px; }}
    .goalbar .stProgress > div > div {{ background-color: {BRAND_MAIN}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================
# 사이드바
# =====================
st.sidebar.header("설정")
uploaded = st.sidebar.file_uploader("CSV 업로드 (열: 월, 매출액, 전년동월, 증감률)", type=["csv"]) 
st.sidebar.write("")
annual_goal = st.sidebar.number_input(
    "연간 매출 목표(원)", min_value=0, step=1_000_000, value=0, format="%d"
)
st.sidebar.markdown(
    "<span class='hint'>※ 헤더명은 반드시 <b>월, 매출액, 전년동월, 증감률</b> 을 사용하세요.</span>",
    unsafe_allow_html=True,
)

# =====================
# 데이터 로드
# =====================

def load_data(file):
    if file is None:
        rows = [
            ("2024-01", 12000000, 10500000, 14.3),
            ("2024-02", 13500000, 11200000, 20.5),
            ("2024-03", 11000000, 12800000, -14.1),
            ("2024-04", 18000000, 15200000, 18.4),
            ("2024-05", 21000000, 18500000, 13.5),
            ("2024-06", 19500000, 17000000, 14.7),
            ("2024-07", 23000000, 20000000, 15.0),
            ("2024-08", 22000000, 19800000, 11.1),
            ("2024-09", 17500000, 15400000, 13.6),
            ("2024-10", 25000000, 22000000, 13.6),
            ("2024-11", 26500000, 23500000, 12.8),
            ("2024-12", 28000000, 24700000, 13.4),
        ]
        df = pd.DataFrame(rows, columns=["월", "매출액", "전년동월", "증감률"])
    else:
        df = pd.read_csv(file)
        expected = {"월", "매출액", "전년동월", "증감률"}
        if not expected.issubset(df.columns):
            st.warning("CSV에 필요한 컬럼이 없습니다. 예시 데이터로 표시합니다.")
            return load_data(None)
    df = df.copy()
    df["월"] = pd.to_datetime(df["월"], errors="coerce")
    df = df.dropna(subset=["월"]).sort_values("월")
    for col in ["매출액", "전년동월", "증감률"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["이동평균_3M"] = df["매출액"].rolling(3, min_periods=1).mean()
    return df


df = load_data(uploaded)

# =====================
# 유틸
# =====================

def fmt_won(v):
    try:
        return f"{int(v):,} 원"
    except Exception:
        return "-"

# =====================
# 헤더
# =====================
st.markdown("<h1 style='margin:4px 0 8px;'>월별 매출 대시보드</h1>", unsafe_allow_html=True)

# =====================
# KPI 영역
# =====================
ytd = int(df["매출액"].sum())
avg_yoy = float(df["증감률"].mean()) if not df["증감률"].isna().all() else 0.0
max_idx = int(df["매출액"].idxmax())
min_idx = int(df["매출액"].idxmin())
max_month = df.loc[max_idx, "월"].strftime("%Y-%m")
min_month = df.loc[min_idx, "월"].strftime("%Y-%m")
max_value = int(df.loc[max_idx, "매출액"])
min_value = int(df.loc[min_idx, "매출액"])

c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
with c1:
    st.markdown("<div class='metric-card'>" \
                "<div class='metric-title'>YTD 누적 매출</div>" \
                f"<div class='metric-value'>{ytd:,} 원</div>" \
                "</div>", unsafe_allow_html=True)
with c2:
    delta_class = "up" if avg_yoy >= 0 else "down"
    arrow = "▲" if avg_yoy >= 0 else "▼"
    st.markdown(
        f"<div class='metric-card'>"
        "<div class='metric-title'>YTD 전년대비 증감률</div>"
        f"<div class='metric-value'>{avg_yoy:,.1f}% "
        f"<span class='metric-delta {delta_class}'>{arrow}</span></div>"
        "</div>",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown("<div class='metric-card'>" \
                "<div class='metric-title'>최고 매출 월</div>" \
                f"<div class='metric-value'>{max_month} · {max_value:,} 원</div>" \
                "</div>", unsafe_allow_html=True)
with c4:
    st.markdown("<div class='metric-card'>" \
                "<div class='metric-title'>최저 매출 월</div>" \
                f"<div class='metric-value'>{min_month} · {min_value:,} 원</div>" \
                "</div>", unsafe_allow_html=True)

if annual_goal and annual_goal > 0:
    progress = min(1.0, ytd / annual_goal) if annual_goal else 0
    st.markdown("<div class='goalbar'>", unsafe_allow_html=True)
    st.progress(progress, text=f"연간 목표 대비 {progress*100:,.1f}%")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='sep'></div>", unsafe_allow_html=True)

# =====================
# ① 매출 추세 & 3M 이동평균
# =====================
st.markdown("<h3>① 매출 추세 & 3M 이동평균</h3>", unsafe_allow_html=True)
base = alt.Chart(df).encode(x=alt.X("월:T", title="월"))

line_sales = base.mark_line(point=alt.OverlayMarkDef(filled=True, fill=BRAND_MAIN)).encode(
    y=alt.Y("매출액:Q", title="원"),
    color=alt.value(BRAND_MAIN),
    tooltip=[
        alt.Tooltip("월:T", title="월", format="%Y-%m"),
        alt.Tooltip("매출액:Q", title="매출액", format=","),
        alt.Tooltip("전년동월:Q", title="전년동월", format=","),
        alt.Tooltip("증감률:Q", title="증감률", format=".1f")
    ],
)

line_ma = base.mark_line(strokeDash=[6, 6]).encode(
    y=alt.Y("이동평균_3M:Q", title=""),
    color=alt.value(BRAND_A),
    tooltip=[alt.Tooltip("이동평균_3M:Q", title="3M 이동평균", format=",.0f")],
)

chart1 = (line_sales + line_ma).properties(height=340)
st.altair_chart(chart1, use_container_width=True)

# =====================
# ② 전년동월 대비
# =====================
st.markdown("<h3>② 전년동월 대비</h3>", unsafe_allow_html=True)

df_yoy = df.copy()
bar = (
    alt.Chart(df_yoy)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("월:T", title="월"),
        y=alt.Y("증감률:Q", title="증감률(%)"),
        color=alt.condition(alt.datum.증감률 < 0, alt.value("#ef4444"), alt.value(BRAND_MAIN)),
        tooltip=[
            alt.Tooltip("월:T", title="월", format="%Y-%m"),
            alt.Tooltip("증감률:Q", title="증감률", format=".1f")
        ],
    )
    .properties(height=260)
)

rule0 = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#9CA3AF").encode(y="y:Q")
st.altair_chart(bar + rule0, use_container_width=True)

# =====================
# ③ (선택) 누적 매출 & 목표선
# =====================
with st.expander("누적 매출 추이 보기"):
    df_cum = df.copy()
    df_cum["누적매출"] = df_cum["매출액"].cumsum()
    base2 = alt.Chart(df_cum).encode(x=alt.X("월:T", title="월"))

    area = base2.mark_area(opacity=0.18, color=BRAND_MAIN).encode(
        y=alt.Y("누적매출:Q", title="누적 매출")
    )
    line_cum = base2.mark_line(color=BRAND_MAIN).encode(y="누적매출:Q")

    layers = area + line_cum

    if annual_goal and annual_goal > 0:
        rule = (
            alt.Chart(pd.DataFrame({"y": [annual_goal]}))
            .mark_rule(strokeDash=[6, 3], color=BRAND_B)
            .encode(y="y:Q")
        )
        text = (
            alt.Chart(pd.DataFrame({"y": [annual_goal]}))
            .mark_text(align="left", dx=6, dy=-6, color=BRAND_DARK)
            .encode(x=alt.value(10), y="y:Q", text=alt.value("연간 목표"))
        )
        layers = layers + rule + text

    st.altair_chart(layers.properties(height=260), use_container_width=True)

# =====================
# ④ (선택) 테이블 보기
# =====================
with st.expander("데이터 테이블 보기"):
    tdf = df.copy()
    tdf["월"] = tdf["월"].dt.strftime("%Y-%m")
    st.dataframe(
        tdf[["월", "매출액", "전년동월", "증감률", "이동평균_3M"]]
        .rename(columns={"이동평균_3M": "3M 이동평균"})
        .style.format({"매출액": "{:,}", "전년동월": "{:,}", "증감률": "{:.1f}", "3M 이동평균": "{:,}"}),
        use_container_width=True,
        hide_index=True,
    )

# 푸터 힌트
st.markdown(
    f"<div class='hint'>ⓘ 차트 색상은 브랜드 컬러 팔레트({BRAND_MAIN}, {BRAND_A}, {BRAND_B})를 사용했습니다.</div>",
    unsafe_allow_html=True,
)

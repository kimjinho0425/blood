# ====== 폰트 설정 (Matplotlib 3.6+ 확실한 방법) ======
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 1) 리포지토리에 TTF를 두면 가장 확실함: ./fonts/NanumGothic.ttf
# 기존 FONT_CANDIDATES 를 아래로 교체
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",                     # 시스템 기본
    "/usr/share/fonts/truetype/nanum/NanumGothic-Regular.ttf",             # 시스템(Regular 파일명)
    str(Path(__file__).parent / "fonts" / "NanumGothic.ttf"),              # 리포에 NanumGothic.ttf
    str(Path(__file__).parent / "fonts" / "NanumGothic-Regular.ttf"),      # 리포에 NanumGothic-Regular.ttf  ← 이거 추가
    str(Path(__file__).parent / "NanumGothic.ttf"),                        # 루트
    str(Path(__file__).parent / "NanumGothic-Regular.ttf"),                # 루트(Regular)
]


def get_korean_font():
    # (A) 먼저 후보 경로에서 찾기
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p

    # (B) 없으면 설치 시도: Nanum 먼저, 실패시 Noto CJK (둘 중 하나만 되어도 OK)
    os.system("apt-get update && apt-get install -y fonts-nanum || true")
    if os.path.exists("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
        return "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

    os.system("apt-get install -y fonts-noto-cjk || true")
    # Noto CJK의 대표 한글 폰트 경로(배포 이미지에 따라 다를 수 있어 패턴 탐색)
    for root, _, files in os.walk("/usr/share/fonts"):
        for f in files:
            if "NotoSansCJK" in f or "NotoSans" in f:
                return os.path.join(root, f)
    return None

_font_path = get_korean_font()

if _font_path:
    # 폰트 파일을 등록하고 '실제 폰트 이름'을 얻어 rcParams에 반영
    fm.fontManager.addfont(_font_path)  # 공식 API
    _font_name = fm.FontProperties(fname=_font_path).get_name()
    plt.rcParams["font.family"] = [_font_name, "DejaVu Sans", "sans-serif"]
else:
    # 폰트를 못 구해도 앱이 죽지 않도록 통과
    # (이 경우 한글이 네모로 나올 수 있음)
    pass

plt.rcParams["axes.unicode_minus"] = False
# ====== 폰트 설정 끝 ======

import streamlit as st
import numpy as np
from matplotlib.ticker import FuncFormatter

# -------------------------------
# 페이지 설정
# -------------------------------
st.set_page_config(page_title="혈류 심화 시뮬레이터", layout="centered")
st.title("혈류 시뮬레이터")

# -------------------------------
# 수식 정의
# -------------------------------
def Q_from(r_m, dP, eta, L):
    return (np.pi * (r_m**4) * dP) / (8.0 * eta * L)

def dP_from(r_m, Q, eta, L):
    return (8.0 * eta * L * Q) / (np.pi * (r_m**4))

def fmt(x, nd=2):
    return f"{x:,.{nd}f}"

def axis_fmt0(x, pos):
    return f"{x:,.0f}"

def to_mL_per_s(Q_m3_s):
    return Q_m3_s * 1_000_000.0

# -------------------------------
# 파라미터 입력
# -------------------------------
st.sidebar.header("변수 조절")
r_mm = st.sidebar.slider("혈관 반지름 r (mm)", 0.2, 3.0, 1.0, 0.1)
eta = st.sidebar.selectbox("혈액 점도 η (Pa·s)", [0.003, 0.004, 0.005], index=1)
dP = st.sidebar.slider("압력차 ΔP (Pa)", 100, 3000, 1000)
L = st.sidebar.slider("혈관 길이 L (m)", 0.05, 0.30, 0.10)
unit = st.radio("표시 단위(유량)", ["mL/s", "m³/s"], horizontal=True, index=0)
r_m = r_mm / 1000.0

# -------------------------------
# ① 유량 Q 계산
# -------------------------------
st.subheader("유량 Q 계산")
st.latex(r"Q=\frac{\pi r^{4}\,\Delta P}{8\,\eta\,L}")

Q_now_m3s = Q_from(r_m, dP, eta, L)
Q_now_disp = to_mL_per_s(Q_now_m3s) if unit == "mL/s" else Q_now_m3s
unit_label = "mL/s" if unit == "mL/s" else "m³/s"

st.markdown(
    f"**대입값:** "
    f"r = {fmt(r_mm,3)} mm,  ΔP = {fmt(dP,0)} Pa,  η = {fmt(eta,3)} Pa·s,  L = {fmt(L,2)} m  "
    f"→  Q = **{fmt(Q_now_disp,4)} {unit_label}**"
)

# 그래프: Q vs r
r_vals = np.linspace(0.2, 3.0, 200)
Q_r_m3s = Q_from(r_vals/1000, dP, eta, L)
Q_r_disp = to_mL_per_s(Q_r_m3s) if unit == "mL/s" else Q_r_m3s

fig1, ax1 = plt.subplots()
ax1.plot(r_vals, Q_r_disp)
ax1.set_xlabel("혈관 반지름 r (mm)")
ax1.set_ylabel(f"유량 Q ({unit_label})")
ax1.set_title("반지름 변화에 따른 유량 (Q vs r)")
ax1.grid(True, alpha=0.3)
st.pyplot(fig1)

# 그래프: Q vs η
eta_vals = np.linspace(0.003, 0.007, 200)
Q_eta_m3s = Q_from(r_m, dP, eta_vals, L)
Q_eta_disp = to_mL_per_s(Q_eta_m3s) if unit == "mL/s" else Q_eta_m3s

fig2, ax2 = plt.subplots()
ax2.plot(eta_vals, Q_eta_disp)
ax2.set_xlabel("점도 η (Pa·s)")
ax2.set_ylabel(f"유량 Q ({unit_label})")
ax2.set_title("점도 변화에 따른 유량 (Q vs η)")
ax2.grid(True, alpha=0.3)
st.pyplot(fig2)

st.divider()

# -------------------------------
# ② 같은 Q 유지 시 필요한 ΔP
# -------------------------------
st.subheader("같은 유량(Q)을 유지하려면 필요한 압력 ΔP (심장 부담)")

# ✅ 현실적 압력 기준 (200 Pa)
dP_base = st.slider("정상 기준 ΔP_base (Pa)", 50, 2000, 200)
Q_target_m3s = Q_from(0.001, dP_base, 0.004, L)
Q_target_disp = to_mL_per_s(Q_target_m3s) if unit == "mL/s" else Q_target_m3s
st.markdown(f"**기준 유량(Q_target)** = {fmt(Q_target_disp,4)} {unit_label}")

st.latex(r"\Delta P=\frac{8\,\eta\,L\,Q}{\pi r^{4}}")

# -------------------------------
# 상태별 ΔP 계산
# -------------------------------
st.markdown("**정상인과 질환자 비교: 점도(η)와 반지름(r)의 영향**")

scenarios = {
    "정상":      {"r_mm": 1.0, "eta": 0.004},
    "동맥경화":  {"r_mm": 0.7, "eta": 0.005},
    "고지혈증":  {"r_mm": 1.0, "eta": 0.005},
    "탈수":      {"r_mm": 1.0, "eta": 0.006},
}

names, dPs = [], []
for name, vals in scenarios.items():
    r_ = vals["r_mm"] / 1000
    e_ = vals["eta"]
    dP_need = dP_from(r_, Q_target_m3s, e_, L)
    dPs.append(dP_need)
    names.append(name)

# -------------------------------
# 그래프 표시
# -------------------------------
fig3, ax3 = plt.subplots(figsize=(7,5))
colors = ["#2E86AB", "#F18F01", "#C73E1D", "#6C5B7B"]
bars = ax3.bar(names, dPs, color=colors)
ax3.set_ylabel("필요한 ΔP (Pa)")
ax3.set_title("")
ax3.grid(True, axis="y", alpha=0.3)
ax3.yaxis.set_major_formatter(FuncFormatter(axis_fmt0))

for bar, (name, vals) in zip(bars, scenarios.items()):
    height = bar.get_height()
    r_txt = vals["r_mm"]
    eta_txt = vals["eta"]
    grad = height / L
    ax3.text(bar.get_x() + bar.get_width()/2, height + 50,
             f"{name}\n(r={r_txt:.2f}mm, η={eta_txt:.3f})",
             ha='center', va='bottom', fontsize=8)
    ax3.text(bar.get_x() + bar.get_width()/2, height * 0.02,
             f"{fmt(height,3)} Pa\n({fmt(grad,0)} Pa/m)",
             ha='center', va='bottom', fontsize=8, color="#222")

st.pyplot(fig3)

if max(dPs) > 5333:
    st.warning("현재 설정은 단일 구간 압력 강하가 큰 편입니다. ΔP_base를 낮춰보세요.")







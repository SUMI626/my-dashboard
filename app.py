import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re
import plotly.express as px

st.set_page_config(
    page_title="이용자 현황 분석 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 가독성을 높이기 위한 전역 CSS 및 브랜드 컬러 적용
BRAND_RED = "#BE1E2D"
BRAND_GRAY = "#4D4D4D"
BRAND_YELLOW = "#F1A42B"
BRAND_BLUE = "#136698"

# 그래프용 채도 조절 포인트 컬러 (조금 더 부드러운 느낌)
CHART_RED = "#D65C69"
CHART_BLUE = "#5D93B5"
CHART_YELLOW = "#F5C370"
CHART_GRAY = "#7A7A7A"
# 브랜드 컬러 기반의 확장된 팔레트 (항목 구분을 위해 명/암 조절된 보조색 포함)
COLOR_PALETTE = [
    BRAND_RED, BRAND_BLUE, BRAND_YELLOW, BRAND_GRAY, 
    CHART_RED, CHART_BLUE, CHART_YELLOW, CHART_GRAY,
    "#E98C8E", "#A4CAD2", "#F9D59B", "#BDBDBD"
]



st.markdown(f"""
<style>
/* 1. 전체 앱 기본 폰트 및 색상 강제 지정 (다크모드 대비) */
.stApp {{
    background-color: white !important;
    color: #31333f !important;
}}

/* 모든 텍스트 요소를 명시적으로 어두운 색으로 지정 */
p, span, label, div[data-testid="stMarkdownContainer"] p {{
    color: #31333f !important;
}}

/* 장애유형 강조 색상 (전역 span 스타일 덮어쓰기용) */
.disability-highlight {{
    color: #BE1E2D !important;
    font-weight: bold !important;
}}

/* 데이터 소스 라디오 버튼 글씨 */
div[data-testid="stWidgetLabel"] p, div[data-testid="stRadio"] label {{
    color: #31333f !important;
    font-weight: 600 !important;
}}

/* 2. 메트릭(숫자) 강조 및 박스 스타일 */
div[data-testid="stMetricValue"], .stMetricValue {{
    font-size: 38px !important;
    font-weight: 800 !important;
    color: {BRAND_RED} !important;
}}

/* 항목 이름 (총 연인원 등) */
div[data-testid="stMetricLabel"] p {{
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #4D4D4D !important;
    margin-bottom: 0px !important;
}}
/* 메트릭 박스 센터 정렬 및 간격 축소 */
div[data-testid="stMetric"], .stMetric {{
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    width: 100% !important;
    padding: 0px !important; /* 내부 패딩 제거 */
}}
/* 요약 박스 테두리 및 패딩 축소 */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border: 4px solid {BRAND_GRAY} !important; /* 6px -> 4px */
    border-radius: 10px !important;
    padding: 10px 20px !important; /* 위아래 패딩 대폭 축소 */
    background-color: white !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
}}
/* 탭 디자인 수정 */
.stTabs [data-baseweb="tab-list"] {{
    gap: 24px;
}}
.stTabs [data-baseweb="tab"] {{
    height: 50px;
    white-space: pre-wrap;
    background-color: #ffffff;
    border-radius: 10px 10px 0px 0px;
    gap: 1px;
    padding-left: 20px;
    padding-right: 20px;
    font-weight: bold;
    font-size: 18px;
}}
/* 탭 선택 색상 차별화 - 변수 대신 헥사코드 직접 사용 (f-string 오류 방지) */
/* 내부 p, span 태그에도 글자색을 강제 적용하여 전역 색상에 덮어씌워지는 현상 방지 */
.stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"],
.stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"] p,
.stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"] span,
.stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"] div {{
    background-color: #136698 !important;
    color: white !important;
}}

.stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"],
.stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"] p,
.stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"] span,
.stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"] div {{
    background-color: #BE1E2D !important;
    color: white !important;
}}

/* 차트 외부 여백 제거 전용 */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    padding: 0px !important;
}}

/* ========= 태블릿/모바일 반응형 레이아웃 전용 (데스크톱 원본 유지) ========= */
/* 아이패드 프로 12.9 (해상도 1366px) 등 대형 태블릿까지 포괄 */
@media (max-width: 1366px) {{
    /* 1. 대시보드 메인 - 메트릭 박스 간격 확보 */
    div[data-testid="stMetric"], .stMetric {{
        padding: 5px 2px !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        padding: 12px 10px !important;
    }}

    /* 2. 헤더 행 (타이틀+버튼+드롭다운) - 태블릿에서도 가로 한 줄 강제 유지 */
    [data-testid="stHorizontalBlock"]:first-of-type {{
        flex-wrap: nowrap !important;
        flex-direction: row !important;
    }}
    [data-testid="stHorizontalBlock"]:first-of-type > div {{
        min-width: 0 !important;
        flex-shrink: 1 !important;
    }}
    
    /* 3. 프리젠테이션 모드 - 강제 몰입형 뷰의 하단 잘림 방지를 위해 빈 공간 추가 */
    body.pres-active [data-testid="stAppViewBlockContainer"] {{
        padding-bottom: 200px !important; /* 태블릿 하단 잘림 방지용 여유 공간 대폭 확대 */
    }}
}}

/* ========= 프리젠테이션 모드 스타일 ========= */
body.pres-active [data-testid="stSidebar"],
body.pres-active [data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}
body.pres-active [data-testid="stHeader"] {{
    display: none !important;
}}
body.pres-active .pres-hide {{
    display: none !important;
}}
body.pres-active [data-testid="stMainBlockContainer"] {{
    max-width: 100% !important;
    padding: 0 1rem !important;
}}
.pres-slide-title {{
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    background: rgba(0,0,0,0.35);
    display: inline-block;
    padding: 4px 16px;
    border-radius: 6px;
    margin-bottom: 12px;
}}
@keyframes pressFadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.pres-slide-content {{
    animation: pressFadeIn 0.5s ease;
}}
/* ========= 프리젠테이션 보기 버튼 스타일 ========= */
.pres-main-btn-container button,
.pres-main-btn-container button[data-testid="baseButton-primary"] {{
    background-color: {BRAND_RED} !important;
    background: {BRAND_RED} !important;
    color: white !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100% !important;
    transition: background 0.2s ease !important;
    margin-top: 12px !important;
}}
.pres-main-btn-container button:hover,
.pres-main-btn-container button[data-testid="baseButton-primary"]:hover {{
    background-color: #9a1825 !important;
    background: #9a1825 !important;
}}

/* ========= 라이트 모드 완전 강제 (태블릿/모바일 다크모드 대응) ========= */
html, body {{
    background-color: #ffffff !important;
    color: #31333f !important;
}}
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {{
    background-color: #ffffff !important;
    color: #31333f !important;
}}
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"] {{
    background-color: #f8f9fa !important;
    color: #31333f !important;
}}
[data-testid="stHeader"] {{
    background-color: #ffffff !important;
}}
/* 모든 입력 요소 라이트 모드 강제 */
.stSelectbox, .stMultiSelect, .stTextInput, .stRadio,
.stCheckbox, .stFileUploader, .stContainer {{
    background-color: #ffffff !important;
    color: #31333f !important;
}}
/* 사이드바 텍스트 */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {{
    color: #31333f !important;
}}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        return clean_and_map_data(df)
    except Exception as e:
        return pd.DataFrame(), str(e)

@st.cache_data(ttl=600)
def load_data_gsheets(spreadsheet_url):
    """gspread를 직접 사용하여 구글 스프레드시트 데이터를 로드합니다."""
    try:
        # secrets.toml에서 서비스 계정 정보 읽기
        _raw = dict(st.secrets["connections"]["gsheets"])
        _sa_keys = {
            "type", "project_id", "private_key_id", "private_key",
            "client_email", "client_id", "auth_uri", "token_uri",
            "auth_provider_x509_cert_url", "client_x509_cert_url",
        }
        creds_info = {k: v for k, v in _raw.items() if k in _sa_keys}
        creds_info.setdefault("type", "service_account")
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_url(spreadsheet_url)
        
        # '취합_자동' 시트 먼저 시도
        try:
            ws = spreadsheet.worksheet("취합_자동")
        except gspread.exceptions.WorksheetNotFound:
            ws = spreadsheet.get_worksheet(0)
        
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        return clean_and_map_data(df)
    except Exception as e:
        return pd.DataFrame(), f"GSheets Connection Error: {repr(e)}"

def clean_and_map_data(df):
    if df.empty:
        return pd.DataFrame(), "데이터가 비어 있습니다."
    # 모든 컬럼명에서 모든 공백을 제거하여 완벽하게 정제합니다. 
    # (예: ' 이름' -> '이름', '명 / 건' -> '명/건')
    df.columns = df.columns.astype(str).str.replace(r'\s+', '', regex=True)
    
    # 필수 컬럼 존재하는지 유연하게 찾기
    def find_col(keywords, exclude=None):
        for col in df.columns:
            # exclude 키워드가 있으면 그것이 포함된 컬럼은 건너뜀
            if exclude and any(e in col for e in exclude):
                continue
            if any(k in col for k in keywords):
                return col
        return None
        
    col_name = find_col(['이름', '성명'], exclude=['팀']) or '이름'
    col_birth = find_col(['생년월일', '생일', '000000-2']) or '생년월일'
    col_basic = find_col(['기초생활', '수급']) or '기초생활'
    col_disability = find_col(['장애정도', '장애등급']) or '장애정도'
    col_date = find_col(['날짜', '일자', '일시']) or '날짜'
    col_team = find_col(['팀', '부서']) or '팀'
    col_project = find_col(['세부사업', '사업명', '프로그램']) or '세부사업'
    col_residence = find_col(['거주지', '주소', '지역']) or '거주지'
    col_disability_type = find_col(['장애유형', '장애종류']) or '장애유형'
    # ----------------------------------------------------
    # ★ 근본적인 해결책: GSheets의 실제 컬럼명 우선 사용
    # col_map (find_col) 로직이 GSheets 환경에서 오작동하는 것을 방지하기 위해,
    # 스프레드시트에 고정된 실제 컬럼명을 최우선으로 찾습니다.
    # ----------------------------------------------------
    actual_name_col = '이름' if '이름' in df.columns else col_name
    actual_birth_col = '생년월일' if '생년월일' in df.columns else col_birth
    actual_type_col = '장애유형' if '장애유형' in df.columns else col_disability_type
    actual_deg_col = '장애정도' if '장애정도' in df.columns else col_disability
    actual_team_col = '팀이름' if '팀이름' in df.columns else col_team
    
    # ----------------------------------------------------
    # ★ 기존의 ffill/bfill 로직 삭제
    # 이름이 같다고 해서 생년월일/장애정도를 강제로 덮어씌우면 '동명이인' 데이터가 훼손됨.
    # 빈 칸은 빈 칸 그대로 두어 서로 다른 사람으로 취급되도록 원복합니다.
    # ----------------------------------------------------
    def normalize_birth_col(series):
        result = []
        for val in series.fillna('').astype(str):
            val = val.strip()
            if not val or val in ('nan', 'None', ''):
                result.append('')
                continue
            digits = re.sub(r'[^0-9]', '', val)
            if len(digits) >= 8 and digits[:2] in ('19', '20'):
                result.append(digits[2:8])   # YYYYMMDD → YYMMDD
            elif len(digits) >= 6:
                result.append(digits[:6])    # YYMMDD or YYMMDD-성별 → YYMMDD
            else:
                result.append(digits)
        return pd.Series(result, index=series.index)

    def normalize_text_col(series):
        return series.fillna('').astype(str).str.strip().str.replace(r'\s+', '', regex=True)

    id_parts = []
    for i, col in enumerate([actual_name_col, actual_birth_col, actual_type_col, actual_deg_col]):
        if col in df.columns:
            if i == 1:
                id_parts.append(normalize_birth_col(df[col]))
            else:
                id_parts.append(normalize_text_col(df[col]))
        else:
            id_parts.append(pd.Series([''] * len(df), index=df.index))

    if id_parts:
        df['고유ID'] = id_parts[0] + "_" + id_parts[1] + "_" + id_parts[2] + "_" + id_parts[3]
        
        # 이름/생년월일/유형/정도가 모두 공백인 경우 '___'가 생성되어 한 사람으로 뭉쳐버리는 문제 방지
        mask_blank = df['고유ID'] == '___'
        if mask_blank.any():
            df.loc[mask_blank, '고유ID'] = '미상_' + df.index.astype(str)[mask_blank]
            
        # [진단용] 엑셀과 완전히 똑같이 공백/오타를 유지하는 Raw ID 생성 (사용자 수동 계산 비교용)
        raw_id_parts = []
        for col in [actual_name_col, actual_birth_col, actual_type_col, actual_deg_col]:
            if col in df.columns:
                raw_id_parts.append(df[col].fillna('').astype(str))
            else:
                raw_id_parts.append(pd.Series([''] * len(df), index=df.index))
        df['raw_고유ID'] = raw_id_parts[0] + "_" + raw_id_parts[1] + "_" + raw_id_parts[2] + "_" + raw_id_parts[3]
        if mask_blank.any():
            df.loc[mask_blank, 'raw_고유ID'] = '미상_' + df.index.astype(str)[mask_blank]
            
    else:
        df['고유ID'] = df.index.astype(str)
        df['raw_고유ID'] = df.index.astype(str)

    # '실적' 강제 변환
    actual_perf_col = '실적' if '실적' in df.columns else col_performance
    if actual_perf_col in df.columns:
        df[actual_perf_col] = pd.to_numeric(df[actual_perf_col], errors='coerce').fillna(0)
        
    # 빈칸 채우기
    if col_basic in df.columns:
        df[col_basic] = df[col_basic].fillna('비수급')
    if actual_deg_col in df.columns:
        df[actual_deg_col] = df[actual_deg_col].fillna('정보없음')
        
    # 4. 날짜 데이터 변환 (예: '2026년 1월 2일 금요일' -> datetime)
    if col_date in df.columns:
        def parse_korean_date(x):
            if pd.isna(x): return pd.NaT
            if isinstance(x, (int, float)):
                # 엑셀/구글시트 숫자형 날짜 처리 (1899-12-30 기준)
                try:
                    return pd.to_datetime(x, unit='D', origin='1899-12-30').replace(microsecond=0)
                except:
                    pass
            
            x_str = str(x).strip()
            # 1. '2026-01-01 00:00:00' 형태 직접 파싱 시도 (숫자 추출 전 수행)
            try:
                dt = pd.to_datetime(x_str)
                if pd.notna(dt): return dt
            except:
                pass

            # 2. 숫자 추출 (년, 월, 일)
            nums = re.findall(r'\d+', x_str)
            if len(nums) >= 3:
                try:
                    # YYYY-MM-DD or YY-MM-DD
                    y, m, d = int(nums[0]), int(nums[1]), int(nums[2])
                    if y < 100: y += 2000
                    return pd.to_datetime(f"{y}-{m}-{d}")
                except:
                    pass
            
            return pd.NaT
                
        df['_ParsedDate'] = df[col_date].apply(parse_korean_date)
        df['월'] = df['_ParsedDate'].dt.month
        df['분기'] = df['_ParsedDate'].dt.quarter
        # 요일 정보 추가 (0=월, 6=일)
        df['요일'] = df['_ParsedDate'].dt.dayofweek
        df['요일명'] = df['_ParsedDate'].dt.day_name()
    else:
        df['_ParsedDate'] = pd.NaT
        df['월'] = 1
        df['분기'] = 1
        df['요일'] = 0
        df['요일명'] = 'Monday'
        
    # 지역 분류 (거주지 컬럼 기반)
    if col_residence in df.columns:
        def categorize_residence(x):
            x = str(x)
            if '은평' in x: return '은평'
            if '서울' in x: return '서울'
            if '경기' in x: return '경기'
            return '그외'
        df['_지역'] = df[col_residence].apply(categorize_residence)
    else:
        df['_지역'] = '정보없음'

    # 연령대 분류 (생년월일 데이터 우선, 없을 경우 나이 컬럼 활용)
    col_age = find_col(['만나이', '나이', '연령'])
    
    def group_by_age_num(age):
        try:
            age = float(age)
            if age < 10: return '10대미만'
            elif age < 20: return '10대'
            elif age < 30: return '20대'
            elif age < 40: return '30대'
            elif age < 50: return '40대'
            elif age < 60: return '50대'
            elif age < 70: return '60대'
            elif age < 80: return '70대'
            else: return '80대 이상'
        except:
            return '정보없음'

    if col_birth in df.columns:
        def get_age_group(x):
            if pd.isna(x): return '정보없음'
            x_str = str(x).strip()
            import re
            nums = re.findall(r'\d+', x_str)
            if not nums: return '정보없음'
            
            year = None
            for n in nums:
                if len(n) == 4 and (n.startswith('19') or n.startswith('20')):
                    year = int(n)
                    break
            
            if not year:
                # try YYMMDD or YY.MM.DD
                if len(nums[0]) == 6 or len(nums[0]) == 8:
                    y = int(nums[0][:2])
                    year = 1900 + y if y > 25 else 2000 + y
                elif len(nums[0]) == 2:
                    y = int(nums[0])
                    year = 1900 + y if y > 25 else 2000 + y
                    
            if not year: return '정보없음'
            
            age = 2025 - year
            return group_by_age_num(age)
            
        df['_연령대'] = df[col_birth].apply(get_age_group)
    elif col_age in df.columns:
        df['_연령대'] = df[col_age].apply(group_by_age_num)
    else:
        df['_연령대'] = '정보없음'

    # 장애유형 데이터 정제 (불필요한 값 정리)
    if col_disability_type in df.columns:
        def clean_disability(x):
            if pd.isna(x): return '미등록'
            x = str(x).strip()
            if x == '비장애/미등록': return '미등록'
            elif x == '뇌병변': return '뇌병변장애'
            elif x == '': return '미등록'
            return x
        df[col_disability_type] = df[col_disability_type].apply(clean_disability)
    else:
        df[col_disability_type] = '정보없음'

    # 세부사업 데이터 정제 (합치기 요청 반영: 발달재활 통합)
    if col_project in df.columns:
        def merge_projects(x):
            if pd.isna(x): return x
            x_str = str(x).strip()
            if x_str in ['언어발달', '인지발달', '미술심리', '음악심리']:
                return '발달재활'
            return x_str
        df[col_project] = df[col_project].apply(merge_projects)

    col_performance = find_col(['실적']) or '실적'
    col_unit = find_col(['명/건']) or '명/건'
    
    if col_performance in df.columns:
        df[col_performance] = pd.to_numeric(df[col_performance], errors='coerce').fillna(0)

    # 필요한 컬럼 매핑 저장
    columns_map = {
        '이름': col_name,
        '팀': col_team,
        '세부사업': col_project,
        '장애유형': col_disability_type,
        '실적': col_performance,
        '단위': col_unit,
        '고유ID': '고유ID',
    }
    return df, columns_map

# ================= 차트 유틸리티 및 심층 분석 함수 =================

# ================= 차트 유틸리티 및 심층 분석 함수 =================

def apply_chart_style(fig):
    """범례 크기 조정 및 모든 텍스트 색상 강제 지정. 프리젠테이션 모드에서는 폰트/높이를 키움."""
    _pres = st.session_state.get("presentation_mode", False)
    _font_size   = 16 if _pres else 13
    _legend_size = 16 if _pres else 13
    _tick_size   = 16 if _pres else 12
    _title_size  = 18 if _pres else 15
    _height      = 500 if _pres else None
    _margin      = dict(t=30, b=30, l=60, r=40) if _pres else dict(t=10, b=50, l=50, r=50)

    layout_kwargs = dict(
        legend=dict(itemsizing='constant', font=dict(size=_legend_size, color="#31333F")),
        margin=_margin,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#31333F", size=_font_size),
    )
    if _height is not None:
        layout_kwargs["height"] = _height

    fig.update_layout(**layout_kwargs)
    
    fig.update_xaxes(
        tickfont=dict(color="#31333F", size=_tick_size),
        title_font=dict(color="#31333F", size=_title_size),
        automargin=True
    )
    fig.update_yaxes(
        tickfont=dict(color="#31333F", size=_tick_size),
        title_font=dict(color="#31333F", size=_title_size),
        automargin=True
    )
    return fig

# 1. 월별 이용자 추이 (선 그래프 + 전월대비 %)
def draw_monthly_trend(df_data):
    performance_col = col_map.get('실적', '실적')
    if '월' in df_data.columns:
        # '실적' 합계 기준으로 집계 (단위 '명' 데이터만 들어온 df_yeon 기준)
        if performance_col in df_data.columns:
            monthly_counts = df_data.groupby('월')[performance_col].sum().reset_index(name='이용자수')
        else:
            monthly_counts = df_data.groupby('월').size().reset_index(name='이용자수')
            
        monthly_counts = monthly_counts.sort_values('월')
        
        # 전월 대비 증감률(%) 계산
        monthly_counts['증감률'] = monthly_counts['이용자수'].pct_change() * 100
        monthly_counts['증감률_텍스트'] = monthly_counts['증감률'].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A"
        )
        
        with st.container(border=True):
            st.markdown(f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-bottom:5px;'>📅 월별 이용자 추이 (연인원 합계 기준)</div>", unsafe_allow_html=True)
            fig = px.line(monthly_counts, x='월', y='이용자수', markers=True,
                          text='이용자수',
                          hover_data={'증감률_텍스트': True, '이용자수': ':,.0f'})
            fig.update_traces(line_color=CHART_BLUE, marker=dict(size=10),
                              textposition='top center', texttemplate='<b>%{text:,.0f}</b>')
            fig.update_xaxes(dtick=1, labelalias={i: f"{i}월" for i in range(1, 13)})
            fig.update_yaxes(title="연인원 합계")
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
    else:
        st.info("차트를 그릴 수 있는 월 데이터가 없습니다.")

# 2. 요일별 이용 현황 (막대 차트)
def draw_daily_crowdedness(df_data):
    if '요일' in df_data.columns:
        day_map = {0:'월', 1:'화', 2:'수', 3:'목', 4:'금', 5:'토', 6:'일'}
        daily_counts = df_data.groupby('요일').size().reset_index(name='이용자수')
        daily_counts['요일명'] = daily_counts['요일'].map(day_map)
        daily_counts = daily_counts.sort_values('요일')
        
        with st.container(border=True):
            st.markdown(f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-bottom:5px;'>🕒 요일별 이용 현황</div>", unsafe_allow_html=True)
            fig = px.bar(daily_counts, x='요일명', y='이용자수', 
                         text='이용자수',
                         color='이용자수',
                         color_continuous_scale='Blues')
            fig.update_traces(texttemplate='<b>%{text:,.0f}</b>', textposition='inside')
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)

# 3. 히트맵 (연령대/장애유형 x 세부사업)
def draw_heatmap(df_data, col_map, row_col, title):
    project_col = col_map.get('세부사업', '세부사업')
    if row_col in df_data.columns and project_col in df_data.columns:
        pivot_df = df_data.groupby([row_col, project_col]).size().unstack(fill_value=0)
        
        if not pivot_df.empty:
            with st.container(border=True):
                fig = px.imshow(pivot_df, text_auto=True, aspect="auto",
                                title=f"<b>🔥 {title} vs 세부사업 분석</b>",
                                color_continuous_scale='Reds')
                fig.update_layout(xaxis_title="세부사업", yaxis_title=row_col)
                st.plotly_chart(apply_chart_style(fig), use_container_width=True)
        else:
            st.info(f"{title} 히트맵을 생성할 데이터가 없습니다.")

# 4. '기타' 인원 참여 사업 (Top 10)
def draw_etc_analysis(df_data, col_map):
    name_col = col_map.get('이름', '이름')
    project_col = col_map.get('세부사업', '세부사업')
    
    if name_col in df_data.columns and project_col in df_data.columns:
        df_etc = df_data[df_data[name_col].astype(str).str.contains('기타', na=False)]
        
        if not df_etc.empty:
            etc_stats = df_etc.groupby(project_col).size().reset_index(name='참여수')
            etc_stats = etc_stats.sort_values('참여수', ascending=False).head(10)
            
            with st.container(border=True):
                fig = px.bar(etc_stats, x='참여수', y=project_col, orientation='h',
                             title="<b>👤 '기타' 이용자 참여 Top 10 사업</b>",
                             text='참여수',
                             color='참여수',
                             color_continuous_scale='Greys')
                fig.update_traces(texttemplate='<b>%{text:,.0f}</b>', textposition='inside')
                fig.update_coloraxes(showscale=False)
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(apply_chart_style(fig), use_container_width=True)
        else:
            st.info("'기타' 성명으로 등록된 데이터가 없습니다.")

# 5. 장애유형 분포 (도넛 차트)
def draw_disability_donut(df_data, title_suffix):
    if disability_col in df_data.columns:
        if '인원수' in df_data.columns:
            dist_data = df_data
        else:
            dist_data = df_data.groupby(disability_col).size().reset_index(name='인원수')
            
        if not dist_data.empty and dist_data['인원수'].sum() > 0:
            dist_data = dist_data.sort_values(by='인원수', ascending=False).reset_index(drop=True)
            total_sum = dist_data['인원수'].sum()
            dist_data['_LegendLabel'] = dist_data.apply(
                lambda r: f"{r[disability_col]} ({r['인원수']:,.0f}명, {(r['인원수']/total_sum)*100:.1f}%)", axis=1
            )
            
            chart_labels = []
            for i, row in dist_data.iterrows():
                if i < 5 and str(row[disability_col]) != '비장애':
                    perc = (row['인원수'] / total_sum) * 100
                    chart_labels.append(f"<b>{row[disability_col]}</b><br>{perc:.1f}%")
                else:
                    chart_labels.append("")
            
            with st.container(border=True):
                fig = px.pie(dist_data, names='_LegendLabel', values='인원수', hole=0.45, 
                             title=f"<b>장애유형 분포 ({title_suffix})</b>",
                             color_discrete_sequence=COLOR_PALETTE)
                fig.update_traces(
                    text=chart_labels, textinfo='text', textposition='outside', textfont_size=15,
                    hovertemplate="<b>%{label}</b><br>인원: %{value:,.0f}명<extra></extra>",
                    connector=dict(visible=False)
                )
                fig.update_layout(
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="right", x=1.1, font=dict(size=14)),
                    height=550
                )
                st.plotly_chart(apply_chart_style(fig), use_container_width=True)
        else:
            st.info(f"해당 조건의 {title_suffix} 장애유형 데이터가 없습니다.")

# 6. 연령대 분포 (바 차트)
def draw_age_charts(df_data, title_suffix):
    if '_연령대' in df_data.columns and disability_col in df_data.columns:
        is_disabled = df_data[disability_col] != '비장애'
        groups = [("장애/미등록", df_data[is_disabled], CHART_RED), ("비장애", df_data[~is_disabled], CHART_YELLOW)]
        
        cols = st.columns(2)
        for i, (label, sub_df, color) in enumerate(groups):
            with cols[i]:
                if not sub_df.empty:
                    if '인원수' in sub_df.columns:
                        age_data = sub_df.groupby('_연령대')['인원수'].sum().reset_index()
                    else:
                        age_data = sub_df.groupby('_연령대').size().reset_index(name='인원수')
                        
                    if not age_data.empty:
                        with st.container(border=True):
                            fig = px.bar(age_data, x='_연령대', y='인원수', 
                                           title=f"<b>{label} 연령대 ({title_suffix})</b>",
                                           color_discrete_sequence=[color],
                                           category_orders={"_연령대": ['10대미만', '10대', '20대', '30대', '40대', '50대', '60대', '70대', '80대 이상', '정보없음']},
                                           text='인원수')
                            fig.update_traces(texttemplate='<b>%{text:,.0f}</b>', textposition='inside', textfont_size=16)
                            st.plotly_chart(apply_chart_style(fig), use_container_width=True)
                else:
                    st.write(f"{label} 연령대 데이터 없음")

# ================= 프리젠테이션 모드 세션 상태 초기화 =================
if "presentation_mode" not in st.session_state:
    st.session_state["presentation_mode"] = False
if "pres_slide_idx" not in st.session_state:
    st.session_state["pres_slide_idx"] = 0
if "pres_interval" not in st.session_state:
    st.session_state["pres_interval"] = 5
if "_pres_source_option" not in st.session_state:
    st.session_state["_pres_source_option"] = "2025년 최종본(엑셀)"

# 타이틀 | 프리젠테이션 보기 버튼 | 시간 드롭다운
st.markdown("""
<style>
.main-title-container h1 {
    margin-top: 0 !important;
    padding-top: 0 !important;
    font-size: 2.2rem !important;
}
button[kind="primary"],
button[data-testid="baseButton-primary"],
div.stButton button[kind="primary"] {
    background-color: #BE1E2D !important;
    background: #BE1E2D !important;
    border-color: #BE1E2D !important;
    color: #FFFFFF !important;
    font-size: 16px !important;
    font-weight: 700 !important;
}
button[kind="primary"] *,
button[data-testid="baseButton-primary"] *,
div.stButton button[kind="primary"] p,
div.stButton button[data-testid="baseButton-primary"] p {
    color: #FFFFFF !important;
}
button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover,
div.stButton button[kind="primary"]:hover {
    background-color: #9a1825 !important;
    background: #9a1825 !important;
    border-color: #9a1825 !important;
    color: #FFFFFF !important;
}
div[data-testid="stSelectbox"] {
    margin-top: -5px !important;
}
</style>
""", unsafe_allow_html=True)

_is_pres = st.session_state.get("presentation_mode", False)

if not _is_pres:
    _title_col, _btn_col, _interval_col = st.columns([7.7, 1.5, 0.8], vertical_alignment="center")
    with _title_col:
        st.markdown("<div class='main-title-container'><h1>📊 이용자 현황 분석 대시보드</h1></div>", unsafe_allow_html=True)
    with _btn_col:
        if st.button("🎥 프리젠테이션 보기", key="pres_main_btn", use_container_width=True, type="primary"):
            st.session_state["presentation_mode"] = True
            st.session_state["pres_slide_idx"] = 0
            st.rerun()
    with _interval_col:
        st.session_state["pres_interval"] = st.selectbox(
            "간격",
            options=[5, 10],
            format_func=lambda x: f"{x}초",
            index=0 if st.session_state.get("pres_interval", 5) == 5 else 1,
            key="pres_interval_select",
            label_visibility="collapsed"
        )
    # JS: 렌더링 후 첫 번째 가로 행을 강제로 한 줄 유지 (flex-wrap 강제 override)
    st.markdown("""
    <script>
    (function fixHeaderRow() {
        var attempts = 0;
        var maxAttempts = 30;
        function tryFix() {
            var blocks = window.parent.document.querySelectorAll('[data-testid="stHorizontalBlock"]');
            if (blocks.length > 0) {
                var firstBlock = blocks[0];
                firstBlock.style.setProperty('flex-wrap', 'nowrap', 'important');
                firstBlock.style.setProperty('flex-direction', 'row', 'important');
                firstBlock.style.setProperty('align-items', 'center', 'important');
                var cols = firstBlock.querySelectorAll('[data-testid="stColumn"]');
                cols.forEach(function(col) {
                    col.style.setProperty('min-width', '0', 'important');
                    col.style.setProperty('overflow', 'hidden', 'important');
                });
            } else if (attempts < maxAttempts) {
                attempts++;
                setTimeout(tryFix, 100);
            }
        }
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', tryFix);
        } else {
            tryFix();
        }
    })();
    </script>
    """, unsafe_allow_html=True)
else:
    _exit_col = st.columns([9.25, 0.75])[1]
    with _exit_col:
        if st.button("❌ 종료", key="pres_exit_btn", use_container_width=True, type="primary"):
            st.session_state["presentation_mode"] = False
            st.rerun()

# ================= 데이터 소스 설정 (메인 화면, 프리젠테이션 모드에서는 숨김) =================
DEFAULT_GSHEETS_URL = "https://docs.google.com/spreadsheets/d/1EZ1wmywG0i5Plv1Rxppatyn-mlNwp_uPKIFzdm-TY9c/edit?gid=0#gid=0"

if not _is_pres:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-bottom:10px;'>🛠️ 데이터 소스 선택</div>", unsafe_allow_html=True)
        source_option = st.radio(
            "분석할 데이터를 선택해 주세요:",
            ["2026년 실시간(구글 스프레드시트)", "2025년 최종본(엑셀)"],
            index=0,
            label_visibility="collapsed"
        )
        st.session_state["_pres_source_option"] = source_option

        if source_option == "2026년 실시간(구글 스프레드시트)":
            spreadsheet_url = DEFAULT_GSHEETS_URL
            data_source = spreadsheet_url
            st.session_state["_pres_data_source"] = data_source
        else:
            uploaded_file = st.file_uploader("📂 엑셀 파일 업로드 (.xlsx)", type=['xlsx'], label_visibility="collapsed")
            if uploaded_file is not None:
                data_source = uploaded_file
            else:
                data_source = "2025실적데이터.xlsx"
                st.info("ℹ️ 업로드된 파일이 없어 '2025실적데이터.xlsx'를 기본으로 사용합니다.")
            st.session_state["_pres_data_source"] = data_source
else:
    source_option = st.session_state.get("_pres_source_option", "2026년 실시간(구글 스프레드시트)")
    data_source = st.session_state.get("_pres_data_source", DEFAULT_GSHEETS_URL)

with st.spinner("데이터를 불러오고 처리하는 중입니다..."):
    if source_option == "2025년 최종본(엑셀)":
        df, col_map = load_data_excel(data_source)
    else:
        if "docs.google.com/sheets" not in str(data_source) and "docs.google.com/spreadsheets" not in str(data_source):
            df, col_map = pd.DataFrame(), "올바른 구글 스프레드시트 URL 형식이 아닙니다."
        else:
            df, col_map = load_data_gsheets(data_source)

# 데이터 로딩 오류 처리
if isinstance(col_map, str) or df.empty:
    error_msg = col_map if isinstance(col_map, str) else "데이터가 비어 있습니다."
    st.error(f"⚠️ 데이터 처리 중 오류가 발생했습니다: {error_msg}")
    st.info("💡 엑셀 파일의 컬럼명이나 구글 시트의 탭 이름('취합_자동') 및 공유 권한을 확인해 주세요.")
    st.stop()

# ================= 필터 사이드바 =================
st.sidebar.header("🔍 필터 설정")

def checkbox_group(label, options, key_prefix, is_sidebar=True, expanded=False, default_all=True):
    """
    세션 상태를 활용한 강력한 전체 선택/해제 기능이 포함된 체크박스 그룹입니다.
    """
    # 키에 한글이 섞이면 윈도우 환경에서 인코딩 오류가 날 수 있어 ASCII 기반 인덱스 사용 권장
    all_key = f"{key_prefix}_all"
    
    # 1. 초기화
    if all_key not in st.session_state:
        st.session_state[all_key] = default_all
    
    for i, opt in enumerate(options):
        opt_key = f"{key_prefix}_{i}"
        if opt_key not in st.session_state:
            st.session_state[opt_key] = st.session_state[all_key]

    # 2. 콜백 함수: 전체 선택 상태가 바뀔 때
    def on_all_change():
        new_val = st.session_state.get(all_key, False)
        for i in range(len(options)):
            st.session_state[f"{key_prefix}_{i}"] = new_val

    # 3. 콜백 함수: 개별 항목이 바뀔 때
    def on_item_change():
        is_all_checked = all(st.session_state.get(f"{key_prefix}_{i}", False) for i in range(len(options)))
        st.session_state[all_key] = is_all_checked
        # st.rerun() 제거: 콜백 내부에서는 no-op이기 때문

    container = st.sidebar.expander(label, expanded=expanded) if is_sidebar else st.container()
    
    selected = []
    with container:
        st.checkbox("전체선택", key=all_key, on_change=on_all_change)
        st.markdown('<div style="margin-top:-10px; margin-bottom:10px; border-top:1px solid #ddd;"></div>', unsafe_allow_html=True)
        for i, opt in enumerate(options):
            opt_label = f"{opt}월" if "month" in key_prefix else str(opt)
            if st.checkbox(opt_label, key=f"{key_prefix}_{i}", on_change=on_item_change):
                selected.append(opt)
                
    return selected

# 1. 팀 필터 (체크박스)
team_col = col_map['팀']
if team_col in df.columns:
    teams = sorted([str(x) for x in df[team_col].dropna().unique()])
    selected_teams = checkbox_group("팀 선택", teams, "team_filter")
else:
    selected_teams = []

# 2. 월 필터 (체크박스)
months = list(range(1, 13))
selected_months = checkbox_group("월 선택", months, "month_filter")

# 3. 거주지 필터 (체크박스)
residence_opts = ['서울', '은평', '경기', '그외']
selected_residence = checkbox_group("거주지 선택", residence_opts, "res_filter")

# 4. 장애유형 필터 (체크박스) - 실제 데이터에서 동적으로 로드
disability_col = col_map['장애유형']
if disability_col in df.columns:
    # 하드코딩 목록 대신 실제 데이터에 있는 값 전체를 사용 (순서는 고정 목록 기준 정렬)
    preferred_order = ['지체장애', '뇌병변장애', '시각장애', '청각장애', '언어장애', '안면장애',
                       '뇌전증장애', '호흡기장애', '장루요루장애', '간장애', '심장장애', '신장장애',
                       '지적장애', '자폐성장애', '정신장애', '미등록', '비장애']
    actual_disabilities = [str(x) for x in df[disability_col].dropna().unique() if str(x).strip() != '']
    # 선호 순서대로 정렬 (목록에 없는 값은 뒤에 추가)
    ordered = [d for d in preferred_order if d in actual_disabilities]
    extras = sorted([d for d in actual_disabilities if d not in preferred_order])
    all_disabilities = ordered + extras
    selected_disabilities = checkbox_group("장애유형 선택", all_disabilities, "dis2_filter")
else:
    selected_disabilities = []

# 5. 연령대 필터 (체크박스)
age_groups = ['10대미만', '10대', '20대', '30대', '40대', '50대', '60대', '70대', '80대 이상', '정보없음']
if '_연령대' in df.columns:
    selected_ages = checkbox_group("연령대 선택", age_groups, "age_filter")
else:
    selected_ages = []

# 필터 적용
filtered_df = df.copy()

if team_col in filtered_df.columns:
    filtered_df = filtered_df[filtered_df[team_col].astype(str).isin(selected_teams)]

filtered_df = filtered_df[filtered_df['월'].isin(selected_months)]

if '_지역' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['_지역'].isin(selected_residence)]

if disability_col in filtered_df.columns:
    filtered_df = filtered_df[filtered_df[disability_col].isin(selected_disabilities)]

if '_연령대' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['_연령대'].isin(selected_ages)]


# ================= 핵심 지표 계산 =================
performance_col = col_map.get('실적', '실적')
name_col = col_map.get('이름', '이름')
team_col = col_map.get('팀', '팀')

# ★ 근본적인 해결책: 컬럼 자동 매핑(col_map)이 GSheets에서 오작동하고 있을 확률이 높음.
# 스프레드시트의 실제 컬럼명인 '명/건'을 명시적으로 찾아 사용.
actual_unit_col = None
if '명/건' in filtered_df.columns:
    actual_unit_col = '명/건'
elif col_map.get('단위') in filtered_df.columns:
    actual_unit_col = col_map.get('단위')
elif '단위' in filtered_df.columns:
    actual_unit_col = '단위'

# ================================================================
# 지표별 집계 방식 (데이터 소스 분리 적용)
# ================================================================

# --- 공통 전처리: '명' 단위 행 추출 ---
if actual_unit_col and actual_unit_col in filtered_df.columns:
    cleaned_unit = filtered_df[actual_unit_col].astype(str).str.strip()
    is_person = (cleaned_unit == '명') | (cleaned_unit == '명(실인원)')
    df_person = filtered_df[is_person].copy()
else:
    df_person = filtered_df.copy()

# ================= 데이터 소스 통합 집계 로직 =================
# 1. 연인원: '명' 행의 실적 합산 (기타 포함)
if performance_col in df_person.columns:
    df_person[performance_col] = pd.to_numeric(df_person[performance_col], errors='coerce').fillna(0)
    총연인원 = df_person[performance_col].sum()
else:
    총연인원 = len(df_person)

# --- 실인원/중복실인원 기준 컬럼: 실제 스프레드시트 컬럼명 직접 매핑 ---
_col_name  = '이름'     if '이름'     in df_person.columns else name_col
_col_birth = '생년월일' if '생년월일' in df_person.columns else None
_col_dtype = '장애유형' if '장애유형' in df_person.columns else None
_col_ddeg  = '장애정도' if '장애정도' in df_person.columns else None
_col_team  = '팀이름'   if '팀이름'   in df_person.columns else (team_col if team_col in df_person.columns else None)

# 실인원용 4개 컬럼 / 중복실인원용 5개 컬럼 (존재하는 컬럼만)
_uniq_cols_4 = [c for c in [_col_name, _col_birth, _col_dtype, _col_ddeg] if c and c in df_person.columns]
_uniq_cols_5 = [c for c in [_col_name, _col_birth, _col_dtype, _col_ddeg, _col_team] if c and c in df_person.columns]

# 2. 실인원 처리를 위해 '기타' 제외
if _col_name in df_person.columns:
    _is_etc = df_person[_col_name].astype(str).str.contains('기타', na=False)
    _df_for_uniq = df_person[~_is_etc].copy()
else:
    _df_for_uniq = df_person.copy()

# 3. 총실인원: 4컬럼 기준 중복 제거 후 남은 행의 개수
if _uniq_cols_4:
    총실인원 = len(_df_for_uniq[_uniq_cols_4].drop_duplicates())
else:
    총실인원 = len(_df_for_uniq)

# 4. 중복실인원: 5컬럼(팀이름 포함) 기준 중복 제거 후 남은 행의 개수
if _uniq_cols_5:
    중복실인원 = len(_df_for_uniq[_uniq_cols_5].drop_duplicates())
else:
    중복실인원 = 총실인원

# 4. 일평균 이용자: 연인원 / 운영 일수 (주말 및 법정공휴일 제외)
def get_biz_days(parsed_dates):
    if len(parsed_dates) == 0: return 0
    start_date = parsed_dates.min().date()
    end_date = parsed_dates.max().date()
    
    # 한국 법정공휴일 (2025-2026)
    holidays = [
        # 2025
        "2025-01-01", "2025-01-28", "2025-01-29", "2025-01-30", "2025-03-01", "2025-03-03", 
        "2025-05-05", "2025-05-06", "2025-06-06", "2025-08-15", "2025-10-03", "2025-10-05", 
        "2025-10-06", "2025-10-07", "2025-10-08", "2025-10-09", "2025-12-25",
        # 2026
        "2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18", "2026-03-01", "2026-03-02",
        "2025-05-05", "2025-05-06", "2025-06-06", "2025-08-15", "2025-10-03", "2025-10-05", 
        "2025-10-06", "2025-10-07", "2025-10-08", "2025-10-09", "2025-12-25",
        # 2026
        "2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18", "2026-03-01", "2026-03-02",
        "2026-05-05", "2026-05-24", "2026-05-25", "2026-06-06", "2026-08-15", "2026-08-17",
        "2026-09-24", "2026-09-25", "2026-09-26", "2026-10-03", "2026-10-05", "2026-10-09",
        "2026-12-25"
    ]
    holiday_set = set(pd.to_datetime(holidays).date)
    
    # 선택된 범위 내의 모든 날짜 생성
    all_dates = pd.date_range(start=start_date, end=end_date).date
    # 주말(5,6) 및 공휴일 제외
    biz_list = [d for d in all_dates if d.weekday() < 5 and d not in holiday_set]
    return len(biz_list)

if '_ParsedDate' in filtered_df.columns:
    valid_dates = filtered_df['_ParsedDate'].dropna()
    biz_days = get_biz_days(valid_dates)
else:
    biz_days = 0

일평균이용자 = 총연인원 / biz_days if biz_days > 0 else 0

# ================= 일반 대시보드 UI (프리젠테이션 모드 OFF시에만 표시) =================
if not st.session_state.get("presentation_mode", False):
    st.markdown(f"<h3 style='color: {BRAND_GRAY}; border-left: 5px solid {BRAND_RED}; padding-left: 10px; margin-bottom: 20px;'>📈 주요 실적 요약</h3>", unsafe_allow_html=True)
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 연인원", f"{총연인원:,.0f} 명")
        col2.metric("총 실인원", f"{총실인원:,.0f} 명")
        col3.metric("중복 실인원", f"{중복실인원:,.0f} 명")
        if biz_days > 0:
            col4.metric("일평균 이용자", f"{일평균이용자:,.1f} 명")
        else:
            col4.metric("일평균 이용자", "-")





# ================= 연인원 전용 차트 함수 =================

# ================= 연인원 전용 차트 함수 =================

# 1. 장애유형별 이용 현황 (도넛 그래프 / 가로 막대 그래프 전환)
def draw_disability_bar_yeon(df_yeon, col_map, title_label="연인원"):
    disability_col = col_map.get('장애유형', '장애유형')
    perf_col = col_map.get('실적', '실적')
    
    if disability_col in df_yeon.columns:
        if title_label == "실인원":
            dist_data = df_yeon.groupby(disability_col).size().reset_index(name='실적')
        else:
            dist_data = df_yeon.groupby(disability_col)[perf_col].sum().reset_index(name='실적')
        dist_data = dist_data[dist_data['실적'] > 0]
        
        if not dist_data.empty:
            dist_data = dist_data.sort_values(by='실적', ascending=True).reset_index(drop=True)
            total_sum = dist_data['실적'].sum()
            
            with st.container(border=True):
                st.markdown(f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-bottom:5px;'>📊 장애유형별 이용 현황 ({title_label}: {total_sum:,.0f}명)</div>", unsafe_allow_html=True)
                
                color = CHART_RED if title_label == "실인원" else BRAND_BLUE
                fig = px.bar(dist_data, x='실적', y=disability_col, orientation='h',
                             text='실적', color_discrete_sequence=[color])
                
                fig.update_traces(texttemplate='<b>%{text:,.0f}</b>', textposition='inside')
                fig.update_layout(
                    xaxis_title="인원(명)", 
                    yaxis_title="장애유형",
                    margin=dict(t=10, b=10, l=10, r=40),
                    height=max(400, len(dist_data) * 25 + 100)
                )
                st.plotly_chart(apply_chart_style(fig), use_container_width=True)

def draw_disability_donut_yeon(df_yeon, col_map, title_label="연인원", target_col=None, custom_title=None, center_label=None):
    disability_col = target_col if target_col else col_map.get('장애유형', '장애유형')
    perf_col = col_map.get('실적', '실적')
    
    if disability_col in df_yeon.columns:
        # 장애유형별 실적 집계 (연인원이면 합산, 실인원이면 인원수)
        if title_label == "실인원":
            dist_data = df_yeon.groupby(disability_col).size().reset_index(name='실적')
        else:
            dist_data = df_yeon.groupby(disability_col)[perf_col].sum().reset_index(name='실적')
        dist_data = dist_data[dist_data['실적'] > 0]
        
        if not dist_data.empty:
            dist_data = dist_data.sort_values(by='실적', ascending=False).reset_index(drop=True)
            total_sum = dist_data['실적'].sum()
            
            # 범례용 텍스트 (유형 실적명 (%))
            dist_data['_범례'] = dist_data.apply(
                lambda r: f"{r[disability_col]} {r['실적']:,.0f}명 ({(r['실적']/total_sum)*100:.1f}%)", axis=1
            )
            
            # 상위 5개는 차트 안에 표시 (유형과 % 만)
            chart_labels = []
            for i, row in dist_data.iterrows():
                if i < 5:
                    perc = (row['실적'] / total_sum) * 100
                    chart_labels.append(f"<b>{row[disability_col]}</b><br>{perc:.1f}%")
                else:
                    chart_labels.append("")
            
            # 채도 조절된 브랜드 컬러 (연인원=파랑, 실인원=빨강 차별화)
            if title_label == "실인원":
                colors = ["#7A7A7A", BRAND_RED, "#9E9E9E", CHART_RED, "#BDBDBD", "#EF9A9A", "#D6D6D6", "#FFCDD2"]
            else:
                colors = ["#7A7A7A", BRAND_BLUE, "#9E9E9E", "#64B5F6", "#BDBDBD", "#BBDEFB", "#D6D6D6", "#90CAF9"]
            
            
            with st.container(border=True):
                display_title = custom_title if custom_title else f"♿ 장애유형별 이용 현황 ({title_label}: {total_sum:,.0f}명)"
                _pres = st.session_state.get("presentation_mode", False)
                _label_size = 18 if _pres else 13
                _legend_fsize = 18 if _pres else 12
                st.markdown(f"<div style='font-size:{24 if _pres else 18}px; font-weight:bold; color:{BRAND_GRAY}; margin-bottom:5px;'>{display_title}</div>", unsafe_allow_html=True)
                fig = px.pie(dist_data, names='_범례', values='실적', hole=0.5, 
                             color_discrete_sequence=colors)
                
                # 공통 스타일 먼저 적용
                fig = apply_chart_style(fig)
                
                # 사용자 요청 세부 스타일 덮어쓰기
                fig.update_traces(
                    text=chart_labels, textinfo='text', textposition='outside', textfont_size=_label_size,
                    hovertemplate="<b>%{label}</b><br>실적: %{value:,.0f}<extra></extra>",
                    domain=dict(x=[0.2, 0.55], y=[0.2, 0.8])
                )
                fig.update_layout(
                    showlegend=True,
                    legend=dict(
                        x=0.65, xanchor='left',
                        y=0.5, yanchor='middle',
                        font=dict(size=_legend_fsize)
                    ),
                    margin=dict(t=0, b=0, l=0, r=0, pad=0),
                    height=500,
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                # 중앙 라벨 추가 (특정 유형 분석 시)
                if center_label:
                    fig.add_annotation(
                        text=f"<b>{center_label}</b>",
                        showarrow=False,
                        font=dict(size=18, color=BRAND_GRAY),
                        x=0.375, y=0.5, # 도넛 중앙 위치 조정 (domain x=[0.2, 0.55])
                        xref="paper", yref="paper"
                    )
                
                st.plotly_chart(fig, use_container_width=True)

# 2 & 3. 연급대별 현황 (막대 그래프)
def draw_age_bar_custom(df_yeon, is_disabled=True, title_label="연인원"):
    disability_col = col_map.get('장애유형', '장애유형')
    perf_col = col_map.get('실적', '실적')
    title = "장애/미등록 연령대" if is_disabled else "비장애 연령대"
    color = CHART_RED if is_disabled else CHART_BLUE
    
    # 필터링
    if is_disabled:
        sub_df = df_yeon[df_yeon[disability_col] != '비장애']
    else:
        sub_df = df_yeon[df_yeon[disability_col] == '비장애']
    
    if not sub_df.empty and '_연령대' in sub_df.columns:
        if title_label == "실인원":
            age_data = sub_df.groupby('_연령대').size().reset_index(name='실적')
        else:
            age_data = sub_df.groupby('_연령대')[perf_col].sum().reset_index(name='실적')
            
        max_val = age_data['실적'].max() if not age_data.empty else 100
        total_sub = age_data['실적'].sum()
        
        with st.container(border=True):
            _pres = st.session_state.get("presentation_mode", False)
            _bar_txt = 18 if _pres else 12
            st.markdown(f"<div style='font-size:{24 if _pres else 18}px; font-weight:bold; color:{BRAND_GRAY}; margin-bottom:5px;'>👥 {title} ({title_label}: {total_sub:,.0f}명)</div>", unsafe_allow_html=True)
            fig = px.bar(age_data, x='_연령대', y='실적',
                         color_discrete_sequence=[color],
                         category_orders={"_연령대": ['10대미만', '10대', '20대', '30대', '40대', '50대', '60대', '70대', '80대 이상', '정보없음']},
                         text='실적')
            fig.update_traces(texttemplate='<b>%{text:,.0f}</b>', textposition='inside', textfont_size=_bar_txt)
            # apply_chart_style 먼저 적용 (전체 스타일 + 축 폰트 크기)
            fig = apply_chart_style(fig)
            fig.update_layout(margin=dict(t=10))
            fig.update_xaxes(title_text="연령대")
            fig.update_yaxes(title_text="실적 합계", range=[0, max_val * 1.2])
            st.plotly_chart(fig, use_container_width=True)

# 4. 익명 참여자 분석 (Top 5 - 트리맵 방식 또는 프레젠테이션 모드 도넛)
def draw_etc_top10_yeon(df_yeon, col_map, presentation_mode=False):
    name_col = col_map.get('이름', '이름')
    project_col = col_map.get('세부사업', '세부사업')
    team_col = col_map.get('팀', '팀')
    perf_col = col_map.get('실적', '실적')
    
    df_etc = df_yeon[df_yeon[name_col].astype(str).str.contains('기타', na=False)].copy()
    
    if not df_etc.empty:
        if team_col in df_etc.columns:
            mask_8gihek = df_etc[team_col].astype(str).str.contains('8기획', na=False)
            mask_target_project = df_etc[project_col].astype(str).str.contains('이용자욕구만족도조사', na=False)
            df_etc = df_etc[~(mask_8gihek & ~mask_target_project)]
            
        etc_stats = df_etc.groupby(project_col)[perf_col].sum().reset_index(name='실적')
        etc_stats = etc_stats.sort_values('실적', ascending=False).head(5)
        total_etc = etc_stats['실적'].sum()
        
        if not etc_stats.empty:
            # --- 시각화 전용 로직: 영역 비중 조절 (중식제공 50% 고정) ---
            others_mask = ~etc_stats[project_col].astype(str).str.contains('중식', na=False)
            others_sum = etc_stats.loc[others_mask, '실적'].sum()
            
            etc_stats['visual_weight'] = etc_stats['실적'].copy()
            etc_stats.loc[~others_mask, 'visual_weight'] = others_sum if others_sum > 0 else 1.0
            
            etc_stats['비중'] = (etc_stats['실적'] / total_etc) * 100
            
            if presentation_mode:
                # --- 프레젠테이션 모드 전용 로직: 대형 도넛 차트 ---
                with st.container(border=True):
                    st.markdown(
                        f"<div style='font-size:24px;font-weight:bold;color:{BRAND_GRAY}'>"
                        f"⭐ <span style='color:{BRAND_GRAY} !important;'>기타(익명)</span> 선호 프로그램 (Top 5) "
                        f"<span style='font-size:16px;color:#888 !important;'>*연인원: {total_etc:,.0f}명</span></div>",
                        unsafe_allow_html=True
                    )
                    
                    colors_p = [BRAND_GRAY, CHART_GRAY, "#BDBDBD", "#D6D6D6", "#EBEBEB", "#999999"]
                    
                    chart_labels_p = []
                    legend_texts = []
                    for i, (_, r) in enumerate(etc_stats.iterrows()):
                        chart_labels_p.append(f"<b>{r[project_col]}</b><br>{r['비중']:.1f}%")
                        legend_texts.append(f"{r[project_col]} {r['실적']:,.0f}명 ({r['비중']:.1f}%)")
                    etc_stats['_legend'] = legend_texts
                    
                    fig_p = px.pie(etc_stats, names='_legend', values='visual_weight', hole=0.48,
                                  color_discrete_sequence=colors_p, custom_data=['실적', project_col])
                    
                    fig_p = apply_chart_style(fig_p)  # 스타일 먼저 적용 (이후 layout 업데이트로 폰트 크기 덮어씀)
                    
                    fig_p.update_traces(
                        rotation=75,
                        text=chart_labels_p, textinfo='text', textposition='outside',
                        textfont_size=17,
                        hovertemplate="<b>%{customdata[1]}</b><br>실적: %{customdata[0]:,.0f}명 (%{percent:.1%})<extra></extra>",
                        domain=dict(x=[0.1, 0.55], y=[0.1, 0.9])
                    )
                    fig_p.update_layout(
                        showlegend=True,
                        legend=dict(x=0.65, xanchor='left', y=0.5, yanchor='middle', font=dict(size=18)),
                        margin=dict(t=0, b=0, l=0, r=0), height=500,
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_p, use_container_width=True)
            else:
                # --- 일반 대시보드 모드: 슬림 트리맵 ---
                with st.container(border=True): # 연령대 그래프와 똑같은 디자인의 박스
                    # 상단 연령대 차트와 타이틀 스타일 완벽 동기화 (폰트, 굵기, 아이콘)
                    st.markdown(f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-bottom:5px;'>👤 '기타' 이용자 참여 비중 분석 (연인원: {total_etc:,.0f}명)</div>", unsafe_allow_html=True)
                    
                    # values는 영역 크기 제어용(visual_weight), color는 색상 농도 제어용(실적)
                    fig = px.treemap(etc_stats, path=[project_col], values='visual_weight',
                                     color='실적',
                                     custom_data=['실적'],
                                     color_continuous_scale=[[0, '#FFF9E1'], [1, BRAND_YELLOW]])
                    
                    fig.update_traces(
                        texttemplate="<b>%{label}</b><br>%{customdata[0]:,.0f}", # 사업명 + 실제 실적 인원수 표시
                        hovertemplate="<b>%{label}</b><br>실적: %{customdata[0]:,.0f}명<extra></extra>",
                        textfont=dict(color="#333333", size=12, family="Arial Black"), # 12px 고정
                        marker=dict(line=dict(width=1, color='white'))
                    )
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', # 회색 배경 완전 제거
                        plot_bgcolor='rgba(0,0,0,0)',  # 회색 배경 완전 제거
                        margin=dict(t=0, b=0, l=0, r=0), # 여백 0으로 밀착
                        height=150 # 슬림한 가로 바 형태
                    )
                    fig.update_coloraxes(showscale=False)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("'기타' 성명으로 등록된 이용 내역이 없습니다. (세부사업 조회 실패)")
    else:
        st.info("'기타' 성명으로 등록된 데이터가 없습니다.")

# 7. 장애유형별 선호 프로그램 (가로 막대그래프)
def draw_preferred_bar_disability(df_yeon, col_map):
    group_col = col_map.get('장애유형', '장애유형')
    project_col = col_map.get('세부사업', '세부사업')
    perf_col = col_map.get('실적', '실적')
    
    # 1. 장애유형 정렬 및 그룹 정의
    disability_order = [
        '지체장애', '뇌병변장애', '시각장애', '청각장애', '언어장애', 
        '신장장애', '심장장애', '간장애', '장루요루장애', '뇌전증장애', 
        '지적장애', '자폐성장애', '정신장애', '미등록', '비장애'
    ]
    
    group_map = {
        '지체장애': 'Red', '뇌병변장애': 'Red', '시각장애': 'Red', '청각장애': 'Red', '언어장애': 'Red',
        '신장장애': 'Blue', '심장장애': 'Blue', '간장애': 'Blue', '장루요루장애': 'Blue', '뇌전증장애': 'Blue',
        '지적장애': 'Yellow', '자폐성장애': 'Yellow', '정신장애': 'Yellow',
        '미등록': 'Gray', '비장애': 'Gray'
    }

    group_palettes = {
        'Red': [BRAND_RED, "#D65C69", "#E98C8E", "#F2B0B2", "#F9D4D5"],
        'Blue': [BRAND_BLUE, CHART_BLUE, "#A4CAD2", "#C6E0E6", "#E3EFF2"],
        'Yellow': [BRAND_YELLOW, CHART_YELLOW, "#F9D59B", "#FBE6C4", "#FDF3E2"],
        'Gray': [BRAND_GRAY, CHART_GRAY, "#BDBDBD", "#D6D6D6", "#EBEBEB"]
    }

    if group_col in df_yeon.columns and project_col in df_yeon.columns:
        with st.container(border=True):
            # 2. 제목 및 로컬 팝오버 필터 (상단 배치, 비율 조정으로 필터 크기 축소)
            col_title, col_filter = st.columns([3, 1])
            with col_title:
                st.markdown(f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-top:5px;'>♿ 장애유형별 선호 프로그램 (비중 분석) <span style='font-size:12px; font-weight:normal; color:#888;'>&nbsp;&nbsp;*중식제공 사업 제외</span></div>", unsafe_allow_html=True)
            
            with col_filter:
                available_types = [t for t in disability_order if t in df_yeon[group_col].unique()]
                with st.popover("분석할 장애유형 선택", use_container_width=True):
                    actual_selection = checkbox_group("장애유형 선택", available_types, f"pref_dis_{group_col}", is_sidebar=False)
            
            if not actual_selection:
                st.info("장애유형을 최소 하나 이상 선택해 주세요.")
                return

            # 3. 데이터 필터링 및 전처리
            df_filtered = df_yeon[df_yeon[group_col].isin(actual_selection)].copy()
            df_filtered = df_filtered[~df_filtered[project_col].astype(str).str.contains('중식', na=False)]
            
            stats = df_filtered.groupby([group_col, project_col])[perf_col].sum().reset_index()
            
            # 각 그룹별 상위 5개 추출 및 순위 부여
            top_stats = stats.sort_values([group_col, perf_col], ascending=[True, False]).groupby(group_col).head(5).copy()
            top_stats['rank'] = top_stats.groupby(group_col).cumcount()
            
            if top_stats.empty:
                st.warning("데이터가 없습니다.")
                return

            group_sums = top_stats.groupby(group_col)[perf_col].transform('sum')
            top_stats['비중'] = (top_stats[perf_col] / group_sums) * 100
            
            # 4. 컬러 매핑 (그룹별 채도 적용용 고유 키 생성)
            top_stats['color_key'] = top_stats.apply(lambda row: f"{row[group_col]}_{row['rank']}", axis=1)
            
            color_map = {}
            for _, row in top_stats.iterrows():
                grp = group_map.get(row[group_col], 'Gray')
                palette = group_palettes[grp]
                color_map[row['color_key']] = palette[min(row['rank'], len(palette)-1)]

            # 5. 시각화
            fig = px.bar(top_stats, x='비중', y=group_col, color='color_key',
                         orientation='h',
                         color_discrete_map=color_map,
                         custom_data=[perf_col, '비중', project_col, 'rank'],
                         category_orders={group_col: [t for t in disability_order if t in actual_selection]})
            
            # 상위 1위(rank 0)와 나머지 구분하여 텍스트 스타일 적용
            def update_trace_style(t):
                # t.name은 '장애유형_순위' 형식 (예: '지체장애_0')
                if t.name.endswith('_0'):
                    # 1위: 가로 배치, 큰 글씨 (13pt)
                    t.update(
                        texttemplate='<b>%{customdata[2]} %{customdata[0]:,.0f}명 (%{customdata[1]:.1f}%)</b>',
                        textfont_size=13,
                        textposition='inside',
                        insidetextanchor='middle'
                    )
                else:
                    # 2위 이하: 줄바꿈 배치, 일반 글씨 (10pt)
                    t.update(
                        texttemplate='<b>%{customdata[2]}<br>%{customdata[0]:,.0f}명 (%{customdata[1]:.1f}%)</b>',
                        textfont_size=10,
                        textposition='inside',
                        insidetextanchor='middle'
                    )
            
            fig.for_each_trace(update_trace_style)
            
            fig.update_layout(
                showlegend=False,
                xaxis_title="프로그램별 참여 비중 (%)",
                yaxis_title="장애유형",
                # 상단 제목/필터 공간을 위해 상단 여백 추가
                height=max(400, min(800, len(actual_selection) * 50 + 100)),
                margin=dict(t=10, b=10, l=10, r=10),
                barmode='stack'
            )
            fig.update_xaxes(range=[0, 100])
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)

# 8. 연령대별 선호 프로그램 (가로 막대그래프)
def draw_preferred_bar_age(df_yeon, col_map, presentation_mode=False):
    project_col = col_map.get('세부사업', '세부사업')
    perf_col = col_map.get('실적', '실적')
    group_col = '_연령대'
    
    age_order = ['10대미만', '10대', '20대', '30대', '40대', '50대', '60대', '70대', '80대 이상']

    if group_col in df_yeon.columns and project_col in df_yeon.columns:
        with st.container(border=True):
            if not presentation_mode:
                col_title, col_filter = st.columns([3, 1])
                with col_title:
                    st.markdown(f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-top:5px;'>👥 연령대별 선호 프로그램 (비중 히트맵) <span style='font-size:12px; font-weight:normal; color:#888;'>&nbsp;&nbsp;*중식제공 제외</span></div>", unsafe_allow_html=True)
                
                with col_filter:
                    available_ages = [a for a in age_order if a in df_yeon[group_col].unique()]
                    with st.popover("분석할 연령대 선택", use_container_width=True):
                        actual_selection = checkbox_group("연령대 선택", available_ages, f"pref_age_{group_col}", is_sidebar=False)
            else:
                st.markdown(f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-top:5px; margin-bottom:15px;'>👥 연령대별 선호 프로그램 (비중 히트맵) <span style='font-size:12px; font-weight:normal; color:#888;'>&nbsp;&nbsp;*중식제공 사업 제외</span></div>", unsafe_allow_html=True)
                available_ages = [a for a in age_order if a in df_yeon[group_col].unique()]
                
                # 프리젠테이션이 시작될 때 현재 session state를 따르거나, 없으면 전체 선택 반환
                actual_selection = []
                all_key = f"pref_age_{group_col}_all"
                if st.session_state.get(all_key, True):
                    actual_selection = available_ages
                else:
                    for i, opt in enumerate(available_ages):
                        if st.session_state.get(f"pref_age_{group_col}_{i}", False):
                            actual_selection.append(opt)
                if not actual_selection:
                    actual_selection = available_ages
            
            if not actual_selection:
                st.info("연령대를 최소 하나 이상 선택해 주세요.")
                return

            df_filtered = df_yeon[df_yeon[group_col].isin(actual_selection)].copy()
            df_filtered = df_filtered[~df_filtered[project_col].astype(str).str.contains('중식', na=False)]
            
            if df_filtered.empty:
                st.warning("조건에 맞는 데이터가 없습니다.")
                return

            stats = df_filtered.groupby([group_col, project_col])[perf_col].sum().reset_index()
            # 상위 5개 프로그램 
            top_stats = stats.sort_values([group_col, perf_col], ascending=[True, False]).groupby(group_col).head(5).copy()

            if top_stats.empty:
                st.warning("표시할 수 있는 데이터가 없습니다.")
                return

            pivot_df = top_stats.pivot(index=project_col, columns=group_col, values=perf_col).fillna(0)
            existing_cols = [col for col in age_order if col in pivot_df.columns and col in actual_selection]
            if not existing_cols:
                return
            pivot_df = pivot_df[existing_cols]

            pivot_pct = pivot_df.transpose().apply(lambda x: x / x.sum() * 100 if x.sum() != 0 else x, axis=1).transpose()

            pivot_df["_Total"] = pivot_df.sum(axis=1)
            pivot_df = pivot_df.sort_values("_Total", ascending=True)
            pivot_df = pivot_df.drop(columns=["_Total"])

            pivot_pct = pivot_pct.loc[pivot_df.index]

            text_matrix = []
            for i, row in pivot_df.iterrows():
                row_text = []
                for col in pivot_df.columns:
                    val = pivot_df.loc[i, col]
                    pct = pivot_pct.loc[i, col]
                    if val > 0:
                        is_dark_cell = (col in ['50대', '60대'] and i == '복지일자리(근무)') or \
                                       (col in ['10대미만', '10대'] and i == '발달재활')
                        if is_dark_cell:
                            row_text.append(f"<span style='color: white;'><b>{val:,.0f}명<br>({pct:.1f}%)</b></span>")
                        else:
                            row_text.append(f"<b>{val:,.0f}명<br>({pct:.1f}%)</b>")
                    else:
                        row_text.append("")
                text_matrix.append(row_text)

            # 프리젠테이션 모드면 높이를 좀 더 크게
            _h = min(700, max(450, len(pivot_df)*45 + 100)) if not presentation_mode else 750
            
            import plotly.graph_objects as go
            fig = go.Figure(data=go.Heatmap(
                z=pivot_pct.values,
                x=pivot_df.columns,
                y=pivot_df.index,
                colorscale="Reds",
                showscale=False,
                text=text_matrix,
                texttemplate="%{text}",
                textfont=dict(size=16 if presentation_mode else 12, color="#4D4D4D"),
                hovertemplate="<b>%{y}</b><br>연령대: %{x}<br>비중: %{z:.1f}%<extra></extra>"
            ))
            
            fig = apply_chart_style(fig)
            fig.update_layout(
                xaxis_title="연령대",
                yaxis_title="세부사업 (Top 5 인기 사업 위주)",
                coloraxis_showscale=False,
                height=_h,
                margin=dict(t=20, b=30, l=10, r=10),
                xaxis=dict(tickangle=0)
            )
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)

# 9. 장애유형 X 연령대별 선호 프로그램 (가로 막대그래프)
def draw_cross_analysis(df_yeon, col_map, presentation_mode=False):
    disability_col = col_map.get('장애유형', '장애유형')
    age_col = '_연령대'
    project_col = col_map.get('세부사업', '세부사업')
    perf_col = col_map.get('실적', '실적')

    if disability_col not in df_yeon.columns or age_col not in df_yeon.columns or project_col not in df_yeon.columns:
        st.info("교차 분석에 필요한 데이터 컬럼이 없습니다.")
        return

    # 1. 연령대 정렬 및 그룹 정의 (기존 draw_preferred_bar_age에서 가져옴)
    age_order = ['10대미만', '10대', '20대', '30대', '40대', '50대', '60대', '70대', '80대 이상']
    disability_order = ['지체장애', '뇌병변장애', '시각장애', '청각장애', '언어장애', '지적장애', '자폐성장애', '정신장애', '신장장애', '심장장애', '호흡기장애', '간장애', '안면장애', '장루요루장애', '간질장애', '기타']

    # 컬러 팔레트 (기존 draw_preferred_bar_disability에서 가져옴)
    group_map_disability = {
        '지체장애': 'Red', '뇌병변장애': 'Red',
        '시각장애': 'Blue', '청각장애': 'Blue', '언어장애': 'Blue',
        '지적장애': 'Yellow', '자폐성장애': 'Yellow', '정신장애': 'Yellow',
        '신장장애': 'Gray', '심장장애': 'Gray', '호흡기장애': 'Gray', '간장애': 'Gray', '안면장애': 'Gray', '장루요루장애': 'Gray', '간질장애': 'Gray', '기타': 'Gray'
    }
    group_palettes = {
        'Red': [BRAND_RED, "#D65C69", "#E98C8E", "#F2B0B2", "#F9D4D5"],
        'Blue': [BRAND_BLUE, CHART_BLUE, "#A4CAD2", "#C6E0E6", "#E3EFF2"],
        'Yellow': [BRAND_YELLOW, CHART_YELLOW, "#F9D59B", "#FBE6C4", "#FDF3E2"],
        'Gray': [BRAND_GRAY, CHART_GRAY, "#BDBDBD", "#D6D6D6", "#EBEBEB"]
    }

    with st.container(border=True):
        if not presentation_mode:
            st.markdown(
                f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-bottom:8px;'>"
                "🔀 장애유형 X 연령대별 선호 프로그램 (비중 분석) <span style='font-size:12px; font-weight:normal; color:#888;'>&nbsp;&nbsp;*중식제공 사업 제외</span>"
                "</div>",
                unsafe_allow_html=True
            )

        # 항목 목록 준비
        available_disabilities = [
            t for t in disability_order if t in df_yeon[disability_col].unique()
        ] + [t for t in sorted(df_yeon[disability_col].dropna().unique())
             if t not in disability_order]
        available_ages = [a for a in age_order if a in df_yeon[age_col].unique()]

        # 필터 정보 텍스트 함수
        def _get_filter_text(selected, available):
            if not selected: return "선택된 항목 없음"
            if len(selected) == len(available): return "전체선택"
            return f"[{', '.join(selected)}]"

        if presentation_mode:
            # 프리젠테이션 모드: UI 없이 세션 스테이트에서 직접 로드
            if "cross_d_all" not in st.session_state:
                st.session_state["cross_d_all"] = False
                for i, opt in enumerate(available_disabilities):
                    st.session_state[f"cross_d_{i}"] = (opt in ['지적장애', '자폐성장애'])
            sel_disabilities = [opt for i, opt in enumerate(available_disabilities)
                                 if st.session_state.get(f"cross_d_{i}", opt in ['지적장애', '자폐성장애'])]
            sel_ages = available_ages
        else:
            col_filter_d, col_filter_a = st.columns(2)
            with col_filter_d:
                with st.popover("장애유형 선택", use_container_width=True):
                    if "cross_d_all" not in st.session_state:
                        st.session_state["cross_d_all"] = False
                        for i, opt in enumerate(available_disabilities):
                            st.session_state[f"cross_d_{i}"] = (opt in ['지적장애', '자폐성장애'])
                    sel_disabilities = checkbox_group("장애유형 선택", available_disabilities, "cross_d", is_sidebar=False, default_all=False)
            with col_filter_a:
                with st.popover("연령대 선택", use_container_width=True):
                    sel_ages = checkbox_group("연령대 선택", available_ages, "cross_a", is_sidebar=False, default_all=True)

        if not sel_disabilities or not sel_ages:
            if not presentation_mode:
                st.markdown(
                    "<div style='text-align:center; padding:60px 0; color:#aaa;'>"
                    "<div style='font-size:26px; margin-bottom:12px;'>&#128269;</div>"
                    "<div style='font-size:17px; font-weight:bold; color:#888;'>분석할 장애유형과 연령대를 먼저 선택해 주세요.</div>"
                    "<div style='font-size:13px; margin-top:8px; color:#bbb;'>우측 상단의 버튼에서 조건을 선택하면 분석 결과가 표시됩니다.</div>"
                    "</div>",
                    unsafe_allow_html=True
                )
            return

        # ── 데이터 필터링 ──
        df_filtered = df_yeon.copy()
        df_filtered = df_filtered[df_filtered[disability_col].isin(sel_disabilities)]
        df_filtered = df_filtered[df_filtered[age_col].isin(sel_ages)]
        df_filtered = df_filtered[~df_filtered[project_col].astype(str).str.contains('중식', na=False)]

        if df_filtered.empty:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
            return

        # ── 세부사업별 집계 ──
        stats = df_filtered.groupby(project_col)[perf_col].sum().reset_index()
        stats = stats[stats[perf_col] > 0].sort_values(perf_col, ascending=False).copy()

        if stats.empty:
            st.warning("선택한 조건에 해당하는 프로그램 데이터가 없습니다.")
            return

        total_perf_val = stats[perf_col].sum()

        # ── 상위 5개만 추출 (기타 없음) ──
        plot_stats = stats.head(5).copy().reset_index(drop=True)

        # ── 장애유형별 고정 색상 규칙 ──
        RED_GROUP = {'지체장애', '뇌병변장애', '시각장애', '청각장애', '언어장애'}
        BLUE_GROUP = {'신장장애', '심장장애', '간장애', '장루요루장애', '뇌전증장애'}
        YELLOW_GROUP = {'지적장애', '자폐성장애', '정신장애'}

        def _pick_group(sel_list):
            for t in sel_list:
                if t in RED_GROUP: return 'Red'
                if t in BLUE_GROUP: return 'Blue'
                if t in YELLOW_GROUP: return 'Yellow'
            return 'Gray'

        main_group = _pick_group(sel_disabilities)
        palette = group_palettes[main_group]

        # ── 고정 색상 적용 ──
        colors = [palette[min(i, len(palette)-1)] for i in range(len(plot_stats))]

        # ── 제목 & 필터 요약 ──
        d_label = sel_disabilities[0] if len(sel_disabilities) == 1 else f"{len(sel_disabilities)}개 유형"
        a_label = sel_ages[0] if len(sel_ages) == 1 else f"{len(sel_ages)}개 연령대"
        chart_title = f"{d_label} × {a_label} · 세부사업 비중 (Top 5)"

        if not presentation_mode:
            st.markdown(f"### {chart_title}")

        d_text = ', '.join(sel_disabilities) if sel_disabilities else '-'
        a_text = '전체선택' if len(sel_ages) == len(available_ages) else ', '.join(sel_ages)
        filter_caption_text = f"장애유형: {d_text} │ 연령대: {a_text} │ 합계: {total_perf_val:,.0f}명"

        if presentation_mode:
            st.markdown(f"<p style='font-size:20px; font-weight:600; color:#333; margin:4px 0 8px 0;'>{filter_caption_text}</p>", unsafe_allow_html=True)
        else:
            st.caption(filter_caption_text)

        # ── 도넛 그래프 ──
        fig = px.pie(
            plot_stats,
            names=project_col,
            values=perf_col,
            hole=0.48,
            color_discrete_sequence=colors
        )
        
        fig = apply_chart_style(fig)
        
        fig.update_traces(
            texttemplate="<b>%{label}</b><br>%{percent:.1%}",
            textposition="outside",
            hovertemplate="<b>%{label}</b><br>연인원: %{value:,.0f}명<br>비중: %{percent:.1%}<extra></extra>",
            domain=dict(x=[0.1, 0.55], y=[0.1, 0.9])
        )
        fig.update_layout(
            showlegend=True,
            title="",
            legend=dict(orientation="v", x=0.65, xanchor="left", y=0.5, yanchor="middle", font=dict(size=18 if presentation_mode else 12)),
            margin=dict(t=0, b=0, l=0, r=0, pad=0),
            paper_bgcolor='rgba(0,0,0,0)',
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

# ================= 차트 영역: 두 개의 탭으로 구성 =================
# tab1, tab2 = st.tabs(["📊 연인원 현황", "👤 실인원 현황"]) # 중복 탭 제거

# 연인원 데이터 필터링 (명 단위 & 실적 합산용)
unit_col = col_map.get('단위', '명/건')
is_person_all = filtered_df[unit_col].astype(str).str.strip() == '명'
df_yeon = filtered_df[is_person_all].copy()

# 5. 신규 이용자 현황 (접수상담 기준)
def draw_new_user_analysis(df_data, col_map):
    project_col = col_map.get('세부사업', '세부사업')
    id_col = col_map.get('고유ID', '고유ID')
    month_col = '월'
    perf_col = col_map.get('실적', '실적')
    
    if project_col not in df_data.columns or id_col not in df_data.columns:
        return
        
    # 1) 접수상담 기록이 있는 이용자 식별
    is_intake = df_data[project_col].astype(str).str.contains('접수상담', na=False)
    intake_df = df_data[is_intake]
    new_user_ids = intake_df[id_col].unique()
    
    if len(new_user_ids) == 0:
        return
        
    # 2) 신규 이용자들의 전체 기록 추출
    new_users_full_df = df_data[df_data[id_col].isin(new_user_ids)]
    
    # 3) 월별 신규 이용자 추이
    new_users_monthly = intake_df.drop_duplicates(subset=[id_col, month_col]).groupby(month_col).size().reset_index(name='신규 이용자수').sort_values(month_col)
    
    # 4) 타 프로그램 이용 건수 Top 10
    other_programs_df = new_users_full_df[~new_users_full_df[project_col].astype(str).str.contains('접수상담', na=False)]
    if perf_col in other_programs_df.columns:
        other_programs_count = other_programs_df.groupby(project_col)[perf_col].sum().reset_index(name='이용건수')
    else:
        other_programs_count = other_programs_df.groupby(project_col).size().reset_index(name='이용건수')
        
    top10_others = other_programs_count.sort_values('이용건수', ascending=False).head(10).sort_values('이용건수', ascending=True)
    
    with st.container(border=True):
        st.markdown(f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-bottom:15px;'>🌱 신규 이용자 현황 (접수상담 이력자 기준: 총 {len(new_user_ids):,.0f}명)</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"<div style='font-size:15px; font-weight:bold; color:#555; margin-bottom:5px;'>📅 월별 신규 이용자 추이</div>", unsafe_allow_html=True)
            if not new_users_monthly.empty:
                fig1 = px.line(new_users_monthly, x=month_col, y='신규 이용자수', markers=True, text='신규 이용자수')
                fig1.update_traces(line_color=BRAND_BLUE, marker=dict(size=10), textposition='top center', texttemplate='<b>%{text:,.0f}명</b>')
                fig1.update_xaxes(dtick=1, labelalias={i: f"{i}월" for i in range(1, 13)}, title="")
                fig1.update_yaxes(title="")
                fig1 = apply_chart_style(fig1)
                fig1.update_layout(height=400, margin=dict(t=10, b=20, l=20, r=20))
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("월별 신규 이용자 데이터가 없습니다.")
                
        with col2:
            st.markdown(f"<div style='font-size:15px; font-weight:bold; color:#555; margin-bottom:5px;'>🎯 신규 이용자의 타 프로그램 이용 (Top 10)</div>", unsafe_allow_html=True)
            if not top10_others.empty:
                n = len(top10_others)
                fig2 = px.bar(top10_others, x='이용건수', y=project_col, orientation='h', text='이용건수')
                
                # 하위 순위(파일관리 포함)은 텍스트를 바깥으로 위치
                # top10_others는 오름차순(ascending=True) 상태이므로 맨 마지막(n-1)이 1위
                text_pos = ['inside' if (n - i) <= 4 else 'outside' for i in range(n)]
                
                fig2.update_traces(marker_color=BRAND_RED, texttemplate='<b>%{text:,.0f}건</b>', textposition=text_pos)
                fig2.update_layout(yaxis={'categoryorder': 'total ascending'}, yaxis_title="", xaxis_title="")
                fig2 = apply_chart_style(fig2)
                
                # outside 텍스트가 화면 우측에서 잘리지 않도록 r 여백을 80으로 확보
                fig2.update_layout(height=400, margin=dict(t=10, b=20, l=220, r=80))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("타 프로그램 이용 내역이 없습니다.")

# 6. 팀별 실인원 현황 (중복포함)
def draw_team_duplicated_sil(valid_unique_df, col_map):
    team_col = col_map.get('팀', '팀')
    if team_col in valid_unique_df.columns:
        # 팀별 실인원(중복) 계산: 고유ID + 팀 기준으로 중복 제거
        df_team_sil = valid_unique_df.drop_duplicates(subset=['고유ID', team_col]).copy()
        team_counts = df_team_sil.groupby(team_col).size().reset_index(name='실인원')
        team_counts = team_counts.sort_values('실인원', ascending=False)
        total_dup = team_counts['실인원'].sum()

        with st.container(border=True):
            st.markdown(f"<div style='font-size:18px; font-weight:bold; color:{BRAND_GRAY}; margin-bottom:5px;'>📊 팀세부 실인원 현황 (중복 실인원 합계: {total_dup:,.0f}명)</div>", unsafe_allow_html=True)
            # 수직 막대 그래프로 변경 (팀별 규모 파악 용이)
            fig = px.bar(team_counts, x=team_col, y='실인원', text='실인원',
                         color_discrete_sequence=[BRAND_RED])
            fig.update_traces(texttemplate='<b>%{text:,.0f}</b>', textposition='inside')
            fig.update_layout(xaxis_title="수행팀", yaxis_title="실인원(명)")
            st.plotly_chart(apply_chart_style(fig), use_container_width=True)

# ======== 연인원 데이터 준비 (명 단위) ========
unit_col = col_map.get('단위', '명/건')
is_person_all = filtered_df[unit_col].astype(str).str.strip() == '명' if unit_col in filtered_df.columns else pd.Series([True] * len(filtered_df))
df_yeon = filtered_df[is_person_all].copy()

# ======== 탭 UI: 프리젠테이션 모드 OFF 시에만 표시 ========
if not st.session_state.get("presentation_mode", False):
    tab1, tab2 = st.tabs(["📊 연인원 현황", "👤 실인원 현황"])

    # ====== Tab 1: 연인원 현황 ======
    with tab1:
        # 1. 장애유형별 이용 현황
        draw_disability_donut_yeon(df_yeon, col_map)
        
        # 2. 장애유형별 선호 프로그램 (가로 막대)
        draw_preferred_bar_disability(df_yeon, col_map)
        
        # 3. 연령대별 현황 (나란히 배치)
        col_age1, col_age2 = st.columns(2)
        with col_age1:
            draw_age_bar_custom(df_yeon, is_disabled=True)
        with col_age2:
            draw_age_bar_custom(df_yeon, is_disabled=False)
        
        # 4. 연령대별 선호 프로그램 (가로 막대)
        draw_preferred_bar_age(df_yeon, col_map)
        
        # 5. 신규 이용자 현황 (접수상담 기준)
        draw_new_user_analysis(df_yeon, col_map)
        
        # 6. 장애유형 X 연인원 교차 분석
        draw_cross_analysis(df_yeon, col_map)
    
        # 7. 익명 참여자 분석
        draw_etc_top10_yeon(df_yeon, col_map)
        
        # 8. 월별 추이 및 요일별 이용 현황 (나란히 배치)
        col_trend, col_crowd = st.columns(2)
        with col_trend:
            draw_monthly_trend(df_yeon)
        with col_crowd:
            draw_daily_crowdedness(df_yeon)

    # ====== Tab 2: 실인원 현황 ======
    with tab2:
        # 실인원용 데이터셋: '기타' 제외 및 [이름+생년월일+장애유형+장애정도] 기준 중복 제거
        _sil_cols_tab = None
        if all(c in _df_for_uniq.columns for c in ['이름', '생년월일', '장애유형', '장애정도']):
            _sil_cols_tab = ['이름', '생년월일', '장애유형', '장애정도']
        elif '고유ID' in _df_for_uniq.columns:
            _sil_cols_tab = ['고유ID']
        
        df_sil = _df_for_uniq.drop_duplicates(subset=_sil_cols_tab).copy() if _sil_cols_tab else _df_for_uniq.copy()
        
        if not df_sil.empty:
            # 1. 장애유형별 이용 현황 (실인원)
            st.markdown(f"<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
            draw_disability_donut_yeon(df_sil, col_map, title_label="실인원")
            
            # 2 & 3. 연령대별 현황 (실인원 - 나란히 배치)
            col_age1, col_age2 = st.columns(2)
            with col_age1:
                draw_age_bar_custom(df_sil, is_disabled=True, title_label="실인원")
            with col_age2:
                draw_age_bar_custom(df_sil, is_disabled=False, title_label="실인원")
                
            # 4. 팀별 중복 실인원 현황
            draw_team_duplicated_sil(_df_for_uniq, col_map)
                
        else:
            st.info("실인원 현황을 구성할 수 있는 데이터가 없습니다.")


# ============================================================
# ================= 프리젠테이션 모드 렌더링 =================
# ============================================================
if st.session_state.get("presentation_mode", False):
    # 전체화면 CSS 적용
    st.markdown("""
    <style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    .stAppDeployButton,
    header { display: none !important; }
    footer,
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"] { display: none !important; }
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stMainBlockContainer"] {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 100% !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    .pres-hide { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    pres_interval_val = st.session_state.get("pres_interval", 5)

    # 실인원용 데이터셋 준비
    _sil_cols_p = None
    if all(c in _df_for_uniq.columns for c in ['이름', '생년월일', '장애유형', '장애정도']):
        _sil_cols_p = ['이름', '생년월일', '장애유형', '장애정도']
    elif '고유ID' in _df_for_uniq.columns:
        _sil_cols_p = ['고유ID']
    df_sil_p = _df_for_uniq.drop_duplicates(subset=_sil_cols_p).copy() if _sil_cols_p else _df_for_uniq.copy()

    # 슬라이드 함수 정의
    def _slide_disability_yeon():
        draw_disability_donut_yeon(df_yeon, col_map)

    def _slide_age_disabled():
        draw_age_bar_custom(df_yeon, is_disabled=True)

    def _slide_age_nondisabled():
        draw_age_bar_custom(df_yeon, is_disabled=False)

    def _slide_monthly():
        draw_monthly_trend(df_yeon)

    def _slide_daily():
        draw_daily_crowdedness(df_yeon)

    def _slide_etc():
        draw_etc_top10_yeon(df_yeon, col_map, presentation_mode=True)

    def _slide_new_user():
        draw_new_user_analysis(df_yeon, col_map)

    def _slide_disability_sil():
        draw_disability_donut_yeon(df_sil_p, col_map, title_label="실인원")

    def _slide_age_disabled_sil():
        draw_age_bar_custom(df_sil_p, is_disabled=True, title_label="실인원")

    def _slide_age_nondisabled_sil():
        draw_age_bar_custom(df_sil_p, is_disabled=False, title_label="실인원")

    def _slide_team_sil():
        draw_team_duplicated_sil(_df_for_uniq, col_map)

    def _slide_cross():
        draw_cross_analysis(df_yeon, col_map, presentation_mode=True)

    def _slide_pref_age():
        import plotly.express as px
        project_col = col_map.get('세부사업', '세부사업')
        perf_col = col_map.get('실적', '실적')
        group_col = '_연령대'
        age_order = ['10대미만', '10대', '20대', '30대', '40대', '50대', '60대', '70대', '80대 이상']
        
        if group_col in df_yeon.columns and project_col in df_yeon.columns:
            df_filtered = df_yeon[df_yeon[group_col].isin(age_order)].copy()
            df_filtered = df_filtered[~df_filtered[project_col].astype(str).str.contains('중식', na=False)]
            
            if not df_filtered.empty:
                # 너무 많은 사업(난잡함) 방지를 위해 전체 실적 기준 Top 12 사업만 필터링
                top_projects = df_filtered.groupby(project_col)[perf_col].sum().nlargest(12).index
                df_filtered = df_filtered[df_filtered[project_col].isin(top_projects)]
                
                stats = df_filtered.groupby([group_col, project_col])[perf_col].sum().reset_index()
                # 각 연령대별 Top 3
                top_stats = stats.sort_values([group_col, perf_col], ascending=[True, False]).groupby(group_col).head(3).copy()
                
                pivot_df = top_stats.pivot(index=project_col, columns=group_col, values=perf_col).fillna(0)
                existing_cols = [col for col in age_order if col in pivot_df.columns]
                pivot_df = pivot_df[existing_cols]
                
                pivot_pct = pivot_df.transpose().apply(lambda x: x / x.sum() * 100 if x.sum() != 0 else x, axis=1).transpose()
                
                pivot_df["_Total"] = pivot_df.sum(axis=1)
                pivot_df = pivot_df.sort_values("_Total", ascending=True)
                pivot_df = pivot_df.drop(columns=["_Total"])
                pivot_pct = pivot_pct.loc[pivot_df.index]
                
                text_matrix = []
                for i, row in pivot_df.iterrows():
                    row_text = []
                    for col in pivot_df.columns:
                        val = pivot_df.loc[i, col]
                        pct = pivot_pct.loc[i, col]
                        if val > 0:
                            # 캡처본 포맷: 100명 (50.0%) - 줄바꿈 없음
                            is_dark_cell = (col in ['50대', '60대'] and i == '복지일자리(근무)') or \
                                           (col in ['10대미만', '10대'] and i == '발달재활')
                            if is_dark_cell:
                                row_text.append(f"<span style='color: white;'><b>{val:,.0f}명 ({pct:.1f}%)</b></span>")
                            else:
                                row_text.append(f"<b>{val:,.0f}명 ({pct:.1f}%)</b>")
                        else:
                            row_text.append("")
                    text_matrix.append(row_text)
                
                # 커스텀 베이지-다크레드 색상 (다중 스탑을 통해 낮은 비중이 과도하게 붉어지는 현상 방지)
                custom_colorscale = [
                    [0.0, '#FFF5E6'],   # 완전 베이지 배경
                    [0.2, '#FFE1CC'],   # 연한 살구색
                    [0.5, '#F9A88F'],   # 코랄 핑크
                    [0.7, '#E36568'],   # 부드러운 다홍색
                    [1.0, '#B81D22']    # 짙은 정통 레드
                ]

                with st.container(border=True):                    
                    import plotly.graph_objects as go
                    fig = go.Figure(data=go.Heatmap(
                        z=pivot_pct.values,
                        x=pivot_df.columns,
                        y=pivot_df.index,
                        colorscale=custom_colorscale,
                        showscale=False,
                        text=text_matrix,
                        texttemplate="%{text}",
                        textfont=dict(size=16, color="#4D4D4D"),  # 축 라벨과 통일된 폰트 크기 및 색상
                        hovertemplate="<b>%{y}</b><br>연령대: %{x}<br>비중: %{z:.1f}%<extra></extra>"
                    ))
                    
                    fig = apply_chart_style(fig)
                    fig.update_layout(
                        xaxis_title="연령대", 
                        yaxis_title="프로그램명",
                        height=600,  # 강제로 높이 설정 (스크린에 맞게 축소)
                        margin=dict(l=50, r=50, t=30, b=30)
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("데이터가 없습니다.")

    # 동적 슬라이드: 장애유형별 선호 프로그램 (도넛 - 각 장애유형당 1개 슬라이드)
    DYNAMIC_PREF_SLIDES = []
    disability_col_pres = col_map.get('장애유형', '장애유형')
    if disability_col_pres in df_yeon.columns:
        # 사용자의 대시보드 화면과 완벽히 동일한 고정 순서 적용 (Red -> Blue -> Yellow -> Gray)
        dashboard_order = [
            '지체장애', '뇌병변장애', '시각장애', '청각장애', '언어장애', 
            '신장장애', '심장장애', '간장애', '장루요루장애', '뇌전증장애', '호흡기장애', '안면장애', '간질장애',
            '지적장애', '자폐성장애', '정신장애', 
            '미등록', '비장애', '기타'
        ]
        
        actual_disabilities_pres = [str(x) for x in df_yeon[disability_col_pres].dropna().unique() if str(x).strip() != '']
        ordered_pres = [d for d in dashboard_order if d in actual_disabilities_pres]
        extras_pres = sorted([d for d in actual_disabilities_pres if d not in dashboard_order])
        dynamic_disabilities_pres = ordered_pres + extras_pres

        _proj_col = col_map.get('세부사업', '세부사업')
        _perf_col = col_map.get('실적', '실적')

        for d_type in dynamic_disabilities_pres:
            def make_slide_fn(dt=d_type):
                def _fn():
                    _df = df_yeon[df_yeon[disability_col_pres] == dt].copy()
                    _df = _df[~_df[_proj_col].astype(str).str.contains('중식', na=False)] if _proj_col in _df.columns else _df
                    if _df.empty or _proj_col not in _df.columns:
                        st.info(f"{dt}: 데이터 없음")
                        return
                    stats = _df.groupby(_proj_col)[_perf_col].sum().reset_index()
                    stats = stats[stats[_perf_col] > 0].sort_values(_perf_col, ascending=False).head(5).copy()
                    if stats.empty:
                        st.info(f"{dt}: 프로그램 데이터 없음")
                        return
                    total_p = stats[_perf_col].sum()
                    stats['pct'] = stats[_perf_col] / total_p * 100
                    
                    group_map_local = {
                        '지체장애': 'Red', '뇌병변장애': 'Red', '시각장애': 'Red', '청각장애': 'Red', '언어장애': 'Red',
                        '신장장애': 'Blue', '심장장애': 'Blue', '호흡기장애': 'Blue', '간장애': 'Blue', '안면장애': 'Blue', '장루요루장애': 'Blue', '뇌전증장애': 'Blue', '간질장애': 'Blue',
                        '지적장애': 'Yellow', '자폐성장애': 'Yellow', '정신장애': 'Yellow',
                        '미등록': 'Gray', '비장애': 'Gray', '기타': 'Gray'
                    }
                    group_palettes_local = {
                        'Red': [BRAND_RED, "#D65C69", "#E98C8E", "#F2B0B2", "#F9D4D5", BRAND_GRAY, "#BDBDBD"],
                        'Blue': [BRAND_BLUE, CHART_BLUE, "#A4CAD2", "#C6E0E6", "#E3EFF2", BRAND_GRAY, "#BDBDBD"],
                        'Yellow': [BRAND_YELLOW, CHART_YELLOW, "#F9D59B", "#FBE6C4", "#FDF3E2", BRAND_GRAY, "#BDBDBD"],
                        'Gray': [BRAND_GRAY, CHART_GRAY, "#BDBDBD", "#D6D6D6", "#EBEBEB", "#999999", "#777777"]
                    }
                    _grp = group_map_local.get(dt, 'Gray')
                    colors_p = group_palettes_local[_grp]
                    
                    chart_labels_p = []
                    legend_texts = []
                    for i, (_, r) in enumerate(stats.iterrows()):
                        chart_labels_p.append(f"<b>{r[_proj_col]}</b><br>{r['pct']:.1f}%")
                        legend_texts.append(f"{r[_proj_col]} {r[_perf_col]:,.0f}명 ({r['pct']:.1f}%)")
                    stats['_legend'] = legend_texts
                        
                    with st.container(border=True):
                        _dname_color = colors_p[0]
                        st.markdown(
                            f"<div style='font-size:24px;font-weight:bold;color:{BRAND_GRAY};'>"
                            f"⭐ <span style='color:{_dname_color} !important;'>{dt}</span> 선호 프로그램 (Top 5) "
                            f"<span style='font-size:16px;color:#888 !important;'>*중식제공 제외</span></div>",
                            unsafe_allow_html=True
                        )
                        fig_p = px.pie(stats, names='_legend', values=_perf_col, hole=0.48,
                                      color_discrete_sequence=colors_p, custom_data=[_proj_col])

                        fig_p = apply_chart_style(fig_p)  # 스타일 먼저 적용 (이후 layout 업데이트로 폰트 크기 덮어씀)

                        _rot_angle = 0
                        if dt == '장루요루장애':
                            _rot_angle = -90
                        elif dt == '뇌전증장애':
                            _rot_angle = 90
                        elif dt == '시각장애':
                            _rot_angle = 20
                        elif dt == '비장애':
                            _rot_angle = 50

                        fig_p.update_traces(
                            rotation=_rot_angle,
                            text=chart_labels_p, textinfo='text', textposition='outside',
                            textfont_size=17,
                            hovertemplate="<b>%{customdata[0]}</b><br>%{value:,.0f}명 (%{percent:.1%})<extra></extra>",
                            domain=dict(x=[0.1, 0.55], y=[0.1, 0.9])
                        )
                        fig_p.update_layout(
                            showlegend=True,
                            legend=dict(x=0.65, xanchor='left', y=0.5, yanchor='middle', font=dict(size=18)),
                            margin=dict(t=0, b=0, l=0, r=0), height=500,
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_p, use_container_width=True)
                return _fn
            
            # 사이드바에서 장애유형 이름이 구별되도록 제목에 (유형명) 추가
            DYNAMIC_PREF_SLIDES.append((f"장애유형별 선호 프로그램 ({d_type})", make_slide_fn()))

    SLIDES = [
        ("장애유형별 이용 현황 (연인원)",              _slide_disability_yeon),
    ] + DYNAMIC_PREF_SLIDES + [
        ("연령대별 현황 – 장애/미등록 (연인원)",       _slide_age_disabled),
        ("연령대별 현황 – 비장애 (연인원)",            _slide_age_nondisabled),
        ("연령대별 선호 프로그램",                    _slide_pref_age),
        ("장애유형 X 연령대별 선호 프로그램",             _slide_cross),
        ("기타 이용자 참여비중 분석",                   _slide_etc),
        ("신규 이용자 현황",                            _slide_new_user),
        ("월별 이용자 추이",                            _slide_monthly),
        ("요일별 이용 현황",                            _slide_daily),
        ("장애유형별 이용 현황 (실인원)",              _slide_disability_sil),
        ("연령대별 현황 – 장애/미등록 (실인원)",       _slide_age_disabled_sil),
        ("연령대별 현황 – 비장애 (실인원)",            _slide_age_nondisabled_sil),
        ("팀별 세부 실인원 현황",                       _slide_team_sil),
    ]
    TOTAL_SLIDES = len(SLIDES)
    idx = st.session_state.get("pres_slide_idx", 0) % TOTAL_SLIDES
    slide_title, slide_fn = SLIDES[idx]

    # 상단 헤더
    st.markdown(
        """
        <div style='padding: 24px 32px 20px 32px; margin-bottom: 12px; text-align: center;'>
            <span style='font-size: 52px; font-weight: 900; color: #BE1E2D; letter-spacing: 2px;'>
                서부장애인종합복지관 이용자 현황 분석
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 슬라이드 제목
    st.markdown(f"<div class='pres-slide-title'>📌 {slide_title}</div>", unsafe_allow_html=True)

    # 슬라이드 콘텐츠
    with st.container():
        st.markdown("<div class='pres-slide-content'>", unsafe_allow_html=True)
        slide_fn()
        st.markdown("</div>", unsafe_allow_html=True)

    # 슬라이드 번호 + 이동 버튼
    col_prev, col_info, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("◀ 이전", key="pres_prev", use_container_width=True):
            st.session_state["pres_slide_idx"] = (idx - 1) % TOTAL_SLIDES
            st.rerun()
    with col_info:
        st.markdown(
            f"<div style='text-align:center; color:#666; font-size:15px; padding-top:6px;'>"
            f"{idx+1} / {TOTAL_SLIDES}&nbsp;&nbsp;|&nbsp;&nbsp;{pres_interval_val}초 자동 전환</div>",
            unsafe_allow_html=True
        )
    with col_next:
        if st.button("다음 ▶", key="pres_next", use_container_width=True):
            st.session_state["pres_slide_idx"] = (idx + 1) % TOTAL_SLIDES
            st.rerun()

    # JS: 자동전환 + 키보드 방향키
    import streamlit.components.v1 as components
    components.html(
        f"""
        <script>
        /* slide_idx={idx} */
        (function() {{
            var doc = window.parent.document;
            var elem = doc.documentElement;
            // 전체화면 시도 (데스크톱)
            var _fullscreenOk = false;
            try {{
                if (!doc.fullscreenElement) {{
                    var _req = elem.requestFullscreen
                        || elem.webkitRequestFullscreen
                        || elem.mozRequestFullScreen
                        || elem.msRequestFullscreen;
                    if (_req) {{
                        _req.call(elem).then(function() {{
                            _fullscreenOk = true;
                        }}).catch(function() {{
                            // 태블릿 fallback: 스크롤 최상단 + 스크롤바 숨김
                            window.parent.scrollTo(0, 0);
                            doc.body.style.overflow = 'hidden';
                        }});
                    }}
                }}
            }} catch(e) {{
                // 동기식 실패(구형 브라우저) fallback
                window.parent.scrollTo(0, 0);
                doc.body.style.overflow = 'hidden';
            }}

            var _timer = setTimeout(function() {{
                var btns = doc.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {{
                    if (btns[i].textContent.trim().includes('다음')) {{
                        btns[i].click();
                        break;
                    }}
                }}
            }}, {pres_interval_val * 1000});

            function _keyHandler(e) {{
                if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {{
                    clearTimeout(_timer);
                    var btns = doc.querySelectorAll('button');
                    for (var i = 0; i < btns.length; i++) {{
                        if (btns[i].textContent.trim().includes('다음')) {{ btns[i].click(); break; }}
                    }}
                }} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {{
                    clearTimeout(_timer);
                    var btns = doc.querySelectorAll('button');
                    for (var i = 0; i < btns.length; i++) {{
                        if (btns[i].textContent.trim().includes('이전')) {{ btns[i].click(); break; }}
                    }}
                }}
            }}
            doc.addEventListener('keydown', _keyHandler);
            window.addEventListener('beforeunload', function() {{
                clearTimeout(_timer);
                doc.removeEventListener('keydown', _keyHandler);
            }});
        }})();
        </script>
        """,
        height=0,
    )




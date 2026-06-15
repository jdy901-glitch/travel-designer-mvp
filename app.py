import streamlit as st
import pandas as pd
import json
from datetime import datetime
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials

# --- 1. 페이지 및 기본 설정 ---
st.set_page_config(page_title="AI 여행 디자이너", page_icon="✈️", layout="centered")

# --- 2. 제미나이 AI 세팅 ---
# 스트림릿 금고(Secrets)에서 제미나이 키를 꺼내옵니다.
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
generation_config = {"response_mime_type": "application/json"}
model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)

# --- 3. 구글 시트 출입증 세팅 (와인 앱 방식과 100% 동일) ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
certs = {
    "type": st.secrets["gcp_service_account"]["type"],
    "project_id": st.secrets["gcp_service_account"]["project_id"],
    "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
    "private_key": st.secrets["gcp_service_account"]["private_key"],
    "client_email": st.secrets["gcp_service_account"]["client_email"],
    "client_id": st.secrets["gcp_service_account"]["client_id"],
    "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
    "token_uri": st.secrets["gcp_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
}
creds = Credentials.from_service_account_info(certs, scopes=scope)
gc = gspread.authorize(creds)

# --- 4. 임시 저장소(Session State) 초기화 ---
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "locked_states" not in st.session_state:
    st.session_state.locked_states = {}

# --- 5. 제미나이에게 일정 짜달라고 부탁하는 함수 ---
def ask_ai_designer(prompt):
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        # 마크다운 찌꺼기 제거 안전장치
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1)
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("```", 1)[0]
        
        return json.loads(raw_text.strip())
    except Exception as e:
        st.error("AI가 여행 일정을 짜는 중 고민에 빠졌습니다. 다시 버튼을 눌러주세요!")
        return []

# --- 6. 구글 시트에 기록 저장하는 함수 ---
def save_to_google_sheet(destination, days, intensity, companions, itinerary_data):
    try:
        # ⚠️ 1단계에서 새로 만드신 구글 시트 이름을 여기에 적어주세요.
        sh = gc.open("여행 디자이너 기록") 
        worksheet = sh.get_worksheet(0)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        itinerary_string = json.dumps(itinerary_data, ensure_ascii=False)
        
        worksheet.append_row([timestamp, destination, days, intensity, companions, itinerary_string])
        st.success("🎉 나의 소중한 여행 기록이 구글 시트에 안전하게 저장되었습니다!")
    except Exception as e:
        st.error(f"구글 시트 저장 실패: {e}")

# --- 7. 화면 구성 (사이드바 - 조건 입력) ---
with st.sidebar:
    st.header("✈️ 여행 조건 입력")
    destination = st.text_input("목적지", placeholder="예: 나트랑, 제주도, 오사카")
    days = st.number_input("여행 기간 (일)", min_value=1, max_value=14, value=3)
    intensity = st.slider("희망 여행 강도", min_value=1, max_value=10, value=5, help="1: 휴양 ~ 10: 빡빡한 일정")
    companions = st.text_input("인원 구성", placeholder="예: 우진이, 아내, 나")
    base_comment = st.text_area("추가 요청사항 (선택)", placeholder="예: 동선은 최대한 짧게, 유모차 다니기 편한 곳")
    
    if st.button("✨ 첫 번째 여행 코스 짜기", use_container_width=True):
        if destination:
            with st.spinner('제미나이가 최고의 동선을 깎고 있습니다...'):
                prompt = f"""
                당신은 10년 차 베테랑 최고급 여행 디자이너입니다. 실존하는 구체적인 장소명(식당, 카페, 관광지 등)을 포함해 일정별 JSON 배열 포맷으로 답변하세요.
                목적지:{destination}, 기간:{days}일, 강도:{intensity}/10, 인원:{companions}, 요청사항:{base_comment}.
                반드시 아래 형식의 JSON 배열로만 출력하세요:
                [
                  {{"id":"1-오전", "day":1, "time":"오전", "place":"장소명", "category":"식당/카페/관광지", "reason":"이 장소를 추천하는 디테일한 이유"}},
                  ...
                ]
                """
                st.session_state.itinerary = ask_ai_designer(prompt)
                st.session_state.locked_states = {item["id"]: False for item in st.session_state.itinerary}
        else:
            st.warning("목적지를 입력해 주세요!")

# --- 8. 화면 구성 (메인 화면 - 코스 확인 및 수정) ---
st.title("🗺️ 나의 맞춤형 여행 코스")

if not st.session_state.itinerary:
    st.info("왼쪽 사이드바에서 여행 조건을 입력하고 코스를 생성해 보세요.")
else:
    st.write("마음에 드는 일정은 **🔒 고정**하고, 나머지는 피드백을 주어 다시 짤 수 있습니다.")
    st.divider()

    current_day = 0
    for item in st.session_state.itinerary:
        if item["day"] != current_day:
            st.subheader(f"📍 {item['day']}일차")
            current_day = item["day"]
        
        col1, col2 = st.columns([8, 2])
        with col1:
            st.markdown(f"**[{item['time']}] {item['place']}** ({item['category']})")
            st.caption(f"💡 {item['reason']}")
        with col2:
            is_locked = st.checkbox("🔒 고정", key=f"lock_{item['id']}", value=st.session_state.locked_states.get(item["id"], False))
            st.session_state.locked_states[item["id"]] = is_locked
        st.write("")

    st.divider()
    
    st.subheader("🔄 코스 수정 및 저장")
    reroll_comment = st.text_input("수정 요청 코멘트", placeholder="예: 오전에 갈 만한 실내 일정으로 바꿔줘")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("선택 안 된 일정 다시 짜기", type="primary", use_container_width=True):
            with st.spinner('피드백을 반영하여 일정을 새로 고치고 있습니다...'):
                prompt = f"""
                당신은 최고급 여행 디자이너입니다. 기존 일정 중 유저가 '고정(locked)'하지 않은 일정만 피드백을 반영해 완전히 새로운 구체적 장소로 교체하세요. 
                고정된 일정은 장소와 이유를 절대 변경하지 마세요.
                기존과 완벽히 동일한 JSON 배열 형식으로만 응답하세요.
                
                현재 일정: {json.dumps(st.session_state.itinerary, ensure_ascii=False)}
                현재 고정상태: {json.dumps(st.session_state.locked_states)}
                유저 피드백: {reroll_comment}
                """
                st.session_state.itinerary = ask_ai_designer(prompt)
                st.rerun()
                
    with col_btn2:
        if st.button("💾 이 여행 일정 최종 저장하기", use_container_width=True):
            save_to_google_sheet(destination, days, intensity, companions, st.session_state.itinerary)

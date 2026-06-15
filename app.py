import streamlit as st
import json
from google import genai
from google.genai import types

# --- 페이지 설정 ---
st.set_page_config(page_title="AI 여행 디자이너", page_icon="✈️", layout="centered")

# --- Gemini API 설정 (최신 SDK 적용!) ---
# 구형 라이브러리 대신 2026년형 최신 google-genai 라이브러리를 사용합니다.
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- 임시 저장소(Session State) 초기화 ---
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "locked_states" not in st.session_state:
    st.session_state.locked_states = {}

# --- 제미나이 호출 함수 ---
def ask_ai_designer(prompt):
    try:
        # 최신 문법에 맞춘 제미나이 호출 방식
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1)
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("```", 1)[0]
        return json.loads(raw_text.strip())
    except Exception as e:
        # 혹시라도 에러가 나면 무슨 에러인지 화면에 직접 띄워주는 기능 추가
        st.error(f"AI가 여행 일정을 짜는 중 고민에 빠졌습니다: {e}")
        return []

# --- 사이드바: 조건 입력 ---
with st.sidebar:
    st.header("✈️ 여행 조건 입력")
    destination = st.text_input("목적지", placeholder="예: 나트랑, 오사카, 제주도")
    days = st.number_input("여행 기간 (일)", min_value=1, max_value=14, value=3)
    intensity = st.slider("희망 여행 강도", min_value=1, max_value=10, value=5, help="1: 휴양 ~ 10: 빡빡한 일정")
    companions = st.text_input("인원 구성", placeholder="예: 21개월 아기, 아내, 나")
    base_comment = st.text_area("추가 요청사항 (선택)", placeholder="예: 동선은 최대한 짧게")
    
    if st.button("✨ 첫 번째 여행 코스 짜기", use_container_width=True):
        if destination:
            with st.spinner('제미나이가 최고의 동선을 깎고 있습니다...'):
                prompt = f"""
                당신은 베테랑 최고급 여행 디자이너입니다. 실존하는 구체적인 장소명을 포함해 일정별 JSON 배열 포맷으로 답변하세요.
                목적지:{destination}, 기간:{days}일, 강도:{intensity}/10, 인원:{companions}, 요청사항:{base_comment}.
                반드시 아래 형식의 JSON 배열로만 출력하세요:
                [
                  {{"id":"1-오전", "day":1, "time":"오전", "place":"장소명", "category":"식당/카페/관광지", "reason":"추천 이유"}},
                  ...
                ]
                """
                st.session_state.itinerary = ask_ai_designer(prompt)
                st.session_state.locked_states = {item["id"]: False for item in st.session_state.itinerary}
        else:
            st.warning("목적지를 입력해 주세요!")

# --- 메인 화면: 코스 튜닝 ---
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
    
    st.subheader("🔄 코스 수정")
    reroll_comment = st.text_input("수정 요청 코멘트", placeholder="예: 오전에 갈 만한 실내 일정으로 바꿔줘")
    
    if st.button("선택 안 된 일정 다시 짜기", type="primary", use_container_width=True):
        with st.spinner('피드백을 반영하여 일정을 새로 고치고 있습니다...'):
            prompt = f"""
            당신은 최고급 여행 디자이너입니다. 기존 일정 중 유저가 '고정(locked)'하지 않은 일정만 피드백을 반영해 완전히 새로운 구체적 장소로 교체하세요. 고정된 일정은 절대 변경하지 마세요.
            기존과 완벽히 동일한 JSON 배열 형식으로만 응답하세요.
            
            현재 일정: {json.dumps(st.session_state.itinerary, ensure_ascii=False)}
            현재 고정상태: {json.dumps(st.session_state.locked_states)}
            유저 피드백: {reroll_comment}
            """
            st.session_state.itinerary = ask_ai_designer(prompt)
            st.rerun()

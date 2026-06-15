import streamlit as st
import pandas as pd
import json

# --- 페이지 설정 ---
st.set_page_config(page_title="AI 여행 디자이너", page_icon="✈️", layout="centered")

# --- Session State 초기화 (데이터 유지) ---
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "locked_states" not in st.session_state:
    st.session_state.locked_states = {}

# --- 더미 AI 함수 (나중에 실제 LLM API 호출로 교체할 부분) ---
def generate_mock_itinerary(destination, days):
    """최초 초안 생성용 더미 데이터"""
    mock_data = []
    for day in range(1, days + 1):
        mock_data.extend([
            {"id": f"{day}-오전", "day": day, "time": "오전", "place": f"{destination} 핫플 카페", "category": "카페", "reason": "가볍게 하루를 시작하기 좋습니다."},
            {"id": f"{day}-오후", "day": day, "time": "오후", "place": f"{destination} 유명 관광지", "category": "관광지", "reason": "가장 필수적인 코스입니다."},
            {"id": f"{day}-저녁", "day": day, "time": "저녁", "place": f"{destination} 로컬 맛집", "category": "식당", "reason": "하루를 마무리하는 든든한 식사입니다."}
        ])
    return mock_data

def reroll_mock_itinerary(current_itinerary, locked_states, comment):
    """리롤(부분 재생성)용 더미 데이터"""
    new_data = []
    for item in current_itinerary:
        # 잠긴 항목은 그대로 유지
        if locked_states.get(item["id"], False):
            new_data.append(item)
        else:
            # 잠기지 않은 항목은 새로운 데이터로 교체 (코멘트 반영 흉내)
            new_item = item.copy()
            new_item["place"] = f"✨ 새로 추천된 장소 ({comment[:5]}...)"
            new_item["reason"] = "피드백을 반영하여 새로 추천해 드립니다."
            new_data.append(new_item)
    return new_data

# --- 사이드바: 1단계 조건 입력 ---
with st.sidebar:
    st.header("✈️ 여행 조건 입력")
    destination = st.text_input("목적지", placeholder="예: 제주도, 오사카")
    days = st.number_input("여행 기간 (일)", min_value=1, max_value=14, value=3)
    intensity = st.slider("희망 여행 강도", min_value=1, max_value=10, value=5, 
                          help="1: 거의 리조트에서 쉼 ~ 10: 빡빡한 일정")
    companions = st.text_input("인원 구성", placeholder="예: 18개월 아기, 남편, 나")
    base_comment = st.text_area("주관식 코멘트 (선택)", placeholder="예: 무조건 동선은 짧게 짜줘")
    
    if st.button("✨ 첫 번째 여행 코스 짜기", use_container_width=True):
        if destination:
            # AI 초안 생성 및 Session State 저장
            st.session_state.itinerary = generate_mock_itinerary(destination, days)
            # 잠금 상태 초기화
            st.session_state.locked_states = {item["id"]: False for item in st.session_state.itinerary}
        else:
            st.warning("목적지를 입력해 주세요!")

# --- 메인 화면: 2단계 코스 튜닝 ---
st.title("🗺️ 나의 맞춤형 여행 코스")

if not st.session_state.itinerary:
    st.info("왼쪽 사이드바에서 여행 조건을 입력하고 코스를 생성해 보세요.")
else:
    st.write("마음에 드는 일정은 **체크박스를 눌러 고정(Lock)**하고, 나머지는 다시 추천받을 수 있습니다.")
    st.divider()

    # --- 일정 렌더링 (일차별로 묶어서 표시) ---
    current_day = 0
    for item in st.session_state.itinerary:
        # 일차가 바뀔 때마다 구분선 및 헤더 출력
        if item["day"] != current_day:
            st.subheader(f"📍 {item['day']}일차")
            current_day = item["day"]
        
        # 각 일정 카드
        col1, col2 = st.columns([8, 2])
        with col1:
            st.markdown(f"**[{item['time']}] {item['place']}** ({item['category']})")
            st.caption(f"💡 {item['reason']}")
        with col2:
            # 체크박스로 Lock 상태 관리
            is_locked = st.checkbox("🔒 고정", 
                                    key=f"lock_{item['id']}", 
                                    value=st.session_state.locked_states.get(item["id"], False))
            st.session_state.locked_states[item["id"]] = is_locked
        st.write("") # 간격 띄우기

    st.divider()
    
    # --- 부분 재생성 (Reroll) 영역 ---
    st.subheader("🔄 마음에 안 드는 일정 새로고침")
    reroll_comment = st.text_input("수정 요청 코멘트", placeholder="예: 오전에 갈 만한 실내 일정으로 바꿔줘")
    
    if st.button("선택 안 된 일정 다시 짜기", type="primary"):
        # 잠기지 않은 일정만 재생성하는 로직 실행
        st.session_state.itinerary = reroll_mock_itinerary(
            st.session_state.itinerary, 
            st.session_state.locked_states, 
            reroll_comment if reroll_comment else "새로운 추천"
        )
        st.rerun() # 화면 새로고침하여 바뀐 결과 즉시 반영

import streamlit as st
import gspread
import google.generativeai as genai
from datetime import datetime

# 1. AI 및 구글 시트 기본 세팅 (보안상 파일 연동)
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # <--여기에 파트너의 실제 API 키를 넣어주세요!
genai.configure(api_key=GEMINI_API_KEY)

# 구글 시트 연결 함수
def connect_to_sheet():
    try:
        # 깃허브에 올린 travel-key.json 파일로 로그인
        gc = gspread.service_account(filename='travel-key.json')
        # 파트너가 만든 구글 시트 이름
        sh = gc.open("my_travel_guide_db")
        return sh.worksheet("history")
    except Exception as e:
        st.error(f"구글 시트 연결 실패: {e}")
        return None

# 2. 모바일 최적화 화면 레이아웃 설정
st.set_page_config(page_title="나만의 AI 트레블 가이드", layout="centered")

st.title("✈️ AI 트레블 가이드")
st.caption("모바일에 최적화된 맞춤형 여행 코스 플래너")
st.markdown("---")

# 3. 1번 기능: 여행 조건 입력창 UI
st.subheader("📍 1. 여행 조건 입력")

destination = st.text_input("어디로 떠나시나요?", placeholder="예: 제주도 서귀포, 일본 유레시노")
duration = st.selectbox("여행 일정", ["1박 2일", "2박 3일", "3박 4일", "4박 5일 이상"])
members = st.text_input("구성 인원", placeholder="예: 18개월 아기 동반 부부, 혼자, 친구 3명")

# 여행 강도 (1: 완전 널널함 ~ 10: 완전 빡빡함)
intensity = st.slider("여행 강도 (1: 널널함 ~ 10: 빡빡함)", 1, 10, 5)

special_comment = st.text_area("특별 코멘트 (선택사항)", placeholder="예: 조용한 카페 위주로 다녀오고 싶어요. 맛집 중심 등")

st.markdown("---")

# 4. 코스 생성 버튼 작동 트리거
if st.button("✨ 맞춤형 여행 코스 짜기", use_container_width=True):
    if not destination or not members:
        st.warning("여행지와 구성 인원을 입력해 주세요!")
    else:
        with st.spinner("🤖 AI 소믈리에가 완벽한 코스를 짜고 있습니다..."):
            try:
                # Gemini 프롬프트 구성 (AI에게 역할 부여)
                model = genai.GenerativeModel('gemini-pro')
                prompt = f"""
                너는 10년 경력의 베테랑 베테랑 여행 가이드 수석 디렉터야. 아래 조건에 맞는 완벽한 여행 코스를 짜줘.
                
                - 여행지: {destination}
                - 일정: {duration}
                - 구성인원: {members}
                - 여행강도: {intensity}/10 (1에 가까울수록 휴식 위주, 10에 가까울수록 일정 빡빡함)
                - 요청사항: {special_comment}
                
                각 일자별로 방문할 곳을 명확하게 나누어 보기 쉽게 한글로 작성해 줘.
                """
                
                response = model.generate_content(prompt)
                ai_course = response.text
                
                # 화면에 추천 코스 띄우기
                st.success("🎉 AI 추천 코스가 완성되었습니다!")
                st.markdown(ai_course)
                
                # [다음 스텝용] 세션 상태에 저장해두기
                st.session_state['current_course'] = ai_course
                
            except Exception as e:
                st.error(f"코스 생성 중 오류 발생: {e}")

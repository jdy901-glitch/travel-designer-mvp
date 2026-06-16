import streamlit as st
import gspread
import google.generativeai as genai
from datetime import datetime

# 🔒 제미니 키는 스트림릿 금고(Secrets)에서 안전하게 가져옵니다.
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error("Gemini API 키가 설정되지 않았습니다. Streamlit Secrets 설정을 확인해주세요.")

# 구글 시트 연결 및 데이터 누적 저장 함수
def save_to_google_sheet(destination, duration, members, intensity, comment, course, feedback):
    try:
        # 기존 성공 방식대로 깃허브에 올린 travel-key.json 파일로 로그인합니다.
        gc = gspread.service_account(filename='travel-key.json')
        sh = gc.open("my_travel_guide_db")
        worksheet = sh.worksheet("history")
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row_data = [now, destination, duration, members, intensity, comment, course, feedback]
        worksheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"구글 시트 저장 실패: {e}")
        return False

# 모바일 화면 최적화 세팅
st.set_page_config(page_title="AI 트레블 가이드", layout="centered")
st.title("✈️ AI 트레블 가이드")
st.caption("모바일에 최적화된 맞춤형 여행 코스 플래너")

# 모든 입력창을 왼쪽 접이식 '사이드바'로 이동
with st.sidebar:
    st.header("📍 여행 조건 입력")
    destination = st.text_input("어디로 떠나시나요?", placeholder="예: 일본 유레시노, 제주 서귀포")
    duration = st.selectbox("여행 일정", ["1박 2일", "2박 3일", "3박 4일", "4박 5일 이상"])
    members = st.text_input("구성 인원", placeholder="예: 18개월 아기 동반 부부")
    intensity = st.slider("여행 강도 (1:널널 ~ 10:빡빡)", 1, 10, 5)
    special_comment = st.text_area("특별 코멘트 (선택사항)", placeholder="예: 조용한 카페 위주, 맛집 중심 등")
    
    create_btn = st.button("✨ 맞춤형 코스 생성", use_container_width=True)

st.markdown("---")

if 'ai_course_result' not in st.session_state:
    st.session_state['ai_course_result'] = ""

# 코스 생성 버튼 작동
if create_btn:
    if not destination or not members:
        st.sidebar.warning("여행지와 구성 인원을 입력해 주세요!")
    else:
        with st.spinner("🤖 AI 가이드가 최적의 코스를 설계 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"""
                너는 10년 경력의 베테랑 여행 가이드 수석 디렉터야. 아래 조건에 맞는 맞춤형 여행 코스를 짜줘.
                
                - 여행지: {destination}
                - 일정: {duration}
                - 구성인원: {members}
                - 여행강도: {intensity}/10
                - 요청사항: {special_comment}
                
                출력 포맷: 반드시 '줄바꿈'을 기준으로 명확히 일정을 나누어 작성해줘.
                """
                response = model.generate_content(prompt)
                st.session_state['ai_course_result'] = response.text
            except Exception as e:
                st.error(f"오류 발생: {e}")

# 생성된 코스가 있을 때 체크박스 및 피드백창 노출
if st.session_state['ai_course_result']:
    st.subheader("🗓️ 추천된 여행 코스")
    
    course_lines = st.session_state['ai_course_result'].split('\n')
    st.info("💡 마음에 드는 일정은 체크하고, 수정하고 싶은 내용은 아래에 코멘트를 남겨보세요.")
    
    for idx, line in enumerate(course_lines):
        if line.strip():
            st.checkbox(line, key=f"line_{idx}", value=True)
            
    st.markdown("---")
    
    st.subheader("✍️ 일정 수정 및 이력 남기기")
    user_feedback = st.text_area("마음에 안 들거나 수정하고 싶은 내용을 적어주세요:", 
                                 placeholder="예: 2일차 오후 일정은 아기 컨디션 보고 바다 산책으로 대체할 예정")
    
    if st.button("💾 이 여행 일정 구글 시트에 저장하기", use_container_width=True):
        with st.spinner("📋 창고(구글 시트)에 안전하게 기록을 남기는 중..."):
            success = save_to_google_sheet(
                destination, duration, members, intensity, special_comment, 
                st.session_state['ai_course_result'], user_feedback
            )
            if success:
                st.success("🎉 여행 이력이 구글 시트에 성공적으로 저장되었습니다!")
else:
    st.write("📱 왼쪽 위의 **사이드바 메뉴( > 모양 버튼 )**를 열어 여행 조건을 입력하고 버튼을 눌러보세요!")

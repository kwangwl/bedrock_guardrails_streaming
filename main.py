# main.py
import streamlit as st
from llm.bedrock import get_streaming_response
from buffer_manager.buffer_manager import BufferManager

# 설정값
MODEL_ID = {
    "Haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "Sonnet 3.5 v1": "anthropic.claude-3-5-sonnet-20240620-v1:0",
}

# main page
st.set_page_config(page_title="Guardrails Demo")
st.title("🤖 Bedrock Guardrails 데모")

# 사이드바에 모델과 버퍼 크기 선택 옵션 추가
st.sidebar.header("설정")
selected_model = st.sidebar.selectbox(
    "모델 선택",
    options=list(MODEL_ID.keys()),
    key="model_select"
)

text_unit = st.sidebar.slider(
    "버퍼 크기",
    min_value=0,
    max_value=1000,
    value=250,
    step=10,
    help="한 번에 처리할 텍스트 단위 크기"
)

# 사용자 입력 UI
user_input = st.text_input("질문을 입력하세요:", "")

if st.button("답변 생성"):
    if user_input:
        # AI 응답을 위한 컨테이너 생성
        message_placeholder = st.container()

        # LLM 호출 (가드레일과 동일 리전 사용)
        llm_region = st.secrets["GUARDRAIL_REGION"]
        response = get_streaming_response(user_input, MODEL_ID[selected_model], llm_region)

        # 버퍼 매니저 초기화
        buffer_manager = BufferManager(
            placeholder=message_placeholder,
            text_unit=text_unit,
            guardrail_region=st.secrets["GUARDRAIL_REGION"],
            guardrail_id=st.secrets["GUARDRAIL_ID"],
            guardrail_version=st.secrets["GUARDRAIL_VERSION"]
        )

        # 스트리밍 응답 처리
        final_text = buffer_manager.process_stream(response)

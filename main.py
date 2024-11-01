import streamlit as st
from llm.bedrock import get_streaming_response
from buffer_manager.buffer_first_manager import BufferFirstManager

# 설정값
MODEL_ID = {
    "Haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "Sonnet 3.5 v1": "anthropic.claude-3-5-sonnet-20240620-v1:0",
}

# 가드레일 설정
GUARDRAIL_CONFIG = {
    "region": st.secrets["GUARDRAIL_REGION"],
    "guardrail_id": st.secrets["GUARDRAIL_ID"],
    "guardrail_version": st.secrets["GUARDRAIL_VERSION"]
}


def main():
    # 페이지 설정
    st.set_page_config(page_title="Guardrails Demo")
    st.title("🤖 Bedrock Guardrails 데모")

    # 사이드바 설정
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

    if st.button("답변 생성") and user_input:
        try:
            # LLM 호출
            response = get_streaming_response(
                prompt=user_input,
                model_id=MODEL_ID[selected_model],
                region=GUARDRAIL_CONFIG["region"]
            )

            # 버퍼 매니저로 응답 처리
            buffer_manager = BufferFirstManager(st.container(), text_unit, GUARDRAIL_CONFIG)
            buffer_manager.process_stream(response)

        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()

import streamlit as st
from llm.bedrock import get_streaming_response
from buffer_manager.post_guardrail_manager import PostGuardrailStreamManager
from buffer_manager.pre_guardrail_manager import PreGuardrailStreamManager


# 설정값
MODEL_ID = {
    "Haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "Sonnet 3.5 v1": "anthropic.claude-3-5-sonnet-20240620-v1:0",
}

BUFFER_MANAGERS = {
    "실시간 스트리밍 (가드레일 후처리)": PostGuardrailStreamManager,
    "지연 처리 (가드레일 선처리)": PreGuardrailStreamManager
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

    # 버퍼 매니저 선택
    selected_manager = st.sidebar.selectbox(
        "처리 방식 선택",
        options=list(BUFFER_MANAGERS.keys()),
        help="실시간 스트리밍: 텍스트를 즉시 표시하면서 가드레일 처리\n"
             "지연 처리: 버퍼에 모았다가 가드레일 처리 후 순차적으로 표시",
        key="manager_select"
    )

    # 버퍼 크기 설정
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

            # 선택된 버퍼 매니저로 응답 처리
            buffer_manager_class = BUFFER_MANAGERS[selected_manager]
            buffer_manager = buffer_manager_class(
                placeholder=st.container(),
                text_unit=text_unit,
                guardrail_config=GUARDRAIL_CONFIG
            )
            buffer_manager.process_stream(response)

        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()

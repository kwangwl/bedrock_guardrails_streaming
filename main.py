import streamlit as st
from llm.bedrock import get_streaming_response
from buffer_manager.post_guardrail_manager import PostGuardrailManager
from buffer_manager.pre_guardrail_manager import PreGuardrailManager
from buffer_manager.dynamic_pre_guardrail_manager import DynamicPreGuardrailManager


# 설정값
MODEL_ID = {
    "Haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "Sonnet 3.5 v1": "anthropic.claude-3-5-sonnet-20240620-v1:0",
}

BUFFER_MANAGERS = {
    "실시간 스트리밍 (가드레일 후처리)": PostGuardrailManager,
    "지연 처리 (가드레일 선처리)": PreGuardrailManager,
    "동적 버퍼 처리 (가드레일 선처리)": DynamicPreGuardrailManager
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
             "지연 처리: 버퍼에 모았다가 가드레일 처리 후 순차적으로 표시\n"
             "동적 버퍼: 첫 응답은 작은 버퍼로 빠르게, 이후는 큰 버퍼로 효율적으로 처리",
        key="manager_select"
    )

    # 버퍼 크기 설정
    initial_buffer_size = 0
    buffer_size = 0

    if selected_manager == "동적 버퍼 처리 (가드레일 선처리)":
        initial_buffer_size = st.sidebar.slider(
            "초기 버퍼 크기",
            min_value=0,
            max_value=500,
            value=50,
            step=10,
            help="첫 번째 응답의 버퍼 크기"
        )
        buffer_size = st.sidebar.slider(
            "이후 버퍼 크기",
            min_value=0,
            max_value=1000,
            value=250,
            step=10,
            help="두 번째 이후 응답의 버퍼 크기"
        )
    else:
        buffer_size = st.sidebar.slider(
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
            if selected_manager == "동적 버퍼 처리 (가드레일 선처리)":
                buffer_manager = buffer_manager_class(
                    placeholder=st.container(),
                    initial_buffer_size=initial_buffer_size,
                    subsequent_buffer_size=buffer_size,
                    guardrail_config=GUARDRAIL_CONFIG
                )
            else:
                buffer_manager = buffer_manager_class(
                    placeholder=st.container(),
                    buffer_size=buffer_size,
                    guardrail_config=GUARDRAIL_CONFIG
                )
            buffer_manager.process_stream(response)

        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
from guardrails.bedrock import apply_guardrail
import time


class BaseManager:
    """스트리밍 응답을 처리하는 기본 관리자 클래스"""

    def __init__(self, placeholder, buffer_size, guardrail_config, debug_mode):
        """초기 설정 및 상태 초기화"""
        self.placeholder = placeholder
        self.buffer_size = buffer_size
        self.guardrail_config = guardrail_config
        self.debug_mode = debug_mode

        # 공통 상태
        self.buffer_text = ""
        self.full_text = ""
        self.content_placeholder = None
        self.start_time = None
        self.b_first_write = True

    def process_stream(self, response):
        """스트림 응답을 처리하고 결과 텍스트 반환"""
        try:
            stream = response.get('stream')
            if not stream:
                return ""

            for event in stream:
                if 'messageStart' in event:
                    self.placeholder.divider()
                    self.start_time = time.time()
                if 'contentBlockDelta' in event:
                    should_stop = self._handle_content(event['contentBlockDelta']['delta']['text'])
                    if should_stop:
                        return self.full_text
                elif 'messageStop' in event:
                    self._handle_stream_end()
                elif 'metadata' in event:
                    self.placeholder.divider()
                    # self.placeholder.json(event['metadata'])

            return self.full_text

        except Exception as e:
            st.error(f"스트리밍 처리 중 오류 발생: {str(e)}")
            return ""

    def _apply_guardrail(self):
        """버퍼 텍스트에 가드레일 적용"""
        return apply_guardrail(
            text=self.buffer_text,
            text_type="OUTPUT",
            **self.guardrail_config
        )

    def _show_results(self, status, violations, response):
        """가드레일 검사 결과를 UI에 표시"""
        if self.debug_mode:
            # debug mode 일때만 출력
            status_messages = {
                "blocked": ("가드레일 검사 결과 : 🚫 Blocked", "error"),
                "anonymized": ("가드레일 검사 결과 : ⚠️ Anonymized", "warning"),
                "passed": ("가드레일 검사 결과 : ✅ Passed", "success")
            }

            message, method = status_messages.get(status)
            getattr(self.placeholder, method)(message)

            with self.placeholder.expander("가드레일 검사 Trace"):
                st.dataframe(pd.DataFrame(violations), hide_index=True, use_container_width=True)
                st.json(response)

    def _ensure_placeholder(self):
        """UI 표시를 위한 플레이스홀더 생성"""
        if self.content_placeholder is None:
            self.content_placeholder = self.placeholder.empty()

    def _reset_buffer(self):
        """버퍼 와 플레이스홀더 초기화"""
        self.buffer_text = ""
        self.content_placeholder = None

    # 하위 클래스에서 구현해야 하는 메서드들
    def _handle_content(self, new_text):
        """새로운 텍스트 컨텐츠 처리"""
        raise NotImplementedError

    def _handle_stream_end(self):
        """스트림 종료 시 처리"""
        raise NotImplementedError

    def _print_start_time(self):
        if self.b_first_write:
            end_time = time.time()
            elapsed_time = end_time - self.start_time
            self.placeholder.info(f"답변 Start (소요 시간: {elapsed_time:.2f} 초)")
            self.b_first_write = False

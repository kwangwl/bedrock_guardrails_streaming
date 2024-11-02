import streamlit as st
import pandas as pd
from guardrails.bedrock import apply_guardrail


class DelayedBufferManager:
    def __init__(self, placeholder, text_unit, guardrail_config):
        self.placeholder = placeholder
        self.text_unit = text_unit
        self.guardrail_config = guardrail_config

        # 텍스트 관련 상태
        self.buffer_text = ""
        self.full_text = ""
        self.processed_text = ""

        # 스트리밍 위치
        self.current_start_position = 0
        self.current_end_position = 0

        # UI 상태
        self.content_placeholder = None

    def process_stream(self, response):
        try:
            stream = response.get('stream')
            if not stream:
                return ""

            for event in stream:
                if 'messageStart' in event:
                    self.placeholder.markdown("**답변 Start**")

                elif 'contentBlockDelta' in event:
                    self._handle_content(event['contentBlockDelta']['delta']['text'])

                elif 'messageStop' in event:
                    self._finalize_streaming()

                elif 'metadata' in event:
                    self.placeholder.json(event['metadata'])

            return self.full_text

        except Exception as e:
            st.error(f"스트리밍 처리 중 오류 발생: {str(e)}")
            return ""

    def _handle_content(self, new_text):
        """새로운 텍스트 처리"""
        self._ensure_placeholder()
        self.buffer_text += new_text
        self._stream_current_content()

        if len(self.buffer_text) > self.text_unit:
            self._process_buffer()

    def _finalize_streaming(self):
        """스트리밍 종료 처리"""
        if self.buffer_text:
            self._process_buffer()
        self._ensure_placeholder()
        self._stream_remaining_content()

    def _ensure_placeholder(self):
        """플레이스홀더 확보"""
        if self.content_placeholder is None:
            self.content_placeholder = self.placeholder.empty()

    def _stream_current_content(self, chunk_size=5):
        """현재 처리된 텍스트 스트리밍"""
        if not self.processed_text or self.current_end_position >= len(self.processed_text):
            return

        end_pos = min(self.current_end_position + chunk_size, len(self.processed_text))
        chunk = self.processed_text[self.current_start_position:end_pos]
        self.content_placeholder.write(chunk)
        self.current_end_position = end_pos

    def _stream_remaining_content(self):
        """남은 텍스트 모두 스트리밍"""
        while self.current_end_position < len(self.processed_text):
            self._stream_current_content()

    def _process_buffer(self):
        """버퍼 처리 및 가드레일 적용"""
        if not self.buffer_text:
            return

        self._stream_remaining_content()
        status, violations, filtered_text, response = self._apply_guardrail()

        self._update_text_state(status, filtered_text)
        self._show_results(status, violations, response)
        self._reset_buffer()

    def _apply_guardrail(self):
        """가드레일 적용"""
        return apply_guardrail(
            text=self.buffer_text,
            text_type="OUTPUT",
            **self.guardrail_config
        )

    def _update_text_state(self, status, filtered_text):
        """텍스트 상태 업데이트"""
        self.full_text += filtered_text
        if status != "blocked":
            self.processed_text += filtered_text
            self.current_start_position = self.current_end_position

    def _show_results(self, status, violations, response):
        """가드레일 결과 표시"""
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

    def _reset_buffer(self):
        """버퍼 초기화"""
        self.buffer_text = ""
        self.content_placeholder = None

import streamlit as st
import pandas as pd
from guardrails.bedrock import apply_guardrail


class DelayedBufferManager:
    def __init__(self, placeholder, text_unit, guardrail_config):
        self.placeholder = placeholder
        self.text_unit = text_unit
        self.guardrail_config = guardrail_config

        self.buffer_text = ""
        self.full_text = ""
        self.processed_text = ""
        self.current_start_position = 0
        self.current_end_position = 0
        self.content_placeholder = None

    def process_stream(self, response):
        try:
            stream = response.get('stream')
            if not stream:
                return ""

            for event in stream:
                if 'messageStart' in event:
                    self.placeholder.markdown("**답변 Start**")

                if 'contentBlockDelta' in event:
                    new_text = event['contentBlockDelta']['delta']['text']
                    self._handle_content(new_text, is_last='messageStop' in event)

                if 'metadata' in event:
                    self.placeholder.json(event['metadata'])

            return self.full_text

        except Exception as e:
            st.error(f"스트리밍 처리 중 오류 발생: {str(e)}")
            return ""

    def _handle_content(self, new_text, is_last=False):
        """새로운 텍스트 처리"""
        if self.content_placeholder is None:
            self.content_placeholder = self.placeholder.empty()

        self.buffer_text += new_text
        self._stream_processed_content()

        # 버퍼가 기준 크기를 넘거나 마지막 청크일 경우에만 처리
        if len(self.buffer_text) > self.text_unit or is_last:
            self._process_buffer()

    def _stream_processed_content(self, chunk_size=5):
        """처리된 텍스트 스트리밍"""
        if self.processed_text and self.current_end_position < len(self.processed_text):
            end_pos = min(self.current_end_position + chunk_size, len(self.processed_text))
            chunk = self.processed_text[self.current_start_position:end_pos]
            self.content_placeholder.write(chunk)
            self.current_end_position = end_pos

    def _complete_current_streaming(self):
        """현재 처리된 텍스트 스트리밍 완료"""
        while self.current_end_position < len(self.processed_text):
            self._stream_processed_content()

    def _process_buffer(self):
        """버퍼 처리 및 가드레일 적용"""
        if not self.buffer_text:  # 빈 버퍼는 처리하지 않음
            return

        self._complete_current_streaming()

        status, violations, filtered_text, response = apply_guardrail(
            text=self.buffer_text,
            text_type="OUTPUT",
            **self.guardrail_config
        )

        self.full_text += filtered_text
        self._show_results(status, violations, response)

        if status != "blocked":
            self.processed_text += filtered_text
            self.current_start_position = self.current_end_position

        self._reset_buffer()

    def _show_results(self, status, violations, response):
        """가드레일 결과 표시"""
        if status == "blocked":
            self.placeholder.error("가드레일 검사 결과 : 🚫 Blocked")
        elif status == "anonymized":
            self.placeholder.warning("가드레일 검사 결과 : ⚠️ Anonymized")
        else:
            self.placeholder.success("가드레일 검사 결과 : ✅ Passed")

        with self.placeholder.expander("가드레일 검사 Trace"):
            st.dataframe(pd.DataFrame(violations), hide_index=True, use_container_width=True)
            st.json(response)

    def _reset_buffer(self):
        """버퍼 초기화"""
        self.buffer_text = ""
        self.content_placeholder = None

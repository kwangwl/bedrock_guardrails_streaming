import streamlit as st
import pandas as pd
from guardrails.bedrock import apply_guardrail
from collections import deque


class DelayedBufferManager:
    """버퍼에 텍스트를 모았다가 가드레일 처리 후 순차적으로 표시하는 매니저"""

    def __init__(self, placeholder, text_unit, guardrail_config):
        self.placeholder = placeholder
        self.text_unit = text_unit
        self.guardrail_config = guardrail_config

        self.buffer_text = ""
        self.full_text = ""
        self.content_placeholder = None
        self.output_queue = deque()  # 가드레일 처리된 텍스트를 저장할 큐

    def process_stream(self, response):
        """스트리밍 응답을 버퍼에 모아서 처리"""
        try:
            stream = response.get('stream')
            if not stream:
                return ""

            for event in stream:
                if 'messageStart' in event:
                    self.placeholder.markdown("**답변 Start**")

                if 'contentBlockDelta' in event:
                    # 새로운 텍스트를 버퍼에 추가
                    new_text = event['contentBlockDelta']['delta']['text']
                    self.buffer_text += new_text

                    # 버퍼가 기준 크기를 넘으면 가드레일 처리
                    if len(self.buffer_text) > self.text_unit:
                        self._process_buffer()
                        self._display_processed_text()

                if 'messageStop' in event:
                    # 남은 버퍼 처리
                    if self.buffer_text:
                        self._process_buffer()
                        self._display_processed_text()

            return self.full_text

        except Exception as e:
            st.error(f"스트리밍 처리 중 오류 발생: {str(e)}")
            return ""

    def _process_buffer(self):
        """버퍼 내용을 가드레일 처리하고 큐에 저장"""
        status, violations, filtered_text, response = apply_guardrail(
            text=self.buffer_text,
            text_type="OUTPUT",
            **self.guardrail_config
        )

        # 가드레일 결과 표시
        self._show_guardrail_results(status, violations, response)

        # 필터링된 텍스트를 한 글자씩 큐에 저장
        for char in filtered_text:
            self.output_queue.append(char)

        # 버퍼 초기화
        self.buffer_text = ""

    def _display_processed_text(self):
        """가드레일 처리된 텍스트를 순차적으로 표시"""
        if self.content_placeholder is None:
            self.content_placeholder = self.placeholder.empty()

        # 큐에서 텍스트를 하나씩 꺼내서 표시
        while self.output_queue:
            char = self.output_queue.popleft()
            self.full_text += char
            self.content_placeholder.write(self.full_text)

    def _show_guardrail_results(self, status, violations, response):
        """가드레일 결과 표시"""
        if status == "blocked":
            self.placeholder.error("가드레일 검사 결과 : 🚫 Blocked")
            return True
        elif status == "anonymized":
            self.placeholder.warning("가드레일 검사 결과 : ⚠️ Anonymized")
        else:
            self.placeholder.success("가드레일 검사 결과 : ✅ Passed")

        with self.placeholder.expander("가드레일 검사 Trace"):
            st.dataframe(pd.DataFrame(violations), hide_index=True, use_container_width=True)
            st.json(response)

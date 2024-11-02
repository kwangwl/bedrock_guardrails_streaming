# buffer_manager/delayed_buffer_manager.py

import streamlit as st
import pandas as pd
from guardrails.bedrock import apply_guardrail
from collections import deque


class DelayedBufferManager:
    """
    버퍼가 찰 때까지 텍스트를 모았다가 가드레일 처리 후 
    스트리밍 방식으로 보여주는 매니저
    """

    def __init__(self, placeholder, text_unit, guardrail_config):
        self.placeholder = placeholder
        self.text_unit = text_unit
        self.guardrail_config = guardrail_config

        self.buffer_text = ""
        self.full_text = ""
        self.content_placeholder = None
        self.processed_chunks = deque()  # 가드레일 처리된 청크를 저장

    def process_stream(self, response):
        try:
            stream = response.get('stream')
            if not stream:
                return ""

            if self.content_placeholder is None:
                self.content_placeholder = self.placeholder.empty()

            for event in stream:
                if 'messageStart' in event:
                    self.placeholder.markdown("**답변 Start**")

                if 'contentBlockDelta' in event:
                    # 새로운 텍스트를 버퍼에 추가
                    new_text = event['contentBlockDelta']['delta']['text']
                    self.buffer_text += new_text

                    # 버퍼가 기준 크기를 넘으면 가드레일 처리
                    if len(self.buffer_text) > self.text_unit:
                        # 가드레일 처리 및 결과 저장
                        processed_text = self._process_buffer()
                        if processed_text:
                            # 처리된 텍스트를 스트리밍 방식으로 표시
                            self._stream_processed_text(processed_text)

                if 'messageStop' in event:
                    # 남은 버퍼 처리
                    if self.buffer_text:
                        processed_text = self._process_buffer()
                        if processed_text:
                            self._stream_processed_text(processed_text)

            return self.full_text

        except Exception as e:
            st.error(f"스트리밍 처리 중 오류 발생: {str(e)}")
            return ""

    def _process_buffer(self):
        """버퍼 내용을 가드레일 처리"""
        status, violations, filtered_text, response = apply_guardrail(
            text=self.buffer_text,
            text_type="OUTPUT",
            **self.guardrail_config
        )

        # 가드레일 결과 표시
        if self._show_guardrail_results(status, violations, response):
            return None  # blocked 상태면 None 반환

        # 버퍼 초기화
        self.buffer_text = ""

        return filtered_text

    def _stream_processed_text(self, text):
        """처리된 텍스트를 스트리밍 방식으로 표시"""
        # 청크 단위로 텍스트 표시 (더 자연스러운 스트리밍 효과를 위해)
        chunk_size = 5  # 적절한 크기로 조정 가능
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            self.full_text += chunk
            self.content_placeholder.write(self.full_text)
            # time.sleep(0.05)  # 필요한 경우 딜레이 추가

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

        return False
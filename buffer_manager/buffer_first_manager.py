import streamlit as st
import pandas as pd
from guardrails.bedrock import apply_guardrail


class BufferFirstManager:
    def __init__(self, placeholder, text_unit, guardrail_config):
        """
        placeholder: streamlit 컨테이너
        text_unit: 버퍼 크기
        guardrail_config: 가드레일 설정 (region, id, version)
        """
        self.placeholder = placeholder
        self.text_unit = text_unit
        self.guardrail_config = guardrail_config

        self.buffer_text = ""
        self.full_text = ""
        self.content_placeholder = None

    def process_stream(self, response):
        """스트리밍 응답 처리"""
        try:
            stream = response.get('stream')
            if not stream:
                return ""

            for event in stream:
                # 시작 메시지
                if 'messageStart' in event:
                    self.placeholder.markdown("**답변 Start**")

                # 컨텐츠 처리
                if 'contentBlockDelta' in event:
                    should_stop = self._handle_content(event['contentBlockDelta']['delta']['text'])
                    if should_stop:
                        return self.full_text

                # 종료 메시지
                if 'messageStop' in event:
                    self._process_remaining_buffer()

                # 메타데이터
                if 'metadata' in event:
                    self.placeholder.json(event['metadata'])

            return self.full_text

        except Exception as e:
            st.error(f"스트리밍 처리 중 오류 발생: {str(e)}")
            return ""

    def _handle_content(self, new_text):
        """새로운 텍스트 처리"""
        # 컨텐츠 플레이스홀더 생성
        if self.content_placeholder is None:
            self.content_placeholder = self.placeholder.empty()

        # 버퍼에 텍스트 추가 및 표시
        self.buffer_text += new_text
        self.content_placeholder.write(self.buffer_text)

        # 버퍼가 기준 크기를 넘으면 가드레일 처리
        if len(self.buffer_text) > self.text_unit:
            should_stop = self._apply_guardrail()
            self._reset_buffer()
            return should_stop

        return False

    def _process_remaining_buffer(self):
        """남은 버퍼 처리"""
        if self.buffer_text:
            self._apply_guardrail()
            self._reset_buffer()

    def _apply_guardrail(self):
        """가드레일 적용"""
        status, violations, filtered_text, response = apply_guardrail(
            text=self.buffer_text,
            text_type="OUTPUT",
            **self.guardrail_config
        )

        self.full_text += filtered_text
        self._show_results(status, violations, response)

        return status == "blocked"

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

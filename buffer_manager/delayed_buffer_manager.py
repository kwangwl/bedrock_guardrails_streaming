import streamlit as st
import pandas as pd
from guardrails.bedrock import apply_guardrail


class DelayedBufferManager:
    def __init__(self, placeholder, text_unit, guardrail_config):
        self.placeholder = placeholder
        self.text_unit = text_unit
        self.guardrail_config = guardrail_config

        self.buffer_text = ""  # 현재 채우고 있는 버퍼
        self.full_text = ""  # 최종 출력된 전체 텍스트
        self.processed_text = ""  # 가드레일 통과해서 현재 출력 중인 텍스트
        self.current_end_position = 0  # 현재 출력 중인 마지막 위치
        self.content_placeholder = None

    def process_stream(self, response):
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

        # 이전에 처리된 텍스트가 있다면 계속 출력
        self._continue_streaming(len(new_text))

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

        # 남은 처리된 텍스트 모두 출력
        while self.current_position < len(self.processed_text):
            self._continue_streaming()

    def _continue_streaming(self, chunk_size=5):
        """현재 처리된 텍스트를 계속 스트리밍"""
        if self.processed_text and self.current_end_position < len(self.processed_text):
            end_pos = min(self.current_end_position + chunk_size, len(self.processed_text))
            chunk = self.processed_text[:end_pos]
            self.content_placeholder.write(chunk)

            self.current_end_position = end_pos

    def _apply_guardrail(self):
        """가드레일 적용"""
        status, violations, filtered_text, response = apply_guardrail(
            text=self.buffer_text,
            text_type="OUTPUT",
            **self.guardrail_config
        )

        self.full_text += filtered_text
        self._show_results(status, violations, response)

        if status != "blocked":
            # 새로운 처리된 텍스트 설정
            self.processed_text = filtered_text
            self.current_position = 0

        # 버퍼 초기화
        self.buffer_text = ""

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

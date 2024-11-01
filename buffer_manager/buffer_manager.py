from guardrail import bedrock_guardrails
import pandas as pd
import streamlit as st


class BufferManager:
    def __init__(self, placeholder, text_unit, guardrail_region, guardrail_id, guardrail_version):
        self.placeholder = placeholder
        self.text_unit = text_unit
        self.guardrail_region = guardrail_region
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version

        self.content_placeholder = None
        self.full_text = ""
        self.buffer_text = ""

    def process_stream(self, response):
        try:
            stream = response.get('stream')
            if not stream:
                return ""

            for event in stream:
                if 'messageStart' in event:
                    self.placeholder.markdown("**답변 Start**")

                if 'contentBlockDelta' in event:
                    if self._handle_content(event['contentBlockDelta']['delta']['text']):
                        return self.full_text

                if 'messageStop' in event:
                    self._handle_message_stop()

                if 'metadata' in event:
                    self.placeholder.json(event['metadata'])

            return self.full_text

        except Exception as e:
            print(f"버퍼 처리 중 오류 발생: {str(e)}")

    def _handle_content(self, new_text):
        """새로운 컨텐츠 처리"""
        b_stop = False
        if self.content_placeholder is None:
            self.content_placeholder = self.placeholder.empty()

        self.buffer_text += new_text
        self.content_placeholder.write(self.buffer_text)

        if len(self.buffer_text) > self.text_unit:
            b_stop = self._process_buffer()
            self.buffer_text = ""
            self.content_placeholder = None

        return b_stop

    def _handle_message_stop(self):
        if self.buffer_text:
            self._process_buffer()

    def _process_buffer(self):
        b_stop = False

        status, violations, filtered_text, response = bedrock_guardrails.apply_guardrail(
            text=self.buffer_text,
            text_type="OUTPUT",
            region=self.guardrail_region,
            guardrail_id=self.guardrail_id,
            guardrail_version=self.guardrail_version
        )
        self.full_text += filtered_text

        # status 처리
        if status == "blocked":
            self.placeholder.error("가드레일 검사 결과 : 🚫 Blocked")
            b_stop = True

        elif status == "anonymized":
            self.placeholder.warning("가드레일 검사 결과 : ⚠️ Anonymized")

        else:   # status == "passed"
            self.placeholder.success("가드레일 검사 결과 : ✅ Passed")

        with self.placeholder.expander("가드레일 검사 Trace"):
            st.dataframe(pd.DataFrame(violations), hide_index=True, use_container_width=True)
            st.json(response)

        return b_stop

import time
from buffer_manager.base_manager import BaseManager


class PreGuardrailManager(BaseManager):
    """가드레일 검사 후 승인된 텍스트만 점진적으로 표시하는 관리자"""

    def __init__(self, placeholder, buffer_size, guardrail_config, debug_mode):
        super().__init__(placeholder, buffer_size, guardrail_config, debug_mode)
        self.processed_text = ""
        self.current_start_position = 0
        self.current_end_position = 0

    def _handle_content(self, new_text):
        """새로운 텍스트를 버퍼에 추가하고 청크 단위로 처리"""
        self.buffer_text += new_text
        self._stream_current_content(len(new_text))

        if len(self.buffer_text) > self.buffer_size:
            self._process_buffer()
        return False

    def _handle_stream_end(self):
        """처리된 텍스트를 청크 단위로 표시"""
        if self.buffer_text:
            self._process_buffer()
        self._stream_remaining_content()

    def _stream_current_content(self, chunk_size=5):
        """처리된 텍스트를 청크 단위로 순차적으로 표시"""
        if not self.processed_text or self.current_end_position >= len(self.processed_text):
            return

        self._ensure_placeholder()
        end_pos = min(self.current_end_position + chunk_size, len(self.processed_text))
        chunk = self.processed_text[self.current_start_position:end_pos]
        self.content_placeholder.write(chunk)
        self.current_end_position = end_pos

        time.sleep(0.03)

    def _stream_remaining_content(self):
        """남은 처리된 텍스트 모두 표시"""
        while self.current_end_position < len(self.processed_text):
            self._stream_current_content()

    def _process_buffer(self):
        """버퍼 내용을 검사하고 승인된 텍스트만 처리"""
        if not self.buffer_text:
            return

        self._stream_remaining_content()
        status, violations, filtered_text, response = self._apply_guardrail()

        self.full_text += filtered_text
        if status != "blocked":
            self.processed_text += filtered_text
            self.current_start_position = self.current_end_position

        self._show_results(status, violations, response)
        self._reset_buffer()

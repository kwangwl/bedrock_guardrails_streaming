from buffer_manager.base_manager import BaseManager


class PostGuardrailManager(BaseManager):
    """텍스트를 먼저 표시하고 후속으로 가드레일을 적용하는 관리자"""
    def _handle_content(self, new_text):
        """새로운 텍스트를 버퍼에 추가하고 즉시 표시"""
        self._ensure_placeholder()
        self.buffer_text += new_text
        self._display_content(self.buffer_text)

        if len(self.buffer_text) > self.buffer_size:
            return self._process_buffer()
        return False

    def _handle_stream_end(self):
        """스트림 종료 시 남은 버퍼 처리"""
        if self.buffer_text:
            self._process_buffer()

    def _display_content(self, text):
        """UI에 텍스트 표시"""
        if text:
            self.content_placeholder.write(text)

    def _process_buffer(self):
        """버퍼 내용을 검사하고 결과 처리"""
        if not self.buffer_text:
            return False

        status, violations, filtered_text, response = self._apply_guardrail()
        self.full_text += filtered_text
        self._show_results(status, violations, response)
        self._reset_buffer()
        return status == "blocked"

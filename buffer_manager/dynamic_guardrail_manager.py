from buffer_manager.pre_guardrail_manager import PreGuardrailManager


class DynamicGuardrailManager(PreGuardrailManager):
    """첫 버퍼와 이후 버퍼 크기를 다르게 설정하여 처리하는 관리자"""

    def __init__(self, placeholder, initial_buffer_size, subsequent_buffer_size, guardrail_config, debug_mode):
        """초기 설정 및 상태 초기화"""
        super().__init__(placeholder, subsequent_buffer_size, guardrail_config, debug_mode)
        self.initial_buffer_size = initial_buffer_size
        self.subsequent_buffer_size = subsequent_buffer_size
        self.is_first_buffer = True

    def _handle_content(self, new_text):
        """새로운 텍스트를 버퍼에 추가하고 동적 크기로 처리"""
        self.buffer_text += new_text
        self._stream_current_content()

        current_buffer_size = self.initial_buffer_size if self.is_first_buffer else self.subsequent_buffer_size

        if len(self.buffer_text) > current_buffer_size:
            self._process_buffer()
            self.is_first_buffer = False
        return False
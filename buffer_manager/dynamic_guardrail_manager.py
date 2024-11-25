from buffer_manager.pre_guardrail_manager import PreGuardrailManager
import math


class DynamicGuardrailManager(PreGuardrailManager):
    """첫 버퍼와 이후 버퍼 크기를 다르게 설정하여 처리하는 관리자"""

    def __init__(self, placeholder, initial_buffer_size, second_buffer_size, subsequent_buffer_size, guardrail_config,
                 debug_mode):
        """초기 설정 및 상태 초기화"""
        super().__init__(placeholder, subsequent_buffer_size, guardrail_config, debug_mode)
        self.first_buffer_size = initial_buffer_size
        self.second_buffer_size = second_buffer_size
        self.subsequent_buffer_size = subsequent_buffer_size
        self.buffer_stage = 0  # 0: first, 1: second, 2: subsequent
        self.is_first_chunk = True

    def _handle_content(self, new_text):
        """새로운 텍스트를 버퍼에 추가하고 동적 크기로 처리"""
        self.buffer_text += new_text

        if self.buffer_stage == 1:
            chunk_size = max(1, int(len(new_text) / (self.second_buffer_size / self.first_buffer_size)))
        elif self.buffer_stage == 2:
            chunk_size = max(1, int(len(new_text) / (self.subsequent_buffer_size / self.second_buffer_size)))
        else:
            chunk_size = len(new_text)

        self._stream_current_content(chunk_size)

        current_buffer_size = self._get_current_buffer_size()

        if len(self.buffer_text) > current_buffer_size:
            self._process_buffer()
            self.buffer_stage = min(2, self.buffer_stage + 1)
            if self.buffer_stage == 2:
                self.is_first_chunk = False
        return False

    def _get_current_buffer_size(self):
        if self.buffer_stage == 0:
            return self.first_buffer_size
        elif self.buffer_stage == 1:
            return self.second_buffer_size
        else:
            return self.subsequent_buffer_size
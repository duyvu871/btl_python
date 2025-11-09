from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message

DESCRIPTOR: _descriptor.FileDescriptor

class TranscribeRequest(_message.Message):
    __slots__ = ("audio_id", "language_code")
    AUDIO_ID_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_CODE_FIELD_NUMBER: _ClassVar[int]
    audio_id: str
    language_code: str
    def __init__(self, audio_id: str | None = ..., language_code: str | None = ...) -> None: ...

class TranscribeResponse(_message.Message):
    __slots__ = ("transcript", "confidence")
    TRANSCRIPT_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    transcript: str
    confidence: float
    def __init__(self, transcript: str | None = ..., confidence: float | None = ...) -> None: ...

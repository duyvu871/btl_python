from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class TranscribeRequest(_message.Message):
    __slots__ = ("audio_id", "language_code")
    AUDIO_ID_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_CODE_FIELD_NUMBER: _ClassVar[int]
    audio_id: str
    language_code: str
    def __init__(self, audio_id: _Optional[str] = ..., language_code: _Optional[str] = ...) -> None: ...

class TranscribeResponse(_message.Message):
    __slots__ = ("transcript", "confidence")
    TRANSCRIPT_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    transcript: str
    confidence: float
    def __init__(self, transcript: _Optional[str] = ..., confidence: _Optional[float] = ...) -> None: ...

from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CheckQuotaRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    def __init__(self, user_id: _Optional[str] = ...) -> None: ...

class QuotaResponse(_message.Message):
    __slots__ = ("has_quota", "error_message")
    HAS_QUOTA_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    has_quota: bool
    error_message: str
    def __init__(self, has_quota: bool = ..., error_message: _Optional[str] = ...) -> None: ...

class CreateRecordingRequest(_message.Message):
    __slots__ = ("user_id", "source", "language", "meta_json")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    META_JSON_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    source: str
    language: str
    meta_json: str
    def __init__(self, user_id: _Optional[str] = ..., source: _Optional[str] = ..., language: _Optional[str] = ..., meta_json: _Optional[str] = ...) -> None: ...

class CompleteRecordingRequest(_message.Message):
    __slots__ = ("recording_id", "duration_ms", "segments")
    RECORDING_ID_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    SEGMENTS_FIELD_NUMBER: _ClassVar[int]
    recording_id: str
    duration_ms: int
    segments: _containers.RepeatedCompositeFieldContainer[SegmentData]
    def __init__(self, recording_id: _Optional[str] = ..., duration_ms: _Optional[int] = ..., segments: _Optional[_Iterable[_Union[SegmentData, _Mapping]]] = ...) -> None: ...

class SegmentData(_message.Message):
    __slots__ = ("idx", "start_ms", "end_ms", "text")
    IDX_FIELD_NUMBER: _ClassVar[int]
    START_MS_FIELD_NUMBER: _ClassVar[int]
    END_MS_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    idx: int
    start_ms: int
    end_ms: int
    text: str
    def __init__(self, idx: _Optional[int] = ..., start_ms: _Optional[int] = ..., end_ms: _Optional[int] = ..., text: _Optional[str] = ...) -> None: ...

class UpdateStatusRequest(_message.Message):
    __slots__ = ("recording_id", "status", "error_message")
    RECORDING_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    recording_id: str
    status: str
    error_message: str
    def __init__(self, recording_id: _Optional[str] = ..., status: _Optional[str] = ..., error_message: _Optional[str] = ...) -> None: ...

class RecordingResponse(_message.Message):
    __slots__ = ("recording_id", "status", "duration_ms")
    RECORDING_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    recording_id: str
    status: str
    duration_ms: int
    def __init__(self, recording_id: _Optional[str] = ..., status: _Optional[str] = ..., duration_ms: _Optional[int] = ...) -> None: ...

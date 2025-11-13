from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI


class ModelName(str, Enum):
    """Các models của Google Gemini."""
    GEMINI_FLASH_LATEST = "gemini-flash-latest"
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_0_PRO = "gemini-2.0-pro"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"


@dataclass
class LLMConfig:
    """Cấu hình cho Gemini LLM.

    Attributes:
        model_name: Tên model
        temperature: Độ ngẫu nhiên (0-1)
        max_output_tokens: Số tokens tối đa
        top_p: Nucleus sampling
        top_k: Top-k sampling
        api_key: Google API key
    """
    model_name: ModelName = ModelName.GEMINI_2_5_FLASH
    temperature: float = 0.7
    max_output_tokens: int = 2048
    top_p: float = 0.95
    top_k: int = 40
    api_key: str | None = None

class CompletionChain(ABC):
    """Base class cho completion chains.
    """

    def __init__(self, config: LLMConfig):
        """Khởi tạo chain.
        """
        self.config = config
        self.llm = self._initialize_llm()
        self.chain: Runnable | None = None

    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Khởi tạo Gemini LLM.
        """
        return ChatGoogleGenerativeAI(
            model=self.config.model_name.value,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            google_api_key=self.config.api_key,
        )

    @abstractmethod
    def _build_chain(self) -> Runnable:
        pass

    def build(self) -> 'CompletionChain':
        self.chain = self._build_chain()
        return self

    async def ainvoke(self, input_data: dict[str, Any]) -> str:
        if not self.chain:
            self.build()

        result = await self.chain.ainvoke(input_data)
        return result if isinstance(result, str) else result.get("output", str(result))

    def invoke(self, input_data: dict[str, Any]) -> str:
        if not self.chain:
            self.build()

        result = self.chain.invoke(input_data)
        return result if isinstance(result, str) else result.get("output", str(result))


class PromptBasedCompletionChain(CompletionChain):
    """Completion chain
    """

    def __init__(self, config: LLMConfig, prompt_template: ChatPromptTemplate):
        """Khởi tạo prompt-based completion chain.

        Args:
            config: Cấu hình LLM.
            prompt_template: ChatPromptTemplate
        """
        self.prompt_template = prompt_template
        super().__init__(config)

    def _build_chain(self) -> Runnable:
        """Xây dựng chain với prompt template.

        Returns:
            Runnable: Chain runnable.
        """
        return self.prompt_template | self.llm | StrOutputParser()
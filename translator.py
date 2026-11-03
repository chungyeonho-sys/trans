"""번역 로직 모듈. UI(app.py)와 분리되어 있다."""

import os

import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "gpt-6-astra"

SYSTEM_PROMPT = (
    "You are a professional translator.\n"
    "Translate the user's text into {target_language}.\n"
    "Output ONLY the translated text without any explanation, notes, or quotation marks.\n"
    "Preserve the original meaning, tone, line breaks, and formatting."
)


class TranslationError(Exception):
    """사용자에게 그대로 보여줄 수 있는 메시지를 담은 번역 오류 (PRD 10장)."""


def get_model() -> str:
    return os.getenv("OPENAI_MODEL") or DEFAULT_MODEL


def translate(text: str, target_language: str) -> str:
    """text를 target_language로 번역하여 번역문만 반환한다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise TranslationError(
            "❌ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해 주세요."
        )

    model = get_model()
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(target_language=target_language)},
                {"role": "user", "content": text},
            ],
        )
    except openai.AuthenticationError:
        raise TranslationError("❌ API 키가 올바르지 않습니다.") from None
    except openai.NotFoundError:
        raise TranslationError(
            f"❌ 모델({model})을 찾을 수 없습니다. .env의 OPENAI_MODEL을 확인해 주세요."
        ) from None
    except openai.RateLimitError:
        raise TranslationError("❌ 요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.") from None
    except openai.APIStatusError as e:
        raise TranslationError(f"❌ 번역 중 오류가 발생했습니다: HTTP {e.status_code}") from None
    except openai.APIError as e:
        # 연결 오류 등. 메시지에 API 키가 포함되지 않는 예외 클래스명만 노출한다.
        raise TranslationError(f"❌ 번역 중 오류가 발생했습니다: {type(e).__name__}") from None

    result = (response.choices[0].message.content or "").strip()
    if not result:
        raise TranslationError("❌ 번역 중 오류가 발생했습니다: 빈 응답")
    return result

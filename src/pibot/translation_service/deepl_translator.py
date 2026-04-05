"""DeepL translator service."""

from typing import cast

import deepl

from pibot.translation_service.translator import Translator


class DeepLTranslator(Translator):
    """DeepL translator service."""

    def __init__(self, api_key: str):
        """
        Initialize the DeepL translator.

        :param api_key: The API key for DeepL.
        """
        self.client = deepl.DeepLClient(api_key)

    def get_available_language(self) -> list[str]:
        """
        Get the available languages for translation.

        :return: A list of available languages.
        """
        return [lang.code for lang in self.client.get_target_languages()]

    def translate(self, text: str, target_lang: str) -> str:
        """
        Translate the given text to the target language.

        :param text: The text to translate.
        :param target_lang: The target language to translate to.
        :return: The translated text.
        """
        result = self.client.translate_text(
            text=text,
            target_lang=target_lang,
            context="A user sent this message on Discord.",
        )
        if isinstance(result, list):
            first = result[0] if result else None
            return cast(deepl.TextResult, first).text if first else ""
        return cast(deepl.TextResult, result).text

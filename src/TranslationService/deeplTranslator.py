import deepl

from TranslationService.translator import Translator


class DeepLTranslator(Translator):
    def __init__(self, api_key: str):
        self.client = deepl.DeepLClient(api_key)

    def get_available_language(self) -> list[str]:
        return [lang.code for lang in self.client.get_target_languages()]

    def translate(self, text: str, target_lang: str) -> str:
        return self.client.translate_text(text, target_lang=target_lang).text

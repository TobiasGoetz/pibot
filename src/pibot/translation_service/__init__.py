"""Translation service package."""

from pibot.translation_service.deepl_translator import DeepLTranslator
from pibot.translation_service.translator import Translator

__all__ = ["DeepLTranslator", "Translator"]

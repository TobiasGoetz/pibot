"""Abstract base class for translation services."""

from abc import ABC, abstractmethod


class Translator(ABC):
    """Abstract base class for translation services."""

    @abstractmethod
    def get_available_language(self) -> list[str]:
        """
        Get the available languages for translation.

        :return: A list of available languages.
        """
        ...

    @abstractmethod
    def translate(self, text: str, target_lang: str) -> str:
        """
        Translate the given text to the target language.

        :param text: The text to translate.
        :param target_lang: The target language to translate to.
        :return: The translated text.
        """
        ...

from abc import ABC, abstractmethod


class TranscriberInterface(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> tuple[str, dict]:
        """
        Transcribe un archivo de audio y retorna el texto y metadatos.
        """
        pass

import os
import re
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import torch

class SummarizationModel:
    def __init__(self, model_path: str = None):
        """
        Initialize the summarization model.
        
        Args:
            model_path: Path to the saved model. If None, uses the default location.
        """
        if model_path is None:
            deployed_model_path = Path(__file__).parent / "saved_summary_model"
            local_model_path = Path(__file__).parent.parent / "saved_summary_model"
            model_path = str(
                deployed_model_path if deployed_model_path.exists() else local_model_path
            )
        
        self.model_path = model_path
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()
            print(f"✓ Model loaded from {self.model_path} on device: {self.device}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model from {self.model_path}: {str(e)}")
    
    def summarize(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        """
        Generate a summary for the given text.
        
        Args:
            text: The text to summarize
            max_length: Maximum length of the summary
            min_length: Minimum length of the summary
            
        Returns:
            The generated summary
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        
        # Tokenize the input
        # The model was trained with a 512-token encoder input limit.
        inputs = self.tokenizer.encode(text, return_tensors="pt", max_length=512, truncation=True)
        inputs = inputs.to(self.device)
        
        # Generate summary
        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs,
                max_length=max_length,
                min_length=min_length,
                num_beams=4,
                early_stopping=True
            )
        
        # Decode the summary
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary

# Global model instance
_model_instance = None


class LightweightSummarizationModel:
    """Extractive summarizer for small-memory deployments."""

    def summarize(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text.strip()) if sentence.strip()]
        if not sentences:
            raise ValueError("Input text cannot be empty")

        words = re.findall(r"[A-Za-z']+", text.lower())
        frequencies = {}
        for word in words:
            frequencies[word] = frequencies.get(word, 0) + 1

        ranked = sorted(
            enumerate(sentences),
            key=lambda item: sum(frequencies.get(word, 0) for word in re.findall(r"[A-Za-z']+", item[1].lower()))
            / max(len(item[1].split()), 1),
            reverse=True,
        )
        selected = []
        length = 0
        for index, sentence in sorted(ranked, key=lambda item: item[0]):
            sentence_length = len(sentence.split())
            if selected and length + sentence_length > max_length:
                continue
            selected.append(sentence)
            length += sentence_length
            if length >= min_length:
                break

        return " ".join(selected)[: max_length * 7].strip()

class HuggingFaceSummarizationModel:
    """Summarizer backed by the Hugging Face Inference API."""

    def __init__(self, model_id: str, token: str):
        self.endpoint = f"https://router.huggingface.co/hf-inference/models/{model_id}"
        self.token = token

    def summarize(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        payload = json.dumps({
            "inputs": text,
            "parameters": {
                "max_length": max_length,
                "min_length": min_length,
            },
        }).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=90) as response:
                    result = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as error:
                if error.code == 503 and attempt < 2:
                    retry_after = error.headers.get("Retry-After")
                    try:
                        wait_seconds = min(float(retry_after), 30) if retry_after else 10
                    except ValueError:
                        wait_seconds = 10
                    time.sleep(wait_seconds)
                    continue
                raise RuntimeError("Hugging Face summarization request failed.") from error
            except (URLError, ValueError) as error:
                raise RuntimeError("Hugging Face summarization request failed.") from error

        if not isinstance(result, list) or not result or not isinstance(result[0], dict):
            raise RuntimeError("Hugging Face returned an invalid summarization response.")
        summary = result[0].get("summary_text", "").strip()
        if not summary:
            raise RuntimeError("Hugging Face returned an empty summary.")
        return summary


class ResilientSummarizationModel:
    """Prefer Hugging Face while keeping the web API available during outages."""

    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    def summarize(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        try:
            return self.primary.summarize(text, max_length, min_length)
        except RuntimeError:
            return self.fallback.summarize(text, max_length, min_length)


def get_model() -> SummarizationModel:
    """Get or create the global model instance."""
    global _model_instance
    if _model_instance is None:
        hf_token = os.getenv("HF_API_TOKEN", "").strip()
        hf_model_id = os.getenv("HF_MODEL_ID", "facebook/bart-large-cnn").strip()
        lightweight_mode = os.getenv("LIGHTWEIGHT_MODE", "").lower() in {"1", "true", "yes"}
        if lightweight_mode:
            _model_instance = LightweightSummarizationModel()
        elif hf_token:
            _model_instance = ResilientSummarizationModel(
                HuggingFaceSummarizationModel(hf_model_id, hf_token),
                LightweightSummarizationModel(),
            )
        elif os.getenv("LIGHTWEIGHT_MODE", "").lower() in {"1", "true", "yes"}:
            _model_instance = LightweightSummarizationModel()
        else:
            _model_instance = SummarizationModel()
    return _model_instance

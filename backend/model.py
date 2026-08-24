import os
import re
from pathlib import Path

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
        import torch

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

def get_model() -> SummarizationModel:
    """Get or create the global model instance."""
    global _model_instance
    if _model_instance is None:
        if os.getenv("LIGHTWEIGHT_MODE", "").lower() in {"1", "true", "yes"}:
            _model_instance = LightweightSummarizationModel()
        else:
            _model_instance = SummarizationModel()
    return _model_instance

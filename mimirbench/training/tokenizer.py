"""Deterministic tokenizers for synthetic small-transformer training."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

__all__ = [
    "BOS_TOKEN",
    "EOS_TOKEN",
    "PAD_TOKEN",
    "SEP_TOKEN",
    "SPECIAL_TOKENS",
    "UNK_TOKEN",
    "SymbolTokenizer",
    "TraceTokenizer",
]

PAD_TOKEN = "<pad>"
BOS_TOKEN = "<bos>"
EOS_TOKEN = "<eos>"
UNK_TOKEN = "<unk>"
SEP_TOKEN = "<sep>"
SPECIAL_TOKENS = (PAD_TOKEN, BOS_TOKEN, EOS_TOKEN, UNK_TOKEN, SEP_TOKEN)

_TOKEN_RE = re.compile(r"<[^>\s]+>|[A-Za-z_][A-Za-z0-9_]*|[0-9]+(?:\.[0-9]+)?|[^\s]")


class SymbolTokenizer:
    """Backward-compatible bidirectional mapping between symbols and ids."""

    def __init__(self, vocab: Sequence[str]) -> None:
        tokens = list(SPECIAL_TOKENS[:3]) + [t for t in vocab if t not in SPECIAL_TOKENS[:3]]
        if len(set(tokens)) != len(tokens):
            raise ValueError("vocabulary contains duplicate symbols.")
        self._id_to_token: list[str] = tokens
        self._token_to_id: dict[str, int] = {t: i for i, t in enumerate(tokens)}

    @classmethod
    def from_corpus(cls, sequences: Iterable[Sequence[str]]) -> SymbolTokenizer:
        """Build a tokenizer from all symbols seen in ``sequences`` (sorted)."""
        seen: set[str] = set()
        for seq in sequences:
            seen.update(seq)
        return cls(sorted(seen))

    @property
    def vocab_size(self) -> int:
        return len(self._id_to_token)

    @property
    def pad_id(self) -> int:
        return self._token_to_id[PAD_TOKEN]

    @property
    def bos_id(self) -> int:
        return self._token_to_id[BOS_TOKEN]

    @property
    def eos_id(self) -> int:
        return self._token_to_id[EOS_TOKEN]

    def encode(self, tokens: Sequence[str], *, add_bos: bool = False, add_eos: bool = False) -> list[int]:
        ids = [self._token_to_id[t] for t in tokens]
        if add_bos:
            ids = [self.bos_id, *ids]
        if add_eos:
            ids = [*ids, self.eos_id]
        return ids

    def decode(self, ids: Sequence[int], *, skip_special: bool = True) -> list[str]:
        out: list[str] = []
        for token_id in ids:
            token = self._id_to_token[token_id]
            if skip_special and token in SPECIAL_TOKENS[:3]:
                continue
            out.append(token)
        return out


class TraceTokenizer:
    """Simple regex tokenizer with fixed-length padding and attention masks."""

    def __init__(self, vocab: Sequence[str], *, max_length: int = 128) -> None:
        if max_length < 4:
            raise ValueError("max_length must be >= 4.")
        tokens = list(SPECIAL_TOKENS) + [token for token in vocab if token not in SPECIAL_TOKENS]
        if len(set(tokens)) != len(tokens):
            raise ValueError("vocabulary contains duplicate tokens.")
        self._id_to_token = tokens
        self._token_to_id = {token: idx for idx, token in enumerate(tokens)}
        self.max_length = max_length

    @classmethod
    def from_texts(cls, texts: Iterable[str], *, max_length: int = 128) -> TraceTokenizer:
        """Build a deterministic vocabulary from text examples."""
        seen: set[str] = set()
        for text in texts:
            seen.update(tokenize_text(text))
        return cls(sorted(seen), max_length=max_length)

    @classmethod
    def from_traces(cls, traces: Iterable[Mapping[str, Any]], *, max_length: int = 128) -> TraceTokenizer:
        """Build a vocabulary from trace inputs and serialized target labels."""
        texts: list[str] = []
        for trace in traces:
            input_text = trace.get("input")
            if isinstance(input_text, str):
                texts.append(input_text)
            targets = trace.get("targets")
            if isinstance(targets, Mapping):
                texts.extend(str(value) for value in targets.values() if isinstance(value, str))
        return cls.from_texts(texts, max_length=max_length)

    @classmethod
    def load(cls, path: str | Path) -> TraceTokenizer:
        """Load a tokenizer vocabulary from disk."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("tokenizer file must contain a JSON object.")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TraceTokenizer:
        """Construct from the serialised form produced by :meth:`to_dict`."""
        vocab = data.get("tokens")
        if not isinstance(vocab, list) or not all(isinstance(item, str) for item in vocab):
            raise ValueError("tokenizer payload is missing string token list.")
        max_length = data.get("max_length", 128)
        if not isinstance(max_length, int):
            raise ValueError("tokenizer max_length must be an integer.")
        payload_tokens = [token for token in vocab if token not in SPECIAL_TOKENS]
        return cls(payload_tokens, max_length=max_length)

    @property
    def vocab_size(self) -> int:
        return len(self._id_to_token)

    @property
    def pad_id(self) -> int:
        return self._token_to_id[PAD_TOKEN]

    @property
    def bos_id(self) -> int:
        return self._token_to_id[BOS_TOKEN]

    @property
    def eos_id(self) -> int:
        return self._token_to_id[EOS_TOKEN]

    @property
    def unk_id(self) -> int:
        return self._token_to_id[UNK_TOKEN]

    @property
    def sep_id(self) -> int:
        return self._token_to_id[SEP_TOKEN]

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text deterministically."""
        return tokenize_text(text)

    def encode(
        self,
        text: str | Sequence[str],
        *,
        add_special_tokens: bool = True,
        padding: bool = True,
        truncation: bool = True,
    ) -> dict[str, list[int]]:
        """Encode text or pre-tokenized input to ids plus an attention mask."""
        tokens = list(text) if not isinstance(text, str) else self.tokenize(text)
        if add_special_tokens:
            tokens = [BOS_TOKEN, *tokens, EOS_TOKEN]
        ids = [self._token_to_id.get(token, self.unk_id) for token in tokens]
        if len(ids) > self.max_length:
            if not truncation:
                raise ValueError(
                    f"encoded sequence length {len(ids)} exceeds max_length={self.max_length}."
                )
            ids = ids[: self.max_length]
            if add_special_tokens:
                ids[-1] = self.eos_id
        attention_mask = [1] * len(ids)
        if padding and len(ids) < self.max_length:
            pad_count = self.max_length - len(ids)
            ids = [*ids, *([self.pad_id] * pad_count)]
            attention_mask = [*attention_mask, *([0] * pad_count)]
        return {"input_ids": ids, "attention_mask": attention_mask}

    def decode(self, ids: Sequence[int], *, skip_special: bool = True) -> str:
        """Decode token ids to a whitespace-normalized string."""
        tokens: list[str] = []
        for token_id in ids:
            if not 0 <= int(token_id) < len(self._id_to_token):
                token = UNK_TOKEN
            else:
                token = self._id_to_token[int(token_id)]
            if skip_special and token in SPECIAL_TOKENS:
                continue
            tokens.append(token)
        return " ".join(tokens)

    def to_dict(self) -> dict[str, Any]:
        """Serialise tokenizer metadata and vocabulary."""
        return {
            "type": "TraceTokenizer",
            "max_length": self.max_length,
            "tokens": self._id_to_token,
        }

    def save(self, path: str | Path) -> Path:
        """Save the tokenizer vocabulary as JSON."""
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        return output


def tokenize_text(text: str) -> list[str]:
    """Tokenize text using the project-local synthetic trace regex."""
    return _TOKEN_RE.findall(text)

"""Tests for the deterministic trace tokenizer."""

from __future__ import annotations

from pathlib import Path

from mimirbench.training.tokenizer import UNK_TOKEN, TraceTokenizer


def test_trace_tokenizer_roundtrips_simple_trace_text() -> None:
    text = "prior A=0.400 B=0.600; observations X not_X"
    tokenizer = TraceTokenizer.from_texts([text], max_length=32)
    encoded = tokenizer.encode(text)
    decoded = tokenizer.decode(encoded["input_ids"])
    assert decoded == "prior A = 0.400 B = 0.600 ; observations X not_X"
    assert len(encoded["input_ids"]) == 32
    assert len(encoded["attention_mask"]) == 32


def test_trace_tokenizer_unknown_token_and_save_load(tmp_path: Path) -> None:
    tokenizer = TraceTokenizer.from_texts(["known token"], max_length=12)
    encoded = tokenizer.encode("unknown_token")
    assert tokenizer.unk_id in encoded["input_ids"]
    assert UNK_TOKEN in tokenizer.decode(encoded["input_ids"], skip_special=False)
    path = tokenizer.save(tmp_path / "vocab.json")
    loaded = TraceTokenizer.load(path)
    assert loaded.encode("known") == tokenizer.encode("known")

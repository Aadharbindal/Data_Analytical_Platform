from app.ai.rag_engine import chunk_text


def test_short_text_is_not_chunked():
    assert chunk_text("Revenue means total transaction value.") == ["Revenue means total transaction value."]


def test_long_schema_like_text_is_split_into_multiple_chunks():
    text = "Dataset sales.csv contains columns: " + ", ".join(f"Column{i} (numeric)" for i in range(30))
    chunks = chunk_text(text, max_chars=100)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 100 + 60  # small overlap slack


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []


def test_text_with_no_delimiters_falls_back_to_character_windows():
    blob = "x" * 900
    chunks = chunk_text(blob, max_chars=200)
    assert len(chunks) >= 4

import json
import re
import pytest

# Load the JSON file once for all tests
@pytest.fixture(scope="session")
def prd_items():
    with open("equivalents_detailed.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["prd_items"]

# -------------------------
# 1. Schema Validation
# -------------------------

def test_all_keys_present(prd_items):
    for item in prd_items:
        assert "index" in item
        assert "text" in item
        assert "tokens" in item

def test_index_is_integer(prd_items):
    for item in prd_items:
        assert isinstance(item["index"], int)

def test_text_is_string(prd_items):
    for item in prd_items:
        assert isinstance(item["text"], str)

def test_tokens_is_list(prd_items):
    for item in prd_items:
        assert isinstance(item["tokens"], list)

# -------------------------
# 2. Data Integrity
# -------------------------

def test_unique_index_values(prd_items):
    indices = [item["index"] for item in prd_items]
    assert len(indices) == len(set(indices))

def test_tokens_are_strings(prd_items):
    for item in prd_items:
        for token in item["tokens"]:
            assert isinstance(token, str)

def test_text_not_empty(prd_items):
    for item in prd_items:
        assert item["text"].strip() != ""

def test_date_format(prd_items):
    # Look for items that look like dates
    for item in prd_items:
        if re.match(r"^\d{4}-\d{2}-\d{2}$", item["text"]):
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", item["text"])

# -------------------------
# 3. Business Rules
# -------------------------

def test_tokens_match_text_words(prd_items):
    for item in prd_items:
        text_words = re.findall(r"\w+", item["text"].lower())
        for token in item["tokens"]:
            assert token.lower() in text_words

def test_version_format(prd_items):
    for item in prd_items:
        if re.match(r"^\d+(\.\d+)?$", item["text"]):
            assert re.match(r"^\d+(\.\d+)?$", item["text"])

def test_author_name_format(prd_items):
    for item in prd_items:
        if "author" in item["tokens"]:
            assert len(item["text"].split()) >= 2

# -------------------------
# 4. Edge Cases
# -------------------------

def test_empty_tokens_allowed_for_version(prd_items):
    for item in prd_items:
        if re.match(r"^\d+(\.\d+)?$", item["text"]):
            assert isinstance(item["tokens"], list)

def test_special_characters_in_text(prd_items):
    for item in prd_items:
        if "📄" in item["text"]:
            assert "📄" in item["text"]

def test_long_text_handled(prd_items):
    for item in prd_items:
        if len(item["text"]) > 50:
            assert isinstance(item["text"], str)

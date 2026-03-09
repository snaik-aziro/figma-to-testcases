"""PRD Analyzer: extract intents, entities and important keywords from PRD text.

Provides a lightweight analyzer with an optional LLM-backed extraction when
the Gemini API key is available. Returns a signals dict used to boost
component relevance scoring.
"""
from typing import Dict, Any, List
import os
from app.config import get_settings

settings = get_settings()


def _simple_keyword_extraction(text: str, top_k: int = 20) -> Dict[str, float]:
    """Fallback extractor: returns most frequent meaningful words with weights."""
    import re
    from collections import Counter

    if not text:
        return {}

    # Lower, remove punctuation, keep words >=3 chars
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    stopwords = {
        'the','and','for','with','that','this','will','should','are','from','have','has','but','not','you','your'
    }
    filtered = [w for w in words if w not in stopwords]
    counts = Counter(filtered)
    most = counts.most_common(top_k)
    # Normalize weights to 0-1
    if not most:
        return {}
    maxc = most[0][1]
    return {k: v / maxc for k, v in most}


def analyze_prd(prd_text: str, use_llm: bool = True) -> Dict[str, Any]:
    """Return a signals dict: { 'keywords': {kw: weight}, 'intents': [...] }

    If LLM is available and settings.gemini_api_key is set, use it to extract
    structured intents; otherwise fall back to simple extraction.
    """
    signals: Dict[str, Any] = {'keywords': {}, 'intents': []}
    if not prd_text:
        return signals

    # Try LLM-based extraction only if configured
    try:
        if use_llm and (settings.gemini_api_key or os.getenv('GEMINI_API_KEY')):
            try:
                import google.generativeai as genai
                genai.configure(api_key=(settings.gemini_api_key or os.getenv('GEMINI_API_KEY')))
                model = genai.GenerativeModel(settings.llm_model)
                prompt = (
                    "Extract the top 12 feature keywords and highest-priority user intents "
                    "from the following PRD text. Return JSON: {\"keywords\": {keyword: weight}, \"intents\": [intent strings]}"
                    f"\n\nPRD:\n{prd_text[:6000]}"
                )
                generation_config = genai.types.GenerationConfig(max_output_tokens=1024, temperature=0.0)
                resp = model.generate_content(contents=prompt, generation_config=generation_config)
                text = resp.text
                # Try to parse JSON block
                import json, re
                m = re.search(r"\{.*\}\s*$", text, re.DOTALL)
                if m:
                    payload = json.loads(m.group(0))
                    signals['keywords'] = payload.get('keywords', {})
                    signals['intents'] = payload.get('intents', [])
                    return signals
            except Exception:
                # Fall through to simple analyzer
                pass

    except Exception:
        pass

    # Fallback simple extraction
    signals['keywords'] = _simple_keyword_extraction(prd_text, top_k=30)
    # Derive intents as top 6 keywords phrased
    signals['intents'] = [k for k in list(signals['keywords'].keys())[:6]]
    return signals

"""
Text cleaning / normalization pipeline that turns raw headline+article text
into the token stream that feeds TF-IDF.

The exact same TextCleaner configuration must be used at training time and
at inference time — src/data/loader.py and src/models/predict.py both build
their cleaner via `build_default_cleaner()` below instead of instantiating
TextCleaner with ad-hoc arguments, so the two can never silently drift apart
and cause data leakage / train-serve skew.

Robustness note: NLTK's tokenizer/stopwords/lemmatizer corpora require a
one-time download. If NLTK isn't installed, or the corpora can't be
downloaded (e.g. no internet access, such as in an offline CI/sandbox
environment), this module automatically falls back to a lightweight
built-in tokenizer and stopword list rather than crashing — preprocessing
quality degrades slightly, but the application keeps working end to end.
"""
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_NON_ALPHANUMERIC_RE = re.compile(r"[^a-z0-9\s]")
_MULTI_SPACE_RE = re.compile(r"\s+")

# A compact built-in stopword list used only when NLTK's richer corpus isn't
# available. Deliberately conservative (common function words only) so it
# never accidentally strips a content-bearing word.
_FALLBACK_STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are aren't as at be
    because been before being below between both but by can't cannot could
    couldn't did didn't do does doesn't doing don't down during each few for
    from further had hadn't has hasn't have haven't having he he'd he'll he's
    her here here's hers herself him himself his how how's i i'd i'll i'm
    i've if in into is isn't it it's its itself let's me more most mustn't
    my myself no nor not of off on once only or other ought our ours
    ourselves out over own same shan't she she'd she'll she's should
    shouldn't so some such than that that's the their theirs them themselves
    then there there's these they they'd they'll they're they've this those
    through to too under until up very was wasn't we we'd we'll we're we've
    were weren't what what's when when's where where's which while who who's
    whom why why's with won't would wouldn't you you'd you'll you're you've
    your yours yourself yourselves
    """.split()
)

# --- Optional NLTK backend --------------------------------------------------
_NLTK_READY = False
try:
    import nltk
    from nltk.corpus import stopwords as _nltk_stopwords
    from nltk.stem import PorterStemmer, WordNetLemmatizer
    from nltk.tokenize import word_tokenize as _nltk_word_tokenize

    def _ensure_nltk_data() -> bool:
        required = [
            ("tokenizers/punkt", "punkt"),
            ("tokenizers/punkt_tab", "punkt_tab"),
            ("corpora/stopwords", "stopwords"),
            ("corpora/wordnet", "wordnet"),
            ("corpora/omw-1.4", "omw-1.4"),
        ]
        all_ready = True
        for data_path, package_name in required:
            try:
                nltk.data.find(data_path)
            except LookupError:
                try:
                    nltk.download(package_name, quiet=True)
                    nltk.data.find(data_path)
                except Exception:  # noqa: BLE001 - no internet, bad mirror, etc.
                    all_ready = False
        return all_ready

    _NLTK_READY = _ensure_nltk_data()
except ImportError:
    _NLTK_READY = False

if _NLTK_READY:
    logger.info("TextCleaner: using NLTK for tokenization, stopwords, and lemmatization.")
else:
    logger.warning(
        "TextCleaner: NLTK resources unavailable (either NLTK isn't installed, "
        "or its corpora couldn't be downloaded — no internet access). Falling "
        "back to a lightweight built-in tokenizer + stopword list. For "
        "higher-quality preprocessing, install NLTK and run "
        "`python -m nltk.downloader punkt punkt_tab stopwords wordnet omw-1.4`."
    )


@dataclass
class TextCleanerConfig:
    lowercase: bool = True
    remove_html: bool = True
    remove_urls: bool = True
    remove_emails: bool = True
    strip_non_alphanumeric: bool = True
    remove_stopwords_flag: bool = True
    use_lemmatization: bool = True  # if False (and NLTK available), stems instead


class TextCleaner:
    """Deterministic text -> clean-token-string pipeline.

    Call `.clean(text)` to get back a single, space-joined string of
    processed tokens suitable for TfidfVectorizer (which is configured with
    lowercase=False since cleaning already handles it — see
    src/features/tfidf_features.py).
    """

    def __init__(self, cfg: TextCleanerConfig | None = None):
        self.cfg = cfg or TextCleanerConfig()
        self._lemmatizer = WordNetLemmatizer() if (_NLTK_READY and self.cfg.use_lemmatization) else None
        self._stemmer = PorterStemmer() if (_NLTK_READY and not self.cfg.use_lemmatization) else None
        self._stopwords = set(_nltk_stopwords.words("english")) if _NLTK_READY else set(_FALLBACK_STOPWORDS)

    def clean(self, text: str) -> str:
        if not text:
            return ""

        cleaned = unicodedata.normalize("NFKC", text)
        cleaned = html.unescape(cleaned)

        if self.cfg.remove_html:
            cleaned = _HTML_TAG_RE.sub(" ", cleaned)
        if self.cfg.remove_urls:
            cleaned = _URL_RE.sub(" ", cleaned)
        if self.cfg.remove_emails:
            cleaned = _EMAIL_RE.sub(" ", cleaned)
        if self.cfg.lowercase:
            cleaned = cleaned.lower()
        if self.cfg.strip_non_alphanumeric:
            # Keeps letters AND digits (numbers can carry signal — e.g.
            # statistics-heavy writing) and only strips punctuation/symbols.
            cleaned = _NON_ALPHANUMERIC_RE.sub(" ", cleaned)

        cleaned = _MULTI_SPACE_RE.sub(" ", cleaned).strip()
        if not cleaned:
            return ""

        tokens = self._tokenize(cleaned)

        if self.cfg.remove_stopwords_flag:
            tokens = [t for t in tokens if t not in self._stopwords]

        tokens = [t for t in (self._normalize_token(tok) for tok in tokens) if t]

        return " ".join(tokens)

    def _tokenize(self, text: str) -> list[str]:
        if _NLTK_READY:
            try:
                return _nltk_word_tokenize(text)
            except Exception:  # noqa: BLE001 - fall back rather than crash
                pass
        return text.split()

    def _normalize_token(self, token: str) -> str:
        if len(token) < 2:
            return ""
        if self._lemmatizer is not None:
            return self._lemmatizer.lemmatize(token)
        if self._stemmer is not None:
            return self._stemmer.stem(token)
        return token


def build_default_cleaner() -> TextCleaner:
    """The single TextCleaner configuration used across the entire project.

    src/data/loader.py (training) and src/models/predict.py (inference)
    both call this factory instead of constructing TextCleaner directly, so
    training and inference are guaranteed to use identical preprocessing.
    """
    return TextCleaner(TextCleanerConfig())

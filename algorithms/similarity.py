"""
algorithms/similarity.py

Core text-similarity algorithms used by the Plagiarism Detector module.

Implements, from first principles (no external NLP libraries), the
algorithms explicitly required by the project spec:

    1. Jaccard Similarity        - set-based similarity
    2. Cosine Similarity         - vector-space similarity using term
                                    frequency dictionaries (hash tables)
    3. Rabin-Karp String Matching - substring search using rolling hash
    4. KMP String Matching        - substring search using a prefix
                                    function (failure function)

Data structures explicitly demonstrated here:
    * Hash Tables (Python dict)  -> term-frequency vectors, char->index maps
    * Sets                       -> Jaccard similarity, common/unique words
    * Lists                      -> tokenized word sequences
"""

import math
import re
from typing import Dict, List, Set, Tuple


# ---------------------------------------------------------------------- #
# Tokenization helpers
# ---------------------------------------------------------------------- #
_WORD_RE = re.compile(r"[A-Za-z0-9']+")


def tokenize(text: str) -> List[str]:
    """
    Split raw text into a list of lowercase word tokens, stripping
    punctuation. This is the canonical tokenizer used across the
    plagiarism module so all algorithms operate on consistent input.
    """
    if not text:
        return []
    return [w.lower() for w in _WORD_RE.findall(text)]


# ---------------------------------------------------------------------- #
# 1. Jaccard Similarity (Set-based)
# ---------------------------------------------------------------------- #
def jaccard_similarity(text_a: str, text_b: str) -> Tuple[float, Set[str], Set[str], Set[str]]:
    """
    Compute Jaccard similarity between two texts:

        J(A, B) = |A ∩ B| / |A ∪ B|

    where A and B are the SETS of unique words in each text.

    Returns:
        (similarity_ratio, common_words, unique_to_a, unique_to_b)
    """
    set_a: Set[str] = set(tokenize(text_a))
    set_b: Set[str] = set(tokenize(text_b))

    if not set_a and not set_b:
        return 0.0, set(), set(), set()

    intersection = set_a & set_b
    union = set_a | set_b

    similarity = len(intersection) / len(union) if union else 0.0
    unique_to_a = set_a - set_b
    unique_to_b = set_b - set_a

    return similarity, intersection, unique_to_a, unique_to_b


# ---------------------------------------------------------------------- #
# 2. Cosine Similarity (Vector-space, term-frequency based)
# ---------------------------------------------------------------------- #
def _term_frequency(words: List[str]) -> Dict[str, int]:
    """
    Build a term-frequency hash table (dict) from a list of words.
    Demonstrates Hash Table usage explicitly.
    """
    freq: Dict[str, int] = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    return freq


def cosine_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between the term-frequency vectors of two
    texts:

        cos(theta) = (A . B) / (||A|| * ||B||)

    Vectors are represented sparsely via hash tables (dict[word] -> count)
    rather than dense arrays, which is the standard approach for text data.
    """
    freq_a = _term_frequency(tokenize(text_a))
    freq_b = _term_frequency(tokenize(text_b))

    if not freq_a or not freq_b:
        return 0.0

    # Dot product over the shared vocabulary
    shared_vocab = set(freq_a.keys()) & set(freq_b.keys())
    dot_product = sum(freq_a[w] * freq_b[w] for w in shared_vocab)

    magnitude_a = math.sqrt(sum(count ** 2 for count in freq_a.values()))
    magnitude_b = math.sqrt(sum(count ** 2 for count in freq_b.values()))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


# ---------------------------------------------------------------------- #
# 3. Rabin-Karp String Matching (rolling hash substring search)
# ---------------------------------------------------------------------- #
def rabin_karp_search(text: str, pattern: str, base: int = 256, prime: int = 101) -> List[int]:
    """
    Find all starting indices where `pattern` occurs inside `text` using
    the Rabin-Karp algorithm (rolling hash).

    Time complexity: O(n + m) average case, O(n*m) worst case (hash
    collisions), where n = len(text), m = len(pattern).

    Returns:
        A list of 0-indexed starting positions of each match.
    """
    n, m = len(text), len(pattern)
    matches: List[int] = []
    if m == 0 or m > n:
        return matches

    # Precompute base^(m-1) % prime for use in rolling hash removal step
    high_order = pow(base, m - 1, prime)

    pattern_hash = 0
    text_hash = 0
    for i in range(m):
        pattern_hash = (base * pattern_hash + ord(pattern[i])) % prime
        text_hash = (base * text_hash + ord(text[i])) % prime

    for i in range(n - m + 1):
        if pattern_hash == text_hash:
            # Hash matched -> verify character by character to rule out
            # a hash collision (Rabin-Karp requires this verification step).
            if text[i:i + m] == pattern:
                matches.append(i)

        if i < n - m:
            text_hash = (base * (text_hash - ord(text[i]) * high_order) + ord(text[i + m])) % prime
            text_hash = (text_hash + prime) % prime  # normalize negative values

    return matches


def find_matching_phrases_rabin_karp(text_a: str, text_b: str, phrase_len: int = 5) -> List[str]:
    """
    Slide a window of `phrase_len` words over text_a, and use Rabin-Karp
    to check whether each resulting phrase appears verbatim in text_b.
    Used to highlight contiguous matching phrases (not just shared words)
    between two documents.
    """
    words_a = tokenize(text_a)
    text_b_lower = text_b.lower()

    found_phrases = []
    seen = set()
    for i in range(len(words_a) - phrase_len + 1):
        phrase = " ".join(words_a[i:i + phrase_len])
        if phrase in seen:
            continue
        matches = rabin_karp_search(text_b_lower, phrase)
        if matches:
            found_phrases.append(phrase)
            seen.add(phrase)

    return found_phrases


# ---------------------------------------------------------------------- #
# 4. KMP (Knuth-Morris-Pratt) String Matching
# ---------------------------------------------------------------------- #
def _build_kmp_prefix_table(pattern: str) -> List[int]:
    """
    Build the KMP "failure function" / longest-proper-prefix-suffix (LPS)
    table for the given pattern. lps[i] = length of the longest proper
    prefix of pattern[0..i] which is also a suffix of pattern[0..i].
    """
    m = len(pattern)
    lps = [0] * m
    length = 0  # length of the previous longest prefix suffix
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length != 0:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    return lps


def kmp_search(text: str, pattern: str) -> List[int]:
    """
    Find all starting indices where `pattern` occurs inside `text` using
    the Knuth-Morris-Pratt algorithm.

    Time complexity: O(n + m) worst case, where n = len(text),
    m = len(pattern). Unlike naive search, KMP never re-examines a
    character of `text` that has already been matched, by using the
    precomputed prefix (failure) table to skip ahead intelligently.

    Returns:
        A list of 0-indexed starting positions of each match.
    """
    n, m = len(text), len(pattern)
    matches: List[int] = []
    if m == 0 or m > n:
        return matches

    lps = _build_kmp_prefix_table(pattern)

    i = 0  # index into text
    j = 0  # index into pattern
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == m:
                matches.append(i - j)
                j = lps[j - 1]
        elif j != 0:
            j = lps[j - 1]
        else:
            i += 1

    return matches


# ---------------------------------------------------------------------- #
# Aggregate helper used directly by the UI layer
# ---------------------------------------------------------------------- #
def common_and_unique_words(text_a: str, text_b: str) -> Tuple[Set[str], Set[str], Set[str]]:
    """Convenience wrapper returning (common, unique_a, unique_b) word sets."""
    set_a, set_b = set(tokenize(text_a)), set(tokenize(text_b))
    return set_a & set_b, set_a - set_b, set_b - set_a

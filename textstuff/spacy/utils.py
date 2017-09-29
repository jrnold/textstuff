"""Utility functions and classes for working with SpaCy."""
import logging
import re

import spacy
from spacy.tokens import Doc, Span

LOGGER = logging.getLogger(__name__)

DEFAULT_ATTRS = [
    spacy.attrs.HEAD, spacy.attrs.DEP, spacy.attrs.TAG, spacy.attrs.ENT_TYPE,
    spacy.attrs.ENT_IOB
    ]
""" Attributes needed to reconstruct a SpaCy parse """

ENTITIES_TIME = ("DATE", "TIME")
"""Time entities recognized by Spacy."""

ENTITIES_NUMERIC = ("PERCENT", "MONEY", "QUANTITY", "ORDINAL", "CARDINAL")
"""Numeric entiies recognizd by Spacy."""

# Content words
CONTENT_POS = ("ADJ", "ADV", "NOUN", "PROPN", "VERB")
"""Content word part of speech tags."""

# Function words
FUNCTION_POS = ("ADP", "AUX", "CONJ", "DET", "INTJ", "PRON", "PART", "PRON",
                "SCONJ")
""".Function words part of speech tags."""

OPEN_CLASS_POS = ("ADJ", "ADV", "INTJ", "NOUN", "PROPN", "VERB")
"""Open-class Word POS Tags.

POS corresponding to open class words in the
 [Universal Part of Speech Tags](http://universaldependencies.org/u/pos/)
"""

CLOSED_CLASS_POS = ("ADP", "AUX", "CONJ", "DET", "NUM", "PART", "PRON",
                    "SCONJ")
""" Open Class Word POS Tags

POS corresponding to closed class words in the
 [Universal Part of Speech Tags](http://universaldependencies.org/u/pos/)
"""

# Others
OTHER_POS = ("PUNCT", "SYM", "X")
""" Non Open or Closed Class POS Tags

POS corresponding to closed class words in the
[Universal Part of Speech Tags](http://universaldependencies.org/u/pos/)
"""


def doc_copy(doc):
    """Create a copy of a Spacy document.

    Currently this serializes and deserializes the document to make a copy.
    I haven't figured out another way to do this.

    This is useful, because some methods, like Span are useful but change
    the document in place.

    Parameters
    ------------
    doc : :py:class:`~spacy.tokens.Doc`
        Spacy document

    Returns
    --------
    doc : :py:class:`~spacy.tokens.Doc`
        Copy of the Spacy document

    """
    # There has to be a better way of doing it, but I can't figure out how
    # copy.deepcopy doesn't work because Doc objects can't be pickled
    return Doc(doc.vocab).from_bytes(doc.to_bytes())


def find_spans(tok, spans):
    """Get any spans in which a token appears.

    Parameters
    ----------
    tok: :class:`spacy.tokens.Token`, :class:`spacy.token.Span`
        A SpaCy token or span. If ``tok`` is a span, then its root token is
        used.
    spans: iterable
        An iterable yielding :py:class:`~spacy.tokens.Span` objects

    Yields
    --------
    list of (int, :class:`spacy.tokens.Span`)
        A tuple with the span number and span object in which the
        token appears.

    """
    if isinstance(tok, Span):
        tok = tok.root
    for i, span in enumerate(spans):
        if tok in span:
            yield (i, span)


def find_first_span(tok, spans):
    """Return the first span in which a token appears.

    Parameters
    ----------
    tok: :class:`spacy.tokens.Token`, :class:`spacy.token.Span`
        A SpaCy token or span. If ``tok`` is a span, then its root token is
        used.
    spans: iterable
        An iterable yielding :py:class:`~spacy.tokens.Span` objects

    Yields
    --------
    (int, :class:`spacy.tokens.Span`)
        A tuple with the span number and span object for the first span in
        which the token appears.

    """
    if isinstance(tok, Span):
        tok = tok.root
    try:
        return next(find_spans(tok, spans))
    except StopIteration:
        return None


def find_ent(tok):
    """Find the named entity span in which a token appears.

    Parameters
    ----------
    tok: :class:`spacy.tokens.Token`, :class:`spacy.token.Span`
        A SpaCy token or span. If ``tok`` is a span, then its root token is
        used.

    Returns
    --------
    (int, :class:`spacy.tokens.Span`) or None
        A tuple with the span number and mamed entity span which the
        token appears. If the token is not in a named entity, then this
        function returns ``None``.

    """
    if isinstance(tok, Span):
        tok = tok.root
    if tok.ent_iob_ is None or tok.ent_iob_ == "O":
        return None
    else:
        return find_first_span(tok, tok.doc.ents)


def find_noun_chunk(tok):
    """Find the noun-chunk in which a token appears.

    Parameters
    ----------
    tok: :class:`spacy.tokens.Token`, :class:`spacy.token.Span`
        A SpaCy token or span. If ``tok`` is a span, then its root token is
        used.

    Returns
    --------
    (int, :class:`spacy.tokens.Span`) or None
        A tuple with the span number and moun chunk span which the
        token appears. If the token is not in a noun chunk, then this
        function returns ``None``.

    """
    if isinstance(tok, Span):
        tok = tok.root
    return find_first_span(tok, tok.noun_chunks)


def find_sent(tok):
    """Find the sentence in which the token appears.

    Parameters
    ----------
    tok: :class:`spacy.tokens.Token`, :class:`spacy.token.Span`
        A SpaCy token or span. If ``tok`` is a span, then its root token is
        used.

    Returns
    --------
    (int, :class:`spacy.tokens.Span`) or None
        A tuple with the sentence number and sentence span in which the
        token appears. If the token is not in a noun chunk, then this
        function returns ``None``.

    """
    if isinstance(tok, Span):
        tok = tok.root
    return find_first_span(tok, tok.sents)


def remove_leading(predicate, span):
    """Remove leading tokens from a span.

    Drop leading tokens from a span as long as the predicate is true.

    Parameters
    -----------
    predicate: callable
        A callable that returns ``True`` if the token is to be dropped.
    span: :py:class:`~spacy.tokens.Span`
        A SpaCy span.

    Returns
    --------
    :py:class:`~spacy.tokens.Span`
        A SpaCy span without the leading tokens that matched the predicate.

    """
    while predicate(span[0]):
        span = span[1:]
    if len(span) > 0:
        return span


def remove_trailing(predicate, span):
    """Remove trailing tokens from a span.

    Drop trailing tokens from a span as long as the predicate is true.

    Parameters
    -----------
    predicate: callable
        A callable that returns ``True`` if the token is to be dropped.
    span: :py:class:`~spacy.tokens.Span`
        A SpaCy span.

    Returns
    --------
    :py:class:`~spacy.tokens.Span`
        A SpaCy span without the leading tokens that matched the predicate.

    """
    while predicate(span[-1]):
        span = span[:-1]
    if len(span) > 0:
        return span


def spans_overlap(x, y):
    """Check if two spans overlap.

    Parameters
    ------------
    x, y: :class:`spacy.tokens.Span`
        Spacy spans

    Returns
    --------
    bool
        ``True`` if the spans overlap, ``False`` otherwise.

    """
    return not (x.end > y.start or x.start > y.end)


def filter_overlapping_spans(spans, keep_longest=True):
    """Remove overlapping Spans.

    Parameters
    -----------
    spans: ``iterable`` of :class:`spacy.token.Span`
        An iterable of spans.

    Yield
    -------
    :class:`spacy.token.Span`
        An iterable of spans. Only non-overlapping spans are
        returned, with earlier spans taking precedence,
        after sorting the spans in increasing order.

    """
    i = -1
    if keep_longest:
        # by end, then shortest
        sspans = sorted(spans, lambda x: (x.start, -x.end))
    else:
        # by start, then shortest
        sspans = sorted(spans, lambda x: (x.start, x.end))
    for span in sspans:
        if span.start > i:
            yield span
            i = span.end - 1


def merge_entities(doc):
    """Merge entities in-place.

    Parameters
    -----------
    doc: :py:class:`~spacy.tokens.Doc`
        Merge named entities into tokens, in place.

    """
    for ent in doc.ents:
        try:
            ent.merge(ent.root.tag_, ent.text, ent.root.ent_type_)
        except IndexError as e:
            LOGGER.exception("Unable to merge entity \"%s\"; skipping...",
                             ent.text)


def merge_noun_chunks(doc):
    """Merge noun chunks in-place.

    Parameters
    -----------
    doc: :py:class:`~spacy.tokens.Doc`
        Merge named entities into tokens, in place.

    """
    for np in doc.noun_chunks:
        try:
            np.merge(np.root.tag_, np.text, np.root.ent_type_)
        except IndexError as e:
            LOGGER.exception("Unable to merge noun chunk \"%s\"; skipping ...",
                             np.text)


def spans_subset(x, y):
    """Check whether span x is a subset of span y."""
    return (x.start >= y.start) and (x.end <= y.end)


def spans_superset(x, y):
    """Chec whether span x is a superset of span y."""
    return (x.start < y.start) and (x.end > y.end)


def span_before(x, y):
    """Is span x immediately before span y."""
    return (x.end == y.start)


def span_after(x, y):
    """Check whether span x is immediately after span y."""
    return (x.end == y.start)


def span_neighboring(x, y):
    """Check whether span x is an immediate neighbor of span y."""
    return span_before(x, y) or span_after(x, y)


def span_union(x, y):
    """Return a span with the union of span x and span y."""
    # if not neighboring?
    return Span(x.doc, min(x.start, y.start), max(x.end, y.end))


def span_intersect(x, y):
    """Return a span with intersection of span x and span y."""
    if spans_overlap(x, y):
        return Span(x.doc, max(x.start, y.start), min(x.end, y.end))


def span_diff(x, y):
    """Return a span with the difference of span x and span y."""
    if not spans_overlap(x, y):
        return x
    else:
        return Span(x.doc, max(x.start, y.start), min(x.end, y.end))


def tokens_to_span(tokens, contiguous=True):
    """Return a span incorporating all tokens."""
    # assumed but not checked that all tokens are from the same doc
    start = min((tok.i for tok in tokens))
    end = max((tok.i for tok in tokens)) + 1
    # check all tokens are contiguous
    if contiguous:
        # use set to ensure tha they are unique indices
        tokens = sorted(list(set(tokens)), lambda x: x.i)
        # by pigeon hole - only need to check the size to see that they're all
        # there
        if len(tokens) < (start - end + 1):
            return None
    return Span(tokens[0].doc, start, end)


def tokens_to_spans(tokens):
    """Yield spans of contiguous tokens from an iterable of tokens."""
    # The document is finite, so I can assume that the iterable is ...?
    # assumed but not checked that all tokens are from the same doc
    toks = sorted(list(set(tokens)), lambda x: x.i)
    last_i = None
    start = None
    end = None
    for tok in toks:
        if start is None:
            start = tok.i
            end = tok.i
        else:
            if tok.i - last_i == 1:
                end = tok.i
            else:
                yield Span(tok.doc, start, end + 1)
                start = tok.i
                end = tok.i
    return Span(tok.doc, start, end + 1)


# Check whether tokens start spans

def in_span(tok, spans):
    """Is token ``tok`` in a span in ``spans``."""
    return find_first_span(tok, spans) is not None


def in_ent(tok):
    """Is the token in an entity."""
    return tok.ent_iob_ and tok.ent_iob_ != "O"


def in_noun_chunk(tok, spans):
    """Is token ``tok`` in a span in ``spans``."""
    return find_first_span(tok, tok.doc.noun_chunks) is not None

# since sentences either partition the doc or don't exist, no need for fun


# Check whether tokens start spans

def is_span_start(tok, spans):
    """Does token start a span from an iterable in spans.

    If ``tok`` is in multiple spans in ``Span``.

    """
    span = find_first_span(tok, spans)
    if span is None:
        return False
    if isinstance(tok, Span):
        return tok.start == span.start
    else:
        return tok.i == tok.start


def is_ent_start(tok, spans):
    """Does token start a named entity."""
    if isinstance(tok, Span):
        return tok.doc[tok.start] == "B"
    else:
        return tok.ent_iob_ == "B"


def is_noun_chunk_start(tok, spans):
    """Does token start a noun chunk."""
    return is_span_start(tok, tok.doc.noun_chunks)


def is_sent_start(tok, spans):
    """Does token start a sentence."""
    return is_span_start(tok, tok.doc.sents)


def is_doc_start(tok):
    """Does token start a document."""
    if isinstance(tok, Span):
        return tok.start == 0
    else:
        return tok.i == 0


# Check whether tokens end spans

def is_span_end(tok, span):
    """Does token start a span from an iterable in spans.

    If ``tok`` is in multiple spans in ``Span``.

    """
    if isinstance(tok, Span):
        return tok.end == span.end
    if span:
        return tok.i == (span.end - 1)
    return False


def is_ent_end(tok):
    """Does token end a named entity."""
    if isinstance(tok, Span):
        tok = tok.doc[tok.end]
    if tok.ent_iob_ is None or tok.ent_iob_ == "O":
        return False
    else:
        try:
            return tok.nbor(1).ent_iob_ == "B"
        except IndexError:  # end of document
            return True


def is_noun_chunk_end(tok):
    """Does token start a noun chunk."""
    _, span = find_first_span(tok, tok.doc.noun_chunks)
    return is_span_end(tok, span)


def is_sent_end(tok):
    """Does token start a sentence."""
    _, span = find_first_span(tok, tok.doc.sents)
    return is_span_end(tok, span)


def is_doc_end(tok):
    """Does token start a document."""
    if isinstance(tok, Span):
        return tok.end == (len(tok.doc) - 1)
    else:
        return tok.i == (len(tok.doc) - 1)


# Whitespace stuff

def whitespace_after(tok):
    """Does whitespace follow a token."""
    if isinstance(tok, Span):
        tok = tok.end
    if len(tok.whitespace_) > 0:
        return True
    try:
        return tok.nbor(1).pos_ == "SPACE"
    except IndexError:  # end of doc
        return False


def whitespace_before(tok):
    """Does whitespace occur before a token."""
    if isinstance(tok, Span):
        tok = tok.start
    if tok.i == 0:  # start of doc
        return False
    prevtok = tok.nbor(-1)
    return bool(len(prevtok.whitespace_)) or prevtok.pos_ == "SPACE"


# Get word number within a span

def span_token_i(tok, span):
    """Token number within a span."""
    if span is None:
        return None
    if isinstance(tok, Span):
        return tok.start - span.start
    else:
        return tok.i - span.start


def ent_token_i(tok):
    """Token number within a named entity if in one."""
    _, span = find_ent(tok)
    return span_token_i(tok, span)


def noun_chunk_token_i(tok):
    """Token number within a span."""
    _, span = find_noun_chunk(tok)
    return span_token_i(tok, span)


def sent_token_i(tok):
    """Token number within a sentence."""
    _, span = find_sent(tok)
    return span_token_i(tok, span)

# New lines


_RE_NEWLINE = re.compile("\n", re.M)


def new_line(tok):
    """Is token a new line."""
    # actually returns number of new-lines in a token
    return sum(len(_RE_NEWLINE.findall(tok.orth_)))


def is_line_start(tok):
    """Is token at the start of a line."""
    if isinstance(tok, Span):
        tok = tok.doc[tok.start]
    if tok.i == 0:
        return True
    else:
        return bool(new_line(tok.nbor(-1)))


def is_line_end(tok):
    """Is token at the end of a line."""
    if isinstance(tok, Span):
        tok = tok.doc[tok.end]
    if tok.i == (len(tok.doc) - 1):
        return True
    else:
        return bool(new_line(tok.nbor(1)))


def line_spans(doc):
    """Yield spans for each line in a document."""
    line_num = 0
    start = None
    end = None
    new_line = True
    for tok in doc:
        if new_line:
            start = tok.i  # using this means doc can be a span
            new_line = False
        if new_line(tok):
            end = tok.i + 1
            yield Span(doc, start, end, label=f"Line {linenum}")
            line_num += 1
            new_line = True
    # return last line
    return Span(doc, start, end, label=f"Line {linenum}")


def find_line(tok):
    """Return line of a token."""
    return find_first_span(tok, line_spans(tok.doc))


# Paragraphs


_RE_PARA_TOKEN = re.compile("[\n]{2,}", re.M)


def is_new_para(tok):
    """Does the token start a paragraph."""
    return _RE_PARA_TOKEN.search(tok.orth_) is not None


def para_start(tok):
    """Is the token the start of a paragraph."""
    if isinstance(tok, Span):
        tok = tok.doc[tok.start]
    if tok.i == 0:
        return True
    else:
        return is_new_para(tok.nbor(-1))


def para_end(tok):
    """Is the token the end of a paragraph."""
    if isinstance(tok, Span):
        tok = tok.doc[tok.end]
    if tok.i == (len(tok.doc) - 1):
        return True
    else:
        return is_new_para(tok.nbor(1))


def para_spans(doc):
    """Yield spans for each line in a document."""
    para_num = 0
    start = None
    end = None
    new_para = True
    for tok in doc:
        if new_para:
            start = tok.i  # using this means doc can be a span
            new_para = False
        if is_new_para(tok):
            end = tok.i + 1
            yield Span(doc, start, end, label=f"Para {para_num}")
            para_num += 0
            new_para = True
    # return last line
    return Span(doc, start, end, label=f"Para {para_num}")


def find_para(tok):
    """Return paragraph of a token."""
    return find_first_span(tok, para_spans(tok.doc))

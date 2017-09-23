"""Convert SpaCy documents to formats."""
import re
import pickle

import spacy.attrs
from spacy.tokens import Doc


_DEFAULT_ATTRS = [
    spacy.attrs.HEAD, spacy.attrs.DEP, spacy.attrs.TAG, spacy.attrs.ENT_TYPE,
    spacy.attrs.ENT_IOB
]
""" Attributes needed to reconstruct a SpaCy parse """


def doc_to_tuple(doc, attrs=None):
    """Convert a SpaCy Document to a tuple.

    The SpaCy document can be reconstructed from this information. It's also
    safer than the serialization method for SpaCy < 2.0.0, which has issues
    with unknown characters.
    See this `issue <https://github.com/explosion/spaCy/issues/927>`__ for
    more information.

    The primary purpose of this function is to serialize SpaCy parsed docsuments.
    SpaCy 2.0.0 introduces a new serialization method, at which point this will
    be obsolete.

    """  # noqa
    attrs = attrs or _DEFAULT_ATTRS
    tokens = list(tok.text for tok in doc)
    whitespace = list(len(tok.whitespace_) > 0 for tok in doc)
    return (tokens, whitespace, attrs, doc.to_array(attrs))


def doc_from_tuple(vocab, x):
    """Return SpaCy document from vocab and a tuple."""
    tokens, whitespace, attrs, array = x
    return Doc(vocab, tokens, whitespace).from_array(attrs, array)


def dump_doc(doc, file):
    """Pickle and dump a ``doc`` to ``file``."""
    return pickle.dump(doc_to_tuple(doc), file)


def dumps_doc(doc):
    """Pickle an SpaCy document and return the byte string."""
    return pickle.dumps(doc_to_tuple(doc))


def load_doc(vocab, file):
    """Load a picked from a file-like object.

    Parameters
    -----------
    vocab: :py:class:`spacy.vocab.Vocab`
        The vocab used to create the pickled object
    file: file
        An open file object

    Returns
    --------
    :py:class:`spacy.tokens.Doc`
        A SpaCy document

    """  # noqa
    return doc_from_tuple(vocab, *pickle.load(file))


def loads_doc(vocab, bytes_object):
    """Load a document from vocab and a pickled string."""
    return doc_from_tuple(vocab, *pickle.loads(bytes_object))


def _rep_val(x):
    """Represent a value for CONLL formats."""
    return "_" if x is None else str(x)


def token_whitespace(doc):
    """Yield (token, whitespace) tuples.

    This ignores whitespace tokens, and adjusts the whitespace value
    accordingly.

    """
    # this ignores whitespace tokens
    space_pos = {
        "SPACE",
    }
    for tok in doc:
        if tok.pos_ not in space_pos:
            if len(tok.whitespace_):
                ws = True
            else:
                try:
                    ws = doc[tok.i + 1].pos_ in space_pos
                except IndexError:
                    # space assumed at end of doc
                    ws = True
            yield (tok, ws)


def to_conllu(doc,
              fs,
              sent_headers=True,
              doc_text=True,
              sent_ids=None,
              doc_id=None):
    """Dump Document to CONLL-U format."""
    # fields = ("ID", "FORM", "LEMMA", "UPOSTAG", "XPOSTAG", "FEATS", "HEAD",
    #           "DEPREL", "DEPS", "MISC")
    if doc_text:
        text = re.sub(r"\s+", " ", doc.text)
        fs.write(f"# text = {text}\n\n")
    for i, sent in enumerate(doc.sents):
        if i > 0:
            fs.write("\n")
        if sent_headers:
            fs.write(f"# sent_id = {i + 1}\n")
            fs.write(f"# text = {sent.text}\n")
        tokens = token_whitespace(sent)
        for j, (tok, ws) in enumerate(tokens):
            head = str(tok.head.i + 1)
            feats = None
            if ws:
                misc = None
            else:
                misc = "SpacesAfter=No"
            row = (j + 1, tok.orth_, tok.lemma_, tok.pos_, tok.tag_, feats,
                   head, tok.dep_, misc)
            fs.write('\t'.join(_rep_val(c) for c in row) + "\n")


def to_conllx(doc, fs, sent_headers=True, doc_text=True, projective=True):
    """Dump Document to CONLL-X 2006 format."""
    for i, sent in enumerate(doc.sents):
        if i > 0:
            fs.write("\n")
        for j, tok in enumerate(sent):
            if tok.dep_ == "ROOT":
                head = "0"
            else:
                head = str(tok.head.i + 1)
            deprel = tok.dep_
            #  is
            if projective:
                phead = head
                pdeprel = deprel
            else:
                phead = None
                pdeprel = None
            # tokens are 1-indexed
            row = (j + 1, tok.orth_, tok.lemma_, tok.pos_, tok.tag_, None,
                   head, deprel, phead, pdeprel)
            fs.write('\t'.join(_rep_val(x) for x in row) + "\n")


def _prev_tok(tok, k=1):
    try:
        return tok.doc[tok.i - k]
    except IndexError:
        return None


def to_bracket_ner(doc, fs):
    """Dump document to bracket tagged NER format.

    This is the output format of the
    `Illinois tagger <https://github.com/danyaljj/illinois-cogcomp-nlp-1/tree/master/ner>`__.

    """  # noqa
    for tok in doc:
        if tok.ent_iob_ == "B":
            fs.write(f"[{tok.ent_type_} ")
        elif tok.i > 0 and tok.ent_iob_ == "O":
            if _prev_tok(tok).ent_iob_ != "O":
                fs.write(" ] ")
        fs.write(tok.text_with_ws)

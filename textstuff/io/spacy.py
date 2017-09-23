"""Convert SpaCy documents to formats."""
import hashlib
import re
import sqlite3
from collections import OrderedDict

import pandas as pd


def _doc_hash(doc):
    h = hashlib.sha1()
    h.update(doc.text.encode("utf-8"))
    return h.hexdigest()


def doc_dict(doc, doc_id=None):
    """Return an ordered dictionary from a SpaCy document."""
    doc_id = doc_id or _doc_hash(doc)
    """Return Spacy Document information as an ordered dictionary."""
    return OrderedDict(
        (('doc_id', doc_id), ('tokens', len(doc)), ('sentences',
                                                    len(list(doc.sents))),
         ('noun_chunks', len(list(doc.noun_chunks))), ('ents',
                                                       len(list(doc.ents)))))


def doc_dataframe(doc, doc_id=None):
    """Convert a SpaCy document to Pandas data frame."""
    return pd.DataFrame.from_dict([doc_dict(doc)])


def tokens_dict(doc, doc_id=None):
    """Yield an ordered dict for each token."""
    doc_id = doc_id or _doc_hash(doc)
    for sid, sent in enumerate(doc.sents):
        for tok in sent:
            yield OrderedDict(
                (('doc_id', doc_id), ('sent', sid), ('i', tok.i),
                 ('orth', tok.orth_), ('lemma', tok.lemma_), ('ent_iob',
                                                              tok.ent_iob_),
                 ('ent_type', tok.ent_type_), ('ent_id', tok.ent_id),
                 ('shape', tok.shape_), ('pos', tok.pos_), ('tag', tok.tag_),
                 ('head', tok.head.i), ('dep', tok.dep_), ('lang', tok.lang_),
                 ('idx', tok.idx), ('whitespace',
                                    tok.whitespace_), ('is_alpha',
                                                       tok.is_alpha),
                 ('is_ascii', tok.is_ascii), ('is_digit',
                                              tok.is_digit), ('is_title',
                                                              tok.is_title),
                 ('is_punct', tok.is_punct), ('is_space',
                                              tok.is_space), ('like_num',
                                                              tok.like_num),
                 ('like_email', tok.like_email), ('is_oov',
                                                  tok.is_oov), ('is_stop',
                                                                tok.is_stop)))


def tokens_dataframe(doc, doc_id=None):
    return pd.DataFrame.from_records(list(tokens_dict(doc, doc_id=doc_id)))


def ents_records(doc, doc_id=None):
    doc_id = doc_id or _doc_hash(doc)
    for i, ent in enumerate(doc.ents):
        yield OrderedDict(
            (('doc_id', doc_id), ('ent_id', i), ('start',
                                                 ent.start), ('end', ent.end),
             ('root', ent.root.i), ('label', ent.label_), ('text', ent.text),
             ('lemma', ent.lemma_), ('pos', ent.root.pos_), ('tag',
                                                             ent.root.tag_)))


def ents_dataframe(doc, doc_id=None):
    """Return document entities as a DataFrame."""
    return pd.DataFrame.from_records(ents_records(doc))


def noun_chunks_records(doc, doc_id=None):
    doc_id = doc_id or _doc_hash(doc)
    for i, chunk in enumerate(doc.noun_chunks):
        yield OrderedDict(
            (('doc_id', doc_id), ('chunk_id', i), ('start', chunk.start),
             ('end', chunk.end), ('root', chunk.root.i),
             ('label', chunk.label_), ('text', chunk.text), ('lemma',
                                                             chunk.lemma_),
             ('pos', chunk.root.pos_), ('tag', chunk.root.tag_)))


def noun_chunks_dataframe(doc, doc_id=None):
    """Return document noun chunks as a Pandas data frame."""
    return pd.DataFrame.from_records(noun_chunks_records(doc))


class ParsedCorpusDB:
    """Store a corpus of Spacy parsed documents to a database.

    This stores the parsed documents in a database with the
    following tables
    - ``documents``: One row per document
    - ``token``: One row per token per document
    - ``ents``: Entities
    - ``noun_chunks``: Noun chunks
    Parameters
    -----------
    db : str
        Database engine string
    """

    _TABLE_DDL = """
    CREATE TABLE documents (
        doc_id TEXT,
        tokens INT CHECK (tokens >= 0),
        sentences INT (sentences >= 0),
        noun_chunks INT (noun_chunks >= 0),
        ents INT CHECK (ents >= 0),
        PRIMARY KEY (doc_id)
    );
    CREATE TABLE tokens (
        doc_id TEXT NOT NULL,
        sent INT NOT NULL CHECK (sent >= 0),
        i INT NOT NULL CHECK (i >= 0),
        orth TEXT NOT NULL,
        lemma TEXT,
        ent_iob TEXT,
        ent_type TEXT,
        ent_id BIGINT,
        shape TEXT,
        pos TEXT,
        tag TEXT,
        head BIGINT,
        dep TEXT,
        lang TEXT,
        idx INT NOT NULL,
        whitespace TEXT NOT NULL,
        is_alpha BOOLEAN NOT NULL,
        is_ascii BOOLEAN NOT NULL,
        is_digit BOOLEAN NOT NULL,
        is_title BOOLEAN NOT NULL,
        is_punct BOOLEAN NOT NULL,
        is_space BOOLEAN NOT NULL,
        like_num BOOLEAN NOT NULL,
        like_email BOOLEAN NOT NULL,
        is_oov BOOLEAN NOT NULL,
        is_stop BOOLEAN NOT NULL,
        CHECK (is_alpha IN (0, 1)),
        CHECK (is_ascii IN (0, 1)),
        CHECK (is_digit IN (0, 1)),
        CHECK (is_title IN (0, 1)),
        CHECK (is_punct IN (0, 1)),
        CHECK (is_space IN (0, 1)),
        CHECK (like_num IN (0, 1)),
        CHECK (like_email IN (0, 1)),
        CHECK (is_oov IN (0, 1)),
        CHECK (is_stop IN (0, 1)),
        PRIMARY KEY (doc_id, i),
        FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
    );
    CREATE TABLE ents (
        doc_id TEXT NOT NULL,
        ent_num INT CHECK (ent_Num >= 0),
        start_i INT NOT NULL CHECK (start_i >= 0),
        end_i INT NOT NULL CHECK (end_i >= 0),
        root INT NOT NULL CHECK (root >= 0),
        label TEXT,
        text TEXT,
        lemma TEXT,
        pos TEXT,
        tag TEXT,
        PRIMARY KEY (doc_id, ent_num),
        FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
    );
    CREATE TABLE noun_chunks (
        doc_id TEXT,
        chunk_num INT,
        start_i INT NOT NULL CHECK (start_i >= 0),
        end_i INT NOT NULL CHECK (end_i >= 0),
        root INT NOT NULL CHECK (root >= 0),
        label TEXT,
        text TEXT,
        lemma TEXT,
        pos TEXT,
        tag TEXT,
        PRIMARY KEY (doc_id, chunk_id),
        FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
    );
    """
    _TABLES = {
        'documents': doc_dataframe,
        'tokens': tokens_dataframe,
        'ents': ents_dataframe,
        'noun_chunks': noun_chunks_dataframe
    }

    def __init__(self, db):
        """Initialize the object."""
        self.db = db
        # internal counter for number of docs
        self._i = 0
        # initialze tables if a SQLite3 connection
        if isinstance(db, sqlite3.Connection):
            self.db.executescript(self._TABLE_DDL)

    @staticmethod
    def _digest(doc):
        """Create unique ID for a document."""
        m = hashlib.sha1()
        m.update(doc.text.encode("utf-8"))
        return m.digest()

    def _add_rows(self, id_, doc, table, f, *args, **kwargs):
        """Add multiple rows into a table."""
        df = f(doc, doc_id=id_, *args, **kwargs)
        if df is not None:
            df.to_sql(table, self.db, index=False, if_exists="append")

    def add_doc(self, doc, id_=None, *args, **kwargs):
        """Add a document to the database.

        Parameters
        -----------
        doc: :class:`spacy.Doc`
            A Spacy document
        id_: str
            An identifier for the document

        """
        id_ = id_ or self._digest(doc)
        for tbl, f in self._TABLES.items():
            self._add_rows(id_, doc, tbl, f, *args, **kwargs)

    def add_docs(self, docs, *args, **kwargs):
        """Add multiple documents to the corpus.

        Parameters
        -----------
        docs: iterator of (str, :class:`spacy.Doc`) tuples
            An iterator providing tuples with document identifiers
            the Spacy parsed documents.

        """
        for id_, d in docs:
            self.add_doc(id_, d, *args, **kwargs)


def to_conll2003(doc, fs, fine_grained=True, ent_types=None, doc_start=False):
    """Dump document to CONLL 2003 format."""
    # There are no phrase chunks in SpaCy
    if doc_start:
        fs.write("\t".join(("-DOCSTART-", "-X-", "_", "O")) + "\n\n")
    for i, sent in enumerate(doc.sents):
        if i > 0:
            fs.write("\n")
        for tok in sent:
            pos = tok.tag_ if fine_grained else tok.pos_
            if tok.ent_iob_ != "O":
                if not ent_types or tok.ent_type_ in ent_types:
                    if (tok.i > 0 and tok.ent_iob_ == "B"
                            and tok.doc[tok.i - 1].ent_type == tok.ent_type):
                        iob = "B"
                    else:
                        iob = "I"
                    iob = f"{iob}-{tok.ent_type_}"
                else:
                    iob = "O"
            else:
                iob = "O"
            row = (tok.orth_, pos, "_", iob)
            fs.write('\t'.join(row) + "\n")


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


def _rep_val(x):
    """Represent a value for CONLL formats."""
    return "_" if x is None else str(x)


# http://universaldependencies.org/format.html
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


def _next_tok(tok, i=1):
    try:
        return tok.doc[tok.i + i]
    except IndexError:
        return None


def _prev_tok(tok, i=1):
    try:
        return tok.doc[tok.i - i]
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

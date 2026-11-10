from itertools import islice
import unicodedata

from backend.retrieval import chunks


def test_tamil_spacing_vowel_sign_does_not_start_a_chunk():
    text='கா'*25
    pieces=list(chunks(text,11,2))
    assert pieces and pieces[-1].endswith('கா')
    assert all(not unicodedata.category(piece[0]).startswith('M') for piece in pieces)
    assert all(piece in text for piece in pieces)


def test_oversized_combining_sequence_makes_progress_without_losing_text():
    cluster='a'+'\u0301'*12
    pieces=list(islice(chunks(cluster+'bcdef',3,1),10))
    assert pieces==[cluster,'bcd','def']

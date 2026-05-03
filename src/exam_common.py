"""Shared helpers for JLPT and Genki mock exams.

Builds 4-choice MCQs from vocabulary/grammar rows. Each question carries the
signature (item_type, item_id, subtype) so callers can dedup across sessions.
"""

import random


def has_kanji(s):
    return any("一" <= ch <= "鿿" for ch in (s or ""))


def vocab_question(item, subtype, dpool, mf):
    """Build one vocab MCQ. Returns (prompt, options[4], correct_idx) or None."""
    word, reading = item["word"], item["reading"]
    meaning = item[mf]

    if subtype == "kanji_to_reading":
        if not has_kanji(word):
            return None
        prompt = word
        correct = reading
        cand = [d["reading"] for d in dpool if d["reading"] != correct]

    elif subtype == "reading_to_kanji":
        if not has_kanji(word):
            return None
        prompt = reading
        correct = word
        cand = [d["word"] for d in dpool
                if has_kanji(d["word"]) and d["word"] != correct]

    elif subtype == "meaning_to_word":
        if not meaning:
            return None
        prompt = meaning
        correct = f"{word} ({reading})" if has_kanji(word) else word
        cand = []
        for d in dpool:
            label = f"{d['word']} ({d['reading']})" if has_kanji(d["word"]) else d["word"]
            if label != correct:
                cand.append(label)

    elif subtype == "word_to_meaning":
        if not meaning:
            return None
        prompt = f"{word}  ({reading})" if has_kanji(word) else word
        correct = meaning
        cand = [d[mf] for d in dpool if d[mf] and d[mf] != correct]

    else:
        return None

    if len(cand) < 3:
        return None
    distractors = random.sample(cand, 3)
    options = [correct] + distractors
    random.shuffle(options)
    return prompt, options, options.index(correct)


def grammar_question(item, subtype, dpool, mf):
    pattern = item["pattern"]
    meaning = item[mf]

    if subtype == "pattern_to_meaning":
        if not meaning:
            return None
        prompt = pattern
        example = item.get("example_jp")
        if example:
            prompt = f"{pattern}\n  [dim]ör: {example}[/dim]"
        correct = meaning
        cand = [d[mf] for d in dpool if d[mf] and d[mf] != correct]
        if len(cand) < 3:
            return None
        distractors = random.sample(cand, 3)
        options = [correct] + distractors
        random.shuffle(options)
        return prompt, options, options.index(correct)

    return None


def build_question(section, item, subtype, dpool, mf):
    """Dispatch builder. section: 'vocabulary' | 'grammar'."""
    if section == "vocabulary":
        return vocab_question(item, subtype, dpool, mf)
    if section == "grammar":
        return grammar_question(item, subtype, dpool, mf)
    return None

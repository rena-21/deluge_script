"""
Core SEO analysis engine — FR / EN / AR, zero external API calls.
"""
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

# ── Stop words ────────────────────────────────────────────────────────────────

STOP_WORDS: dict[str, set[str]] = {
    "en": {
        "a","about","above","after","again","against","all","also","am","an","and",
        "any","are","as","at","be","because","been","before","being","below","between",
        "both","but","by","can","did","do","does","doing","don","down","during","each",
        "few","for","from","get","got","had","has","have","he","her","here","him","his",
        "how","i","if","in","into","is","it","its","just","me","more","most","my","no",
        "nor","not","now","of","off","on","once","only","or","other","our","out","over",
        "own","same","she","should","so","some","such","than","that","the","their",
        "them","then","there","these","they","this","those","through","to","too","under",
        "until","up","us","very","was","we","were","what","when","where","which","while",
        "who","will","with","would","you","your","s","t","re","ve","ll","d","m",
    },
    "fr": {
        "a","au","aux","avec","ce","ces","cet","cette","dans","de","des","du","elle",
        "elles","en","et","eu","eux","il","ils","je","la","le","les","leur","leurs","lui",
        "ma","mais","me","même","mes","mon","ni","nos","notre","nous","on","ou","où","par",
        "pas","pour","qu","que","qui","sa","se","ses","si","son","sur","ta","te","tes",
        "ton","tu","un","une","vos","votre","vous","y","à","été","être","c","d","j","l",
        "m","n","s","y","plus","tout","bien","aussi","comme","très","car","donc","dont",
        "encore","puis","après","avant","quand","quel","quelle","quels","quelles",
    },
    "ar": {
        "في","من","إلى","على","هذا","هذه","التي","الذي","ما","كان","كانت","هو","هي",
        "نحن","أنا","أنت","أنتم","هم","هن","كل","بعض","عند","مع","لكن","أو","إن",
        "أن","لا","لم","لن","قد","قال","قالت","ذلك","تلك","هناك","هنا","حتى","بين",
        "عن","بعد","قبل","خلال","منذ","حول","فوق","تحت","عبر","ضد","بدون","غير",
        "ثم","بل","إذا","لو","مما","ومن","وفي","وهو","وهي","وإن","فإن","فهو","فهي",
        "الذين","اللذين","اللتين","اللواتي","الذي","التي",
    },
}


# ── Language detection ─────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    arabic = len(re.findall(r"[؀-ۿ]", text))
    total = len(text.replace(" ", ""))
    if arabic / max(total, 1) > 0.3:
        return "ar"
    french_markers = len(re.findall(
        r"\b(le|la|les|de|du|des|un|une|et|est|pour|dans|sur|avec|par|au|aux|ce|qui|que|à)\b",
        text, re.I
    ))
    english_markers = len(re.findall(
        r"\b(the|a|an|is|are|was|were|for|with|this|that|have|has|from|they|you)\b",
        text, re.I
    ))
    return "fr" if french_markers >= english_markers else "en"


# ── Text utilities ─────────────────────────────────────────────────────────────

def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?؟।]+", text) if len(s.strip()) > 5]


def _words(text: str, lang: str) -> list[str]:
    raw = re.findall(r"[\w؀-ۿ]{2,}", text.lower())
    stops = STOP_WORDS.get(lang, set())
    return [w for w in raw if w not in stops]


def _count_syllables_en(word: str) -> int:
    word = word.lower()
    count = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e"):
        count = max(1, count - 1)
    return max(1, count)


def _count_syllables_fr(word: str) -> int:
    return max(1, len(re.findall(r"[aeiouyàâéèêëîïôùûüœæ]+", word.lower())))


def _avg_syllables(words_raw: list[str], lang: str) -> float:
    if not words_raw:
        return 1.0
    if lang == "ar":
        return sum(max(1, len(w) // 3) for w in words_raw) / len(words_raw)
    fn = _count_syllables_fr if lang == "fr" else _count_syllables_en
    return sum(fn(w) for w in words_raw) / len(words_raw)


# ── Readability ────────────────────────────────────────────────────────────────

def readability_score(text: str, lang: str) -> dict:
    sentences = _sentences(text)
    all_words = re.findall(r"[\w؀-ۿ]{2,}", text)
    if not sentences or not all_words:
        return {"score": 0, "grade": "N/A", "interpretation": "Not enough text"}

    asl = len(all_words) / len(sentences)          # avg sentence length
    asw = _avg_syllables(all_words, lang)           # avg syllables per word

    if lang == "fr":
        score = 207 - (1.015 * asl) - (73.6 * asw)
    elif lang == "en":
        score = 206.835 - (1.015 * asl) - (84.6 * asw)
    else:  # ar — simplified
        avg_word_len = sum(len(w) for w in all_words) / len(all_words)
        score = 200 - (2 * asl) - (10 * avg_word_len)

    score = round(max(0, min(100, score)), 1)

    if score >= 70:
        grade, interpretation = "Easy", "Very easy to read, suitable for all audiences"
    elif score >= 50:
        grade, interpretation = "Medium", "Fairly easy to read, suitable for most adults"
    elif score >= 30:
        grade, interpretation = "Hard", "Difficult — consider simplifying sentences"
    else:
        grade, interpretation = "Very Hard", "Very complex — academic or technical level"

    return {
        "score": score,
        "grade": grade,
        "interpretation": interpretation,
        "avg_sentence_length": round(asl, 1),
        "avg_syllables_per_word": round(asw, 2),
    }


# ── Keyword extraction ─────────────────────────────────────────────────────────

def extract_keywords(text: str, lang: str, top_n: int = 10) -> list[dict]:
    words = _words(text, lang)
    total = len(words)
    if not total:
        return []
    counts = Counter(words)
    return [
        {
            "keyword": word,
            "count": count,
            "density": round(count / total * 100, 2),
        }
        for word, count in counts.most_common(top_n)
    ]


# ── Content structure ──────────────────────────────────────────────────────────

def analyze_structure(text: str) -> dict:
    lines = text.splitlines()
    h1 = sum(1 for l in lines if l.strip().startswith("# ") and not l.strip().startswith("## "))
    h2 = sum(1 for l in lines if l.strip().startswith("## ") and not l.strip().startswith("### "))
    h3 = sum(1 for l in lines if l.strip().startswith("### "))
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if len(p.strip()) > 20]
    sentences = _sentences(text)
    all_words = re.findall(r"[\w؀-ۿ]{2,}", text)
    return {
        "word_count": len(all_words),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "h1_count": h1,
        "h2_count": h2,
        "h3_count": h3,
        "avg_paragraph_length": round(
            sum(len(re.findall(r"[\w؀-ۿ]+", p)) for p in paragraphs) / max(len(paragraphs), 1), 1
        ),
    }


# ── SEO scoring ────────────────────────────────────────────────────────────────

def _score_word_count(wc: int) -> tuple[int, str]:
    if wc >= 1500:
        return 20, "Excellent length (1500+ words)"
    if wc >= 800:
        return 15, "Good length (800+ words)"
    if wc >= 400:
        return 10, "Acceptable length — aim for 800+ words"
    return 5, "Too short — aim for at least 400 words"


def _score_structure(struct: dict) -> tuple[int, str]:
    score = 0
    tips = []
    if struct["h2_count"] >= 2:
        score += 10
    else:
        tips.append("Add at least 2 H2 headings (##) for better structure")
    if struct["h3_count"] >= 1:
        score += 5
    if struct["paragraph_count"] >= 3:
        score += 5
    else:
        tips.append("Split content into more paragraphs")
    return score, "; ".join(tips) or "Good heading structure"


def _score_readability(r_score: float) -> tuple[int, str]:
    if r_score >= 60:
        return 20, "Great readability"
    if r_score >= 40:
        return 12, "Acceptable readability — simplify some sentences"
    return 5, "Hard to read — use shorter sentences and simpler words"


def _score_keyword_density(keywords: list[dict]) -> tuple[int, str]:
    if not keywords:
        return 0, "No keywords detected"
    top = keywords[0]["density"]
    if 1.0 <= top <= 3.0:
        return 15, f'Good keyword density: "{keywords[0]["keyword"]}" at {top}%'
    if top < 1.0:
        return 8, f'Top keyword "{keywords[0]["keyword"]}" used too rarely ({top}%) — increase to 1-3%'
    return 8, f'Top keyword "{keywords[0]["keyword"]}" overused ({top}%) — keyword stuffing risk'


def compute_seo_score(
    text: str, lang: str, title: Optional[str] = None, meta_description: Optional[str] = None
) -> dict:
    struct = analyze_structure(text)
    readability = readability_score(text, lang)
    keywords = extract_keywords(text, lang, top_n=10)

    wc_points, wc_tip = _score_word_count(struct["word_count"])
    struct_points, struct_tip = _score_structure(struct)
    read_points, read_tip = _score_readability(readability["score"])
    kw_points, kw_tip = _score_keyword_density(keywords)

    # Title bonus
    title_points, title_tip = 0, "No title provided"
    if title:
        title_len = len(title)
        if 40 <= title_len <= 65:
            title_points, title_tip = 15, f"Perfect title length ({title_len} chars)"
        elif title_len < 40:
            title_points, title_tip = 8, f"Title too short ({title_len} chars) — aim for 40-65"
        else:
            title_points, title_tip = 8, f"Title too long ({title_len} chars) — aim for 40-65"

    # Meta bonus
    meta_points, meta_tip = 0, "No meta description provided"
    if meta_description:
        meta_len = len(meta_description)
        if 120 <= meta_len <= 160:
            meta_points, meta_tip = 15, f"Perfect meta description ({meta_len} chars)"
        else:
            meta_points, meta_tip = 7, f"Meta description length {meta_len} chars — aim for 120-160"

    total = wc_points + struct_points + read_points + kw_points + title_points + meta_points
    max_score = 20 + 20 + 20 + 15 + (15 if title else 0) + (15 if meta_description else 0)
    normalized = round(total / max_score * 100) if max_score else 0

    if normalized >= 80:
        grade = "A"
    elif normalized >= 65:
        grade = "B"
    elif normalized >= 50:
        grade = "C"
    elif normalized >= 35:
        grade = "D"
    else:
        grade = "F"

    suggestions = [t for t in [wc_tip, struct_tip, read_tip, kw_tip, title_tip, meta_tip] if t]

    return {
        "score": normalized,
        "grade": grade,
        "breakdown": {
            "word_count": wc_points,
            "structure": struct_points,
            "readability": read_points,
            "keyword_density": kw_points,
            "title": title_points,
            "meta_description": meta_points,
        },
        "suggestions": suggestions,
    }


# ── Main entry point ───────────────────────────────────────────────────────────

@dataclass
class AnalysisResult:
    language: str
    structure: dict
    readability: dict
    keywords: list[dict]
    seo: dict
    title: Optional[str] = None
    meta_description: Optional[str] = None


def full_analysis(
    text: str,
    lang: Optional[str] = None,
    title: Optional[str] = None,
    meta_description: Optional[str] = None,
    keyword_count: int = 10,
) -> AnalysisResult:
    detected_lang = lang or detect_language(text)
    return AnalysisResult(
        language=detected_lang,
        structure=analyze_structure(text),
        readability=readability_score(text, detected_lang),
        keywords=extract_keywords(text, detected_lang, top_n=keyword_count),
        seo=compute_seo_score(text, detected_lang, title, meta_description),
        title=title,
        meta_description=meta_description,
    )

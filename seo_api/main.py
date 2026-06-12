"""
Multi-language SEO Analyzer API — FR / EN / AR
Deploy on Render (free), list on RapidAPI, earn money 24/7.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from dataclasses import asdict

from analyzer import full_analysis, detect_language, extract_keywords, readability_score

app = FastAPI(
    title="Multi-Language SEO Analyzer",
    description="Analyze SEO quality of text in French, English, and Arabic. "
                "Returns keyword density, readability score, content structure, "
                "SEO score A-F, and actionable improvement tips.",
    version="1.0.0",
    docs_url="/docs",
)


# ── Request / Response models ──────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=20, description="Text content to analyze (min 20 chars)")
    lang: Optional[str] = Field(None, description="Language: 'en', 'fr', 'ar'. Auto-detected if omitted.")
    title: Optional[str] = Field(None, description="Page/article title for title tag analysis")
    meta_description: Optional[str] = Field(None, description="Meta description for length analysis")
    keyword_count: int = Field(10, ge=1, le=30, description="Number of top keywords to return (1-30)")


class KeywordsRequest(BaseModel):
    text: str = Field(..., min_length=20)
    lang: Optional[str] = None
    top_n: int = Field(10, ge=1, le=50)


class ReadabilityRequest(BaseModel):
    text: str = Field(..., min_length=20)
    lang: Optional[str] = None


class DetectRequest(BaseModel):
    text: str = Field(..., min_length=10)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check — required by RapidAPI."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    **Full SEO analysis** in one call.

    Returns:
    - Detected / specified language
    - Content structure (word count, headings, paragraphs)
    - Readability score (0-100 + grade)
    - Top N keywords with density %
    - SEO score (0-100, grade A-F) with breakdown + suggestions
    """
    try:
        result = full_analysis(
            text=req.text,
            lang=req.lang,
            title=req.title,
            meta_description=req.meta_description,
            keyword_count=req.keyword_count,
        )
        return asdict(result)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/keywords")
def keywords(req: KeywordsRequest):
    """
    **Extract top keywords** from text with density percentages.

    Filters stop words in EN/FR/AR automatically.
    Returns keywords sorted by frequency.
    """
    try:
        lang = req.lang or detect_language(req.text)
        kws = extract_keywords(req.text, lang, top_n=req.top_n)
        return {"language": lang, "keywords": kws, "total_keywords_found": len(kws)}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/readability")
def readability(req: ReadabilityRequest):
    """
    **Readability score** using Flesch-Kincaid (EN/FR) or adapted formula (AR).

    Score 0-100: 70+ = Easy, 50-70 = Medium, 30-50 = Hard, <30 = Very Hard.
    """
    try:
        lang = req.lang or detect_language(req.text)
        result = readability_score(req.text, lang)
        result["language"] = lang
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/detect-language")
def detect_lang(req: DetectRequest):
    """
    **Detect language** of text. Returns 'en', 'fr', or 'ar'.
    """
    lang = detect_language(req.text)
    names = {"en": "English", "fr": "French", "ar": "Arabic"}
    return {"language": lang, "language_name": names[lang]}

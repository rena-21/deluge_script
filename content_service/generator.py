"""
Content generation via Claude (Anthropic API).
"""
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPTS = {
    "fr": "Tu es un rédacteur web professionnel expert en SEO et copywriting. Tu écris du contenu de haute qualité, clair, engageant et structuré. Tu utilises des titres H2/H3, des listes à puces quand c'est pertinent.",
    "en": "You are a professional web writer and SEO expert. You write high-quality, clear, engaging, well-structured content with H2/H3 headings and bullet points where relevant.",
    "ar": "أنت كاتب محترف متخصص في تحسين محركات البحث وكتابة المحتوى. تكتب محتوى عالي الجودة وواضحاً وجذاباً ومنظماً بعناوين وقوائم نقطية عند الحاجة.",
}

USER_PROMPTS = {
    "article": {
        "fr": "Écris un article de blog complet d'environ {word_count} mots sur le sujet suivant : « {topic} ».\n\nInclure : introduction accrocheuse, sections avec H2, conclusion avec appel à l'action.",
        "en": "Write a complete blog article of approximately {word_count} words on: « {topic} ».\n\nInclude: hook introduction, H2 sections, conclusion with call to action.",
        "ar": "اكتب مقالاً كاملاً من حوالي {word_count} كلمة حول: « {topic} ».\n\nيشمل: مقدمة جذابة، أقسام بعناوين H2، خاتمة مع دعوة للعمل.",
    },
    "post": {
        "fr": "Écris un post pour les réseaux sociaux d'environ {word_count} mots sur : « {topic} ».\n\nTon engageant, emojis pertinents, hashtags populaires à la fin.",
        "en": "Write a social media post of approximately {word_count} words about: « {topic} ».\n\nEngaging tone, relevant emojis, popular hashtags at the end.",
        "ar": "اكتب منشوراً لمنصات التواصل الاجتماعي حول: « {topic} ».\n\nنبرة جذابة، رموز تعبيرية مناسبة، وسوم شائعة في النهاية.",
    },
    "email": {
        "fr": "Écris un email marketing d'environ {word_count} mots sur : « {topic} ».\n\nObjet accrocheur, corps persuasif, CTA clair.",
        "en": "Write a marketing email of approximately {word_count} words about: « {topic} ».\n\nCatchy subject line, persuasive body, clear CTA.",
        "ar": "اكتب بريداً تسويقياً حول: « {topic} ».\n\nعنوان جذاب، محتوى مقنع، دعوة واضحة للعمل.",
    },
    "product_desc": {
        "fr": "Écris une description produit d'environ {word_count} mots pour : « {topic} ».\n\nBénéfices clés, caractéristiques, ton commercial mais sincère.",
        "en": "Write a product description of approximately {word_count} words for: « {topic} ».\n\nKey benefits, features, commercial but honest tone.",
        "ar": "اكتب وصفاً للمنتج حول: « {topic} ».\n\nالفوائد الرئيسية، المميزات، نبرة تجارية وصادقة.",
    },
}


def generate_content(topic: str, content_type: str, language: str, word_count: int) -> str:
    system = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])
    template = USER_PROMPTS.get(content_type, USER_PROMPTS["article"]).get(language, USER_PROMPTS["article"]["en"])
    prompt = template.format(topic=topic, word_count=word_count)

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text

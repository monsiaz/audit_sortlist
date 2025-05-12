import os
from openai import OpenAI

# --- OpenAI Configuration ---
os.environ["OPENAI_API_KEY"] = ""
MODEL = "o3-2025-04-16"

# Initialize the client
client = OpenAI()

# --- File Paths ---
input_path = "/Volumes/T7/sortlist/sortlist-analyzer/data/article_main_example.html"
output_path = "/Volumes/T7/sortlist/sortlist-analyzer/data/article_main_rewritten.html"

# --- Read original HTML article ---
with open(input_path, "r", encoding="utf-8") as f:
    original_html = f.read()

# --- DEBUG: Vérification lecture fichier source ---
print("==== DEBUG: FICHIER HTML SOURCE ====")
print("Longueur du HTML:", len(original_html))
print(original_html[:500])  # Affiche les 500 premiers caractères
print("==== FIN DEBUG HTML ====")

# --- English prompt with enrichment instructions ---
prompt = f"""
IMPORTANT: You MUST remain on the exact same topic as the source article. You MUST NOT invent new subjects, change the topic, or introduce unrelated trends. Every fact, company, person and data point in your article MUST come from the original source below.

Generate a detailed press article in HTML in English, focusing on the following news content:

{original_html}

This is not just a rewrite — improve it. Use your web knowledge and factual understanding to enrich the article. Go beyond reformulation by bringing insights, relevant data, and structure that elevate the content's quality and usefulness.

You must completely change the structure and avoid any resemblance in phrasing or layout.

CRITICAL CONSTRAINTS:
- STAY EXACTLY ON THE SAME TOPIC as the source article. Do NOT change the subject.
- ONLY use facts, statistics, quotes and examples that are present in the source.
- If you introduce concepts not in the original source, your answer will be INVALID.
- The companies, people, and statistics mentioned must be EXACTLY those in the source.

Instructions:
- Do NOT include document-level HTML tags (no <html>, <head>, or <body>).
- Begin immediately with an engaging introduction (~60 words).
- End the article with a single closing tag: </div>.

Formatting:
- Use <h2> for all main section headings.
- Use if pertinent <table> and <li>
- Each title must reflect its section content, using lowercase (except for proper nouns and the first letter).
- Use <strong> strategically to highlight important points — this is essential.
- Add line breaks between paragraphs for readability.
- No paragraph should exceed 7 lines — break them up if needed.

Content guidelines:
- Deeply rewrite: Change sentence structures, rephrase with synonyms, and reorder ideas.
- Add analysis: Provide your own insights, commentary, or complementary information.
- Use facts and terminology from your training and real-world knowledge to enhance the piece.
- Include specific details, important data, and rich explanations.
- Avoid clichés: Use original expressions and writing.


Conclusion:
- Use an <h2> tag for the final section, but DO NOT name it "Conclusion".
- Instead, use a creative title that invites reflection or suggests future perspectives.
- The very last sentence must be in <i> and act as a thoughtful summary of the entire article.

Length:
- The article must be between 1600 and 2300 words (randomized) and packed with value for the reader.
- The article must NOT use markdown syntax like ** for formatting — use <strong> instead.

Goal:
If we compare your article with the original side by side, they must look completely different — structure, tone, and content flow must be significantly improved and distinct.

Important:
Do not invent facts. Your reformulation must remain based on the original content, while enriching it intelligently using what you know.

FINAL REMINDER: You MUST only talk about the EXACT same topic, companies, and data points as the source article.
"""

# --- DEBUG: Vérification prompt envoyé à l'IA ---
print("==== DEBUG: PROMPT ENVOYÉ À L'IA ====")
print(prompt[:2000])  # Affiche les 2000 premiers caractères
print("Longueur du prompt:", len(prompt))
print("==== FIN DEBUG PROMPT ====")

# --- Try both chat and completion approaches ---
try:
    # First try with chat completions
    print("Trying with chat completions API...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    rewritten_html = response.choices[0].message.content
except Exception as e1:
    print(f"Chat API failed with error: {e1}")
    try:
        # If chat fails, try with completions
        print("Trying with completions API...")
        response = client.completions.create(
            model=MODEL,
            prompt=prompt,
            max_tokens=45000
        )
        rewritten_html = response.choices[0].text
    except Exception as e2:
        print(f"Completions API also failed with error: {e2}")
        raise Exception("Both API methods failed. Please check the model name and API key.")

# --- Save the rewritten HTML article ---
with open(output_path, "w", encoding="utf-8") as f:
    f.write(rewritten_html)

print(f"✅ Article successfully rewritten and saved to:\n{output_path}")

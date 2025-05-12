import openai
import json
import time # Added for potential timing print
import collections
import random

# === CONFIGURATION ===
OPENAI_API_KEY = ""
JSON_FILE = "/Volumes/T7/sortlist/sortlist-analyzer/data/seo_agencies_egypt.json"
LANGUAGES = ["en"]  # Supported: en (English), fr (French), es (Spanish), de (German), it (Italian)
EGYPT_MARKET_DATA_FILE = "/Volumes/T7/sortlist/sortlist-analyzer/data/egytp_market_resume.txt"

print("OpenAI API key set.")

# === LOAD AGENCY DATA ===
def load_agency_data(path):
    print(f"Attempting to load agency data from: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Successfully loaded {len(data)} agencies.")
    return data

# === LOAD EGYPT MARKET DATA ===
def load_text_file(path):
    print(f"Attempting to load text data from: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"Successfully loaded text data from {path}.")
        return content
    except FileNotFoundError:
        print(f"Error: Text file not found at {path}.")
        return None
    except Exception as e:
        print(f"Error loading text file {path}: {e}")
        return None

# === PREPARE ALL DATA AND MAIN PROMPT ===
def build_all_prompt_data(agencies, egypt_market_data_text):
    print("Building all prompt data (main SEO text and supporting data for FAQ)...")
    if not agencies:
        print("No agencies data to build prompt data.")
        return None, None, None, None, None # Added one None for market data

    # Calculate detailed statistics
    total_agencies = len(agencies)

    overall_ratings = [a.get("overall_rating", 0) for a in agencies if a.get("overall_rating") is not None]
    avg_overall_rating = round(sum(overall_ratings) / len(overall_ratings), 2) if overall_ratings else 0

    team_sizes = [a.get("team_size") for a in agencies if isinstance(a.get("team_size"), int)] # Ensure team_size is int
    avg_team_size = round(sum(team_sizes) / len(team_sizes)) if team_sizes else 0
    min_team_size = min(team_sizes) if team_sizes else 0
    max_team_size = max(team_sizes) if team_sizes else 0

    avg_budget_usd_str, min_budget_usd, max_budget_usd = calc_budget_stats(agencies)

    years_founded = [a.get("year_founded") for a in agencies if isinstance(a.get("year_founded"), int)]
    avg_year_founded = round(sum(years_founded) / len(years_founded)) if years_founded else 0

    portfolio_sizes = [a.get("portfolio_size") for a in agencies if a.get("portfolio_size") is not None]
    avg_portfolio_size = round(sum(portfolio_sizes) / len(portfolio_sizes), 1) if portfolio_sizes else 0

    collaborations = [a.get("collaborations_on_sortlist") for a in agencies if a.get("collaborations_on_sortlist") is not None]
    avg_collaborations = round(sum(collaborations) / len(collaborations), 1) if collaborations else 0

    num_reviews_list = [a.get("number_of_reviews") for a in agencies if a.get("number_of_reviews") is not None]
    avg_num_reviews = round(sum(num_reviews_list) / len(num_reviews_list), 1) if num_reviews_list else 0

    num_projects_per_agency = [len(a.get("projects", [])) for a in agencies]
    avg_projects_per_agency = round(sum(num_projects_per_agency) / len(num_projects_per_agency), 1) if num_projects_per_agency else 0
    total_projects_all_agencies = sum(num_projects_per_agency)

    common_services = list(set(s for a in agencies for s in a.get("services", [])))

    project_industries = [p.get("industry") for agency in agencies for p in agency.get("projects", []) if p.get("industry")]
    top_industries_count = 5
    most_common_industries = collections.Counter(project_industries).most_common(top_industries_count)
    most_common_industries_str = ", ".join([f"{industry} ({count})" for industry, count in most_common_industries])

    # Calculate overall average of individual review ratings
    all_review_ratings = []
    for agency in agencies:
        for review in agency.get("reviews", []):
            if isinstance(review.get("rating"), (int, float)):
                all_review_ratings.append(review.get("rating"))
    avg_individual_review_rating = round(sum(all_review_ratings) / len(all_review_ratings), 2) if all_review_ratings else 0

    # Format DATA SUMMARY string (for both prompts)
    data_summary_for_prompts = f"""### DATA SUMMARY (Derived from agency JSON data for Egypt SEO Agencies):
- Total agencies in dataset: {total_agencies}
- Average overall agency rating: {avg_overall_rating}/5
- Agency team size: Average {avg_team_size} (Range: {min_team_size}-{max_team_size}) employees
- Project budget (USD): Average {avg_budget_usd_str} (Range: ${min_budget_usd:,} - ${max_budget_usd:,} for projects with specified budgets)
- Average agency founding year: {avg_year_founded}
- Average portfolio size: {avg_portfolio_size} projects
- Average collaborations on Sortlist: {avg_collaborations}
- Average number of reviews per agency: {avg_num_reviews}
- Average number of listed projects per agency: {avg_projects_per_agency}
- Total listed projects across all agencies: {total_projects_all_agencies}
- Common services offered: {', '.join(sorted(common_services)[:15])} (showing top 15)
- Top {top_industries_count} project industries (with counts): {most_common_industries_str}
- Overall average of individual client review ratings: {avg_individual_review_rating}/5"""

    # Format SELECTED REVIEW HIGHLIGHTS string (for both prompts)
    selected_reviews_details = []
    review_count_target = 7
    all_reviews_with_agency_name = []
    for agency in agencies:
        agency_name = agency.get("name", "Unnamed Agency")
        for review in agency.get("reviews", []):
            review_data = {
                "agency_name": agency_name,
                "comment": review.get("comment", "No comment provided."),
                "rating": review.get("rating", "N/A"),
                "reviewer_info": f"{review.get('position', 'Reviewer')} at {review.get('company', 'Client Company')}"
            }
            all_reviews_with_agency_name.append(review_data)
    random.shuffle(all_reviews_with_agency_name)
    for review_data in all_reviews_with_agency_name[:review_count_target]:
        review_text = f"Agency: {review_data['agency_name']}\n"
        review_text += f"  Reviewer: {review_data['reviewer_info']}\n"
        review_text += f"  Rating: {review_data['rating']}/5\n"
        review_text += f"  Comment: {review_data['comment']}\n"
        selected_reviews_details.append(review_text)
    review_highlights_for_prompts = f"""### SELECTED REVIEW HIGHLIGHTS (Illustrative examples from clients of agencies in the JSON dataset):
{('\n---\n'.join(selected_reviews_details) if selected_reviews_details else 'No specific review highlights available.')}"""

    # Format PROJECT SHOWCASE string (for both prompts)
    all_projects_details = []
    for agency in agencies:
        agency_name = agency.get("name", "Unnamed Agency")
        for p in agency.get("projects", []):
            project_detail = f"Agency: {agency_name}\n"
            project_detail += f"  Project Name: {p.get('name', 'N/A')}\n"
            project_detail += f"  Industry: {p.get('industry', 'N/A')}\n"
            project_detail += f"  Audience: {p.get('audience', 'N/A')}\n"
            project_detail += f"  Year: {p.get('year', 'N/A')}\n"
            project_detail += f"  Services: {', '.join(p.get('services', []))}\n"
            project_detail += f"  Budget (USD): {p.get('budget_usd', 'N/A')}\n"
            project_detail += f"  Description: {p.get('description', 'N/A')}\n"
            all_projects_details.append(project_detail)
    project_showcase_for_prompts = f"""### PROJECT SHOWCASE (Examples of projects by agencies in the JSON dataset):
{('\n---\n'.join(all_projects_details))}"""

    # Format EGYPT DIGITAL MARKET INSIGHTS string (for both prompts)
    egypt_market_insights_str = ""
    if egypt_market_data_text:
        egypt_market_insights_str = f"""### EGYPT DIGITAL MARKET INSIGHTS (from provided text file):
{egypt_market_data_text}"""
    else:
        egypt_market_insights_str = "### EGYPT DIGITAL MARKET INSIGHTS:\nNo specific market data provided in external file."

    # Build MAIN SEO CONTENT PROMPT
    main_seo_prompt_str = f'''You are a professional SEO and content strategist. Your task is to generate an SEO-optimized HTML text for a webpage about SEO agencies in Egypt, to be used on https://www.sortlist.com/seo/egypt-eg.

### HTML OUTPUT STRUCTURE (Main SEO Text):
- Your output MUST start directly with the first `<h2>` tag.
- Your output MUST ONLY contain the HTML content that would typically reside within the `<body>` of a webpage.
- Do NOT include `<!DOCTYPE html>`, `<html>`, `<head>`, or `<body>` tags themselves.
- Use other HTML tags as appropriate: `<h3>`, `<p>`, `<ul>`, `<li>`, `<strong>`. (Avoid tables for agency comparison).
- Ensure all titles (e.g., in `<h2>`, `<h3>`) use sentence case (capitalize only the first word, unless it's a proper noun or acronym).
- ABSOLUTELY DO NOT create any tables comparing agencies. 
- ABSOLUTELY DO NOT create any section, heading (h2, h3, etc.), or content that is titled or themed around 'Featured Agencies', 'Top Agencies', 'Comparative Glimpse', or any similar comparative spotlight on a subset of agencies. Your focus is to provide a comprehensive overview based on the aggregate data and illustrative examples.

### CONTENT GOALS (Main SEO Text):
- Present Egypt as a competitive and growing market for SEO services using a narrative style. The main text should be substantial and detailed, aiming for approximately 1000-1200 words. If needed to thoroughly incorporate the provided data and examples, exceeding this word count is acceptable.
- Avoid generic introductory or concluding paragraphs. Every part of the text should contribute specific, data-backed insights or directly relevant information. Get straight to the point, particularly in the introduction and conclusion.
- The core subject of this text is SEO agencies in Egypt, their specific SEO projects, the services they offer in this domain, and client experiences related to these SEO services. While the 'EGYPT DIGITAL MARKET INSIGHTS' provide essential background, ensure the narrative continually ties back to the practicalities of SEO in Egypt. Avoid lengthy, general discussions about digital marketing that aren't immediately and specifically relevant to the SEO agency landscape and project work in Egypt based on the provided JSON data and market insights. Do not include overly broad statements about digital marketing in general unless they directly and significantly illuminate the specific SEO context in Egypt, supported by data.
- Construct a text that makes sense, with a logical flow, connecting the different data points into a coherent overview.
- Crucially, avoid making general statements without direct support from the provided data. Every assertion about the SEO landscape, agency capabilities, common project types, or client experiences MUST be substantiated with specific examples from the 'PROJECT SHOWCASE', illustrative statistics from the 'DATA SUMMARY', or direct references/paraphrases from the 'SELECTED REVIEW HIGHLIGHTS'. For example, instead of saying 'Agencies offer many services,' say 'Agencies in Egypt offer a diverse range of services, as seen in projects like [Project X from Showcase] which utilized [Service A, B] or [Project Y] which focused on [Service C]. Client feedback, such as [quote/paraphrase a review comment from SELECTED REVIEW HIGHLIGHTS], often points to [specific strength/area for improvement].'
- Explain the types of SEO services commonly offered by agencies in Egypt, typical client profiles, and general pricing considerations (you can refer to the average project budget and budget range).
- Leverage and highlight interesting statistics from the "DATA SUMMARY" provided below.
- A CRITICAL REQUIREMENT: You MUST directly embed and cite specific statistics and data points from the "EGYPT DIGITAL MARKET INSIGHTS" section when discussing the digital economy. Failure to integrate these specific figures (e.g., exact internet user numbers, penetration rates, mobile connection percentages, specific growth figures, connection speeds) from the provided text file will result in an unsatisfactory output. Use these numbers to make your points concrete. For example:
    BAD: "Egypt has many internet users."
    GOOD: "The digital landscape in Egypt is substantial, with the EGYPT DIGITAL MARKET INSIGHTS reporting 96.3 million internet users in early 2025, representing an online penetration of 81.9 percent."
    BAD: "Mobile usage is high."
    GOOD: "Mobile connectivity is a dominant feature, with active mobile connections reaching 116 million, equivalent to 99.0 percent of the total population, as per the EGYPT DIGITAL MARKET INSIGHTS."
    You should also aim to incorporate other specific figures where relevant, such as the 50.7 million social media users or the median internet speeds (e.g., 24.17 Mbps mobile, 76.67 Mbps fixed), always attributing them to the "EGYPT DIGITAL MARKET INSIGHTS" when used.
- Incorporate insights about Egypt's digital economy. To achieve this, you MUST explicitly cite or paraphrase specific data points, statistics, and trends directly from the "EGYPT DIGITAL MARKET INSIGHTS" section when discussing market size, internet penetration, mobile usage, e-commerce growth, or other relevant economic factors. For example, state 'The digital landscape in Egypt is characterized by [specific statistic from EGYPT DIGITAL MARKET INSIGHTS, e.g., X million internet users], which underscores the vast potential for SEO...' or 'The growth in [e.g., mobile internet speed from EGYPT DIGITAL MARKET INSIGHTS] directly impacts user experience, a key factor in modern SEO strategies.' Make these connections clear and direct, ensuring the text is demonstrably informed by this provided market research. Do not just use this section as background; actively pull from it to enrich the text and substantiate your points.
- Refer to specific examples from the "PROJECT SHOWCASE" section to illustrate agency capabilities or common project types. Draw upon specific project names, industries, and outcomes if possible.
- Within the main content, try to weave in references to 2-3 diverse project examples from the 'PROJECT SHOWCASE' to illustrate common SEO challenges in Egypt and how agencies are addressing them.
- Discuss common client experiences or highlight agency strengths and areas for improvement in the Egyptian market by drawing upon the sentiments and specifics mentioned in the "SELECTED REVIEW HIGHLIGHTS".
- Do NOT include an FAQ section in this output. FAQs will be generated separately.

{data_summary_for_prompts}

{review_highlights_for_prompts}

{project_showcase_for_prompts}

{egypt_market_insights_str}

Please write the HTML content in a helpful, credible, and engaging tone, suitable for business decision-makers looking to hire an SEO agency in Egypt.
'''
    print("Main SEO prompt and supporting data strings built.")
    return main_seo_prompt_str, data_summary_for_prompts, review_highlights_for_prompts, project_showcase_for_prompts, egypt_market_insights_str

# === BUILD FAQ PROMPT ===
def build_faq_prompt(main_seo_content_html, data_summary_str, review_highlights_str, project_showcase_str, egypt_market_insights_str):
    print("Building FAQ prompt...")
    prompt = f"""You are an expert SEO content strategist. You have been provided with a main HTML text about SEO agencies in Egypt, along with detailed supporting data (agency data summary, review highlights, project showcase, and specific Egypt digital market insights).
Your task is to generate a concise and valuable FAQ section (4-5 questions and answers) that complements the main text. 

### IMPORTANT GUIDELINES FOR FAQ GENERATION:
1.  **Non-Redundant:** The FAQs MUST NOT simply repeat information already present in the 'MAIN SEO CONTENT PROVIDED'. They should offer *additional* insights, clarifications, or address related questions not covered in depth.
2.  **Value-Driven:** Each Q&A should provide genuine value to a business decision-maker considering SEO services in Egypt.
3.  **Data-Informed:** Where appropriate, leverage ALL sections of the 'SUPPORTING DATA PROVIDED' (agency summary, reviews, projects, AND ESPECIALLY the 'EGYPT DIGITAL MARKET INSIGHTS') to add credibility, depth, and specificity to your answers.
4.  **HTML Structure:** Format each Q&A as follows:
    `<h3>[Your Question Here?]</h3>\n<p>[Your Answer Here. Can be multiple paragraphs if needed.]</p>`
    Your output MUST start directly with the first `<h3>` tag of the first FAQ.
    Do NOT include `<!DOCTYPE html>`, `<html>`, `<head>`, or `<body>` tags.
5.  **Concise:** Aim for clear and concise answers.

### MAIN SEO CONTENT PROVIDED (for context to avoid redundancy):
```html
{main_seo_content_html}
```

### SUPPORTING DATA PROVIDED (for deeper insights for your answers):
{data_summary_str}

{review_highlights_str}

{project_showcase_str}

{egypt_market_insights_str}

Based on all the above, please generate the FAQ HTML content.
"""
    print("FAQ prompt built.")
    return prompt.strip()

# === CALCULATE BUDGET STATISTICS ===
def calc_budget_stats(agencies):
    budgets_usd_values = []
    for agency in agencies:
        for p in agency.get("projects", []):
            b_str = p.get("budget_usd", "")
            if isinstance(b_str, str) and b_str.startswith("$"):
                try:
                    budgets_usd_values.append(int(b_str.replace("$", "").replace(",", "").strip()))
                except ValueError:
                    continue # Skip if conversion fails

    avg_budget_str = "N/A"
    min_budget = 0
    max_budget = 0

    if budgets_usd_values:
        avg_budget_val = round(sum(budgets_usd_values) / len(budgets_usd_values))
        avg_budget_str = f"${avg_budget_val:,}"
        min_budget = min(budgets_usd_values)
        max_budget = max(budgets_usd_values)

    return avg_budget_str, min_budget, max_budget

# === GENERATE RESPONSE FROM OPENAI ===
def generate_openai_response(prompt_str, model="o3-2025-04-16"):
    print(f"Calling OpenAI API with model {model}...")
    # print(f"Prompt being sent (first 500 chars):\n{prompt_str[:500]}...") # DEBUG
    start_time = time.time()
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt_str}]
        )
        content = response.choices[0].message.content
        end_time = time.time()
        print(f"OpenAI API call completed in {end_time - start_time:.2f} seconds.")
        # print(f"Response (first 200 chars): {content[:200]}...") # DEBUG
        return content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None # Return None on API error

# === TRANSLATE OUTPUT ===
def translate_text(content, target_lang, model="o3-2025-04-16"):
    if not content: # Handle case where previous step failed
        print("No content to translate.")
        return None
    print(f"Translate_text called for language: {target_lang}")
    if target_lang == "en":
        print("Target language is English, no translation needed.")
        return content

    print(f"Attempting to translate content to {target_lang} using OpenAI API...")
    start_time = time.time()
    translation = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a professional technical translator."},
            {"role": "user", "content": f"Translate the following HTML from English to {target_lang}. Keep the HTML structure intact:\n\n{content}"}
        ]
    )
    end_time = time.time()
    print(f"Translation to {target_lang} completed in {end_time - start_time:.2f} seconds.")
    return translation.choices[0].message.content

# === MAIN SCRIPT LOGIC ===
if __name__ == "__main__":
    print("Script started.")
    start_time_main = time.time()

    print("Loading agency data...")
    agencies_data = load_agency_data(JSON_FILE)

    if not agencies_data:
        print("No agency data loaded, exiting script.")
    else:
        # Load Egypt market data text
        egypt_market_text = load_text_file(EGYPT_MARKET_DATA_FILE)

        main_seo_prompt_str, data_summary_str, review_highlights_str, project_showcase_str, egypt_market_insights_formatted_str = build_all_prompt_data(agencies_data, egypt_market_text)

        if not main_seo_prompt_str: # Check if prompt building failed
            print("Failed to build main SEO prompt, exiting.")
        else:
            for lang in LANGUAGES: # Iterate through specified languages
                print(f"\n========== PROCESSING FOR LANGUAGE: {lang.upper()} ==========")

                # 1. Generate Main SEO Content
                print(f"--- Generating Main SEO Content ({lang.upper()}) ---")
                main_seo_content_en = None
                if lang == "en":
                    main_seo_content_en = generate_openai_response(main_seo_prompt_str)
                    main_seo_content_to_save = main_seo_content_en
                else:
                    # First, get English version if not already generated
                    # This assumes if LANGUAGES contains non-'en', 'en' is processed first or available
                    # For simplicity, this example might re-generate EN if it's not the first in list and non-EN is first.
                    # A more robust approach would cache the EN version if multiple non-EN languages are needed.
                    if main_seo_content_en is None: # Generate EN version if not primary lang
                         print("Generating base English version first for translation (main SEO)...")
                         main_seo_content_en = generate_openai_response(main_seo_prompt_str)

                    if main_seo_content_en:
                        print(f"Translating Main SEO Content to {lang.upper()}...")
                        main_seo_content_to_save = translate_text(main_seo_content_en, lang)
                    else:
                        main_seo_content_to_save = None
                        print("Skipping translation for main SEO content due to generation error of English version.")

                if main_seo_content_to_save:
                    output_filename_main = f"main_seo_egypt_{lang}.html"
                    output_filepath_main = f"/Volumes/T7/sortlist/Crawl/Scripts/{output_filename_main}"
                    try:
                        with open(output_filepath_main, "w", encoding="utf-8") as f:
                            f.write(main_seo_content_to_save)
                        print(f"Successfully saved Main SEO Content to: {output_filepath_main}")
                    except IOError as e:
                        print(f"Error saving Main SEO Content to file {output_filepath_main}: {e}")
                    # print(f"\n--- Main SEO HTML ({lang.upper()}) ---\n{main_seo_content_to_save}\n------------------------")
                else:
                    print(f"Skipping save for Main SEO Content ({lang.upper()}) due to generation/translation error.")
                    main_seo_content_en = None # Ensure this is None if saving failed, for FAQ step

                # 2. Generate FAQ Content (only if main SEO content was successfully generated in English)
                if main_seo_content_en: # Use the English main content as context for FAQ prompt
                    print(f"\n--- Generating FAQ Content ({lang.upper()}) ---")
                    faq_prompt_str = build_faq_prompt(main_seo_content_en, data_summary_str, review_highlights_str, project_showcase_str, egypt_market_insights_formatted_str)

                    faq_content_to_save = None
                    if lang == "en":
                        faq_content_en = generate_openai_response(faq_prompt_str)
                        faq_content_to_save = faq_content_en
                    else:
                        # Generate English FAQ first, then translate
                        print("Generating base English version first for translation (FAQ)...")
                        faq_content_en_for_translation = generate_openai_response(faq_prompt_str)
                        if faq_content_en_for_translation:
                            print(f"Translating FAQ Content to {lang.upper()}...")
                            faq_content_to_save = translate_text(faq_content_en_for_translation, lang)
                        else:
                            print("Skipping translation for FAQ content due to generation error of English version.")

                    if faq_content_to_save:
                        output_filename_faq = f"faq_seo_egypt_{lang}.html"
                        output_filepath_faq = f"/Volumes/T7/sortlist/Crawl/Scripts/{output_filename_faq}"
                        try:
                            with open(output_filepath_faq, "w", encoding="utf-8") as f:
                                f.write(faq_content_to_save)
                            print(f"Successfully saved FAQ Content to: {output_filepath_faq}")
                        except IOError as e:
                            print(f"Error saving FAQ Content to file {output_filepath_faq}: {e}")
                        # print(f"\n--- FAQ HTML ({lang.upper()}) ---\n{faq_content_to_save}\n---------------------")
                    else:
                        print(f"Skipping save for FAQ Content ({lang.upper()}) due to generation/translation error.")
                else:
                    print(f"Skipping FAQ generation for {lang.upper()} as main SEO content (English) was not successfully generated.")

    end_time_main = time.time()
    print(f"\nScript finished in {end_time_main - start_time_main:.2f} seconds.")

from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


# def interpret_query(query, profiles):
#     """
#     Use GPT-4o to interpret the search query and suggest filtering criteria.
#     """
#     prompt_template = """
#     You are a helpful assistant for a recruiter platform. Interpret the following search query:
#     "{query}"
#     Based on this query, determine the filtering criteria for the following profiles (provided as JSON).
#
#     Profiles:
#     {profiles}
#
#     Return the filtering criteria in JSON format. Example:
#     {{
#       "skills": ["Python", "Machine Learning"],
#       "experience_years_min": 3
#     }}
#     """
#     # Prepare the prompt
#     prompt = prompt_template.format(query=query, profiles=json.dumps(profiles, indent=2))
#
#     # Call GPT
#     completion = client.chat.completions.create(
#         model="gpt-4o",  # Use the available model
#         messages=[
#             {"role": "system",
#              "content": "You are a helpful assistant that interprets search queries for a recruiter platform."},
#             {"role": "user", "content": prompt}
#         ],
#         max_tokens=500,
#         temperature=0  # Deterministic results
#     )
#
#     # Extract filtering criteria
#     raw_content = completion.choices[0].message.content
#     cleaned_content = raw_content.replace("```json", "").replace("```", "").strip()
#
#     try:
#         return json.loads(cleaned_content)
#     except json.JSONDecodeError:
#         return {"error": "Failed to parse criteria", "raw_content": raw_content}

def interpret_query(query, profiles):
    """
    Use GPT-4o to interpret the search query and suggest filtering criteria.
    Supports complex queries with logical operators.
    """
    prompt_template = """
    You are a helpful assistant for a recruiter platform. Interpret the following search query:
    "{query}"
    Based on this query, determine the filtering criteria for the following profiles (provided as JSON).

    Profiles:
    {profiles}

    Return the filtering criteria in JSON format. Example:
    {{
      "skills": ["Python", "TensorFlow"],
      "experience_years_min": 5,
      "education": ["MSc"]
    }}
    """
    # Prepare the prompt
    prompt = prompt_template.format(query=query, profiles=json.dumps(profiles, indent=2))

    # Call GPT
    completion = client.chat.completions.create(
        model="gpt-4o",  # Use the available model
        messages=[
            {"role": "system",
             "content": "You are a helpful assistant that interprets search queries for a recruiter platform."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0  # Deterministic results
    )

    # Extract filtering criteria
    raw_content = completion.choices[0].message.content

    # Extract JSON block from code block markers
    if "```json" in raw_content:
        json_start = raw_content.index("```json") + len("```json")
        json_end = raw_content.index("```", json_start)
        json_content = raw_content[json_start:json_end].strip()
        try:
            return json.loads(json_content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON from response", "raw_content": raw_content}
    else:
        # Fallback if JSON block is not found
        return {"error": "No JSON block found in response", "raw_content": raw_content}


def filter_profiles(profiles, criteria):
    """
    Filter profiles based on criteria extracted from the query.
    """
    matching_profiles = []

    for profile in profiles:
        # Check skills
        if "skills" in criteria:
            if not any(skill in profile["skills"] for skill in criteria["skills"]):
                continue

        # Check minimum experience
        if "experience_years_min" in criteria:
            cv_experience = profile["experience"]["cv"]
            total_years = sum(int(exp["Duration"].split()[0]) for exp in cv_experience if "Duration" in exp)
            if total_years < criteria["experience_years_min"]:
                continue

        # Check education
        if "education" in criteria:
            profile_education = [edu["Degree"] for edu in profile["education"]]
            if not any(edu in profile_education for edu in criteria["education"]):
                continue

        # Add profile to results if all conditions pass
        matching_profiles.append(profile)

    return matching_profiles

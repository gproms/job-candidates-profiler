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
    Supports logical operators, percentages, and minimum matches.
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
      "skill_match": "all",  # Options: "all", "any", integer (min count), float (min percentage)
      "experience_years_min": 5,
      "education": ["MSc"],
      "logic": "and"  # Options: "and", "or"
    }}

    Ensure the JSON output does not include comments.
    """
    # Prepare the prompt
    prompt = prompt_template.format(query=query, profiles=json.dumps(profiles, indent=2))

    # Call GPT
    completion = client.chat.completions.create(
        model="gpt-4o",
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

        # Remove comments from JSON block
        json_content = "\n".join(line for line in json_content.split("\n") if not line.strip().startswith("#"))
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
    Supports flexible skill matching, percentages, absolute counts, and logical operators.
    """
    matching_profiles = []

    for profile in profiles:
        print(f"\nChecking profile: {profile['name']}")  # Debug: Show profile being checked

        # Initialize a flag for the OR logic
        matches = []

        # Check skills
        if "skills" in criteria:
            required_skills = criteria["skills"]
            profile_skills = profile["skills"]

            # Check skill matching logic
            if "skill_match" in criteria:
                if criteria["skill_match"] == "all":
                    skill_match = all(skill in profile_skills for skill in required_skills)
                elif isinstance(criteria["skill_match"], int):
                    skill_match = sum(1 for skill in required_skills if skill in profile_skills) >= criteria["skill_match"]
                elif isinstance(criteria["skill_match"], float):
                    percentage_matched = sum(1 for skill in required_skills if skill in profile_skills) / len(required_skills)
                    skill_match = percentage_matched >= criteria["skill_match"]
                else:  # Default to "any" logic
                    skill_match = any(skill in profile_skills for skill in required_skills)
            else:  # Default to "any" logic if no specific match logic is given
                skill_match = any(skill in profile_skills for skill in required_skills)

            matches.append(skill_match)
            print(f"  Skill Match: {skill_match}")  # Debug: Skill match result

        # Check education
        if "education" in criteria:
            required_education = criteria["education"]
            profile_education = [edu["Degree"] for edu in profile["education"]]
            education_match = any(edu in profile_education for edu in required_education)
            matches.append(education_match)
            print(f"  Education Match: {education_match}")  # Debug: Education match result

        # Check minimum experience
        if "experience_years_min" in criteria:
            total_years = sum(
                int(exp["Duration"].split()[0]) for exp in profile["experience"]["cv"] if "Duration" in exp
            )
            experience_match = total_years >= criteria["experience_years_min"]
            matches.append(experience_match)
            print(f"  Experience Match: {experience_match}")

        # Apply logic (AND/OR)
        if "logic" in criteria and criteria["logic"] == "or":
            if any(matches):
                print("  Profile matches based on OR logic.")
                matching_profiles.append(profile)
        else:  # Default to AND logic
            if all(matches):
                print("  Profile matches based on AND logic.")
                matching_profiles.append(profile)

    return matching_profiles


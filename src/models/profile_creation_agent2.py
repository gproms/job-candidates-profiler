from openai import OpenAI
from dotenv import load_dotenv
import json
import os

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)


def load_file(file_path):
    """Load text data from a file."""
    with open(file_path, 'r') as file:
        return file.read()


def load_json(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def extract_data_from_text(text, prompt_template):
    """
    Use OpenAI GPT-4o to extract structured information from unstructured text.
    """
    prompt = prompt_template.format(text=text)
    completion = client.chat.completions.create(
        model="gpt-4o",  # Use the available model
        messages=[
            {"role": "system",
             "content": "You are a helpful assistant that extracts structured data from unstructured text."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,  # Limit response length
        temperature=0  # Deterministic outputs for consistent extraction
    )

    # Get the raw content
    raw_content = completion.choices[0].message.content

    # try:
        # Remove code block markers and parse JSON
    cleaned_content = raw_content.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned_content)
    # except json.JSONDecodeError:
    #     # Handle invalid JSON formats by returning raw content
    #     return {
    #         "error": "Invalid JSON format",
    #         "raw_content": raw_content
    #     }


def consolidate_data_with_ai(cv_text, linkedin_data, interview_text):
    """
    Consolidate data using AI extraction for CV and interview text.
    """
    # GPT prompt templates
    cv_prompt = """
    Extract the following fields from the CV below:
    - Name
    - Skills
    - Experience (list each job title, company, duration, and description)
    - Education (list each degree, institution, and graduation year)
    Return the output as JSON.

    CV:
    {text}
    """
    interview_prompt = """
    Extract key additional insights from the following interview transcript.
    Return the output as a JSON array of strings.

    Transcript:
    {text}
    """

    # Extract data from CV and interview using GPT
    cv_data = extract_data_from_text(cv_text, cv_prompt)
    additional_insights = extract_data_from_text(interview_text, interview_prompt)

    # Consolidate with LinkedIn data
    profile = {
        "name": cv_data.get("Name", linkedin_data.get("name")),
        "skills": list(set(cv_data.get("Skills", []) + linkedin_data.get("skills", []))),
        "experience": {
            "cv": cv_data.get("Experience", []),
            "linkedin": linkedin_data.get("experience", [])
        },
        "education": cv_data.get("Education", linkedin_data.get("education", [])),
        "additional_insights": additional_insights
    }
    return profile


def create_profiles_with_ai(data_dir):
    """
    Create unified profiles using AI for data extraction.
    """
    profiles = []

    # Load LinkedIn profiles
    linkedin_data = load_json(os.path.join(data_dir, "linkedin_profiles.json"))

    # Loop through CVs and corresponding interview files
    for i in range(1, 6):  # Assuming 5 individuals
        cv_file = os.path.join(data_dir, f"cv_{i}.txt")
        interview_file = os.path.join(data_dir, f"interview_{i}.txt")

        cv_text = load_file(cv_file)
        interview_text = load_file(interview_file)
        linkedin_profile = linkedin_data[i - 1]  # Corresponding LinkedIn data

        # Consolidate data using AI
        profile = consolidate_data_with_ai(cv_text, linkedin_profile, interview_text)
        profiles.append(profile)

    return profiles


if __name__ == "__main__":
    # Path to the data directory
    data_directory = os.path.join("..", "..", "data")

    # Generate unified profiles
    profiles = create_profiles_with_ai(data_directory)

    # Print consolidated profiles for verification
    for profile in profiles:
        print(json.dumps(profile, indent=4))

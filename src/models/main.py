import json
from src.models.profile_creation_agent import create_profiles_with_ai
from src.models.search_agent import interpret_query, filter_profiles


def main():

    use_json_input_test = False

    # Path to the data directory
    data_directory = "data"

    if use_json_input_test:
        # Step 1: Example Hardcoded Criteria for Testing
        criteria = {
            "skills": ["Python", "TensorFlow"],
            "skill_match": 0.5,  # 50% of skills must match
            "education": ["MSc in AI", "BSc in Software Engineering"],
            "experience_years_min": 3,
            "logic": "or"  # Any condition can pass
        }
    else:
        # Step 1: Create unified Profiles
        print("Generating profiles from data...")
        profiles = create_profiles_with_ai(data_directory)

        # Step 2: Example input query
        query = "Find candidates with Python and TensorFlow skills OR a BSc degree in Software Engineering"

        # Step 3: Interpret query
        criteria = interpret_query(query, profiles)

    print("\nGenerated Criteria:")
    print(json.dumps(criteria, indent=4))

    # Step 4: Filter profiles
    if "error" not in criteria:
        matching_profiles = filter_profiles(profiles, criteria)
        print("\nMatching Profiles:")
        print(json.dumps(matching_profiles, indent=4))
    else:
        print("Failed to interpret query:", criteria["raw_content"])


if __name__ == "__main__":
    main()

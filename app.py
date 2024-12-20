import streamlit as st
import boto3
import json

# AWS Lambda setup
LAMBDA_FUNCTION_NAME = "faangai-query-handler"

# Initialize AWS client
lambda_client = boto3.client("lambda", region_name="eu-west-2")

def query_lambda(query):
    """Invoke the AWS Lambda function and fetch results."""
    try:
        payload = {"query": query}
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        response_payload = json.loads(response["Payload"].read())
        return response_payload
    except Exception as e:
        return {"error": str(e)}

# Streamlit App
st.title("Candidate Search")
st.subheader("Search Profiles Based on Your Query")

query = st.text_input("Enter your search query:", value="Find candidates with Python and TensorFlow skills OR a BSc degree in Software Engineering")

# Submit button
if st.button("Search"):
    if query.strip():
        # st.write("Searching...")
        with st.spinner("Fetching results from Lambda..."):
            results = query_lambda(query)

        if "error" in results:
            st.error(f"Error: {results['error']}")

        # else:
        #     st.success("Query executed successfully!")

        if "profiles" in results["body"]:
            # profiles = json.loads(results["body"])["profiles"]
            # st.write(f"Found {len(profiles)} matching profiles.")
            # for profile in profiles:
            #     st.json(profile)

            # Parse and display profiles
            profiles = json.loads(results["body"])["profiles"]
            for profile in profiles:
                st.markdown("---")
                st.subheader(profile["name"])
                st.write(f"**Skills:** {', '.join(profile['skills'])}")
                st.write(f"**Education:**")
                for edu in profile.get("education", []):
                    st.write(
                        f"- {edu['Degree']} from {edu['Institution']} (Graduation Year: {edu.get('Graduation Year', 'N/A')})")
                st.write(f"**Experience:**")
                for exp in profile.get("experience", {}).get("cv", []):
                    st.write(f"- {exp['Job Title']} at {exp['Company']} ({exp['Duration']})")
                st.write(f"**Additional Insights:**")
                for insight in profile.get("additional_insights", []):
                    st.write(f"- {insight}")
        else:
            st.write("No results found.")
    else:
        st.write("Please enter a query.")

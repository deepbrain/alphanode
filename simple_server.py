import streamlit as st
import openai
from openai import OpenAI
import datetime
import requests

# Set the title of the app
st.title("AlphaNode MVP")

# Define the model to use
MODEL = "gpt-4o-mini"  # Corrected model name if necessary

# Initialize the OpenAI client
client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"],
)
DataUrls = {
    "September 2024": "https://downloads.usda.library.cornell.edu/usda-esmis/files/3197xm04j/6108x5070/dv141k49x/psla0924.txt",
    "August 2024": "https://downloads.usda.library.cornell.edu/usda-esmis/files/3197xm04j/rn302t31p/5t34vb12v/psla0824.txt",
    "September 2023": "https://downloads.usda.library.cornell.edu/usda-esmis/files/3197xm04j/7p88f226b/gx41p340x/psla0923.txt",
}


def ask_openai(full_messages):
    """
    Sends a list of messages to the OpenAI API and returns the assistant's response.
    Args:
        full_messages (list): A list of message dictionaries.
    Returns:
        str: The assistant's response.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=full_messages,
            temperature=0.7,
            max_tokens=16000,
        )
        # Extract the assistant's reply
        reply = response.choices[0].message.content.strip()
        return reply
    except openai.APIError as e:
        # Handle errors gracefully
        st.error(f"An error occurred: {e}")
        return f"An error occurred: {e}"


def get_analysis_prompt(user_input):
    # Construct the analysis prompt
    # convert the dataurls dict to a string
    data_urls_str = "\n".join([f"{month}: {url}" for month, url in DataUrls.items()])
    message = (
        f"You are an investment analyst specializing in the agriculture sector. Analyze the agriculture data given and answer the question: {user_input}\n"
        f"In your analysis, emphasize any trends or insights or original ideas valuable for investors. "
        f"Start from the latest month and compare the data to previous months and the last year. "
        f"Make sure all quoted numbers are accurate and have exact matches in the documents for the respective months above."
        f"Do not include months or data without exact matches in the provided data"
        f"If possible, come up with an original idea or insight that could be valuable for investors."
        f"Produce relevant data in tables format."
        f"Provide references as hyperlinks to the data sources: \n{data_urls_str}"
    )

    # Combine system messages and user messages for context
    full_messages = st.session_state.system_messages + st.session_state.messages + [
        {"role": "user", "content": message}]
    return full_messages


# Initialize session state variables
if "system_messages" not in st.session_state:
    # Fetch the agriculture data
    # do requests get for each URL:
    Data = {}
    for month, url in DataUrls.items():
        response = requests.get(url)
        Data[month] = response.text

    # Construct the hidden system message
    system_message = (
        "Here is the data for the agriculture sector that includes 3 months:\n"
        f"September 2024: {Data['September 2024']}\n"
        f"August 2024: {Data['August 2024']}\n"
        f"September 2023: {Data['September 2023']}\n"
    )

    # Store the system message in session state
    st.session_state.system_messages = [{"role": "system", "content": system_message}]

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history (excluding system messages)
for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Accept user input
user_prompt = st.chat_input(
    "Ask any questions about the Department of Agriculture data")

if user_prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # Display user message in chat container
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant") as assistant_container:
        # Initialize an empty string to collect the assistant's response
        assistant_response = ""

        try:
            # Create the streaming completion
            stream = client.chat.completions.create(
                model=MODEL,
                messages=get_analysis_prompt(user_prompt),
                temperature=0.7,
                max_tokens=16000,
                stream=True,
            )

            # Iterate over the streaming response
            response = st.write_stream(stream)
            # Append the full response to the chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        except openai.APIError as e:
            error_message = f"An error occurred while generating the response: {e}"
            assistant_container.markdown(error_message)
            assistant_response = error_message

        # Add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})


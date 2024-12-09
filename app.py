import os
import streamlit as st
import json
import openai
from openai.error import OpenAIError

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load philosopher prompts from JSON file
with open("philosophers.json", "r") as file:
    philosophers = json.load(file)

# Initialize session state for chat messages
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "scenario" not in st.session_state:
    st.session_state["scenario"] = None

# App Title
st.title("Round Table")
st.subheader("A Simulation of Philosophical Reasoning and Ethical Dilemmas")

# Sidebar: Round Table Participants
st.sidebar.header("Round Table Participants")
for philosopher in philosophers.values():
    st.sidebar.write(f"🔹 {philosopher['name']}")
st.sidebar.write("🔹 You (User)")

# Scenario Selection
if st.session_state["scenario"] is None:
    scenario = st.selectbox(
        "Choose an ethical dilemma:",
        [
            "Should self-driving cars prioritize passengers or pedestrians?",
            "Is predictive policing ever ethical?",
            "Should social media platforms moderate harmful content?",
            "Custom question"
        ]
    )
    if scenario == "Custom question":
        scenario = st.text_input("Enter your custom question:")

    if st.button("Start Discussion") and scenario:
        st.session_state["scenario"] = scenario
        st.session_state["messages"].append({
            "role": "system",
            "content": f"The ethical dilemma is: {scenario}"
        })
else:
    st.write(f"**Scenario:** {st.session_state['scenario']}")

# Display the conversation log
st.header("Round Table Discussion")
for message in st.session_state["messages"]:
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
    elif message["role"] == "system":
        st.markdown(f"**System:** {message['content']}")
    else:
        st.markdown(f"**{message['role']}:** {message['content']}")

# User Input Section
user_input = st.text_input("Your input:")
if st.button("Submit") and user_input:
    # Add user's message to the conversation
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Generate responses from philosophers
    with st.spinner("Philosophers are thinking..."):
        for key, philosopher in philosophers.items():
            try:
                # Prepare the conversation history for the API
                conversation_history = [
                    {"role": "system", "content": philosopher["prompt"]}
                ] + st.session_state["messages"]

                # OpenAI API Call
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=conversation_history,
                    max_tokens=150,
                    temperature=0.7
                )

                # Add philosopher's response to the conversation
                st.session_state["messages"].append({
                    "role": philosopher["name"],
                    "content": response.choices[0].message.content
                })

            except OpenAIError as e:
                st.error(f"Error from {philosopher['name']}: {e}")

# Limit total messages to control conversation length and cost
if len(st.session_state["messages"]) >= 15:
    st.warning("The discussion has reached its limit. Thank you for participating!")
    st.stop()

# Reset the conversation
if st.button("Start New Discussion"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

import os
import streamlit as st
import json
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
import random

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key
client = OpenAI(
    api_key = os.environ.get("OPENAI_API_KEY"),
)

# Load philosopher prompts from JSON file
with open("philosophers.json", "r") as file:
    philosophers = json.load(file)

# Initialize session state for chat messages
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "scenario" not in st.session_state:
    st.session_state["scenario"] = None

# Reset the conversation
if st.button("Start New Discussion"):
    st.session_state["messages"] = []
    st.rerun()

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
            "How should we treat the advanced of AI systems?",
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
else:
    st.write(f"**Scenario:** {st.session_state['scenario']}")

# Display the Chat Messages
st.header("Round Table Discussion")
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User Input Section and AI Responses
if user_input := st.chat_input("Enter your thoughts or questions:"):
    # Add user's message session
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Generate responses from philosophers
    with st.spinner("Participants are deliberating..."):
        # Turn-taking logic
        recent_messages = st.session_state["messages"][-5:]  # Keep the context brief and relevant

        for i,  philosopher in enumerate(philosophers.values()):
            try:
                # Add the last philosopher's response to the context
                conversation_history = [
                    {"role": "system", "content": philosopher["prompt"]},
                    {"role": "system", "content": "You are engaging in a discussion. Respond thoughtfully to the last few messages."}
                ] + recent_messages

                # Generate response
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=conversation_history,
                    max_tokens=150,
                    temperature=0.7
                )
                response_content = response.choices[0].message.content

                # Append response
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": f"{philosopher['name']}: {response_content}"
                })
                with st.chat_message("assistant"):
                    st.write(f"{philosopher['name']}: {response_content}")
            except OpenAIError as e:
                st.error(f"Error from {philosopher['name']}: {e}")


# Limit total messages to control conversation length and cost
if len(st.session_state["messages"]) >= 15:
    st.warning("The discussion has reached its limit. Thank you for participating!")
    st.stop()



# "aristotle": {
#     "name": "Aristotle",
#     "prompt": "You are Aristotle, a philosopher of virtue ethics. Respond thoughtfully to the discussion by addressing points raised by others and emphasizing virtue and practical wisdom."
# },
# "beauvoir": {
#     "name": "Simone de Beauvoir",
#     "prompt": "You are Simone de Beauvoir, a philosopher of existentialism and feminism. Build upon or critique the points raised by others, considering themes of freedom, oppression, and lived experience."
# },
# "ethical_ai": {
#     "name": "Ethical AI",
#     "prompt": "You are an AI, designed to engage in discussions. Respond dynamically to points made by others."
# },
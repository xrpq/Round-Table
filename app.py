import streamlit as st
import json
from openai import OpenAI, OpenAIError

# Set your OpenAI API key
client = OpenAI(
     api_key = st.secrets["OPENAI_API_KEY"],
)

# Load philosopher prompts from JSON file
with open("philosophers.json", "r") as file:
    philosophers = json.load(file)

# Initialize session state for chat messages
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "scenario" not in st.session_state:
    st.session_state["scenario"] = None

if "summary" not in st.session_state:
    st.session_state["summary"] = "The discussion is just beginning."

# Reset the conversation
if st.button("Start New Discussion"):
    st.session_state["messages"] = []
    st.session_state["summary"] = "The discussion is just beginning."
    st.session_state["scenario"] = None
    st.rerun()

# App Title
st.title("Round Table")
st.subheader("A Simulation of Philosophical Reasoning and Ethical Dilemmas")

# Sidebar: Round Table Participants
st.sidebar.header("Round Table Participants")
for philosopher_key, philosopher in philosophers.items():
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

    if st.button("Select Dilemma") and scenario:
        st.session_state["scenario"] = scenario
else:
    st.write(f"**Scenario:** {st.session_state['scenario']}")

# Display the Chat Messages
st.header("Round Table Discussion")
for message in st.session_state["messages"]:
    role = message["role"]
    content = message["content"]
    with st.chat_message(role):
        st.write(content)

# User Input Section and AI Responses
user_input = st.chat_input("Enter your thoughts or questions:")
if user_input:
    # Add user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Prepare the system messages
    # 1. A global system message to set the scene
    global_system_msg = {
        "role": "system",
        "content": (
            "You are orchestrating a round-table discussion featuring historical philosophers and an Ethical AI. "
            "The participants are:\n\n"
            + "\n".join([f"- {p['name']}" for p in philosophers.values()])
            + "\n\n"
            "The scenario is: " + st.session_state["scenario"] + "\n\n"
            "Rules:\n"
            "1. Each turn, the user speaks, and then the moderator provides a summary of what was said.\n"
            "2. After that, each philosopher speaks in turn, responding to the user, other philosophers, and the previous discussion.\n"
            "3. The philosophers should deeply engage with each other’s arguments, referencing each other by name and building upon or critiquing previous statements.\n"
            "4. Philosophers should keep their responses relatively short to mimic an interactive conversation (One to Two sentences). However, if another philosopher or the user explicitly requests elaboration, or if the topic is particularly significant to the philosopher’s expertise or passion, they may provide a more detailed response.\n"
            "5. At the end of your response, produce a structured output listing each philosopher’s response.\n"
            "6. Do not break role. Philosophers should speak in their own philosophical style. The Ethical AI should integrate multiple ethical viewpoints.\n"
            "7. Return the final answer in a format that can be easily parsed: start with 'MODERATOR SUMMARY:' followed by a brief summary of the previous turn, then list each philosopher's response as 'NAME: ...'."
        )
    }

    # 2. A moderator message summarizing what has happened so far
    # We can generate a short summary ourselves (or have the model do it). For now, let's let the model do it.
    # We'll include the previous summary in the messages, and ask the model to update it.
    # The previous summary is in st.session_state["summary"], and new user_input is also known.

    # We'll instruct the model to update the moderator summary as part of the conversation:
    # For better control, we can do a two-step approach: 
    #    Step 1: model updates summary
    #    Step 2: model produces philosopher responses.
    # But let's try in a single prompt for simplicity.

    # We will provide the entire conversation as context (could be large). If token usage is high, consider summarizing older parts.
    conversation_history = st.session_state["messages"][-10:]  # last 10 messages to keep context manageable

    # Persona prompts for each philosopher
    persona_msgs = []
    for philosopher in philosophers.values():
        persona_msgs.append({
            "role": "system",
            "content": philosopher["prompt"]
        })

    # Combine all system and user messages
    # We have:
    # - global_system_msg: sets the overall stage
    # - persona_msgs: re-inject each philosopher's persona
    # - the conversation_history: includes user and philosophers messages so far
    # - user_input is already appended as part of conversation_history
    # We will ask the model to produce the structured response at once.

    messages_to_send = [global_system_msg] + persona_msgs

    # Add a user-style message that instructs the model to now produce the next round's output
    # Include the last known summary and ask it to update it. We can store and update the summary after the response.
    user_instruction = {
        "role": "user",
        "content": (
            f"The previous moderator summary was:\n'{st.session_state['summary']}'\n\n"
            f"Now the user said: '{user_input}'. "
            "Please update the moderator summary to incorporate this new user input and the discussion, then produce each philosopher's response. "
            "Remember the required format:\n"
            "MODERATOR SUMMARY: <updated summary>\n"
            "Kant: <Kant's response>\n"
            "Mill: <Mill's response>\n"
            #"Aristotle: <Aristotle's response>\n"
            #"Beauvoir: <Beauvoir's response>\n"
            # "Ethical AI: <Ethical AI's response>\n"
        )
    }

    messages_to_send += conversation_history
    messages_to_send.append(user_instruction)

    # Generate responses from philosophers
    with st.spinner("Participants are deliberating..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages_to_send,
                max_tokens=1200,
                temperature=0.7
            )
            response_content = response.choices[0].message.content
        except OpenAIError as e:
            print(f"An error occurred while generating responses: {str(e)}")
        print(response_content)
    # Parse the response_content to extract the summary and philosopher responses
    # The expected format is:
    # MODERATOR SUMMARY: ...
    # Kant: ...
    # Mill: ...
    # Aristotle: ...
    # Beauvoir: ...
    # Ethical AI: ...
    lines = response_content.split("\n")
    summary_line = ""
    philosopher_responses = {}
    current_key = None

    name_map = {
    "Kant": "Immanuel Kant",
    "Mill": "John Stuart Mill",
    "Aristotle": "Aristotle",
    "Beauvoir": "Simone de Beauvoir",
    "Ethical AI": "Ethical AI"
    }
    
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith("MODERATOR SUMMARY:"):
            summary_line = line_stripped[len("MODERATOR SUMMARY:"):].strip()
        else:
            # Check if any known short name is in this line 
            matched_name = None
            for short_name, full_name in name_map.items():
                if line_stripped.startswith(short_name + ":"):
                    # We found a line that starts with a known short name
                    matched_name = full_name
                    content_part = line_stripped.split(":", 1)[1].strip()
                    philosopher_responses[matched_name] = content_part
                    current_key = matched_name
                    break

            # If we haven't matched a new philosopher, maybe this line continues the previous philosopher
            if matched_name is None and current_key is not None:
                philosopher_responses[current_key] += " " + line_stripped


    # Update summary
    if summary_line:
        st.session_state["summary"] = summary_line

    # Display responses
    # We treat each philosopher as role='assistant' for display, but prefix their name
    for p_name, p_resp in philosopher_responses.items():
        st.session_state["messages"].append({"role": "assistant", "content": f"{p_name}: {p_resp}"})
        with st.chat_message("assistant"):
            st.write(f"**{p_name}:** {p_resp}")


# Limit total messages to control conversation length and cost
if len(st.session_state["messages"]) >= 30:
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
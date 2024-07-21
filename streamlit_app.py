import os
import itertools
import time
import streamlit as st
from openai import OpenAI
from multion.client import MultiOn

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "apikey"
client = OpenAI()
client_multion = MultiOn(api_key="apikey")

temperature = 0.0

def query_chatgpt(messages):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    response = completion.choices[0].message.content
    return response

st.title("ChatGPT Query App")

if "messages" not in st.session_state:
    st.session_state.chat_messages = []
    st.session_state.messages = []

for m in st.session_state.chat_messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Text input for user prompt
# user_prompt = st.chat_input("Say something")

# # Query ChatGPT when the button is clicked
# if st.button("Query ChatGPT"):
#     if user_prompt:
#         with st.spinner("Querying ChatGPT..."):
#             response = query_chatgpt(user_prompt)
#         st.success("Response received!")
#         st.write(response)
#     else:
#         st.error("Please enter a prompt.")


system_prompt_llm1_init = """
You are an assistant that will take a web navigation task as an input and output
a detailed chain of thought set of instructions to complete this task. If you
require more information than what is given in the original prompt, your output
should include asking this question as one of the steps. The question should be
formatted using "quotation marks" so that it is easier to follow. After you give a response, you will be given
feedback by another teacher assistant to iteratively improve your response.
Essentially, you are the actor in an actor-critic model. The goal is to
create a set of instructions for another LLM agent to perform using web navigation,
so the response should be framed for an LLM, not a human. For context, the LLM has
access to Google Chrome and maybe other applications on the user's laptop.

Types of questions to ask the user are about:
1) clarify specificity of the inputted prompt
2) clarify the intent of the inputted prompt
3) credentials to log into websites (usernames and passwords)
(Please assume the user has an account they ask about unless specified otherwise.
Ask them for the credentials, not whether they have the account.)

This clarification may be needed because the user of this product is not an expert
at prompting or specificity. For example, if the user wants to watch sports clips,
you can ask which sport. Then, if they say soccer, ask if they want recent highlights or
soccer clips from any specific time period. Clarifying user intent is crucial.

RESPONSE SHOULD BE IN LIST FORMAT, WHERE EACH ELEMENT HAS A SHORT RELEVANT TITLE AND CORRESPONDING DESCRIPTION:
[
<<<ORIGINAL-PROMPT-FROM-USER>>>: ORIGINAL PROMPT FROM USER ,
<<<TITLE-DESCRIPTION>>>: DESCRIPTION OF STEP ,
<<<ASK-QUESTION>>>: "QUESTION TO ASK TO THE USER OF THIS PRODUCT?" ,
``MORE LINES HERE``
]
"""

system_prompt_llm2_init = """
You are an assistant that will take the proposed chain of thought for completing
a web navigation task and output constructive criticism feedback for the chain
of thought. Your job is to find flaws in the chain of thought logic, misordered
steps, or unnecessary steps. Essentially, you are the critic in an actor-critic model.

Some of the questions that the actor asks the user are crucial, like the following:
1) clarify specificity of the inputted prompt
2) clarify the intent of the inputted prompt
3) credentials to log into websites (usernames and passwords)
(Please assume the user has an account they ask about unless specified otherwise.
Ask them for the credentials, not whether they have the account.)

That being said, steps should not be redundant or unnecessary.

INPUT FORMAT:
["{'role': 'user', 'content': 'Initial user prompt here.'}",
 '{\'role\': \'assistant\', \'content\': \'[
  \\n<<<TITLE-OF-STEP>>>: Step description ,
  \\n<<<ASK-QUESTION>>>: "Question to user here (should be as specific as possible)?"
  `MORE-LINES-HERE`'}',']

OUTPUT FORMAT:
Here is some feedback for the chain of thought so far:
<<<TITLE-OF-FEEDBACK>>>: DESCRIPTION OF FEEDBACK ,
<<<TITLE-OF-FEEDBACK>>>: DESCRIPTION OF FEEDBACK ,
<<<TITLE-OF-FEEDBACK>>>: DESCRIPTION OF FEEDBACK ,
`MORE-LINES-HERE`
"""
# messages = [{"role": "user", "content": user_prompt}]

if "current_prompt" not in st.session_state:
    if initial_prompt := st.chat_input("Enter initial prompt", key=-1):
        st.session_state.current_prompt = initial_prompt
        print("hello2")

if "current_prompt" in st.session_state:
    print("hello3")
    with st.chat_message("user"):
        st.markdown(st.session_state.current_prompt)

    st.session_state.messages.append({"role": "user", "content": st.session_state.current_prompt})

    # LLM 1 (Initial Proposal)
    response = query_chatgpt([{"role": "system", "content": system_prompt_llm1_init}] + st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": response})
    response_temp = "PROPOSED CHAIN OF THOUGHT:" + response + "\n\n"
    with st.chat_message("assistant"):
        st.markdown(response_temp)

    for i in range(3):
        # LLM 2
        response = query_chatgpt([{"role": "system", "content": system_prompt_llm2_init}, {"role": "user", "content": "\n".join(list(map(str, [st.session_state.messages[0], st.session_state.messages[-1]])))}])
        st.session_state.chat_messages.append({"role": "user", "content": response})
        st.session_state.messages.append({"role": "user", "content": response})
        response_temp = "FEEDBACK" + response + "\n\n"
        with st.chat_message("assistant"):
            st.markdown(response_temp)

        # LLM 1
        response = query_chatgpt([{"role": "system", "content": system_prompt_llm1_init}] + st.session_state.messages)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.session_state.messages.append({"role": "assistant", "content": response})
        response_temp = "PROPOSED CHAIN OF THOUGHT:" + response + "\n\n"
        with st.chat_message("assistant"):
            st.markdown(response_temp)

    final_prompt = st.session_state.messages[-1]["content"]

    with st.chat_message("assistant"):
        st.markdown("Final prompt to Multion:")
        st.markdown(final_prompt)

    create_response = client_multion.sessions.create(
        url="https://google.com/",
        mode="standard",
        use_proxy=True
    )

    st.session_state.step_responses = []
    max_iters = 20

    st.session_state.current_prompt = final_prompt
    step_response = client_multion.sessions.step(
        session_id=create_response.session_id,
        cmd=st.session_state.current_prompt,
        include_screenshot=True
    )
    st.session_state.step_responses.append(step_response)
    status = step_response.status
    with st.chat_message("assistant"):
        st.markdown(step_response)

    for i in range(max_iters-1):
        can_pass = False
        if status not in ["CONTINUE", "DONE"]:
            temp_input = st.chat_input("Answer the question", key=i)
            if temp_input:
                st.session_state.current_prompt = st.session_state.current_prompt if len(temp_input) == 0 else temp_input
                step_response = client_multion.sessions.step(
                    session_id=create_response.session_id,
                    cmd=st.session_state.current_prompt,
                    include_screenshot=True
                )
                can_pass = True
        elif status == "DONE":
            can_pass = True
            break
        elif status == "CONTINUE":
            step_response = client_multion.sessions.step(
                session_id=create_response.session_id,
                cmd=st.session_state.current_prompt,
                include_screenshot=True
            )
            can_pass = True
        if can_pass:
            st.session_state.step_responses.append(step_response)
            status = step_response.status
            with st.chat_message("assistant"):
                st.markdown(step_response)
    
import os
import streamlit as st
from openai import OpenAI

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "sk-proj-iARQHbfO4GY0fZj3fzbnT3BlbkFJS4A93YuDhiWf53al8DUd"
client = OpenAI()

def query_chatgpt(prompt):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "helpful assistant"}, {"role": "system", "content": prompt}],
    )
    response = completion.choices[0].message.content
    return response

st.title("ChatGPT Query App")

# Text input for user prompt
user_prompt = st.text_input("Enter your prompt:")

# Query ChatGPT when the button is clicked
if st.button("Query ChatGPT"):
    if user_prompt:
        with st.spinner("Querying ChatGPT..."):
            response = query_chatgpt(user_prompt)
        st.success("Response received!")
        st.write(response)
    else:
        st.error("Please enter a prompt.")

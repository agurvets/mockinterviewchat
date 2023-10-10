import openai
import streamlit as st
# Audio
import wave
from audio_recorder_streamlit import audio_recorder
from IPython.display import Audio


# Set org ID and API key
openai.organization = st.secrets['openai_organization']
openai.api_key = st.secrets['openai_api_key']

st.set_page_config(page_title="Mock Interview", menu_items={"Report a Bug":"mailto:agchromatic@gmail.com"})

# handle audio

class Config:
    channels = 2
    sample_width = 2
    sample_rate = 44100

def save_wav_file(file_path, wav_bytes):
    with wave.open(file_path, 'wb') as wav_file:
        wav_file.setnchannels(Config.channels)
        wav_file.setsampwidth(Config.sample_width)
        wav_file.setframerate(Config.sample_rate)
        wav_file.writeframes(wav_bytes)

def transcribe(file_path):
    audio_file = open(file_path, 'rb')
    transcription = openai.Audio.transcribe("whisper-1", audio_file)
    return transcription['text']

def answer_call_back(voiceInput):
    save_wav_file("temp/audio.wav", voiceInput)
    try:
        input = transcribe("temp/audio.wav")
    except:
        st.session_state['assistant_messages'].append({"role":"assistant", "content":"Sorry, I didn't get that."})
        return "Please try again."
    return input

def gpt_call( placeholder_response):

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        stream=True,
        messages=st.session_state['message_history']
    )

    # process the API response
    assistant_response = ""
    for chunk in response:
        if "content" in chunk["choices"][0]["delta"]:
            text = chunk["choices"][0]["delta"]["content"]
            assistant_response += text
            placeholder_response.chat_message("assistant").markdown(assistant_response, unsafe_allow_html=True)
    
    return assistant_response

#####
st.title(":orange[GPT Mock Residency Interview]")

# initialize session state
if "user_messages" not in st.session_state:
    st.session_state["user_messages"] = []
if "assistant_messages" not in st.session_state:
    st.session_state["assistant_messages"] = ["Hi there! Let me know when you're ready and we'll get started."]
if "message_history" not in st.session_state:
    st.session_state["message_history"] = [
        {"role": "system", "content": "let's do a mock interview for medical residency. you'll ask questions and wait for my responses. if my answer isn't strong, ask follow up questions to clarify before moving on to the next question. Before the first question, tell me the interview will consist of 5 questions. After I answer 5 questions, tell me I did well, wish me luck in my interview and say 'Refresh the page to begin another mock interview'."},
        {"role":"assistant", "content": "Hi there! Let me know when you're ready and we'll get started."}    ]

if len(st.session_state["message_history"]) == 1:
    text = "Your message"
else:
    text = ""

# prompt = st.chat_input(text)
slot1=st.container()

voiceAnswer = audio_recorder(pause_threshold = 2.5, sample_rate = 44100)

if voiceAnswer:
    user_input = answer_call_back(voiceAnswer)
    st.session_state["user_messages"].append(user_input)
    st.session_state['message_history'].append({"role": "user", "content":user_input})

total_assistant_messages = len(st.session_state["assistant_messages"])
total_user_messages = len(st.session_state['user_messages'])

with slot1.container():
    print(total_assistant_messages)
    print(st.session_state['message_history'])
    for i in range(total_assistant_messages):
        st.chat_message("assistant").write(st.session_state["assistant_messages"][i])
        if total_user_messages > 0:
            st.chat_message("user").write(st.session_state["user_messages"][i])
    if total_user_messages > 0:
        placeholder_response = st.empty()
        st.session_state["assistant_messages"].append(gpt_call(placeholder_response))
        st.session_state["message_history"].append({"role":"assistant", "content": st.session_state["assistant_messages"][-1]})

# print(st.session_state['message_history'])
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
        model="gpt-4",
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
st.title(":orange[Mock Residency Interview]")

# initialize session state
if "user_messages" not in st.session_state:
    st.session_state["user_messages"] = [{"role":"user", "content": "Say 'Hi, let's get started' then ask your first question."}]
if "assistant_messages" not in st.session_state:
    st.session_state["assistant_messages"] = []
if "message_history" not in st.session_state:
    st.session_state["message_history"] = [
        {"role": "system", "content": "let's do a mock interview for medical residency in the united states. you'll ask questions and wait for my responses. if my answer isn't strong, ask follow up questions to clarify before moving on to the next question. After I answer three questions, tell me I did well and wish me luck in the real interview."},
        {"role":"user", "content": "Say 'Hi, let's get started' then ask your first question."}
    ]

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

total_user_messages = len(st.session_state["user_messages"])

with slot1.container():
    for i in range(total_user_messages):
        if i != 0:
            st.chat_message("user").write(st.session_state["user_messages"][i])
        if i < total_user_messages - 1:
            st.chat_message("assistant").write(st.session_state["assistant_messages"][i])
        elif i == total_user_messages - 1:
            placeholder_response = st.empty()
            st.session_state["assistant_messages"].append(gpt_call(placeholder_response))
            st.session_state["message_history"].append({"role":"assistant", "content": st.session_state["assistant_messages"][-1]})

print(st.session_state['message_history'])
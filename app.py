import streamlit as st
import speech_recognition as sr
from streamlit_chat import message
import openai
from gtts import gTTS
import os

# Audio
import wave
from audio_recorder_streamlit import audio_recorder
from IPython.display import Audio

# Set org ID and API key
openai.organization = st.secrets['openai_organization']
openai.api_key = st.secrets['openai_api_key']

st.set_page_config(page_title="Mock Interview")

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

def get_llm_response(prompt):
    st.session_state['messages'].append({"role": "user", "content": prompt})

    completion = openai.ChatCompletion.create(
        model=model,
        stream=True,
        messages=st.session_state['messages']
    )
    st.session_state['messages'].append({"role": "assistant", "content": ""})
    st.session_state['generated'].append({""})
    print("last generated message:")
    print(st.session_state['generated'][len(st.session_state['generated'])-1])
    for chunk in completion:
        print(st.session_state['generated'])
        chunk_message = chunk['choices'][0]['delta'].get('content', "")
        print(chunk_message)
        iterator = iter(st.session_state['generated'][len(st.session_state['generated'])-1])
        st.session_state['generated'][len(st.session_state['generated'])-1] = {next(iterator) + chunk_message}
    # response = completion.choices[0].message.content
    # st.session_state['messages'].append({"role": "assistant", "content": response})

    # print(st.session_state['messages'])
    # total_tokens = completion.usage.total_tokens
    # prompt_tokens = completion.usage.prompt_tokens
    # completion_tokens = completion.usage.completion_tokens
    st.session_state['messages'].append({"role": "assistant", "content": st.session_state['generated'][len(st.session_state['generated'])-1]})
    return st.session_state['messages'][-1]['content']
    # return response, total_tokens, prompt_tokens, completion_tokens


def answer_call_back(voiceInput):
    save_wav_file("temp/audio.wav", voiceInput)
    try:
        input = transcribe("temp/audio.wav")
    except:
        st.session_state['generated'].append("Sorry, I didn't get that.")
        return "Please try again."
    return input
        # # OpenAI answer and save to history
        # llm_answer = st.session_state.jd_screen.run(input)
        # # speech synthesis and speak out
        # audio_file_path = synthesize_speech(llm_answer)
        # # create audio widget with autoplay
        # audio_widget = Audio(audio_file_path, autoplay=True)
        # # save audio data to history
        # st.session_state.jd_history.append(
        #     Message("ai", llm_answer)
        # )
        # st.session_state.token_count += cb.total_tokens
        # return audio_widget


st.title('System Design Interviews with ChatGPT')

# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": "I'm a software engineer applying for a job at your company, and you're an expert software architect conducting a system design interview. Ask me a system design interview question, then wait for my response. Feel free to ask one follow up question for each response I give you or to discuss my answer. Don't give me the right answer, but guide me in a better direction."}
    ]
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []

# Sidebar - let user choose model, show total cost of current conversation, and let user clear the current conversation
st.sidebar.title("Settings")
# model_name = st.sidebar.radio("Choose a model:", ("GPT-4", "GPT-3.5"))
clear_button = st.sidebar.button("Clear Conversation", key="clear")

def clear():
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [
        {"role": "system", "content": "I'm a software engineer applying for a job at your company, and you're an expert software architect conducting a system design interview. Ask me a system design interview question, then wait for my response. Feel free to ask one follow up question for each response I give you or to discuss my answer. Don't give me the right answer, but guide me in a better direction."}
    ]
    st.session_state['number_tokens'] = []
    st.session_state['model_name'] = []

# reset everything
if clear_button:
    clear()

# Map model names to OpenAI model IDs
# if model_name == "GPT-3.5":
#     model = "gpt-3.5-turbo"
# else:
model = "gpt-4"

# Choose input mode
input_mode = st.radio("Choose your input mode", ["Type", "Speak"])

if st.button('Start'):
    user_input="Let's get started."
    output = get_llm_response(user_input)
    st.session_state['past'].append(user_input)
    st.session_state['generated'].append(output)

if input_mode == "Speak":
    st.write("Please speak your answer...")
    # Here, you can send the audio input to the chatbot and display the response
    # But for the main chat interface, we'll stick to the typing mode

# container for chat history
response_container = st.container()
# container for text box
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You:", key='input', height=100)
        submit_button = st.form_submit_button(label='Send')
    if input_mode == "Speak":
        voiceAnswer = audio_recorder(pause_threshold = 2.5, sample_rate = 44100)
        #st.warning("An UnboundLocalError will occur if the microphone fails to record.")
        if voiceAnswer:
            user_input = answer_call_back(voiceAnswer)
            st.session_state['past'].append(user_input)
            get_llm_response
            # output = get_llm_response(user_input)
            # st.session_state['generated'].append(output)

    if submit_button and user_input:
        output = get_llm_response(user_input)
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))

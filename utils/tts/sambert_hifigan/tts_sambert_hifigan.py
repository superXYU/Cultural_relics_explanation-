import streamlit as st
from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

# pip install kantts -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
# pip install pytorch_wavelets tensorboardX scipy==1.12.0


@st.cache_resource
def get_tts_model():
    model_id = "damo/speech_sambert-hifigan_tts_zhisha_zh-cn_16k"
    sambert_hifigan_tts = pipeline(task=Tasks.text_to_speech, model=model_id)
    return sambert_hifigan_tts


def gen_tts_wav(sambert_hifigan_tts, text, wav_path):
    print(f"gerning tts for {wav_path} ....")
    output = sambert_hifigan_tts(input=text)
    wav = output[OutputKeys.OUTPUT_WAV]
    with open(wav_path, "wb") as f:
        f.write(wav)
    print(f"gen tts for {wav_path} done!....")

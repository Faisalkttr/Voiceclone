import os
import tempfile

import streamlit as st
from gradio_client import Client, handle_file

st.set_page_config(page_title="Voice Clone", page_icon="🎙️")
st.title("🎙️ Voice Clone")
st.caption("Give a short reference voice + some text. Get the text spoken in that voice.")

HF_TOKEN = None
try:
    HF_TOKEN = st.secrets.get("HF_TOKEN")
except Exception:
    pass

LANGS = {
    "English": "en", "Hindi": "hi", "Spanish": "es", "French": "fr",
    "German": "de", "Italian": "it", "Portuguese": "pt", "Polish": "pl",
    "Turkish": "tr", "Russian": "ru", "Dutch": "nl", "Czech": "cs",
    "Arabic": "ar", "Chinese": "zh-cn", "Japanese": "ja", "Korean": "ko",
    "Hungarian": "hu",
}


def find_audio(result):
    items = result if isinstance(result, (list, tuple)) else [result]
    for x in items:
        if isinstance(x, dict):
            x = x.get("path") or x.get("value")
        if isinstance(x, str) and x.lower().endswith((".wav", ".mp3", ".flac")):
            return x
    return None


# Each backend: (space id, supports language choice, call function)
def call_tonyassi(client, text, lang, ref_path):
    # English-only space: clone(text, audio)
    return client.predict(text, handle_file(ref_path), api_name="/clone")


def call_coqui(client, text, lang, ref_path):
    return client.predict(text, lang, handle_file(ref_path), None, False, False, False, True,
                          api_name="/predict")


BACKENDS = [
    ("tonyassi/voice-clone", False, call_tonyassi),
    ("coqui/xtts", True, call_coqui),
]

lang_name = st.selectbox("Language of the text", list(LANGS), index=0,
                         help="Only English works on the main backend; other languages need the fallback (coqui/xtts) to be online.")

st.subheader("1. Reference voice")
st.write("Use 6–30 seconds of clean speech, no background noise or music.")
tab_up, tab_mic = st.tabs(["Upload", "Record"])
with tab_up:
    uploaded = st.file_uploader("Upload audio", type=["wav", "mp3", "m4a", "ogg", "flac"])
with tab_mic:
    recorded = st.audio_input("Record your voice")

ref = recorded or uploaded
if ref:
    st.audio(ref)

st.subheader("2. Text to speak")
text = st.text_area("Text", height=150, max_chars=2000,
                    placeholder="Type what the cloned voice should say...")

consent = st.checkbox(
    "I confirm this is my own voice, or I have the speaker's permission to clone it."
)

if st.button("Generate", type="primary", disabled=not (ref and text.strip() and consent)):
    tmp_path = None
    audio_bytes = None
    errors = []
    try:
        suffix = os.path.splitext(getattr(ref, "name", "ref.wav"))[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(ref.getvalue())
            tmp_path = f.name

        for space_id, multilingual, fn in BACKENDS:
            if lang_name != "English" and not multilingual:
                errors.append(f"{space_id}: skipped (English only)")
                continue
            with st.spinner(f"Cloning voice via {space_id}... first request can take a minute."):
                try:
                    client = Client(space_id, token=HF_TOKEN) if HF_TOKEN else Client(space_id)
                    result = fn(client, text.strip(), LANGS[lang_name], tmp_path)
                    path = find_audio(result)
                    if not path:
                        raise RuntimeError(f"unexpected response: {result}")
                    with open(path, "rb") as a:
                        audio_bytes = a.read()
                    st.caption(f"Generated with {space_id}")
                    break
                except Exception as e:
                    errors.append(f"{space_id}: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    if audio_bytes:
        st.success("Done!")
        st.audio(audio_bytes)
        st.download_button("Download", audio_bytes, "cloned_voice.wav", "audio/wav")
    else:
        st.error("All backends failed.")
        for e in errors:
            st.write(f"- {e}")
        st.info("Free Spaces can be busy, asleep or broken. Add a free HF_TOKEN in Streamlit secrets (higher quota), wait a minute and retry.")

st.divider()
st.caption("Only clone voices you own or have permission to use. Do not use for impersonation or fraud.")

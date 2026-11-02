import os
import tempfile

import streamlit as st
from gradio_client import Client, handle_file

st.set_page_config(page_title="Voice Clone", page_icon="🎙️")
st.title("🎙️ Voice Clone")
st.caption("Give a short reference voice + some text. Get the text spoken in that voice.")

# Free backend: a public XTTS-v2 Space on Hugging Face (change if it goes down)
SPACE_ID = st.sidebar.text_input("Hugging Face Space", "coqui/xtts")
HF_TOKEN = st.secrets.get("HF_TOKEN", None) if hasattr(st, "secrets") else None

LANGS = {
    "English": "en", "Hindi": "hi", "Spanish": "es", "French": "fr",
    "German": "de", "Italian": "it", "Portuguese": "pt", "Polish": "pl",
    "Turkish": "tr", "Russian": "ru", "Dutch": "nl", "Czech": "cs",
    "Arabic": "ar", "Chinese": "zh-cn", "Japanese": "ja", "Korean": "ko",
    "Hungarian": "hu",
}
lang_name = st.selectbox("Language of the text", list(LANGS), index=0)

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
text = st.text_area("Text", height=150, max_chars=500,
                    placeholder="Type what the cloned voice should say...")

consent = st.checkbox(
    "I confirm this is my own voice, or I have the speaker's permission to clone it."
)

if st.button("Generate", type="primary", disabled=not (ref and text.strip() and consent)):
    with st.spinner("Cloning voice... the first request can take a minute while the Space wakes up."):
        tmp_path = None
        try:
            suffix = os.path.splitext(getattr(ref, "name", "ref.wav"))[1] or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(ref.getvalue())
                tmp_path = f.name

            client = Client(SPACE_ID, hf_token=HF_TOKEN) if HF_TOKEN else Client(SPACE_ID)
            result = client.predict(
                text.strip(),                 # prompt
                LANGS[lang_name],             # language
                handle_file(tmp_path),        # reference audio
                None,                         # mic file (unused)
                False,                        # use_mic
                False,                        # cleanup_reference
                False,                        # auto_detect_language
                True,                         # agree to terms
                api_name="/predict",
            )

            # Result is a tuple/list; find the generated audio file path
            items = result if isinstance(result, (list, tuple)) else [result]
            audio_path = next(
                (x for x in items if isinstance(x, str) and x.lower().endswith((".wav", ".mp3", ".flac"))),
                None,
            )
            if not audio_path:
                st.error(f"Unexpected response from the Space: {result}")
            else:
                with open(audio_path, "rb") as a:
                    audio_bytes = a.read()
                st.success("Done!")
                st.audio(audio_bytes)
                st.download_button("Download", audio_bytes, "cloned_voice.wav", "audio/wav")
        except Exception as e:
            st.error(f"Generation failed: {e}")
            st.info("The free Space may be busy, asleep or changed. Try again, or switch the Space ID in the sidebar.")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

st.divider()
st.caption("Only clone voices you own or have permission to use. Do not use for impersonation or fraud.")

# Voice Clone (free, Streamlit + Hugging Face Space)

Upload or record a reference voice, type text, get speech in that voice.

## Deploy (free)
1. Create a new GitHub repo and add `app.py`, `requirements.txt`, `README.md`.
2. Go to https://share.streamlit.io -> **New app** -> pick the repo, branch `main`, file `app.py` -> **Deploy**.
3. (Optional) If you hit rate limits, create a free token at https://huggingface.co/settings/tokens, then in Streamlit **Settings -> Secrets** add:
   ```
   HF_TOKEN = "hf_xxx"
   ```

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- The model runs on the free `coqui/xtts` Hugging Face Space, not on Streamlit (no GPU there).
- If that Space is down, paste another XTTS/voice-clone Space ID in the sidebar. The API arguments may differ, so adjust `client.predict(...)` in `app.py`.
- Use only your own voice or voices you have permission to clone.

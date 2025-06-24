# Viral Video Club - Bootcamp Social Media Dashboard

A Streamlit dashboard for visualising student social growth and engagement.

## Setup

1. Clone this repo.
2. Install dependencies:
    ```
    pip install -r requirements.txt
    ```
3. Set up `.streamlit/secrets.toml` with your Google Service Account.  
   (See example in `.streamlit/secrets.example.toml`)
4. Run locally:
    ```
    streamlit run app.py
    ```

## Deploy

- Push to GitHub.
- Connect to [Streamlit Cloud](https://streamlit.io/cloud).
- Set `secrets.toml` in the Cloud dashboard.

---

**Caution:** Never commit `secrets.toml` or your service account JSON to GitHub!

---

## 7. Pitfalls & Pro Tips

- **No absolute file paths**. All creds/secrets via secrets.toml or env vars.
- Streamlit Cloud **doesn't support local files** for keys, only secrets.
- Large DataFrames or charts: cache where possible.
- Use `@st.cache_data` for Google Sheet fetches.
- If your dashboard throws "FileNotFoundError" or "No such file", 99% of the time, you hardcoded a local file path.
- For security, keep your Google Sheet read-only unless you need to write.

---

## 8. Example: Refactored Credential Handling

Here’s a simple, clean pattern for Streamlit Cloud/GitHub (just replace your credential bits):

```python
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Load creds from Streamlit secrets (Streamlit Cloud-friendly!)
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(creds)

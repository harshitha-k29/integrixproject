# Integrix — Data Quality Studio

## Run locally (Windows PowerShell)

Open PowerShell in this `Integrix` folder, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

If your `.venv` already exists and works, activate it and run only:
```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Optional Groq AI assistant

Detection and safe repair work without an API key. To enable the optional AI explanation:

1. Create a new Groq API key in your Groq account.
2. In this project folder, make a copy of `.env.example` and name the copy `.env`.
3. Open `.env` and replace the example value:
   `GROQ_API_KEY=your_new_key_here`
4. Make sure `.env` is inside the **same inner `Integrix` folder** as `streamlit_app.py` and `groq_client.py`.
5. Restart Streamlit. In the sidebar, click **Test Groq connection**. A success message confirms the key and API are working.

The app sends Groq only issue counts and quality metrics, not the uploaded dataset rows. The integration uses HTTPS requests directly; it does not use the Groq Python SDK.

**Never upload or commit `.env` to GitHub.** `.gitignore` already excludes it.

## Repair policy

- High-confidence label, date-format and safe phone-format fixes can be applied automatically.
- Missing values, duplicate rows, invalid emails, outliers and ambiguous values remain in the review queue.
- Duplicate rows are not silently deleted.
- Every automatic change appears in the audit log.

## Supported uploads

CSV and Excel (`.xlsx`, `.xls`). The included sample is `sample_data/messy_customers.csv`.


## About Integrix

Integrix helps users inspect spreadsheet quality, identify common data issues, apply cautious repairs, review uncertain changes, compare quality scores, and export a cleaned dataset with an audit trail. It is designed to make data cleaning more transparent and easier to verify.

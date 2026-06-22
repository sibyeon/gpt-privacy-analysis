# 🔒 GPT Privacy Risk Dashboard

**By Sang In Byeon** | ASU Data Science | CSE 467 — Data & Information Security

## 🔗 Live App
👉 [Click here to view the live interactive dashboard](https://a6wrzdrxbhdbu8ppd6wpt6.streamlit.app/)

## 📌 Project Overview
This project investigates privacy risks in the custom ChatGPT GPT ecosystem by analyzing how domain-specific GPTs expose data collection pathways, external API integrations, and privacy disclosures across 15 categories.

**420 GPTs were analyzed across categories including:** Finance, Education, Travel, Development, Utility, Design, Games, Legal, Business, Career, News, Physical Health, Mindfulness, Real Estate, and Entertainment.

## 🔍 What We Did
- Built a **Python web crawler** using BeautifulSoup to collect GPT metadata from public directories
- Reverse-engineered ChatGPT's backend manifest system to inspect API Action specifications
- Scored each GPT on a **0–5 privacy risk scale** based on data sensitivity and external API exposure
- Performed **canary testing** — inserting unique encrypted strings into GPT conversations to test whether ChatGPT uses conversation data for model training
- Built an interactive Streamlit dashboard to visualize all findings

## 📊 Key Findings
- **95% of GPTs (399/420)** had no measurable Action-based privacy risk
- **Finance was the highest risk category** — involving portfolio data, investment context, and third-party API integrations
- **No canary strings were recovered** — suggesting ChatGPT does not visibly exfiltrate conversation data to external parties under tested conditions
- Many GPTs lacked tool-specific privacy policies, creating a **transparency gap** between functionality and disclosure

## 🛠️ Tech Stack
- **Python** — Pandas, Plotly, Streamlit
- **Web Crawling** — Requests, BeautifulSoup
- **Security Research** — Canary testing, manifest inspection, API analysis
- **Deployment** — Streamlit Community Cloud

## 📁 Project Structure

gpt-privacy-analysis/

├── app.py                    # Streamlit dashboard

├── general_gpts.csv          # Dataset 1 — manually collected GPTs

├── lists_gpts.csv            # Dataset 2 — crawler-collected GPTs

├── Crawler_for_Manifest_Files.ipynb  # Web crawler notebook

├── ManifestAnalysis.ipynb    # Analysis notebook

└── requirements.txt

## 🚀 Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 👥 Team
Built as a group project for CSE 467: Data & Information Security at Arizona State University.
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="GPT Privacy Risk Dashboard",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 14px 18px;
    }
    div[data-testid="stMetricValue"]  { color: #58a6ff; font-size: 2rem; }
    div[data-testid="stMetricLabel"]  { color: #8b949e; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111820;
        border-right: 1px solid #30363d;
    }
    section[data-testid="stSidebar"] h2 { color: #58a6ff; }

    /* Dividers */
    hr { border-color: #30363d; margin: 1rem 0; }

    /* Info box */
    .info-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        border-radius: 6px;
        padding: 18px 22px;
        margin-bottom: 18px;
    }
    .info-box h4 { margin-top: 0; color: #e6edf3; }
    .info-box p  { color: #c9d1d9; margin-bottom: 0.5rem; }

    /* Page title */
    h1 { color: #e6edf3 !important; }
    h2, h3 { color: #cdd9e5 !important; }

    /* DataFrames */
    div[data-testid="stDataFrame"] { border: 1px solid #30363d; border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Plotly dark theme helper ────────────────────────────────────────────────────
BG     = "#0d1117"
BG2    = "#161b22"
GRID   = "#21262d"
TEXT   = "#c9d1d9"
TITLE  = "#e6edf3"

def dark_layout(**kwargs):
    base = dict(
        paper_bgcolor=BG,
        plot_bgcolor=BG2,
        font=dict(color=TEXT, size=12),
        title_font=dict(color=TITLE, size=15),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
        legend=dict(bgcolor=BG2, bordercolor=GRID, borderwidth=1),
        margin=dict(t=50, b=30, l=30, r=20),
    )
    base.update(kwargs)
    return base

RISK_COLORS = {
    "None":     "#484f58",
    "Low":      "#3fb950",
    "Medium":   "#d29922",
    "High":     "#f85149",
    "Critical": "#ff7b72",
}
RISK_SCALE = [[0, "#3fb950"], [0.4, "#d29922"], [0.7, "#f85149"], [1.0, "#ff7b72"]]
TIER_ORDER = ["None", "Low", "Medium", "High", "Critical"]


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # ── general_gpts.csv ──────────────────────────────────────────────────────
    gen = pd.read_csv("general_gpts.csv", dtype=str, on_bad_lines="warn")
    # columns: url, topic, canary, tested_gizmo, privacy_risk, reasoning, date_sent_canary, canary_recovered

    def extract_name(val):
        if not isinstance(val, str) or not val.strip():
            return "Unknown"
        val = val.strip()
        if val.startswith("https://"):
            slug = val.rstrip("/").split("/")[-1]          # g-XXXXX-some-name
            parts = slug.split("-", 2)
            return parts[2].replace("-", " ").title() if len(parts) >= 3 else slug
        return val.replace("ChatGPT - ", "").strip()

    gen["name"]   = gen["url"].apply(extract_name)
    gen["source"] = "General"

    # ── lists_gpts.csv ────────────────────────────────────────────────────────
    lst = pd.read_csv("lists_gpts.csv", dtype=str, on_bad_lines="warn")
    # columns: name, gizmo, url, topic, canary, date_sent_canary, tested_gizmo, privacy_risk, reasoning, canary_recovered
    lst["source"] = "Lists"

    # ── Align to common schema ────────────────────────────────────────────────
    KEEP = ["name", "topic", "privacy_risk", "reasoning", "tested_gizmo", "canary_recovered", "source"]
    df = pd.concat([gen[KEEP], lst[KEEP]], ignore_index=True)

    # ── Clean ─────────────────────────────────────────────────────────────────
    df["privacy_risk"]    = pd.to_numeric(df["privacy_risk"], errors="coerce").fillna(0)
    df["topic"]           = df["topic"].str.strip().str.title().fillna("Unknown")
    df["name"]            = df["name"].str.strip().fillna("Unknown")
    df["reasoning"]       = (df["reasoning"].fillna("")
                               .str.replace(r"[\r\n]+", " ", regex=True)
                               .str.strip())
    df["tested_gizmo"]    = df["tested_gizmo"].fillna("N/A").str.strip()
    df["canary_recovered"] = df["canary_recovered"].fillna("").str.strip()

    # ── Derived ───────────────────────────────────────────────────────────────
    def risk_tier(s):
        if s == 0:   return "None"
        if s < 2:    return "Low"
        if s < 3:    return "Medium"
        if s < 4:    return "High"
        return "Critical"

    df["risk_tier"]          = df["privacy_risk"].apply(risk_tier)
    df["api_tested"]         = df["tested_gizmo"].str.startswith("http")
    df["canary_not_recovered"] = df["canary_recovered"].str.contains("Not Recovered", na=False)

    return df


df = load_data()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔒 GPT Privacy")
    st.markdown("### Risk Dashboard")
    st.markdown("---")
    page = st.radio(
        "Navigate to",
        ["Overview", "By Category", "GPT Explorer", "Canary Testing"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(f"📊 **{len(df):,}** total GPTs")
    st.markdown(f"🗂️ **{df['topic'].nunique()}** categories")
    st.markdown(f"🔬 **{int(df['api_tested'].sum())}** API-tested")
    st.markdown(f"⚠️ **{int((df['privacy_risk'] > 0).sum())}** with risk > 0")
    st.markdown("---")
    st.caption("Data sources: general_gpts.csv · lists_gpts.csv")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.markdown("# 🔒 GPT Privacy Risk Dashboard")
    st.markdown("*Analysis of privacy risks in custom ChatGPT GPTs across multiple categories*")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    risky = df[df["privacy_risk"] > 0]
    with k1: st.metric("Total GPTs",          f"{len(df):,}")
    with k2: st.metric("GPTs with Risk",       f"{len(risky):,}")
    with k3: st.metric("Overall Avg Risk",     f"{df['privacy_risk'].mean():.3f}")
    with k4: st.metric("API-Tested GPTs",      f"{int(df['api_tested'].sum())}")
    with k5: st.metric("High / Critical Risk", f"{int((df['privacy_risk'] >= 4).sum())}")

    st.markdown("---")

    # ── Row 1 ─────────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        counts = (df["risk_tier"]
                    .value_counts()
                    .reindex(TIER_ORDER, fill_value=0)
                    .reset_index())
        counts.columns = ["Level", "Count"]

        fig = go.Figure()
        for _, row in counts.iterrows():
            fig.add_trace(go.Bar(
                x=[row["Level"]], y=[row["Count"]],
                marker_color=RISK_COLORS[row["Level"]],
                showlegend=False,
                text=[row["Count"]], textposition="outside",
                textfont=dict(color=TEXT),
            ))
        fig.update_layout(
            title="Privacy Risk Distribution",
            yaxis_title="Number of GPTs",
            height=370,
            **dark_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        src_tier = df.groupby(["source", "risk_tier"]).size().reset_index(name="count")
        fig2 = px.bar(
            src_tier, x="source", y="count", color="risk_tier",
            color_discrete_map=RISK_COLORS,
            category_orders={"risk_tier": TIER_ORDER},
            title="Risk Distribution by Dataset",
            labels={"source": "Dataset", "count": "Count", "risk_tier": "Risk Level"},
        )
        fig2.update_layout(height=370, **dark_layout())
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2 ─────────────────────────────────────────────────────────────────
    c3, c4 = st.columns(2)

    with c3:
        cat_avg = (df.groupby("topic")["privacy_risk"]
                     .mean()
                     .sort_values(ascending=True)
                     .reset_index())
        cat_avg.columns = ["Category", "Avg Risk"]

        fig3 = px.bar(
            cat_avg, x="Avg Risk", y="Category", orientation="h",
            color="Avg Risk", color_continuous_scale=RISK_SCALE,
            range_color=[0, 5],
            title="Average Risk Score by Category",
            text="Avg Risk",
        )
        fig3.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig3.update_layout(
            height=460, showlegend=False, coloraxis_showscale=False,
            xaxis_range=[0, 5.4],
            **dark_layout(),
        )
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        cat_tree = df.groupby("topic").agg(
            count=("name", "count"),
            avg_risk=("privacy_risk", "mean"),
        ).reset_index()

        fig4 = px.treemap(
            cat_tree, path=["topic"], values="count",
            color="avg_risk",
            color_continuous_scale=RISK_SCALE,
            range_color=[0, 5],
            title="GPT Count & Avg Risk by Category",
            hover_data={"avg_risk": ":.2f"},
        )
        fig4.update_layout(height=460, **dark_layout())
        st.plotly_chart(fig4, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — BY CATEGORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "By Category":
    st.markdown("# 📊 Privacy Risk by Category")

    stats = df.groupby("topic").agg(
        Total         = ("name",          "count"),
        Avg_Risk      = ("privacy_risk",  "mean"),
        Max_Risk      = ("privacy_risk",  "max"),
        GPTs_w_Risk   = ("privacy_risk",  lambda x: (x > 0).sum()),
        API_Tested    = ("api_tested",    "sum"),
    ).round(2).reset_index()
    stats["Risky_%"] = (stats["GPTs_w_Risk"] / stats["Total"] * 100).round(1)
    stats = stats.sort_values("Avg_Risk", ascending=False)
    stats.columns = ["Category", "Total GPTs", "Avg Risk", "Max Risk",
                     "GPTs w/ Risk", "API Tested", "Risky %"]

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            stats.sort_values("Avg Risk"), x="Avg Risk", y="Category",
            orientation="h", color="Avg Risk",
            color_continuous_scale=RISK_SCALE, range_color=[0, 5],
            text="Avg Risk",
            title="Average Privacy Risk Score by Category",
            hover_data=["Total GPTs", "GPTs w/ Risk", "Risky %"],
        )
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(
            height=520, showlegend=False, coloraxis_showscale=False,
            xaxis_range=[0, 4.5],
            **dark_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig2 = px.scatter(
            stats, x="Total GPTs", y="Avg Risk",
            size="GPTs w/ Risk", color="Avg Risk",
            color_continuous_scale=RISK_SCALE, range_color=[0, 5],
            hover_name="Category",
            hover_data=["Total GPTs", "GPTs w/ Risk", "Risky %", "API Tested"],
            title="Category Size vs. Avg Risk  (bubble = # risky GPTs)",
            text="Category",
        )
        fig2.update_traces(textposition="top center", textfont=dict(size=10, color=TEXT))
        fig2.update_layout(
            height=520, showlegend=False, coloraxis_showscale=False,
            **dark_layout(),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Summary Table")
    st.dataframe(stats.reset_index(drop=True), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### Category Deep-Dive")
    selected = st.selectbox("Choose a category", sorted(df["topic"].unique()))
    sub = df[df["topic"] == selected].copy()

    ca, cb = st.columns([1, 2])
    with ca:
        st.metric("GPTs in category", len(sub))
        st.metric("Avg Risk",         f"{sub['privacy_risk'].mean():.2f}")
        st.metric("Max Risk",         f"{sub['privacy_risk'].max():.1f}")
        st.metric("API-Tested",       int(sub["api_tested"].sum()))

    with cb:
        td = (sub["risk_tier"]
                .value_counts()
                .reindex(TIER_ORDER, fill_value=0)
                .reset_index())
        td.columns = ["Tier", "Count"]
        fig3 = px.bar(
            td, x="Tier", y="Count", color="Tier",
            color_discrete_map=RISK_COLORS,
            title=f"Risk Distribution — {selected}",
        )
        fig3.update_layout(height=280, showlegend=False, **dark_layout())
        st.plotly_chart(fig3, use_container_width=True)

    tbl = (sub[["name", "privacy_risk", "risk_tier", "reasoning", "api_tested"]]
             .rename(columns={
                 "name": "Name", "privacy_risk": "Risk Score",
                 "risk_tier": "Level", "reasoning": "Reasoning",
                 "api_tested": "API Tested",
             })
             .sort_values("Risk Score", ascending=False)
             .reset_index(drop=True))
    st.dataframe(tbl, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — GPT EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "GPT Explorer":
    st.markdown("# 🔍 GPT Explorer")
    st.markdown("Search and filter all GPTs in the combined dataset.")

    f1, f2, f3 = st.columns([2, 1.5, 1])
    with f1:
        search = st.text_input("Search name or reasoning", placeholder="e.g. finance, API, health…")
    with f2:
        cats = ["All Categories"] + sorted(df["topic"].unique())
        sel_cat = st.selectbox("Category", cats)
    with f3:
        source_opts = ["Both", "General", "Lists"]
        sel_src = st.radio("Dataset", source_opts, horizontal=True)

    f4, f5 = st.columns([2, 1])
    with f4:
        min_risk = st.slider("Minimum Risk Score", 0.0, 5.0, 0.0, 0.5)
    with f5:
        tested_only = st.checkbox("Show only API-tested GPTs")

    flt = df.copy()
    if search:
        mask = (flt["name"].str.contains(search, case=False, na=False) |
                flt["reasoning"].str.contains(search, case=False, na=False))
        flt = flt[mask]
    if sel_cat != "All Categories":
        flt = flt[flt["topic"] == sel_cat]
    if sel_src != "Both":
        flt = flt[flt["source"] == sel_src]
    flt = flt[flt["privacy_risk"] >= min_risk]
    if tested_only:
        flt = flt[flt["api_tested"]]

    st.markdown(f"**{len(flt):,}** GPTs match your filters  *(of {len(df):,} total)*")

    display = (flt[["name", "topic", "privacy_risk", "risk_tier", "reasoning", "api_tested", "source"]]
                 .rename(columns={
                     "name": "Name", "topic": "Category",
                     "privacy_risk": "Risk Score", "risk_tier": "Risk Level",
                     "reasoning": "Reasoning", "api_tested": "API Tested",
                     "source": "Source",
                 })
                 .sort_values("Risk Score", ascending=False)
                 .reset_index(drop=True))

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "Risk Score": st.column_config.NumberColumn(format="%.1f"),
            "API Tested": st.column_config.CheckboxColumn(disabled=True),
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — CANARY TESTING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Canary Testing":
    st.markdown("# 🐦 Canary Testing")

    st.markdown("""
<div class="info-box">
<h4>What is Canary Testing?</h4>
<p>
<b>Canary token testing</b> is a privacy auditing technique where a unique, encrypted identifier is
embedded in a conversation with a GPT. If that token later appears in external traffic — such as
third-party API calls or remote server logs — it confirms the GPT is exfiltrating conversation data
to outside parties without the user's knowledge.
</p>
<p>
<b>How this study works:</b>
</p>
<p>
1. Each GPT received a unique <b>encrypted canary token</b> as part of a test conversation.<br>
2. GPTs that made external API calls were flagged for <b>API Testing</b> — researchers examined exactly
   what data was sent and to whom.<br>
3. A <b>Privacy Risk Score (0–5)</b> was assigned based on the sensitivity of the data found in those
   API calls.<br>
4. The <i>canary_recovered</i> field records whether the token was detected in any external traffic.
   <b>"Not Recovered"</b> means the canary was not seen externally — a sign the GPT did not leak it.
</p>
</div>
""", unsafe_allow_html=True)

    # ── Risk Scale reference ───────────────────────────────────────────────────
    with st.expander("Privacy Risk Score Reference (0–5)"):
        scale_df = pd.DataFrame({
            "Score":       ["0",     "1–1.5", "2–2.5", "3",      "3.5–4",   "4.5–5"],
            "Level":       ["None",  "Low",   "Medium", "Medium", "High",    "Critical"],
            "Description": [
                "No external API calls detected. No privacy risk.",
                "Expected, benign API calls (public data lookup). Minimal risk.",
                "API calls that may collect limited user data (e.g., video IDs, search queries).",
                "APIs exposing moderate user data such as location, preferences, or search history.",
                "Suspicious endpoints; conversation context or personal data potentially exfiltrated.",
                "Clear exfiltration of sensitive conversation data to third-party servers.",
            ],
        })
        st.dataframe(scale_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    api_tested_n  = int(df["api_tested"].sum())
    not_recovered = int(df["canary_not_recovered"].sum())
    risky_n       = int((df["privacy_risk"] > 0).sum())
    high_risk_n   = int((df["privacy_risk"] >= 4).sum())

    with k1: st.metric("Canaries Sent",        f"{len(df):,}")
    with k2: st.metric("API-Tested GPTs",      f"{api_tested_n}")
    with k3: st.metric("'Not Recovered' Canaries", f"{not_recovered}")
    with k4: st.metric("GPTs with Risk > 0",   f"{risky_n}")

    st.markdown("---")

    # ── API-tested risky GPTs — bar chart ─────────────────────────────────────
    risky_tested = df[df["api_tested"] & (df["privacy_risk"] > 0)].sort_values(
        "privacy_risk", ascending=False
    )

    st.markdown("### GPTs API-Tested and Found Risky")

    if not risky_tested.empty:
        fig = px.bar(
            risky_tested, x="name", y="privacy_risk",
            color="privacy_risk",
            color_continuous_scale=RISK_SCALE, range_color=[0, 5],
            hover_data={"topic": True, "reasoning": True, "privacy_risk": ":.1f"},
            labels={"name": "GPT Name", "privacy_risk": "Risk Score"},
            title=f"Risk Scores for All API-Tested GPTs ({len(risky_tested)} with risk > 0)",
        )
        fig.update_layout(
            height=430, xaxis_tickangle=-40,
            yaxis_range=[0, 5.6],
            yaxis_title="Privacy Risk Score (0–5)",
            xaxis_title="",
            coloraxis_showscale=False,
            **dark_layout(),
        )
        st.plotly_chart(fig, use_container_width=True)

        risky_tbl = (risky_tested[["name", "topic", "privacy_risk", "risk_tier", "reasoning"]]
                       .rename(columns={
                           "name": "Name", "topic": "Category",
                           "privacy_risk": "Risk Score", "risk_tier": "Level",
                           "reasoning": "Reasoning",
                       })
                       .reset_index(drop=True))
        st.dataframe(risky_tbl, use_container_width=True, hide_index=True)
    else:
        st.info("No API-tested GPTs with a risk score above 0 found in the dataset.")

    st.markdown("---")

    # ── Canary status ─────────────────────────────────────────────────────────
    st.markdown("### Canary Token Recovery Status")

    c1, c2 = st.columns([1, 2])

    with c1:
        pie_df = pd.DataFrame({
            "Status": ["Not Recovered", "No Status Recorded"],
            "Count":  [not_recovered, len(df) - not_recovered],
        })
        fig_pie = go.Figure(go.Pie(
            labels=pie_df["Status"],
            values=pie_df["Count"],
            hole=0.45,
            marker_colors=["#3fb950", "#484f58"],
            textinfo="label+percent",
            textfont=dict(color=TEXT, size=12),
        ))
        fig_pie.update_layout(
            title="Canary Recovery Status",
            height=320, showlegend=False,
            paper_bgcolor=BG, font=dict(color=TEXT),
            title_font=dict(color=TITLE, size=14),
            margin=dict(t=45, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        not_rec_df = (df[df["canary_not_recovered"]]
                        [["name", "topic", "privacy_risk", "reasoning"]]
                        .rename(columns={
                            "name": "Name", "topic": "Category",
                            "privacy_risk": "Risk Score", "reasoning": "Reasoning",
                        })
                        .reset_index(drop=True))
        st.markdown(f"**{len(not_rec_df)} GPTs** had their canary marked as **'Not Recovered'** — "
                    "meaning the token was not detected in any external traffic, indicating "
                    "the GPT did not exfiltrate it to third parties.")
        if not not_rec_df.empty:
            st.dataframe(not_rec_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── All API-tested GPTs ────────────────────────────────────────────────────
    st.markdown("### All API-Tested GPTs (with and without risk)")
    all_tested = (df[df["api_tested"]]
                    [["name", "topic", "privacy_risk", "risk_tier", "reasoning"]]
                    .rename(columns={
                        "name": "Name", "topic": "Category",
                        "privacy_risk": "Risk Score", "risk_tier": "Level",
                        "reasoning": "Reasoning",
                    })
                    .sort_values("Risk Score", ascending=False)
                    .reset_index(drop=True))

    st.markdown(f"*{len(all_tested)} GPTs were subjected to API analysis.*")
    st.dataframe(
        all_tested, use_container_width=True, hide_index=True,
        column_config={"Risk Score": st.column_config.NumberColumn(format="%.1f")},
    )

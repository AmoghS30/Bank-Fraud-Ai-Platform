"""
Banking Fraud AI Platform — Streamlit Demo
Ties together Stage 1 (Neo4j graph), Stage 2 (LightGBM risk scoring),
and Stage 4 (RAG + Claude SAR generation) into a single demo UI.

Run: streamlit run dashboard/app.py
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")

# Set thread limits before ANY ML library import to prevent OpenMP deadlock
# between LightGBM and PyTorch/sentence-transformers thread pools.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Repo root on path so all stage modules resolve
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "risk_model"))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Banking Fraud AI Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.metric-card {background:#1e1e2e; border-radius:10px; padding:16px; margin:4px 0;}
.risk-critical {color:#ff4444; font-weight:bold;}
.risk-high {color:#ff8800; font-weight:bold;}
.risk-medium {color:#ffcc00; font-weight:bold;}
.risk-low {color:#44ff88; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

st.title("🏦 Banking Fraud AI Platform")
st.caption("AI-powered fraud ring detection • Real-time risk scoring • Regulatory SAR generation")

# ── NEO4J CONNECTION ──────────────────────────────────────────────────────────

@st.cache_resource
def get_neo4j():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD")),
    )

# ── HELPERS ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_fraud_accounts(limit=30):
    driver = get_neo4j()
    with driver.session() as s:
        result = s.run("""
            MATCH (a:Account)-[:MADE]->(t:Transaction {is_fraud: true})
            WITH a, count(t) AS fraud_count, sum(t.amount) AS total_amount
            RETURN a.account_id AS account_id, fraud_count, total_amount
            ORDER BY fraud_count DESC LIMIT $limit
        """, limit=limit).data()
    return result


@st.cache_data(ttl=300)
def get_account_network(account_id: str):
    driver = get_neo4j()
    with driver.session() as s:
        txs = s.run("""
            MATCH (a:Account {account_id: $id})-[:MADE]->(t:Transaction)
            RETURN t.tx_id AS tx_id, t.amount AS amount, t.is_fraud AS is_fraud,
                   t.dt AS dt, t.product AS product
            ORDER BY t.dt ASC
        """, id=account_id).data()

        devices = s.run("""
            MATCH (a:Account {account_id: $id})-[:USES_DEVICE]->(d:Device)
            RETURN d.device_info AS device_info
        """, id=account_id).data()

        linked = s.run("""
            MATCH (a:Account {account_id: $id})-[:USES_DEVICE]->(d:Device)
                  <-[:USES_DEVICE]-(other:Account)
            WHERE other <> a
            OPTIONAL MATCH (other)-[:MADE]->(ft:Transaction {is_fraud: true})
            WITH other.account_id AS linked_account, d.device_info AS device,
                 count(ft) AS fraud_txs
            RETURN linked_account, device, fraud_txs
            ORDER BY fraud_txs DESC LIMIT 20
        """, id=account_id).data()

        domains = s.run("""
            MATCH (a:Account {account_id: $id})-[:MADE]->(t:Transaction)-[:TO_EMAIL]->(e:EmailDomain)
            RETURN e.domain AS domain, count(t) AS tx_count
            ORDER BY tx_count DESC LIMIT 5
        """, id=account_id).data()

    return {"transactions": txs, "devices": devices, "linked": linked, "domains": domains}


def risk_colour(tier: str) -> str:
    return {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(tier, "⚪")


def score_gauge(score: float, tier: str) -> go.Figure:
    colours = {"critical": "#ff4444", "high": "#ff8800", "medium": "#ffcc00", "low": "#44ff88"}
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(score * 100, 1),
        number={"suffix": "%", "font": {"size": 36}},
        title={"text": f"Risk Score [{tier.upper()}]"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": colours.get(tier, "#888")},
            "steps": [
                {"range": [0, 40], "color": "#1a3a1a"},
                {"range": [40, 70], "color": "#3a3a1a"},
                {"range": [70, 90], "color": "#3a2a1a"},
                {"range": [90, 100], "color": "#3a1a1a"},
            ],
            "threshold": {"line": {"color": "white", "width": 2}, "value": score * 100},
        },
    ))
    fig.update_layout(height=250, margin=dict(t=30, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def shap_bar(top_features: list) -> go.Figure:
    labels = [f["feature"] for f in top_features]
    values = [f["shap_value"] for f in top_features]
    colours = ["#ff4444" if v > 0 else "#44ff88" for v in values]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colours, text=[f"{v:+.3f}" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        title="SHAP Feature Contributions",
        xaxis_title="SHAP value (impact on risk score)",
        height=280,
        margin=dict(t=40, b=10, l=0, r=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        xaxis={"gridcolor": "#333"},
        yaxis={"gridcolor": "#333"},
    )
    return fig


# ── TABS ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["🕸 Fraud Network", "⚡ Risk Scorer", "📋 SAR Generator"])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — FRAUD NETWORK
# ════════════════════════════════════════════════════════════════════════════

with tab1:
    st.subheader("Fraud Ring Detection — Neo4j Knowledge Graph")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("**Top accounts by fraud transaction count:**")
        fraud_accounts = get_fraud_accounts()
        fa_df = pd.DataFrame(fraud_accounts)
        if not fa_df.empty:
            fa_df["total_amount"] = fa_df["total_amount"].map("₹{:,.0f}".format)
            fa_df.columns = ["Account ID", "Fraud Txs", "Total Amount"]
            selected_row = st.dataframe(
                fa_df, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row",
            )
            selected_account = None
            if selected_row.selection.rows:
                idx = selected_row.selection.rows[0]
                selected_account = fraud_accounts[idx]["account_id"]
        else:
            st.warning("No fraud accounts found — check Neo4j connection.")
            selected_account = None

        # Manual input override
        manual = st.text_input("Or enter Account ID directly:", placeholder="ACC_15063")
        if manual.strip():
            selected_account = manual.strip()

    with col_right:
        if selected_account:
            st.markdown(f"**Network for `{selected_account}`**")
            net = get_account_network(selected_account)

            # Transaction summary
            txs = net["transactions"]
            fraud_txs = [t for t in txs if t["is_fraud"]]
            st.metric("Total Transactions", len(txs), delta=f"{len(fraud_txs)} flagged as fraud", delta_color="inverse")

            # Linked accounts table
            if net["linked"]:
                st.markdown("**Accounts sharing the same device (fraud ring signal):**")
                linked_df = pd.DataFrame(net["linked"])
                linked_df["device"] = linked_df["device"].str[:55] + "..."
                linked_df.columns = ["Linked Account", "Shared Device", "Fraud Txs"]
                linked_df["Fraud Txs"] = linked_df["Fraud Txs"].apply(lambda x: f"🔴 {x}" if x > 0 else f"✅ {x}")
                st.dataframe(linked_df, use_container_width=True, hide_index=True)
            else:
                st.info("No shared-device links found for this account.")

            # Transaction list
            if txs:
                st.markdown("**Transactions:**")
                tx_df = pd.DataFrame(txs)
                tx_df["amount"] = tx_df["amount"].map("₹{:,.2f}".format)
                tx_df["is_fraud"] = tx_df["is_fraud"].map({True: "🔴 Yes", False: "✅ No"})
                st.dataframe(
                    tx_df[["tx_id", "amount", "is_fraud", "product"]].rename(
                        columns={"tx_id": "TX ID", "amount": "Amount", "is_fraud": "Fraud?", "product": "Product"}
                    ),
                    use_container_width=True, hide_index=True,
                )

            # Device info
            if net["devices"]:
                st.markdown("**Device fingerprints:**")
                for d in net["devices"]:
                    st.code(d["device_info"])

            # Recipient domains
            if net["domains"]:
                st.markdown("**Recipient email domains:**")
                dom_df = pd.DataFrame(net["domains"])
                dom_df.columns = ["Domain", "Transaction Count"]
                st.dataframe(dom_df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — RISK SCORER
# ════════════════════════════════════════════════════════════════════════════

with tab2:
    st.subheader("Real-Time Transaction Risk Scoring — LightGBM + SHAP")
    st.caption("Scores a transaction 0–1 for fraud probability and explains which features drove the score.")

    # ── Load a real test transaction to pre-fill the form ─────────────────────
    @st.cache_data
    def load_real_test_samples():
        import joblib
        test_preds = pd.read_csv(os.path.join(REPO_ROOT, "risk_model/saved/test_predictions.csv"))
        df_raw = pd.read_csv(os.path.join(REPO_ROOT, "data/processed/transactions.csv"))
        sys.path.insert(0, os.path.join(REPO_ROOT, "risk_model"))
        from features import build_features, FEATURE_COLS
        high = test_preds[(test_preds["isFraud"] == 1) & (test_preds["risk_score"] > 0.85)].sample(3, random_state=7)
        low  = test_preds[(test_preds["isFraud"] == 0) & (test_preds["risk_score"] < 0.08)].sample(3, random_state=7)
        picks = pd.concat([high, low])
        txids = picks["TransactionID"].tolist()
        accts = df_raw[df_raw["TransactionID"].isin(txids)]["account_id"].unique().tolist()
        feat = build_features(df_raw[df_raw["account_id"].isin(accts)].copy(), include_graph=False)
        merged = feat.merge(picks[["TransactionID", "risk_score", "isFraud"]], on="TransactionID", how="inner")
        samples = []
        for _, row in merged.iterrows():
            samples.append({
                "label": f"{'🔴 FRAUD' if row['isFraud'] else '✅ LEGIT'} | score={row['risk_score']:.3f} | TX {row['TransactionID']}",
                "features": {c: row[c] for c in FEATURE_COLS},
                "saved_score": float(row["risk_score"]),
                "is_fraud": int(row["isFraud"]),
            })
        return samples

    with st.expander("🗂 Load a real test transaction (verifies model accuracy)", expanded=False):
        try:
            samples = load_real_test_samples()
            chosen = st.selectbox("Select a real transaction from the hold-out test set:", [s["label"] for s in samples])
            chosen_sample = next(s for s in samples if s["label"] == chosen)
            if st.button("Load this transaction into the form below"):
                st.session_state["preload"] = chosen_sample
                st.rerun()
        except Exception as ex:
            st.warning(f"Could not load real samples: {ex}")

    preload = st.session_state.get("preload", None)
    pf = preload["features"] if preload else {}

    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.markdown("**Transaction features:**")
        amt = st.number_input("Transaction Amount (₹)", min_value=0.0, value=float(pf.get("TransactionAmt", 2500.0)), step=100.0)
        product = st.selectbox("Product Code", ["W", "H", "C", "S", "R"], index=["W","H","C","S","R"].index(str(pf.get("ProductCD","W"))) if pf.get("ProductCD","W") in ["W","H","C","S","R"] else 0)
        card_type = st.selectbox("Card Type", ["credit", "debit", "charge card", "debit or credit", "unknown"], index=["credit","debit","charge card","debit or credit","unknown"].index(str(pf.get("card_type","credit"))) if str(pf.get("card_type","credit")) in ["credit","debit","charge card","debit or credit","unknown"] else 0)
        card_network = st.selectbox("Card Network", ["visa", "mastercard", "american express", "discover", "unknown"], index=["visa","mastercard","american express","discover","unknown"].index(str(pf.get("card_network","visa"))) if str(pf.get("card_network","visa")) in ["visa","mastercard","american express","discover","unknown"] else 0)
        device_type = st.selectbox("Device Type", ["desktop", "mobile", "Unknown"], index=["desktop","mobile","Unknown"].index(str(pf.get("device_type","desktop"))) if str(pf.get("device_type","desktop")) in ["desktop","mobile","Unknown"] else 0)

        email_opts = ["gmail.com", "yahoo.com", "anonymous.com", "aol.com", "hotmail.com", "outlook.com", "icloud.com", "unknown"]
        p_email = st.selectbox("Purchaser Email Domain", email_opts, index=email_opts.index(str(pf.get("p_email_domain","gmail.com"))) if str(pf.get("p_email_domain","gmail.com")) in email_opts else 0, help="Email domain of the buyer")
        r_email = st.selectbox("Recipient Email Domain", email_opts, index=email_opts.index(str(pf.get("r_email_domain","gmail.com"))) if str(pf.get("r_email_domain","gmail.com")) in email_opts else 0, help="Email domain money is sent to — anonymous.com is a high-risk signal")

        st.markdown("**Time signals:**")
        col_t1, col_t2 = st.columns(2)
        tx_hour = col_t1.slider("Hour of day (0–23)", 0, 23, int(pf.get("tx_hour", 14)), help="Transactions at 1–4am are higher risk")
        tx_dow = col_t2.slider("Day of week (0=Mon)", 0, 6, int(pf.get("tx_day_of_week", 2)))

        st.markdown("**Velocity (how many txs from this account):**")
        col_v1, col_v2, col_v3 = st.columns(3)
        vel_1h  = col_v1.number_input("Last 1h",  0, 50,  int(pf.get("velocity_1h", 0)))
        vel_24h = col_v2.number_input("Last 24h", 0, 200, int(pf.get("velocity_24h", 1)))
        vel_7d  = col_v3.number_input("Last 7d",  0, 500, int(pf.get("velocity_7d", 3)))

        acct_tx_count = st.number_input("Account total transaction count", 1, 10000, int(pf.get("account_tx_count", 20)), help="Total lifetime transactions on this account")

        st.markdown("**Graph / fraud ring signals:**")
        col_g1, col_g2 = st.columns(2)
        fraud_nb   = col_g1.number_input("Fraud neighbours", 0, 1000, int(pf.get("fraud_neighbors", 0)), help="Other accounts sharing this device that have committed fraud")
        shared_dev = col_g2.number_input("Shared device accounts", 0, 2000, int(pf.get("shared_device_accounts", 0)), help="Total accounts sharing the same device fingerprint")

        col_n1, col_n2, col_n3 = st.columns(3)
        is_new_device = col_n1.checkbox("New device?",           value=bool(pf.get("is_new_device", False)))
        is_new_p      = col_n2.checkbox("New purchaser email?",  value=bool(pf.get("is_new_p_email", False)))
        is_new_r      = col_n3.checkbox("New recipient email?",  value=bool(pf.get("is_new_r_email", False)))

        acct_mean = st.number_input("Account avg tx amount (₹)", 1.0, 50000.0, float(pf.get("amt_to_mean_ratio", 1.0) and (pf.get("TransactionAmt", 800.0) / max(float(pf.get("amt_to_mean_ratio", 1.0)), 0.01)) if pf.get("amt_to_mean_ratio") else 800.0), step=50.0, help="Used to compute how unusual this transaction amount is")

        if preload:
            st.success(f"Loaded real test transaction. Expected score: **{preload['saved_score']:.4f}** ({'fraud' if preload['is_fraud'] else 'legit'})")

        score_btn = st.button("⚡ Score Transaction", type="primary", use_container_width=True)

    with col_b:
        if score_btn:
            with st.spinner("Scoring..."):
                try:
                    from score import score_transaction

                    std_amt = max(acct_mean * 0.4, 1.0)
                    features = {
                        "TransactionAmt":        float(amt),
                        "amt_zscore":            (amt - acct_mean) / std_amt,
                        "amt_to_mean_ratio":     amt / max(acct_mean, 0.01),
                        "account_tx_count":      int(acct_tx_count),
                        "tx_hour":               int(tx_hour),
                        "tx_day_of_week":        int(tx_dow),
                        "velocity_1h":           int(vel_1h),
                        "velocity_24h":          int(vel_24h),
                        "velocity_7d":           int(vel_7d),
                        "amt_velocity_24h":      float(amt * vel_24h),
                        "addr1":                 299,
                        "fraud_neighbors":       int(fraud_nb),
                        "shared_device_accounts": int(shared_dev),
                        "device_known":          0 if device_type == "Unknown" else 1,
                        "is_new_device":         int(is_new_device),
                        "is_new_p_email":        int(is_new_p),
                        "is_new_r_email":        int(is_new_r),
                        "ProductCD":             product,
                        "card_network":          card_network,
                        "card_type":             card_type,
                        "device_type":           device_type,
                        "p_email_domain":        p_email,
                        "r_email_domain":        r_email,
                    }
                    result = score_transaction(features)
                    score = result["risk_score"]
                    tier = result["risk_tier"]

                    st.plotly_chart(score_gauge(score, tier), use_container_width=True)
                    st.plotly_chart(shap_bar(result["top_features"]), use_container_width=True)

                    if preload:
                        err = abs(score - preload["saved_score"])
                        if err < 0.01:
                            st.success(f"✅ Score matches saved prediction (error={err:.5f})")
                        else:
                            st.warning(f"Score {score:.4f} vs expected {preload['saved_score']:.4f} — note: graph features (fraud neighbours) not loaded from Neo4j in this view, so small differences are expected.")

                    st.markdown("**Top risk drivers:**")
                    for f in result["top_features"]:
                        arrow = "↑" if f["shap_value"] > 0 else "↓"
                        colour = "red" if f["shap_value"] > 0 else "green"
                        st.markdown(f":{colour}[{arrow} **{f['feature']}** (SHAP={f['shap_value']:+.3f})]")

                except FileNotFoundError:
                    st.error("Model not found. Run `python3 risk_model/train.py` first.")
                except Exception as e:
                    st.error(f"Scoring error: {e}")
                    st.exception(e)
        else:
            if preload:
                st.info(f"Real transaction loaded. Click **Score Transaction** to verify the model output matches the saved prediction of {preload['saved_score']:.4f}.")
            else:
                st.info("Set features on the left and click **Score Transaction**.")
            st.markdown("""
**How it works:**
1. LightGBM model (244 trees, trained on 472K IEEE-CIS transactions)
2. 22 engineered features: amount deviation, time-of-day, velocity, novelty, graph signals
3. SHAP TreeExplainer shows which features drove the score
4. Model metrics: ROC-AUC 0.829 | AUPRC 0.220

**Try these patterns to see the model respond:**
| Pattern | What to set |
|---|---|
| Fraud ring member | Fraud neighbours > 100, Shared devices > 500 |
| Structuring attack | Velocity 1h > 5, amount just below round number |
| Midnight transaction | Hour = 2, New device = ✓, anonymous.com |
| Normal purchase | Hour = 14, known device, gmail.com, low velocity |
""")


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — SAR GENERATOR
# ════════════════════════════════════════════════════════════════════════════

with tab3:
    st.subheader("Compliance Assistant — RAG + Claude SAR Generation")
    st.caption("Retrieves relevant regulations from PMLA 2002, RBI KYC Master Direction, and FATF Recommendations, then uses Claude (AWS Bedrock) to draft a Suspicious Activity Report.")

    sub1, sub2 = st.tabs(["📄 SAR Draft", "❓ Compliance Q&A"])

    with sub1:
        col_sar_left, col_sar_right = st.columns([1, 2])

        with col_sar_left:
            st.markdown("**Select a flagged account:**")
            demo_accounts = ["ACC_15063", "ACC_4908", "ACC_1553", "ACC_6447", "ACC_13462"]
            sar_account = st.selectbox("Account ID (pre-loaded fraud ring)", demo_accounts)
            custom_id = st.text_input("Or enter any account ID:", "")
            if custom_id.strip():
                sar_account = custom_id.strip()

            st.markdown("---")
            st.markdown("**Regulatory corpus (embedded in ChromaDB):**")
            st.markdown("""
- 📜 PMLA 2002 — Sections 3, 12, 12A, 13 + FIU-IND STR guidelines
- 🏦 RBI KYC Master Direction 2016 — CDD, EDD, suspicious tx monitoring
- 🌐 FATF Recommendations — Rec. 20 (STR), smurfing, layering typologies
""")
            generate_btn = st.button("🤖 Generate SAR with Claude", type="primary", use_container_width=True)

        with col_sar_right:
            if generate_btn:
                try:
                    from compliance_assistant.generate_sar import generate_sar

                    with st.spinner(f"Generating SAR for {sar_account}..."):
                        result = generate_sar(sar_account)

                    if "error" in result:
                        st.error(result["error"])
                    else:
                        # Risk score row
                        m1, m2, m3 = st.columns(3)
                        score = result["risk_score"]
                        tier = result["risk_tier"]
                        m1.metric("AI Risk Score", f"{score:.3f}", delta=tier.upper())
                        m2.metric("Fraud Txs", len(result["case"]["fraud_transactions"]))
                        m3.metric("Linked Accounts", len(result["case"]["linked_accounts"]))

                        # Retrieved chunks
                        with st.expander("📚 Retrieved regulation chunks (RAG)", expanded=False):
                            for chunk in result["retrieved_chunks"]:
                                st.markdown(f"**Source:** `{chunk['source']}` (relevance: {chunk['score']:.2f})")
                                st.text(chunk["text"][:400] + "...")
                                st.markdown("---")

                        # SAR text
                        st.markdown("### Generated SAR")
                        st.markdown(result["sar_text"])
                        st.download_button(
                            "⬇️ Download SAR (.txt)",
                            data=result["sar_text"],
                            file_name=f"SAR_{sar_account}.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )
                except FileNotFoundError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.exception(e)
            else:
                st.info("Select an account and click **Generate SAR** to draft a Suspicious Activity Report.")
                st.markdown("""
**Pipeline:**
```
Account ID
    → Neo4j: pull transactions, devices, linked accounts
    → LightGBM: score highest-risk transaction + SHAP explanation
    → ChromaDB RAG: retrieve top-5 regulatory chunks
    → Claude (Bedrock): draft structured SAR with citations
```
""")

    with sub2:
        st.markdown("**Ask a compliance question — answered from the regulatory corpus only.**")
        question = st.text_input(
            "Question:",
            placeholder="What are the grounds for filing an STR under PMLA 2002?"
        )
        ask_btn = st.button("🔍 Ask", type="primary")

        if ask_btn and question.strip():
            try:
                from compliance_assistant.generate_sar import answer_compliance_question

                with st.spinner("Searching regulations and generating answer..."):
                    result = answer_compliance_question(question)

                st.markdown("### Answer")
                st.markdown(result["answer"])

                with st.expander("📚 Source chunks used"):
                    for s in result["sources"]:
                        st.markdown(f"**{s['source']}**")
                        st.text(s["excerpt"])
                        st.markdown("---")
            except Exception as e:
                st.error(f"Error: {e}")
        elif ask_btn:
            st.warning("Please enter a question.")

        st.markdown("---")
        st.markdown("**Example questions:**")
        examples = [
            "What is the definition of a suspicious transaction under PMLA 2002?",
            "What does FATF say about smurfing and structuring?",
            "How many days does a bank have to file an STR after detecting suspicious activity?",
            "What is enhanced due diligence and when does it apply?",
        ]
        for ex in examples:
            if st.button(ex, key=ex):
                st.session_state["q"] = ex

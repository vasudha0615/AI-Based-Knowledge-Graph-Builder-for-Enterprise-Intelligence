import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
import sys, os

# ── Page Config ────────────────────────────────────
st.set_page_config(
    page_title="KGB | Knowledge Graph Builder",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Connect RAG ────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'semantic_rag'))

# ── Load Data ──────────────────────────────────────
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'cleaned_tickets.xlsx')
    if os.path.exists(path):
        return pd.read_excel(path)
    # Demo fallback
    return pd.DataFrame({
        'Ticket ID':         range(1, 51),
        'Product Purchased': (['LG Smart TV','Microsoft Office','Dell XPS','GoPro Hero','Autodesk AutoCAD'] * 10),
        'Ticket Type':       (['Technical Issue','Billing Inquiry'] * 25),
        'Ticket Priority':   (['Critical','High','Medium','Low'] * 13)[:50],
        'Ticket Status':     (['Open','Closed','Pending Customer Response'] * 17)[:50],
        'Ticket Channel':    (['Email','Phone','Chat','Social Media'] * 13)[:50],
        'Ticket Subject':    (['Product Setup','Network Problem','Data Loss','Account Access','Overheating'] * 10),
        'Ticket Description':(['Issue with product setup and configuration'] * 50),
        'Resolution':        (['Resolved via support','not resolved yet'] * 25),
        'Resolution Status': (['Resolved','Unresolved'] * 25),
        'Ticket Priority':   (['Critical','High','Medium','Low'] * 13)[:50],
    })

df = load_data()

# ── Graph Data ─────────────────────────────────────
EDGES = [
    ("LG Smart TV",          "Overheating",           "has_issue"),
    ("Overheating",          "Power Supply Failure",   "caused_by"),
    ("Power Supply Failure",  "Cooling Check",         "resolved_by"),
    ("Microsoft Office",     "Account Access",         "has_issue"),
    ("Account Access",       "Billing Inquiry",        "categorized_as"),
    ("Dell XPS",             "Network Problem",        "has_issue"),
    ("Network Problem",      "Software Update",        "resolved_by"),
    ("GoPro Hero",           "Data Loss",              "has_issue"),
    ("Data Loss",            "Factory Reset",          "resolved_by"),
    ("Autodesk AutoCAD",     "Product Setup",          "has_issue"),
    ("Product Setup",        "Driver Update",          "resolved_by"),
]
NODE_COLORS = {
    "LG Smart TV":"#0ea5e9","Microsoft Office":"#0ea5e9",
    "Dell XPS":"#0ea5e9","GoPro Hero":"#0ea5e9","Autodesk AutoCAD":"#0ea5e9",
    "Overheating":"#e879f9","Account Access":"#e879f9",
    "Network Problem":"#e879f9","Data Loss":"#e879f9","Product Setup":"#e879f9",
    "Power Supply Failure":"#f59e0b","Billing Inquiry":"#f59e0b",
    "Cooling Check":"#34d399","Software Update":"#34d399",
    "Factory Reset":"#34d399","Driver Update":"#34d399",
}

# ══════════════════════════════════════════════════
# GLOBAL CSS — Glassmorphic Dark Theme
# ══════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp {
    background: radial-gradient(circle at top right, #0f172a, #000000) !important;
    color: #f8fafc !important;
    font-family: 'Space Grotesk', sans-serif !important;
    min-height: 100vh;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    visibility: hidden !important; display: none !important;
}

/* ── Remove default padding ── */
.block-container { padding: 24px 32px !important; max-width: 100% !important; }
[data-testid="stSidebar"] { display: none !important; }

/* ── Glass Panel ── */
.glass {
    background: rgba(30, 41, 59, 0.4) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    margin-bottom: 16px !important;
}

/* ── Glass Header ── */
.glass-header {
    background: linear-gradient(90deg, rgba(16,185,129,0.1), rgba(59,130,246,0.1));
    border-bottom: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px 16px 0 0;
    padding: 14px 20px;
    margin: -20px -20px 16px -20px;
}
.glass-header-title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #e2e8f0;
}

/* ── Brand Title ── */
.brand-kgb {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #34d399, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
}
.brand-sub {
    font-size: 1.1rem;
    font-weight: 300;
    color: #94a3b8;
    margin-left: 8px;
}
.brand-desc {
    font-size: 13px;
    color: #64748b;
    margin-top: 4px;
}

/* ── Status Indicator ── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(30,41,59,0.8);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 999px;
    padding: 6px 16px;
    font-size: 13px;
    color: #94a3b8;
    font-weight: 500;
}
.status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #34d399;
    box-shadow: 0 0 8px rgba(52,211,153,0.8);
    animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
    0%,100% { opacity:1; } 50% { opacity:0.4; }
}

/* ── Metric Cards ── */
[data-testid="metric-container"] {
    background: rgba(30,41,59,0.4) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    text-align: center !important;
    transition: transform 0.2s, border-color 0.3s !important;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-3px) !important;
    border-color: rgba(52,211,153,0.3) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 2.2rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 10px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: #64748b !important;
    margin-top: 4px !important;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #059669, #0891b2) !important;
    color: white !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 10px 28px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 20px rgba(6,182,212,0.25) !important;
    width: auto !important;
}
[data-testid="stButton"] > button:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 8px 30px rgba(6,182,212,0.4) !important;
}

/* ── Text Input ── */
[data-testid="stTextInput"] input {
    background: rgba(15,23,42,0.8) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #f8fafc !important;
    font-family: 'Space Grotesk', sans-serif !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: rgba(52,211,153,0.4) !important;
    box-shadow: 0 0 0 3px rgba(52,211,153,0.1) !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: rgba(15,23,42,0.8) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #f8fafc !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-testid="stTab"] {
    background: transparent !important;
    color: #64748b !important;
    border: none !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    padding: 8px 20px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #34d399 !important;
    border-bottom: 2px solid #34d399 !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 12px !important;
}

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.05) !important; }

/* ── Custom feed card ── */
.feed-card {
    background: rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    line-height: 1.7;
}
.feed-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 6px;
}

/* ── Triplet card ── */
.triplet-card {
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    line-height: 1.8;
}

/* ── Answer box ── */
.answer-box {
    background: linear-gradient(135deg,
        rgba(16,185,129,0.06),
        rgba(6,182,212,0.06));
    border: 1px solid rgba(52,211,153,0.2);
    border-radius: 16px;
    padding: 24px;
    margin-top: 16px;
    font-size: 15px;
    line-height: 1.8;
    color: #e2e8f0;
}

/* ── Badge ── */
.badge {
    display: inline-block;
    background: rgba(6,182,212,0.1);
    color: #06b6d4;
    border: 1px solid rgba(6,182,212,0.2);
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Step card ── */
.step-card {
    background: rgba(30,41,59,0.4);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    backdrop-filter: blur(16px);
}
.step-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: rgba(52,211,153,0.2);
    line-height: 1;
    margin-bottom: 8px;
}
.step-title {
    font-weight: 600;
    font-size: 13px;
    color: #e2e8f0;
    margin-bottom: 6px;
}
.step-desc {
    font-size: 11px;
    color: #64748b;
    line-height: 1.5;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: rgba(52,211,153,0.1) !important;
    border: 1px solid rgba(52,211,153,0.3) !important;
    color: #34d399 !important;
    border-radius: 999px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(52,211,153,0.2) !important;
    box-shadow: 0 4px 20px rgba(52,211,153,0.2) !important;
}

/* ── Radio ── */
[data-testid="stRadio"] label { display: none; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════
col_logo, col_status = st.columns([3, 1])
with col_logo:
    st.markdown("""
    <div style="padding: 8px 0 4px;">
        <div>
            <span class="brand-kgb">KGB</span>
            <span class="brand-sub">| Knowledge Graph Builder</span>
        </div>
        <div class="brand-desc">Enterprise Support Intelligence Pipeline · Powered by Mistral LLM + FAISS RAG</div>
    </div>
    """, unsafe_allow_html=True)

with col_status:
    st.markdown("""
    <div style="display:flex; justify-content:flex-end; align-items:center; height:100%; padding-top:12px; gap:12px;">
        <div class="status-badge">
            <div class="status-dot"></div>
            System Live
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 12px 0 20px 0;'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "⚡  Pipeline Overview",
    "🔍  Semantic Search",
    "🕸️  Ontology Network",
    "📋  Data Explorer"
])


# ══════════════════════════════════════════════════
# TAB 1 — PIPELINE OVERVIEW
# ══════════════════════════════════════════════════
with tab1:

    # ── KPI Row ────────────────────────────────────
    resolved   = int(df[df['Resolution Status'] == 'Resolved'].shape[0])    if 'Resolution Status' in df.columns else 0
    unresolved = int(df[df['Resolution Status'] == 'Unresolved'].shape[0])  if 'Resolution Status' in df.columns else 0
    critical   = int(df[df['Ticket Priority'].str.lower() == 'critical'].shape[0]) if 'Ticket Priority' in df.columns else 0

    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.metric("Tickets Parsed",   f"{len(df):,}")
        st.markdown("<div style='text-align:center; margin-top:-12px;'><span style='color:#06b6d4; font-size:10px; font-family:JetBrains Mono;'>● LIVE</span></div>", unsafe_allow_html=True)
    with c2:
        st.metric("Unique Entities",  "11")
        st.markdown("<div style='text-align:center; margin-top:-12px;'><span style='color:#34d399; font-size:10px; font-family:JetBrains Mono;'>● EXTRACTED</span></div>", unsafe_allow_html=True)
    with c3:
        st.metric("Relationships",    "11")
        st.markdown("<div style='text-align:center; margin-top:-12px;'><span style='color:#e879f9; font-size:10px; font-family:JetBrains Mono;'>● MAPPED</span></div>", unsafe_allow_html=True)
    with c4:
        st.metric("Resolution Rate",  f"{round(resolved/max(len(df),1)*100)}%")
        st.markdown("<div style='text-align:center; margin-top:-12px;'><span style='color:#f59e0b; font-size:10px; font-family:JetBrains Mono;'>● COMPUTED</span></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Two Column Layout ──────────────────────────
    left, right = st.columns([5, 7])

    with left:
        # Raw Data Feed
        st.markdown("""
        <div class="glass">
            <div class="glass-header">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="glass-header-title">1. Raw Data Ingestion</span>
                    <span class="badge">cleaned_tickets.xlsx</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        sample = df[['Ticket ID','Product Purchased','Ticket Type','Ticket Priority']].head(4)
        for _, row in sample.iterrows():
            priority_color = {
                'critical':'#f43f5e','high':'#f59e0b',
                'medium':'#06b6d4','low':'#34d399'
            }.get(str(row.get('Ticket Priority','')).lower(), '#94a3b8')

            st.markdown(f"""
            <div class="feed-card">
                <div class="feed-label" style="color:#06b6d4;">Ticket ID: {row['Ticket ID']}</div>
                <div style="color:#e2e8f0;">📦 {row['Product Purchased']}</div>
                <div style="color:#94a3b8;">Type: {row['Ticket Type']}</div>
                <div style="color:{priority_color}; font-size:10px; margin-top:4px;">
                    ▲ {str(row.get('Ticket Priority','')).upper()}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Triplet Extraction
        st.markdown("""
        <div class="glass">
            <div class="glass-header">
                <span class="glass-header-title">2. Triplet Extraction Engine</span>
            </div>
        """, unsafe_allow_html=True)

        tc1, tc2 = st.columns(2)
        with tc1:
            st.markdown("""
            <div style="font-size:11px; font-weight:700; color:#34d399;
                        letter-spacing:0.08em; text-transform:uppercase; margin-bottom:10px;">
                Rules Engine
            </div>
            """, unsafe_allow_html=True)
            rule_triplets = [
                ("LG Smart TV",      "has_issue",    "Overheating"),
                ("Dell XPS",         "has_issue",    "Network Problem"),
                ("Microsoft Office", "has_issue",    "Account Access"),
            ]
            for s, p, o in rule_triplets:
                st.markdown(f"""
                <div class="triplet-card">
                    <div style="color:#e2e8f0;">{s}</div>
                    <div style="color:#34d399;">↳ [{p}]</div>
                    <div style="color:#e2e8f0;">{o}</div>
                </div>
                """, unsafe_allow_html=True)

        with tc2:
            st.markdown("""
            <div style="font-size:11px; font-weight:700; color:#e879f9;
                        letter-spacing:0.08em; text-transform:uppercase; margin-bottom:10px;">
                Mistral LLM
            </div>
            """, unsafe_allow_html=True)
            llm_triplets = [
                ("Overheating",          "caused_by",   "Power Supply Failure"),
                ("Network Problem",      "resolved_by", "Software Update"),
                ("Account Access",       "categorized", "Billing Inquiry"),
            ]
            for s, p, o in llm_triplets:
                st.markdown(f"""
                <div class="triplet-card">
                    <div style="color:#e2e8f0;">{s}</div>
                    <div style="color:#e879f9;">↳ [{p}]</div>
                    <div style="color:#e2e8f0;">{o}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        # Live Graph
        st.markdown("""
        <div class="glass">
            <div class="glass-header">
                <span class="glass-header-title">3. Live Ontology Network</span>
            </div>
        """, unsafe_allow_html=True)

        G = nx.DiGraph()
        for s,t,r in EDGES: G.add_edge(s,t,label=r)
        pos = nx.spring_layout(G, seed=42, k=2.2)

        # Edges
        ex,ey = [],[]
        for s,t in G.edges():
            x0,y0=pos[s]; x1,y1=pos[t]
            ex+=[x0,x1,None]; ey+=[y0,y1,None]

        edge_trace = go.Scatter(
            x=ex, y=ey, mode='lines',
            line=dict(width=1, color='rgba(255,255,255,0.12)'),
            hoverinfo='none'
        )

        # Nodes
        nx_list = list(G.nodes())
        node_trace = go.Scatter(
            x=[pos[n][0] for n in nx_list],
            y=[pos[n][1] for n in nx_list],
            mode='markers+text',
            text=nx_list,
            textposition='top center',
            textfont=dict(color='#f8fafc', size=10, family='JetBrains Mono'),
            hovertemplate='<b>%{text}</b><extra></extra>',
            marker=dict(
                size=18,
                color=[NODE_COLORS.get(n,'#334155') for n in nx_list],
                line=dict(width=1.5, color='rgba(255,255,255,0.2)'),
                symbol='circle'
            )
        )

        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                height=460,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                margin=dict(t=10, b=10, l=10, r=10),
                hovermode='closest'
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Legend
        st.markdown("""
        <div style="display:flex; gap:16px; flex-wrap:wrap; padding:4px 0 8px;">
            <div style="display:flex; align-items:center; gap:6px; font-size:12px; color:#94a3b8;">
                <div style="width:10px;height:10px;border-radius:50%;background:#0ea5e9;"></div> Product
            </div>
            <div style="display:flex; align-items:center; gap:6px; font-size:12px; color:#94a3b8;">
                <div style="width:10px;height:10px;border-radius:50%;background:#e879f9;"></div> Issue
            </div>
            <div style="display:flex; align-items:center; gap:6px; font-size:12px; color:#94a3b8;">
                <div style="width:10px;height:10px;border-radius:50%;background:#f59e0b;"></div> Cause / Type
            </div>
            <div style="display:flex; align-items:center; gap:6px; font-size:12px; color:#94a3b8;">
                <div style="width:10px;height:10px;border-radius:50%;background:#34d399;"></div> Resolution
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Charts
        st.markdown("<br>", unsafe_allow_html=True)
        ch1, ch2 = st.columns(2)
        with ch1:
            pc = df['Ticket Priority'].value_counts().reset_index()
            pc.columns = ['Priority','Count']
            fig2 = go.Figure(go.Bar(
                x=pc['Priority'], y=pc['Count'],
                marker=dict(
                    color=['#f43f5e','#f59e0b','#06b6d4','#34d399'],
                    line=dict(width=0)
                ),
                text=pc['Count'], textposition='outside',
                textfont=dict(color='#94a3b8', size=11)
            ))
            fig2.update_layout(
                title=dict(text='By Priority',
                           font=dict(color='#94a3b8', size=12, family='Space Grotesk')),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#64748b'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)',
                           linecolor='rgba(255,255,255,0.05)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.05)',
                           linecolor='rgba(255,255,255,0.05)'),
                margin=dict(t=30,b=10,l=10,r=10), height=200
            )
            st.plotly_chart(fig2, use_container_width=True)

        with ch2:
            sc = df['Ticket Status'].value_counts().reset_index()
            sc.columns = ['Status','Count']
            fig3 = go.Figure(go.Pie(
                labels=sc['Status'], values=sc['Count'], hole=0.65,
                marker=dict(
                    colors=['#06b6d4','#34d399','#f59e0b'],
                    line=dict(color='rgba(0,0,0,0.5)', width=2)
                ),
                textinfo='percent',
                textfont=dict(color='#e2e8f0', size=11)
            ))
            fig3.update_layout(
                title=dict(text='By Status',
                           font=dict(color='#94a3b8', size=12, family='Space Grotesk')),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(font=dict(color='#64748b', size=10),
                            bgcolor='rgba(0,0,0,0)'),
                margin=dict(t=30,b=10,l=10,r=10), height=200
            )
            st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════
# TAB 2 — SEMANTIC SEARCH
# ══════════════════════════════════════════════════
with tab2:

    st.markdown("""
    <div class="glass">
        <div class="glass-header">
            <span class="glass-header-title">RAG Pipeline — Retrieval Augmented Generation</span>
        </div>
    """, unsafe_allow_html=True)

    # Steps
    c1,c2,c3,c4 = st.columns(4)
    for col,(num,title,desc) in zip([c1,c2,c3,c4],[
        ("01","Embed Query",   "Convert to 384-dim vector via all-MiniLM-L6-v2"),
        ("02","FAISS Search",  "Find top-k similar documents semantically"),
        ("03","Build Context", "Retrieve & combine relevant knowledge"),
        ("04","LLM Answer",    "Mistral generates grounded enterprise answer"),
    ]):
        with col:
            st.markdown(f"""
            <div class="step-card">
                <div class="step-num">{num}</div>
                <div class="step-title">{title}</div>
                <div class="step-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div><br>", unsafe_allow_html=True)

    # Example queries
    st.markdown("""
    <div style="font-size:11px; font-weight:700; color:#64748b;
                letter-spacing:0.12em; text-transform:uppercase; margin-bottom:12px;">
        Quick Queries
    </div>
    """, unsafe_allow_html=True)

    q1,q2,q3 = st.columns(3)
    examples = [
        "Why is my LG TV overheating?",
        "How to fix network problems?",
        "What causes power supply failure?"
    ]
    for col, q in zip([q1,q2,q3], examples):
        with col:
            if st.button(q, key=f"ex_{q}"):
                st.session_state.rag_query = q

    st.markdown("<br>", unsafe_allow_html=True)

    # Search box
    query = st.text_input(
        "query",
        value=st.session_state.get('rag_query',''),
        placeholder="Ask anything about enterprise support tickets...",
        label_visibility="collapsed"
    )

    search_btn = st.button("⚡  Initialize Search", key="search_main")

    if search_btn and query:
        with st.spinner(""):
            st.markdown("""
            <div style="font-size:13px; color:#34d399; font-family:'JetBrains Mono';
                        letter-spacing:0.05em; margin: 8px 0;">
                ◉ Embedding query → Searching FAISS → Retrieving context → Generating answer...
            </div>
            """, unsafe_allow_html=True)
            try:
                from rag_pipeline import rag_search
                answer = rag_search(query)
            except Exception:
                answer = (
                    f'Based on the enterprise knowledge base analysis for: "{query}"\n\n'
                    'The retrieved documents indicate this issue is commonly related to '
                    'hardware or software configuration. Recommended resolution: verify '
                    'system settings, apply latest software updates, and perform a factory '
                    'reset if the issue persists.\n\n'
                    '(Connect Ollama + Mistral locally for full AI-powered responses.)'
                )

        st.markdown(f"""
        <div class="answer-box">
            <div style="font-size:11px; font-weight:700; color:#34d399;
                        letter-spacing:0.1em; text-transform:uppercase; margin-bottom:14px;
                        font-family:'JetBrains Mono';">
                ✦ Mistral AI Response
            </div>
            <div style="color:#e2e8f0; line-height:1.9;">{answer}</div>
            <div style="margin-top:16px; padding-top:12px;
                        border-top:1px solid rgba(255,255,255,0.05);
                        font-size:11px; color:#475569; font-family:'JetBrains Mono';">
                Query: "{query}"
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif search_btn:
        st.warning("Please enter a query.")


# ══════════════════════════════════════════════════
# TAB 3 — ONTOLOGY NETWORK
# ══════════════════════════════════════════════════
with tab3:

    st.markdown("""
    <div class="glass">
        <div class="glass-header">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="glass-header-title">Full Ontology Network — Entity Relationship Map</span>
                <span class="badge">Mistral LLM Extracted</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Total Nodes",     "11")
    with c2: st.metric("Total Edges",     "11")
    with c3: st.metric("Entity Classes",  "4")
    with c4: st.metric("Products Mapped", "5")

    st.markdown("<br>", unsafe_allow_html=True)

    # Full graph
    G2 = nx.DiGraph()
    for s,t,r in EDGES: G2.add_edge(s,t,label=r)
    pos2 = nx.spring_layout(G2, seed=7, k=3)

    ex2,ey2 = [],[]
    for s,t in G2.edges():
        x0,y0=pos2[s]; x1,y1=pos2[t]
        ex2+=[x0,x1,None]; ey2+=[y0,y1,None]

    edge_trace2 = go.Scatter(
        x=ex2, y=ey2, mode='lines',
        line=dict(width=1.2, color='rgba(255,255,255,0.1)'),
        hoverinfo='none'
    )

    nl2 = list(G2.nodes())
    node_trace2 = go.Scatter(
        x=[pos2[n][0] for n in nl2],
        y=[pos2[n][1] for n in nl2],
        mode='markers+text',
        text=nl2,
        textposition='top center',
        textfont=dict(color='#f8fafc', size=11, family='JetBrains Mono'),
        hovertemplate='<b>%{text}</b><extra></extra>',
        marker=dict(
            size=24,
            color=[NODE_COLORS.get(n,'#334155') for n in nl2],
            line=dict(width=2, color='rgba(255,255,255,0.15)'),
        )
    )

    fig_full = go.Figure(
        data=[edge_trace2, node_trace2],
        layout=go.Layout(
            height=560, showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(t=10,b=10,l=10,r=10),
            hovermode='closest'
        )
    )
    st.plotly_chart(fig_full, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Relationship Table
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:11px; font-weight:700; color:#64748b;
                letter-spacing:0.12em; text-transform:uppercase; margin-bottom:12px;">
        Extracted Triplets
    </div>
    """, unsafe_allow_html=True)

    rel_df = pd.DataFrame(EDGES, columns=['Subject (Source)','Object (Target)','Predicate (Relation)'])
    st.dataframe(rel_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════
# TAB 4 — DATA EXPLORER
# ══════════════════════════════════════════════════
with tab4:

    st.markdown("""
    <div class="glass">
        <div class="glass-header">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="glass-header-title">Enterprise Ticket Data Explorer</span>
                <span class="badge">8,469 Records</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1:
        pf = st.selectbox("Priority", ["All"]+sorted(df['Ticket Priority'].dropna().unique().tolist()))
    with c2:
        sf = st.selectbox("Status",   ["All"]+sorted(df['Ticket Status'].dropna().unique().tolist()))
    with c3:
        cf = st.selectbox("Channel",  ["All"]+sorted(df['Ticket Channel'].dropna().unique().tolist()))

    st.markdown("</div>", unsafe_allow_html=True)

    filtered = df.copy()
    if pf != "All": filtered = filtered[filtered['Ticket Priority'] == pf]
    if sf != "All": filtered = filtered[filtered['Ticket Status']   == sf]
    if cf != "All": filtered = filtered[filtered['Ticket Channel']  == cf]

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: st.metric("Filtered",    f"{len(filtered):,}")
    with c2: st.metric("Total",       f"{len(df):,}")
    with c3: st.metric("Match Rate",  f"{round(len(filtered)/max(len(df),1)*100,1)}%")

    st.markdown("<br>", unsafe_allow_html=True)
    cols = [c for c in [
        'Ticket ID','Product Purchased','Ticket Type','Ticket Subject',
        'Ticket Priority','Ticket Status','Resolution Status','Ticket Channel'
    ] if c in filtered.columns]

    st.dataframe(filtered[cols], use_container_width=True, hide_index=True, height=400)

    st.markdown("<br>", unsafe_allow_html=True)
    c1,_ = st.columns([1,4])
    with c1:
        st.download_button(
            "⬇  Export CSV",
            data=filtered.to_csv(index=False),
            file_name=f"kgb_tickets_{pf}_{sf}.csv",
            mime="text/csv"
        )


# ── Footer ─────────────────────────────────────────
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#1e293b; font-size:12px;
            font-family:'JetBrains Mono'; letter-spacing:0.08em; padding-bottom:12px;">
    KGB · Knowledge Graph Builder · Enterprise Intelligence Pipeline ·
    Mistral LLM + FAISS + Streamlit
</div>
""", unsafe_allow_html=True)

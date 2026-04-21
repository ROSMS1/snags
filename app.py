import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
from supabase import create_client, Client

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FLM Snags Tracker – MTN Congo",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CONNEXION SUPABASE ───────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = get_supabase()

# ─── CONSTANTES ───────────────────────────────────────────────────────────────
REGIONS        = ["PNR", "SOUTH", "BRAZZAVILLE_POOL", "NORTH_CENTRE", "NORTH"]
PRIORITIES     = ["P1", "P2", "P4", "TIS"]
CATEGORIES     = ["PASSIVE", "ACTIVE", "TOWER", "ENVIRONMENTAL"]
SUB_CATEGORIES = [
    "Active Hardware", "AirCon", "ATS", "Automation", "Aviation light",
    "AVR", "Battery backup", "Breaker", "Control Panel", "Cooling", "DG",
    "DG Battery", "Earthing", "Environmental", "Fiber", "Monitoring",
    "Others", "PWR Dimen", "Rack", "SNE", "TXN/RAN/IPRAN",
]
OWNERS         = ["MTN", "MS", "ZTE", "FME", "NOC"]
STATUSES       = ["Open", "Close", "In Progress"]
SNAG_IDS       = ["QA", "PM", "FLM"]
SITE_CATEGORIES = ["Hub Site", "Terminal Site", "BB Site"]

# ─── HELPERS SUPABASE ─────────────────────────────────────────────────────────
def load_snags() -> pd.DataFrame:
    res = supabase.table("snags").select("*").order("id", desc=True).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["id","site_id","site_name","site_priority","region",
        "pm_auditor","audit_date","description","category","sub_category","owner",
        "action_plan","plan_date","deadline","implementer","progress","status",
        "close_date","comments","spare_request","snag_id_type","created_at"])

def load_materials() -> pd.DataFrame:
    res = supabase.table("materials").select("*").order("id", desc=True).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["id","snag_id","site_id","site_name","item",
        "specifications","qty","needed","status","created_at"])

def load_battery() -> pd.DataFrame:
    res = supabase.table("battery_plan").select("*").order("id", desc=True).execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["id","site_id","site_name","region","site_priority",
        "site_category","first_used_date","battery_type","battery_specs","qty",
        "donor_site","requestor","approval_date","planned_date","actual_date",
        "current_autonomy","target_autonomy","battery_health","status","due_date",
        "owner","created_at"])

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def days_left(date_str):
    if not date_str:
        return None
    try:
        d = datetime.strptime(str(date_str)[:10], "%Y-%m-%d").date()
        return (d - date.today()).days
    except Exception:
        return None

def alert_icon(days):
    if days is None: return "⚪"
    if days < 0:     return "🔴"
    if days <= 3:    return "🔴"
    if days <= 7:    return "🟠"
    if days <= 14:   return "🟡"
    return "🟢"

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1a1a2e !important; }
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #e0e0e0 !important; }
.metric-card {
    background: #0f3460; border-radius: 10px;
    padding: 16px 20px; text-align: center; color: white; margin-bottom: 8px;
}
.metric-card .val { font-size: 2rem; font-weight: 800; }
.metric-card .lbl { font-size: 0.82rem; opacity: 0.85; margin-top: 2px; }
.alert-box { border-radius: 8px; padding: 10px 14px; margin: 5px 0; font-size: 0.88rem; }
.a-red    { background: #fde8e8; border-left: 4px solid #e53e3e; }
.a-orange { background: #fef3e2; border-left: 4px solid #dd6b20; }
.a-yellow { background: #fefde8; border-left: 4px solid #d69e2e; }
.sec-title {
    font-size: 1.1rem; font-weight: 700; color: #0f3460;
    border-bottom: 2px solid #e94560; padding-bottom: 3px; margin: 14px 0 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 FLM Snags Tracker")
    st.markdown("**MTN Congo – South Region**")
    st.markdown("---")
    page = st.radio("Navigation", [
        "🏠 Dashboard",
        "➕ Nouveau Snag",
        "📋 Liste des Snags",
        "🔔 Rappels & Alertes",
        "🔧 Besoins Matériels",
        "🔋 Plan Batteries",
    ])
    st.markdown("---")
    st.markdown(f"📅 **{date.today().strftime('%d/%m/%Y')}**")
    st.markdown("🗄️ *Base : Supabase Cloud*")

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.title("📊 Dashboard – FLM Snags Tracker")
    df = load_snags()

    total    = len(df)
    open_s   = len(df[df["status"] == "Open"])   if total else 0
    closed_s = len(df[df["status"] == "Close"])  if total else 0
    in_prog  = len(df[df["status"] == "In Progress"]) if total else 0
    overdue  = 0
    if total:
        for _, row in df[df["status"] != "Close"].iterrows():
            d = days_left(row.get("deadline"))
            if d is not None and d < 0:
                overdue += 1

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, lbl, bg in [
        (c1, total,    "Total Snags",  "#0f3460"),
        (c2, open_s,   "🔴 Open",       "#e53e3e"),
        (c3, closed_s, "✅ Clôturés",   "#38a169"),
        (c4, in_prog,  "🔧 En Cours",   "#dd6b20"),
        (c5, overdue,  "⚠️ En Retard",  "#c53030"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="background:{bg}"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

    if total == 0:
        st.info("Aucun snag enregistré. Cliquez sur **➕ Nouveau Snag** pour commencer.")
    else:
        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="sec-title">Snags par Sous-Catégorie</div>', unsafe_allow_html=True)
            sub_tot   = df.groupby("sub_category").size().reset_index(name="Total")
            sub_open  = df[df["status"] != "Close"].groupby("sub_category").size().reset_index(name="Open")
            sub_close = df[df["status"] == "Close"].groupby("sub_category").size().reset_index(name="Closed")
            sub_df = sub_tot.merge(sub_open, on="sub_category", how="left").merge(sub_close, on="sub_category", how="left").fillna(0)
            sub_df["Closed"] = sub_df["Closed"].astype(int)
            sub_df["Open"]   = sub_df["Open"].astype(int)
            sub_df["%"]      = (sub_df["Closed"] / sub_df["Total"] * 100).round(1).astype(str) + "%"
            st.dataframe(sub_df.rename(columns={"sub_category":"Sub-Category"}), use_container_width=True, hide_index=True)

        with col_b:
            st.markdown('<div class="sec-title">Répartition par Statut</div>', unsafe_allow_html=True)
            st_df = df["status"].value_counts().reset_index()
            st_df.columns = ["Statut","Nombre"]
            fig = px.pie(st_df, names="Statut", values="Nombre", hole=0.4,
                         color_discrete_sequence=["#e53e3e","#38a169","#dd6b20"])
            fig.update_layout(margin=dict(t=10,b=10), height=270)
            st.plotly_chart(fig, use_container_width=True)

        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown('<div class="sec-title">Snags par Région</div>', unsafe_allow_html=True)
            reg = df.groupby(["region","status"]).size().reset_index(name="n")
            fig2 = px.bar(reg, x="region", y="n", color="status", barmode="stack",
                          color_discrete_map={"Open":"#e53e3e","Close":"#38a169","In Progress":"#dd6b20"})
            fig2.update_layout(margin=dict(t=10,b=10), height=270, xaxis_title="", yaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)

        with col_d:
            st.markdown('<div class="sec-title">Snags par Catégorie</div>', unsafe_allow_html=True)
            cat = df["category"].value_counts().reset_index()
            cat.columns = ["Catégorie","Nombre"]
            fig3 = px.bar(cat, x="Catégorie", y="Nombre", color_discrete_sequence=["#0f3460"])
            fig3.update_layout(margin=dict(t=10,b=10), height=270)
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown('<div class="sec-title">10 Derniers Snags</div>', unsafe_allow_html=True)
        cols_show = ["id","site_id","site_name","region","description","sub_category","status","deadline","owner","progress"]
        st.dataframe(df[cols_show].head(10), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# NOUVEAU SNAG
# ══════════════════════════════════════════════════════════════════════════════
elif page == "➕ Nouveau Snag":
    st.title("➕ Enregistrer un Nouveau Snag")
    st.caption("Modèle fidèle à la feuille **PM Snags** du fichier FLM_SNAGS_TRACKER")
    st.markdown("---")

    with st.form("form_snag", clear_on_submit=True):
        st.markdown('<div class="sec-title">🏗️ Informations du Site</div>', unsafe_allow_html=True)
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        with r1c1: site_id       = st.text_input("Site ID *", placeholder="ex: 2000")
        with r1c2: site_name     = st.text_input("Nom du Site *", placeholder="ex: AEROPORT1")
        with r1c3: site_priority = st.selectbox("Priorité", PRIORITIES)
        with r1c4: region        = st.selectbox("Région", REGIONS)

        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1: pm_auditor  = st.text_input("PM / Auditeur", placeholder="ex: Edna")
        with r2c2: audit_date  = st.date_input("Date Audit PM", value=date.today())
        with r2c3: snag_id_type = st.selectbox("Snag Identification", SNAG_IDS)

        st.markdown('<div class="sec-title">⚠️ Description du Snag</div>', unsafe_allow_html=True)
        description = st.text_area("Description *", placeholder="Décrivez le problème observé...", height=80)

        r3c1, r3c2 = st.columns(2)
        with r3c1: category     = st.selectbox("Catégorie", CATEGORIES)
        with r3c2: sub_category = st.selectbox("Sous-Catégorie", SUB_CATEGORIES)

        st.markdown('<div class="sec-title">📋 Plan d\'Action & Responsabilité</div>', unsafe_allow_html=True)
        action_plan = st.text_area("Plan d'Action", placeholder="Actions correctives à mener...", height=75)

        r4c1, r4c2, r4c3, r4c4 = st.columns(4)
        with r4c1: plan_date   = st.date_input("Date Planifiée", value=date.today())
        with r4c2: deadline    = st.date_input("Deadline *", value=date.today() + timedelta(days=30))
        with r4c3: owner       = st.selectbox("Owner", OWNERS)
        with r4c4: implementer = st.text_input("Implémenteur", placeholder="ex: Edna/Eric")

        r5c1, r5c2 = st.columns(2)
        with r5c1: progress = st.slider("Progression (%)", 0, 100, 0)
        with r5c2: status   = st.selectbox("Statut", STATUSES)

        close_date = None
        if status == "Close":
            close_date = st.date_input("Date de Clôture", value=date.today())

        comments = st.text_area("Commentaires", height=60)

        st.markdown('<div class="sec-title">🔧 Besoins en Matériels / Spare Parts</div>', unsafe_allow_html=True)
        spare_request = st.checkbox("Ce snag nécessite des matériels / spare parts")

        mat_rows = []
        if spare_request:
            n_items = st.number_input("Nombre d'articles à demander", min_value=1, max_value=10, value=1)
            for i in range(int(n_items)):
                st.markdown(f"**Article {i+1}**")
                mc1, mc2, mc3, mc4 = st.columns(4)
                with mc1: item_name = st.text_input("Item", key=f"item_{i}", placeholder="ex: DEEP SEA")
                with mc2: item_spec = st.text_input("Spécifications", key=f"spec_{i}", placeholder="ex: 12V135Ah")
                with mc3: item_qty  = st.number_input("Qté", min_value=1, value=1, key=f"qty_{i}")
                with mc4: item_ndd  = st.text_input("Needed", key=f"ndd_{i}", placeholder="ex: urgent")
                mat_rows.append((item_name, item_spec, item_qty, item_ndd))

        submitted = st.form_submit_button("💾 Enregistrer le Snag", type="primary", use_container_width=True)

        if submitted:
            if not site_id.strip() or not site_name.strip() or not description.strip():
                st.error("⚠️ Champs obligatoires manquants : Site ID, Nom du Site, Description.")
            else:
                res = supabase.table("snags").insert({
                    "site_id": site_id.strip(), "site_name": site_name.strip(),
                    "site_priority": site_priority, "region": region,
                    "pm_auditor": pm_auditor, "audit_date": audit_date.isoformat(),
                    "description": description, "category": category,
                    "sub_category": sub_category, "owner": owner,
                    "action_plan": action_plan, "plan_date": plan_date.isoformat(),
                    "deadline": deadline.isoformat(), "implementer": implementer,
                    "progress": progress, "status": status,
                    "close_date": close_date.isoformat() if close_date else None,
                    "comments": comments, "spare_request": 1 if spare_request else 0,
                    "snag_id_type": snag_id_type, "created_at": now_str()
                }).execute()
                new_id = res.data[0]["id"] if res.data else None
                for (itm, spc, qty_, ndd) in mat_rows:
                    if itm:
                        supabase.table("materials").insert({
                            "snag_id": new_id, "site_id": site_id.strip(),
                            "site_name": site_name.strip(), "item": itm,
                            "specifications": spc, "qty": int(qty_),
                            "needed": ndd, "created_at": now_str()
                        }).execute()
                st.success(f"✅ Snag #{new_id} enregistré avec succès !")
                st.balloons()

# ══════════════════════════════════════════════════════════════════════════════
# LISTE DES SNAGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Liste des Snags":
    st.title("📋 Liste & Suivi des Snags")
    df = load_snags()

    if df.empty:
        st.info("Aucun snag enregistré.")
    else:
        st.markdown("### 🔍 Filtres")
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1: f_region = st.multiselect("Région",         REGIONS)
        with fc2: f_status = st.multiselect("Statut",         STATUSES)
        with fc3: f_subcat = st.multiselect("Sous-Catégorie", SUB_CATEGORIES)
        with fc4: f_owner  = st.multiselect("Owner",          OWNERS)

        mask = pd.Series([True]*len(df))
        if f_region: mask &= df["region"].isin(f_region)
        if f_status: mask &= df["status"].isin(f_status)
        if f_subcat: mask &= df["sub_category"].isin(f_subcat)
        if f_owner:  mask &= df["owner"].isin(f_owner)
        filtered = df[mask].copy()

        filtered["Jours restants"] = filtered["deadline"].apply(days_left)
        filtered["🚦"] = filtered["Jours restants"].apply(alert_icon)

        cols_disp = ["🚦","id","site_id","site_name","region","description",
                     "sub_category","owner","status","plan_date","deadline",
                     "Jours restants","progress","implementer","snag_id_type"]
        st.markdown(f"**{len(filtered)} snag(s)**")
        st.dataframe(filtered[cols_disp].rename(columns={
            "id":"#","site_id":"Site ID","site_name":"Site","region":"Région",
            "description":"Description","sub_category":"Sous-Cat.",
            "owner":"Owner","status":"Statut","plan_date":"Date Plan",
            "deadline":"Deadline","progress":"% Avancement",
            "implementer":"Implémenteur","snag_id_type":"ID Type"
        }), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### ✏️ Mettre à Jour un Snag")
        id_list = filtered["id"].tolist()
        if id_list:
            sel = st.selectbox("Sélectionner l'ID du Snag", id_list,
                format_func=lambda x: f"#{x} – {df[df['id']==x]['site_name'].values[0]} – {df[df['id']==x]['description'].values[0][:50]}")
            row = df[df["id"] == sel].iloc[0]
            with st.form(f"edit_{sel}"):
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    idx_status = STATUSES.index(row["status"]) if row["status"] in STATUSES else 0
                    new_status = st.selectbox("Statut", STATUSES, index=idx_status)
                with ec2:
                    new_progress = st.slider("Progression (%)", 0, 100, int(row["progress"] or 0))
                with ec3:
                    new_implementer = st.text_input("Implémenteur", value=row["implementer"] or "")

                new_action   = st.text_area("Plan d'Action",  value=row["action_plan"] or "")
                new_comments = st.text_area("Commentaires",   value=row["comments"] or "")

                ec4, ec5 = st.columns(2)
                with ec4:
                    try:
                        dl_val = datetime.strptime(str(row["deadline"])[:10], "%Y-%m-%d").date()
                    except Exception:
                        dl_val = date.today()
                    new_deadline = st.date_input("Deadline", value=dl_val)
                with ec5:
                    new_close = None
                    if new_status == "Close":
                        new_close = st.date_input("Date Clôture", value=date.today())

                if st.form_submit_button("💾 Sauvegarder", type="primary"):
                    supabase.table("snags").update({
                        "status": new_status, "progress": new_progress,
                        "implementer": new_implementer, "action_plan": new_action,
                        "comments": new_comments, "deadline": new_deadline.isoformat(),
                        "close_date": new_close.isoformat() if new_close else row["close_date"]
                    }).eq("id", int(sel)).execute()
                    st.success("✅ Snag mis à jour !")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RAPPELS & ALERTES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Rappels & Alertes":
    st.title("🔔 Rappels & Alertes – Deadlines")
    df  = load_snags()
    bdf = load_battery()

    open_snags = df[df["status"] != "Close"].copy() if not df.empty else pd.DataFrame()

    if not open_snags.empty:
        open_snags["days"] = open_snags["deadline"].apply(days_left)
        has_date = open_snags.dropna(subset=["days"]).sort_values("days")

        overdue  = has_date[has_date["days"] < 0]
        critical = has_date[(has_date["days"] >= 0) & (has_date["days"] <= 3)]
        warning  = has_date[(has_date["days"] > 3)  & (has_date["days"] <= 7)]
        caution  = has_date[(has_date["days"] > 7)  & (has_date["days"] <= 14)]

        s1, s2, s3, s4, s5 = st.columns(5)
        for col, val, lbl, bg in [
            (s1, len(overdue),  "🔴 En Retard",     "#c53030"),
            (s2, len(critical), "🔴 Critique ≤3j",  "#e53e3e"),
            (s3, len(warning),  "🟠 Attention ≤7j", "#dd6b20"),
            (s4, len(caution),  "🟡 Vigilance ≤14j","#d69e2e"),
            (s5, len(has_date[has_date["days"] > 14]), "🟢 OK", "#2f855a"),
        ]:
            with col:
                st.markdown(f'<div class="metric-card" style="background:{bg}"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        def render_alerts(grp, title, cls, icon):
            if grp.empty: return
            st.markdown(f"### {icon} {title} ({len(grp)})")
            for _, r in grp.iterrows():
                d = int(r["days"])
                lbl = f"**{abs(d)}j de retard**" if d < 0 else f"**J-{d}**"
                st.markdown(f"""
                <div class="alert-box {cls}">
                    {icon} {lbl} &nbsp;|&nbsp;
                    <b>#{r['id']}</b> – {r['site_name']} ({r['site_id']}) – {r['region']}<br/>
                    📌 {r['description']}<br/>
                    👤 Owner: {r['owner']} &nbsp;|&nbsp; Implémenteur: {r.get('implementer') or '—'}<br/>
                    📅 Deadline: <b>{str(r['deadline'])[:10] if r['deadline'] else '—'}</b>
                    &nbsp;|&nbsp; Statut: {r['status']} ({r['progress']}%)
                </div>
                """, unsafe_allow_html=True)

        render_alerts(overdue,  "Snags EN RETARD",             "a-red",    "🔴")
        render_alerts(critical, "Snags CRITIQUES (≤ 3 jours)", "a-red",    "🔴")
        render_alerts(warning,  "Snags – Attention (≤ 7j)",    "a-orange", "🟠")
        render_alerts(caution,  "Snags – Vigilance (≤ 14j)",   "a-yellow", "🟡")

        no_dl = open_snags[open_snags["deadline"].isna() | (open_snags["deadline"] == "")]
        if not no_dl.empty:
            st.markdown("### ⚪ Snags sans Deadline")
            st.dataframe(no_dl[["id","site_id","site_name","description","owner","status"]], hide_index=True, use_container_width=True)
    else:
        st.success("✅ Aucun snag ouvert avec une deadline imminente !")

    if not bdf.empty:
        bopen = bdf[bdf["status"] == "Open"].copy()
        bopen["days"] = bopen["planned_date"].apply(days_left)
        balert = bopen[bopen["days"].notna() & (bopen["days"] <= 14)].sort_values("days")
        if not balert.empty:
            st.markdown("---")
            st.markdown("### 🔋 Alertes – Plan Remplacement Batteries")
            for _, r in balert.iterrows():
                d = int(r["days"])
                cls  = "a-red" if d <= 3 else ("a-orange" if d <= 7 else "a-yellow")
                icon = "🔴" if d <= 3 else ("🟠" if d <= 7 else "🟡")
                st.markdown(f"""
                <div class="alert-box {cls}">
                    {icon} <b>J-{d}</b> | Site: <b>{r['site_name']}</b> ({r['site_id']}) – {r['region']}<br/>
                    🔋 {r['battery_type']} | Qté: {r['qty']} | Owner: {r['owner']}<br/>
                    📅 Date planifiée: <b>{str(r['planned_date'])[:10] if r['planned_date'] else '—'}</b>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BESOINS MATÉRIELS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔧 Besoins Matériels":
    st.title("🔧 Besoins en Matériels par Site")
    tab_list, tab_add = st.tabs(["📦 Liste des Besoins", "➕ Ajouter un Besoin"])

    with tab_list:
        dfm = load_materials()
        if dfm.empty:
            st.info("Aucun besoin matériel enregistré.")
        else:
            mc1, mc2 = st.columns(2)
            with mc1: f_site = st.multiselect("Site",   dfm["site_name"].unique().tolist())
            with mc2: f_mst  = st.multiselect("Statut", ["Pending","Ordered","Received","Installed"])

            mm = pd.Series([True]*len(dfm))
            if f_site: mm &= dfm["site_name"].isin(f_site)
            if f_mst:  mm &= dfm["status"].isin(f_mst)
            fdfm = dfm[mm]

            st.dataframe(fdfm.rename(columns={
                "id":"#","snag_id":"Snag ID","site_id":"Site ID","site_name":"Site",
                "item":"Article","specifications":"Specs","qty":"Qté",
                "needed":"Needed","status":"Statut","created_at":"Créé le"
            }), use_container_width=True, hide_index=True)

            if not fdfm.empty:
                st.markdown("---")
                st.markdown("### 📊 Résumé par Statut")
                summ = fdfm.groupby(["site_name","status"]).size().reset_index(name="n")
                figm = px.bar(summ, x="site_name", y="n", color="status", barmode="stack",
                              color_discrete_map={"Pending":"#e53e3e","Ordered":"#dd6b20",
                                                  "Received":"#d69e2e","Installed":"#38a169"})
                figm.update_layout(xaxis_title="", yaxis_title="Articles", height=300, margin=dict(t=10,b=10))
                st.plotly_chart(figm, use_container_width=True)

            st.markdown("---")
            st.markdown("### ✏️ Mettre à jour le statut")
            if not fdfm.empty:
                mat_sel = st.selectbox("ID Matériel", fdfm["id"].tolist(),
                    format_func=lambda x: f"#{x} – {dfm[dfm['id']==x]['site_name'].values[0]} – {dfm[dfm['id']==x]['item'].values[0]}")
                new_mst = st.selectbox("Nouveau Statut", ["Pending","Ordered","Received","Installed"])
                if st.button("💾 Mettre à Jour Statut"):
                    supabase.table("materials").update({"status": new_mst}).eq("id", int(mat_sel)).execute()
                    st.success("✅ Statut mis à jour !")
                    st.rerun()

    with tab_add:
        st.markdown("### ➕ Ajouter un besoin matériel")
        snags_df = load_snags()
        with st.form("form_mat"):
            am1, am2 = st.columns(2)
            with am1:
                if not snags_df.empty:
                    snag_ref = st.selectbox("Lier à un Snag",
                        ["Aucun"] + [f"#{r['id']} – {r['site_name']} – {r['description'][:35]}" for _, r in snags_df.iterrows()])
                else:
                    snag_ref = "Aucun"
                    st.info("Aucun snag disponible.")
            with am2:
                mat_site_id = st.text_input("Site ID *")

            mat_site_name = st.text_input("Nom du Site *")
            bm1, bm2, bm3, bm4 = st.columns(4)
            with bm1: mat_item  = st.text_input("Article / Spare *", placeholder="ex: DEEP SEA")
            with bm2: mat_specs = st.text_input("Spécifications")
            with bm3: mat_qty   = st.number_input("Quantité", min_value=1, value=1)
            with bm4: mat_ndd   = st.text_input("Needed")

            mat_st_new = st.selectbox("Statut", ["Pending","Ordered","Received","Installed"])

            if st.form_submit_button("💾 Enregistrer", type="primary", use_container_width=True):
                if not mat_site_id or not mat_site_name or not mat_item:
                    st.error("⚠️ Site ID, Nom et Article sont obligatoires.")
                else:
                    ref_id = None
                    if snag_ref != "Aucun":
                        try: ref_id = int(snag_ref.split("–")[0].replace("#","").strip())
                        except Exception: pass
                    supabase.table("materials").insert({
                        "snag_id": ref_id, "site_id": mat_site_id,
                        "site_name": mat_site_name, "item": mat_item,
                        "specifications": mat_specs, "qty": int(mat_qty),
                        "needed": mat_ndd, "status": mat_st_new,
                        "created_at": now_str()
                    }).execute()
                    st.success("✅ Matériel enregistré !")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PLAN BATTERIES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔋 Plan Batteries":
    st.title("🔋 Plan de Remplacement Batteries Backup")
    st.caption("Modèle : feuille « Backup Battery replacement plan »")

    tab_bv, tab_ba = st.tabs(["📋 Suivi", "➕ Ajouter un Site"])

    with tab_bv:
        bdf = load_battery()
        if bdf.empty:
            st.info("Aucun plan batterie enregistré.")
        else:
            br1, br2 = st.columns(2)
            with br1: fb_reg = st.multiselect("Région", REGIONS)
            with br2: fb_st  = st.multiselect("Statut", ["Open","closed"])

            bm = pd.Series([True]*len(bdf))
            if fb_reg: bm &= bdf["region"].isin(fb_reg)
            if fb_st:  bm &= bdf["status"].isin(fb_st)
            fbdf = bdf[bm].copy()
            fbdf["days"] = fbdf["planned_date"].apply(days_left)
            fbdf["🚦"]  = fbdf["days"].apply(alert_icon)

            bcols = ["🚦","site_id","site_name","region","site_priority",
                     "battery_type","battery_specs","qty","planned_date",
                     "current_autonomy","target_autonomy","battery_health","status","owner"]
            st.dataframe(fbdf[bcols].rename(columns={
                "site_id":"Site ID","site_name":"Site","region":"Région",
                "site_priority":"Priorité","battery_type":"Type Batterie",
                "battery_specs":"Specs","qty":"Qté","planned_date":"Date Planifiée",
                "current_autonomy":"Auto. Actuelle","target_autonomy":"Auto. Cible",
                "battery_health":"Santé","status":"Statut","owner":"Owner"
            }), use_container_width=True, hide_index=True)

            b1, b2, b3 = st.columns(3)
            with b1: st.metric("Total Sites", len(bdf))
            with b2: st.metric("Open",        len(bdf[bdf["status"]=="Open"]))
            with b3: st.metric("Clôturés",    len(bdf[bdf["status"]=="closed"]))

            st.markdown("---")
            st.markdown("### ✏️ Mettre à jour un plan batterie")
            bid_list = fbdf["id"].tolist()
            if bid_list:
                sel_b = st.selectbox("ID Plan Batterie", bid_list,
                    format_func=lambda x: f"#{x} – {bdf[bdf['id']==x]['site_name'].values[0]}")
                brow = bdf[bdf["id"]==sel_b].iloc[0]
                with st.form(f"edit_b_{sel_b}"):
                    bc1, bc2, bc3 = st.columns(3)
                    with bc1:
                        idx_bs = 0 if brow["status"]=="Open" else 1
                        nb_st = st.selectbox("Statut", ["Open","closed"], index=idx_bs)
                    with bc2:
                        health_opts = ["OK","NOK","—"]
                        idx_bh = health_opts.index(brow["battery_health"]) if brow["battery_health"] in health_opts else 2
                        nb_health = st.selectbox("Santé Batterie", health_opts, index=idx_bh)
                    with bc3:
                        nb_auto = st.text_input("Autonomie Actuelle", value=brow["current_autonomy"] or "")
                    nb_actual = st.date_input("Date Réelle Installation", value=date.today())
                    if st.form_submit_button("💾 Mettre à Jour", type="primary"):
                        supabase.table("battery_plan").update({
                            "status": nb_st, "battery_health": nb_health,
                            "current_autonomy": nb_auto,
                            "actual_date": nb_actual.isoformat()
                        }).eq("id", int(sel_b)).execute()
                        st.success("✅ Mis à jour !")
                        st.rerun()

    with tab_ba:
        st.markdown("### ➕ Ajouter un site au plan de remplacement")
        with st.form("form_batt"):
            nb1, nb2, nb3, nb4 = st.columns(4)
            with nb1: nbs_id   = st.text_input("Site ID *",      placeholder="ex: 4106")
            with nb2: nbs_name = st.text_input("Nom du Site *",   placeholder="ex: DOLISIE2")
            with nb3: nbs_reg  = st.selectbox("Région",           REGIONS)
            with nb4: nbs_pri  = st.selectbox("Priorité",         PRIORITIES)

            nb5, nb6 = st.columns(2)
            with nb5: nbs_cat = st.selectbox("Catégorie Site",    SITE_CATEGORIES)
            with nb6: nbs_fu  = st.date_input("Date 1ère Installation", value=date.today())

            nb7, nb8, nb9 = st.columns(3)
            with nb7: nbs_btype = st.text_input("Type Batterie",  placeholder="ex: 6-FMX 12V135Ah")
            with nb8: nbs_bspec = st.text_input("Spécifications", placeholder="ex: 135Ah")
            with nb9: nbs_qty   = st.text_input("Quantité",       placeholder="ex: 8")

            nb10, nb11 = st.columns(2)
            with nb10: nbs_plan  = st.date_input("Date Planifiée Remplacement", value=date.today() + timedelta(days=30))
            with nb11: nbs_owner = st.text_input("Owner",         placeholder="ex: Clevy/Bob")

            nb12, nb13, nb14 = st.columns(3)
            with nb12: nbs_cauto  = st.text_input("Autonomie Actuelle", placeholder="ex: 2hr")
            with nb13: nbs_tauto  = st.text_input("Autonomie Cible",    placeholder="ex: 4hr")
            with nb14: nbs_health = st.selectbox("Santé Batterie",      ["OK","NOK","—"])

            nbs_donor = st.text_input("Donor Site (Site/WH)", placeholder="ex: WH")
            nbs_req   = st.text_input("Requesteur",           placeholder="ex: Prince")

            if st.form_submit_button("💾 Enregistrer", type="primary", use_container_width=True):
                if not nbs_id or not nbs_name:
                    st.error("⚠️ Site ID et Nom sont obligatoires.")
                else:
                    supabase.table("battery_plan").insert({
                        "site_id": nbs_id, "site_name": nbs_name,
                        "region": nbs_reg, "site_priority": nbs_pri,
                        "site_category": nbs_cat,
                        "first_used_date": nbs_fu.isoformat(),
                        "battery_type": nbs_btype, "battery_specs": nbs_bspec,
                        "qty": nbs_qty, "donor_site": nbs_donor,
                        "requestor": nbs_req,
                        "planned_date": nbs_plan.isoformat(),
                        "current_autonomy": nbs_cauto,
                        "target_autonomy": nbs_tauto,
                        "battery_health": nbs_health,
                        "status": "Open", "owner": nbs_owner,
                        "created_at": now_str()
                    }).execute()
                    st.success("✅ Site ajouté au plan de remplacement !")
                    st.rerun()

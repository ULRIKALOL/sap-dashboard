import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import hashlib
from datetime import datetime, time

st.set_page_config(
    page_title="SAP × MRO | Dashboard Gerencial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ADMIN_PASSWORD = hashlib.sha256("admin2024".encode()).hexdigest()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── TOP HEADER ── */
.header-wrap {
    background: linear-gradient(135deg, #0f2942 0%, #1a4a7a 100%);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid rgba(255,255,255,0.08);
}
.header-left h1 { color:#fff; font-size:22px; font-weight:700; margin:0 0 4px 0; letter-spacing:-.3px; }
.header-left p  { color:rgba(255,255,255,.55); font-size:13px; margin:0; }
.header-right { display:flex; gap:20px; }
.header-stat { text-align:right; }
.header-stat .val { color:#fff; font-size:22px; font-weight:700; line-height:1; }
.header-stat .lbl { color:rgba(255,255,255,.5); font-size:11px; margin-top:3px; }

/* ── METRIC CARDS ── */
.kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:24px; }
.kpi { background:#fff; border:1px solid #e8edf3; border-radius:14px; padding:20px 22px; position:relative; overflow:hidden; }
.kpi::before { content:''; position:absolute; top:0; left:0; width:4px; height:100%; border-radius:4px 0 0 4px; }
.kpi.blue::before  { background:#185FA5; }
.kpi.green::before { background:#27a96c; }
.kpi.red::before   { background:#e53935; }
.kpi.amber::before { background:#f59e0b; }
.kpi.purple::before{ background:#7c3aed; }
.kpi-label { font-size:11px; font-weight:600; color:#94a3b8; text-transform:uppercase; letter-spacing:.06em; margin-bottom:8px; }
.kpi-value { font-size:30px; font-weight:700; color:#0f172a; line-height:1; }
.kpi-sub   { font-size:11px; color:#94a3b8; margin-top:5px; }

/* ── SECTION HEADERS ── */
.section-hd {
    font-size:12px; font-weight:700; color:#64748b;
    text-transform:uppercase; letter-spacing:.08em;
    margin:28px 0 14px; padding-bottom:8px;
    border-bottom:2px solid #f1f5f9;
    display:flex; align-items:center; gap:8px;
}

/* ── ALERT BANNER ── */
.alert-red {
    background:#fef2f2; border:1px solid #fecaca; border-left:4px solid #e53935;
    border-radius:10px; padding:14px 18px; margin-bottom:20px;
    font-size:13px; color:#7f1d1d;
}
.alert-amber {
    background:#fffbeb; border:1px solid #fde68a; border-left:4px solid #f59e0b;
    border-radius:10px; padding:14px 18px; margin-bottom:20px;
    font-size:13px; color:#78350f;
}

/* ── PILLS ── */
.pill { display:inline-block; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.pill-green  { background:#dcfce7; color:#166534; }
.pill-red    { background:#fee2e2; color:#991b1b; }
.pill-amber  { background:#fef3c7; color:#92400e; }
.pill-blue   { background:#dbeafe; color:#1e40af; }
.pill-gray   { background:#f1f5f9; color:#475569; }
.pill-purple { background:#ede9fe; color:#5b21b6; }

/* ── TURNO BADGES ── */
.t1 { background:#dbeafe; color:#1e40af; }
.t2 { background:#dcfce7; color:#166534; }
.t3 { background:#fef3c7; color:#92400e; }

/* ── TABLE ── */
.tbl-wrap { background:#fff; border:1px solid #e8edf3; border-radius:14px; overflow:hidden; }
.tbl-title { padding:16px 20px; font-size:13px; font-weight:600; color:#1e293b; border-bottom:1px solid #f1f5f9; display:flex; justify-content:space-between; align-items:center; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] { background:#0f2942 !important; }
section[data-testid="stSidebar"] * { color:#fff !important; }
section[data-testid="stSidebar"] input { color:#0f172a !important; }
section[data-testid="stSidebar"] .stButton button { background:#185FA5 !important; border:none !important; border-radius:8px !important; font-weight:600 !important; }

/* Hide defaults */
#MainMenu {visibility:hidden;} footer{visibility:hidden;}
.stDeployButton{display:none;}
header[data-testid="stHeader"]{display:none;}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in [("data", None), ("is_admin", False), ("last_update", None), ("sap_count", 0), ("mro_count", 0)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_turno(t):
    try:
        if isinstance(t, str):
            parts = t.replace('.', ':').split(':')
            h = int(parts[0]); m = int(parts[1]) if len(parts) > 1 else 0
        elif hasattr(t, 'hour'):
            h, m = t.hour, t.minute
        else:
            return "Sin turno"
        minutos = h * 60 + m
        if 360 <= minutos < 840:   return "T1 (6am–2pm)"
        elif 840 <= minutos < 1290: return "T2 (2pm–9:30pm)"
        else:                       return "T3 (9:30pm–6am)"
    except:
        return "Sin turno"

def parse_num(s):
    try:
        return float(str(s).replace(",", "").replace("$", "").strip())
    except:
        return 0.0

def fmt_mxn(v):
    return f"${v:,.2f}"

def fmt_num(v):
    return f"{v:,.0f}"

def process(sap_file, mro_file):
    # ── LEE SAP ──
    sap = pd.read_excel(sap_file, dtype=str)
    sap.columns = sap.columns.str.strip()

    # Filtra solo movimientos 201
    mov_col = next((c for c in sap.columns if "movement" in c.lower() or "movimiento" in c.lower()), None)
    if mov_col:
        sap = sap[sap[mov_col].astype(str).str.strip() == "201"].copy()

    # Columnas clave SAP
    ref_col   = next((c for c in sap.columns if c.strip().lower() == "reference"), None) or "Reference"
    date_col  = next((c for c in sap.columns if "document date" in c.lower()), None) or "Document Date"
    time_col  = next((c for c in sap.columns if "time of entry" in c.lower()), None) or "Time of Entry"
    mat_col   = next((c for c in sap.columns if c.strip().lower() == "material"), None) or "Material"
    qty_col   = next((c for c in sap.columns if "qty in unit" in c.lower()), None) or "Qty in unit of entry"
    amt_col   = next((c for c in sap.columns if "amount in loc" in c.lower()), None) or "Amount in Loc. Curr."
    user_col  = next((c for c in sap.columns if "user name" in c.lower()), None) or "User Name"
    plant_col = next((c for c in sap.columns if c.strip().lower() == "plant"), None) or "Plant"
    mat_desc  = next((c for c in sap.columns if "material description" in c.lower()), None) or "Material Description"

    sap_clean = pd.DataFrame({
        "Reference":      sap.get(ref_col, ""),
        "Fecha":          sap.get(date_col, ""),
        "Hora":           sap.get(time_col, ""),
        "Material":       sap.get(mat_col, ""),
        "Descripcion":    sap.get(mat_desc, "") if mat_desc in sap.columns else "",
        "Cantidad":       sap.get(qty_col, "0").apply(parse_num),
        "Monto":          sap.get(amt_col, "0").apply(parse_num),
        "Usuario_SAP":    sap.get(user_col, ""),
        "Planta":         sap.get(plant_col, "") if plant_col in sap.columns else "",
    })
    sap_clean["Turno"] = sap_clean["Hora"].apply(get_turno)
    sap_clean["Reference"] = sap_clean["Reference"].astype(str).str.strip()

    # ── LEE MRO ──
    mro = pd.read_excel(mro_file, dtype=str)
    mro.columns = mro.columns.str.strip()

    mro_ref    = next((c for c in mro.columns if c.lower() == "reference"), "Reference")
    mro_status = next((c for c in mro.columns if c.lower() == "status"), "Status")
    mro_user   = next((c for c in mro.columns if c.lower() == "user"), "User")
    mro_apr    = next((c for c in mro.columns if c.lower() == "approver"), "Approver")
    mro_req    = next((c for c in mro.columns if c.lower() == "requester"), "Requester")
    mro_cost   = next((c for c in mro.columns if c.lower() == "totalcost"), "TotalCost")
    mro_cc     = next((c for c in mro.columns if c.lower() == "costcenter"), "CostCenter")
    mro_part   = next((c for c in mro.columns if c.lower() == "partnumber"), "PartNumber")
    mro_qty    = next((c for c in mro.columns if c.lower() == "quantity"), "Quantity")
    mro_folio  = next((c for c in mro.columns if c.lower() == "folio"), "Folio")
    mro_date   = next((c for c in mro.columns if c.lower() == "creationdate"), "CreationDate")
    mro_upd    = next((c for c in mro.columns if c.lower() == "lastupdated"), "LastUpdated")

    mro_map = {}
    for _, row in mro.iterrows():
        key = str(row.get(mro_ref, "") or "").strip()
        if key:
            mro_map[key] = row

    ESTADOS_OK = {"approved", "aprobada", "aprobado", "surtida", "surtido", "completed", "completado"}

    merged = []
    for _, s in sap_clean.iterrows():
        ref = s["Reference"]
        m   = mro_map.get(ref)
        if m is not None:
            status_raw = str(m.get(mro_status, "") or "").strip()
            status_norm = status_raw.lower()
            aprobado = status_norm in ESTADOS_OK
            disc     = not aprobado
            merged.append({
                "Folio":        str(m.get(mro_folio, "—") or "—").strip(),
                "Reference":    ref,
                "Fecha":        s["Fecha"],
                "Turno":        s["Turno"],
                "Material":     s["Material"],
                "Descripcion":  s["Descripcion"],
                "Cantidad_SAP": s["Cantidad"],
                "Monto_SAP":    s["Monto"],
                "Usuario_SAP":  str(s["Usuario_SAP"] or "—").strip(),
                "Planta":       str(s["Planta"] or "—").strip(),
                "Status_MRO":   status_raw,
                "Aprobador":    str(m.get(mro_apr, "—") or "—").strip(),
                "Solicitante":  str(m.get(mro_req, "—") or "—").strip(),
                "CentroCosto":  str(m.get(mro_cc,  "—") or "—").strip(),
                "Monto_MRO":    parse_num(m.get(mro_cost, 0)),
                "Qty_MRO":      parse_num(m.get(mro_qty, 0)),
                "En_MRO":       True,
                "Aprobado":     aprobado,
                "Discrepancia": disc,
            })
        else:
            merged.append({
                "Folio":        "—",
                "Reference":    ref,
                "Fecha":        s["Fecha"],
                "Turno":        s["Turno"],
                "Material":     s["Material"],
                "Descripcion":  s["Descripcion"],
                "Cantidad_SAP": s["Cantidad"],
                "Monto_SAP":    s["Monto"],
                "Usuario_SAP":  str(s["Usuario_SAP"] or "—").strip(),
                "Planta":       str(s["Planta"] or "—").strip(),
                "Status_MRO":   "Sin registro MRO",
                "Aprobador":    "—",
                "Solicitante":  "—",
                "CentroCosto":  "—",
                "Monto_MRO":    0,
                "Qty_MRO":      0,
                "En_MRO":       False,
                "Aprobado":     False,
                "Discrepancia": True,
            })

    df = pd.DataFrame(merged)
    st.session_state.sap_count = len(sap_clean)
    st.session_state.mro_count = len(mro)
    return df

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔐 Admin")
    st.markdown("---")
    if not st.session_state.is_admin:
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Entrar", use_container_width=True, type="primary"):
            if hashlib.sha256(pwd.encode()).hexdigest() == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    else:
        st.success("✅ Sesión admin activa")
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()
        st.markdown("---")
        st.markdown("### 📂 Cargar archivos")
        sap_file = st.file_uploader("Archivo SAP (mov. 201)", type=["xlsx","xls","csv"])
        mro_file = st.file_uploader("Archivo MRO System", type=["xlsx","xls","csv"])
        if sap_file and mro_file:
            if st.button("⚡ Procesar", use_container_width=True, type="primary"):
                with st.spinner("Cruzando datos SAP × MRO..."):
                    try:
                        st.session_state.data = process(sap_file, mro_file)
                        st.session_state.last_update = datetime.now()
                        st.success(f"✅ {len(st.session_state.data):,} registros")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    st.markdown("---")
    st.caption("Solo el admin puede actualizar datos.\nGerencia accede con el link.")

# ── LOGIN EN MAIN (fallback) ──────────────────────────────────────────────────
if not st.session_state.is_admin:
    with st.expander("🔐 Acceso Administrador", expanded=False):
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            p2 = st.text_input("Contraseña", type="password", key="pm")
            if st.button("Entrar", use_container_width=True, type="primary", key="bm"):
                if hashlib.sha256(p2.encode()).hexdigest() == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")

# ── HEADER ────────────────────────────────────────────────────────────────────
last_str = st.session_state.last_update.strftime("%d/%m/%Y %H:%M") if st.session_state.last_update else "Sin datos"
sap_n  = f"{st.session_state.sap_count:,}" if st.session_state.sap_count else "—"
mro_n  = f"{st.session_state.mro_count:,}" if st.session_state.mro_count else "—"

st.markdown(f"""
<div class="header-wrap">
  <div class="header-left">
    <h1>📊 SAP × MRO — Comparativo de Descargas Gerencial</h1>
    <p>Movimientos 201 · Cruce automático con MRO System · Actualizado: {last_str}</p>
  </div>
  <div class="header-right">
    <div class="header-stat"><div class="val">{sap_n}</div><div class="lbl">Mov. SAP 201</div></div>
    <div class="header-stat"><div class="val">{mro_n}</div><div class="lbl">Folios MRO</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── SIN DATOS ─────────────────────────────────────────────────────────────────
if st.session_state.data is None:
    st.markdown("""
    <div style="text-align:center;padding:80px 0;color:#94a3b8">
      <div style="font-size:52px;margin-bottom:16px">📂</div>
      <div style="font-size:17px;font-weight:600;color:#475569;margin-bottom:8px">Sin datos cargados</div>
      <div style="font-size:13px">El administrador debe subir los archivos SAP y MRO System en el panel lateral.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = st.session_state.data

# ── CÁLCULOS GENERALES ────────────────────────────────────────────────────────
total       = len(df)
monto_total = df["Monto_SAP"].sum()
aprobados   = df["Aprobado"].sum()
disc        = df["Discrepancia"].sum()
sin_mro     = (~df["En_MRO"]).sum()
pct_apr     = aprobados / total * 100 if total else 0
monto_disc  = df[df["Discrepancia"]]["Monto_SAP"].sum()

# ── ALERTAS ───────────────────────────────────────────────────────────────────
if sin_mro > 0:
    st.markdown(f"""<div class="alert-red">
    🚨 <strong>{int(sin_mro)} movimientos SAP sin folio en MRO System</strong> — 
    Descargas realizadas sin solicitud registrada. Monto en riesgo: <strong>{fmt_mxn(df[~df['En_MRO']]['Monto_SAP'].sum())}</strong>
    </div>""", unsafe_allow_html=True)

disc_con_mro = df[df["En_MRO"] & df["Discrepancia"]]
if len(disc_con_mro) > 0:
    st.markdown(f"""<div class="alert-amber">
    ⚠️ <strong>{len(disc_con_mro)} descargas con folio MRO en estado no aprobado</strong> — 
    Revisión requerida. Monto involucrado: <strong>{fmt_mxn(disc_con_mro['Monto_SAP'].sum())}</strong>
    </div>""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">📈 Resumen ejecutivo</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""<div class="kpi blue">
    <div class="kpi-label">Total descargas SAP</div>
    <div class="kpi-value">{fmt_num(total)}</div>
    <div class="kpi-sub">Movimientos tipo 201</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi green">
    <div class="kpi-label">Monto total descargado</div>
    <div class="kpi-value" style="font-size:22px">{fmt_mxn(monto_total)}</div>
    <div class="kpi-sub">Suma en moneda local</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi green">
    <div class="kpi-label">Aprobados en MRO</div>
    <div class="kpi-value">{fmt_num(aprobados)}</div>
    <div class="kpi-sub">{pct_apr:.1f}% del total</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi red">
    <div class="kpi-label">Con discrepancia</div>
    <div class="kpi-value">{fmt_num(disc)}</div>
    <div class="kpi-sub">{fmt_mxn(monto_disc)} en riesgo</div>
    </div>""", unsafe_allow_html=True)
with c5:
    st.markdown(f"""<div class="kpi amber">
    <div class="kpi-label">Sin folio MRO</div>
    <div class="kpi-value">{fmt_num(sin_mro)}</div>
    <div class="kpi-sub">Sin solicitud registrada</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ── GRÁFICAS ROW 1 ────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">📊 Análisis de descargas</div>', unsafe_allow_html=True)
g1, g2, g3 = st.columns([1.2, 1, 1])

with g1:
    # Dona — status MRO
    status_counts = df["Status_MRO"].value_counts().reset_index()
    status_counts.columns = ["Status", "Cantidad"]
    COLOR_MAP = {
        "approved":"#27a96c","aprobado":"#27a96c","aprobada":"#27a96c","completed":"#27a96c",
        "rejected":"#e53935","rechazado":"#e53935","rechazada":"#e53935","cancelled":"#e53935","cancelado":"#e53935","cancelada":"#e53935",
        "pending":"#f59e0b","pendiente":"#f59e0b",
        "Sin registro MRO":"#94a3b8",
    }
    colors = [COLOR_MAP.get(s.lower(), "#7c3aed") for s in status_counts["Status"]]
    fig = go.Figure(go.Pie(
        labels=status_counts["Status"],
        values=status_counts["Cantidad"],
        hole=.58,
        marker=dict(colors=colors, line=dict(color="#fff", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11, family="Inter"),
        insidetextorientation="radial",
    ))
    fig.add_annotation(text=f"<b>{total}</b><br><span style='font-size:10px'>total</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(size=16, family="Inter"))
    fig.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10), height=280,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.markdown("**Estado MRO de descargas SAP**")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

with g2:
    # Barras — por turno
    turno_df = df.groupby("Turno").agg(Cantidad=("Cantidad_SAP","sum"), Monto=("Monto_SAP","sum"), Movs=("Reference","count")).reset_index()
    TURNO_C = {"T1 (6am–2pm)":"#3b82f6","T2 (2pm–9:30pm)":"#22c55e","T3 (9:30pm–6am)":"#f59e0b","Sin turno":"#94a3b8"}
    fig2 = go.Figure(go.Bar(
        x=turno_df["Turno"], y=turno_df["Movs"],
        marker=dict(color=[TURNO_C.get(t,"#7c3aed") for t in turno_df["Turno"]], line=dict(width=0)),
        text=turno_df["Movs"], textposition="outside", textfont=dict(size=11),
        hovertemplate="<b>%{x}</b><br>Movimientos: %{y}<extra></extra>",
    ))
    fig2.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10), height=280,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"))
    st.markdown("**Movimientos por turno**")
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

with g3:
    # Barras — monto por turno
    fig3 = go.Figure(go.Bar(
        x=turno_df["Turno"], y=turno_df["Monto"],
        marker=dict(color=[TURNO_C.get(t,"#7c3aed") for t in turno_df["Turno"]], line=dict(width=0)),
        text=[fmt_mxn(v) for v in turno_df["Monto"]], textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Monto: $%{y:,.0f}<extra></extra>",
    ))
    fig3.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10), height=280,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickformat="$,.0f"))
    st.markdown("**Monto descargado por turno**")
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

# ── GRÁFICAS ROW 2 ────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">👤 Aprobadores y usuarios</div>', unsafe_allow_html=True)
g4, g5 = st.columns([1, 1])

with g4:
    apr_df = df[df["Aprobador"] != "—"].groupby("Aprobador").agg(
        Monto=("Monto_SAP","sum"), Movs=("Reference","count")
    ).reset_index().sort_values("Monto", ascending=True).tail(10)
    if len(apr_df):
        fig4 = go.Figure(go.Bar(
            y=apr_df["Aprobador"], x=apr_df["Monto"], orientation="h",
            marker=dict(color="#185FA5", line=dict(width=0)),
            text=[fmt_mxn(v) for v in apr_df["Monto"]], textposition="outside", textfont=dict(size=10),
        ))
        fig4.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=90),
            height=max(260, len(apr_df)*38),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickformat="$,.0f"),
            yaxis=dict(showgrid=False))
        st.markdown("**Top aprobadores por monto autorizado**")
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})
    else:
        st.info("Sin datos de aprobadores")

with g5:
    usr_df = df[df["Usuario_SAP"] != "—"].groupby("Usuario_SAP").agg(
        Monto=("Monto_SAP","sum"), Movs=("Reference","count")
    ).reset_index().sort_values("Monto", ascending=True).tail(10)
    if len(usr_df):
        fig5 = go.Figure(go.Bar(
            y=usr_df["Usuario_SAP"], x=usr_df["Monto"], orientation="h",
            marker=dict(color="#7c3aed", line=dict(width=0)),
            text=[fmt_mxn(v) for v in usr_df["Monto"]], textposition="outside", textfont=dict(size=10),
        ))
        fig5.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=90),
            height=max(260, len(usr_df)*38),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickformat="$,.0f"),
            yaxis=dict(showgrid=False))
        st.markdown("**Usuarios SAP por monto descargado**")
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar":False})
    else:
        st.info("Sin datos de usuarios")

# ── TOP MATERIALES ────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">🔩 Top materiales descargados</div>', unsafe_allow_html=True)
mat_df = df.groupby(["Material","Descripcion"]).agg(
    Cantidad=("Cantidad_SAP","sum"), Monto=("Monto_SAP","sum"), Movs=("Reference","count")
).reset_index().sort_values("Monto", ascending=False).head(10)

if len(mat_df):
    fig6 = go.Figure(go.Bar(
        x=mat_df["Material"] + "<br><sub>" + mat_df["Descripcion"].str[:20],
        y=mat_df["Monto"],
        marker=dict(
            color=mat_df["Monto"],
            colorscale=[[0,"#dbeafe"],[0.5,"#3b82f6"],[1,"#1e3a8a"]],
            line=dict(width=0),
            showscale=False,
        ),
        text=[fmt_mxn(v) for v in mat_df["Monto"]], textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Monto: $%{y:,.2f}<extra></extra>",
    ))
    fig6.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickformat="$,.0f"))
    st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar":False})

# ── TABLA DETALLE ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">📋 Detalle de movimientos</div>', unsafe_allow_html=True)

fc1, fc2, fc3, fc4 = st.columns([2,1,1,1])
with fc1:
    q = st.text_input("🔍 Buscar referencia, folio, material, usuario...", placeholder="Escribe para filtrar")
with fc2:
    opts_status = ["Todos"] + sorted(df["Status_MRO"].unique().tolist())
    f_status = st.selectbox("Estado MRO", opts_status)
with fc3:
    opts_turno = ["Todos"] + sorted(df["Turno"].unique().tolist())
    f_turno = st.selectbox("Turno", opts_turno)
with fc4:
    f_disc = st.selectbox("Discrepancia", ["Todos", "Con discrepancia", "Sin discrepancia"])

dff = df.copy()
if q:
    mask = (
        dff["Reference"].str.contains(q, case=False, na=False) |
        dff["Folio"].str.contains(q, case=False, na=False) |
        dff["Material"].str.contains(q, case=False, na=False) |
        dff["Usuario_SAP"].str.contains(q, case=False, na=False) |
        dff["Aprobador"].str.contains(q, case=False, na=False)
    )
    dff = dff[mask]
if f_status != "Todos":
    dff = dff[dff["Status_MRO"] == f_status]
if f_turno != "Todos":
    dff = dff[dff["Turno"] == f_turno]
if f_disc == "Con discrepancia":
    dff = dff[dff["Discrepancia"]]
elif f_disc == "Sin discrepancia":
    dff = dff[~dff["Discrepancia"]]

st.caption(f"{len(dff):,} registros · {fmt_mxn(dff['Monto_SAP'].sum())} en vista")

disp = dff[["Folio","Reference","Fecha","Turno","Material","Descripcion","Cantidad_SAP","Monto_SAP","Usuario_SAP","Status_MRO","Aprobador","Solicitante","CentroCosto","Discrepancia"]].copy()
disp["Monto_SAP"]    = disp["Monto_SAP"].apply(fmt_mxn)
disp["Cantidad_SAP"] = disp["Cantidad_SAP"].apply(lambda x: f"{x:,.2f}")
disp["Discrepancia"] = disp["Discrepancia"].map({True:"⚠️ Sí", False:"✅ No"})
disp = disp.rename(columns={
    "Folio":"Folio MRO","Reference":"Referencia SAP","Cantidad_SAP":"Cantidad",
    "Monto_SAP":"Monto","Usuario_SAP":"Usuario SAP","Status_MRO":"Estado MRO",
    "Aprobador":"Aprobador MRO","Solicitante":"Solicitante","CentroCosto":"Centro Costo",
})

st.dataframe(disp, use_container_width=True, hide_index=True, height=420)

# ── EXPORTAR ──────────────────────────────────────────────────────────────────
buf = io.BytesIO()
dff.to_excel(buf, index=False, engine="openpyxl")
buf.seek(0)
st.download_button(
    "⬇️ Exportar vista actual (.xlsx)",
    data=buf,
    file_name=f"SAP_MRO_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown("""
<div style='text-align:center;margin-top:40px;padding-top:16px;border-top:1px solid #f1f5f9;
font-size:11px;color:#cbd5e1'>
SAP × MRO Analytics · Dashboard Gerencial · Uso interno exclusivo
</div>""", unsafe_allow_html=True)

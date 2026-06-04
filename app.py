import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import hashlib
from datetime import datetime, date

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

.header-wrap {
    background: linear-gradient(135deg, #0f2942 0%, #1a4a7a 100%);
    border-radius: 16px; padding: 28px 36px; margin-bottom: 20px;
    display: flex; align-items: center; justify-content: space-between;
    border: 1px solid rgba(255,255,255,0.08);
}
.header-left h1 { color:#fff; font-size:22px; font-weight:700; margin:0 0 4px 0; }
.header-left p  { color:rgba(255,255,255,.55); font-size:13px; margin:0; }
.header-right   { display:flex; gap:24px; }
.header-stat .val { color:#fff; font-size:22px; font-weight:700; line-height:1; text-align:right; }
.header-stat .lbl { color:rgba(255,255,255,.5); font-size:11px; margin-top:3px; text-align:right; }

/* Alert unificada */
.alert-unified {
    background:#fff8f0; border:1px solid #fed7aa; border-left:5px solid #ea580c;
    border-radius:12px; padding:18px 22px; margin-bottom:20px;
}
.alert-unified .alert-title { font-size:14px; font-weight:700; color:#9a3412; margin-bottom:10px; }
.alert-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:10px; }
.alert-box { background:#fff; border:1px solid #fed7aa; border-radius:8px; padding:12px 14px; text-align:center; }
.alert-box .aval { font-size:24px; font-weight:700; color:#ea580c; }
.alert-box .albl { font-size:11px; color:#9a3412; margin-top:2px; }
.alert-box .asub { font-size:12px; font-weight:600; color:#7c2d12; margin-top:4px; }

/* Filtros rápidos */
.filter-bar { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px; }
.fbtn {
    padding:7px 16px; border-radius:20px; border:1.5px solid #e2e8f0;
    background:#fff; font-size:12px; font-weight:600; cursor:pointer;
    color:#475569; transition:all .15s;
}
.fbtn.active { background:#0f2942; color:#fff; border-color:#0f2942; }
.fbtn.green  { border-color:#86efac; } .fbtn.green.active  { background:#15803d; border-color:#15803d; }
.fbtn.red    { border-color:#fca5a5; } .fbtn.red.active    { background:#b91c1c; border-color:#b91c1c; }
.fbtn.amber  { border-color:#fcd34d; } .fbtn.amber.active  { background:#b45309; border-color:#b45309; }
.fbtn.purple { border-color:#c4b5fd; } .fbtn.purple.active { background:#6d28d9; border-color:#6d28d9; }
.fbtn.gray   { border-color:#cbd5e1; } .fbtn.gray.active   { background:#475569; border-color:#475569; }

/* KPIs */
.kpi { background:#fff; border:1px solid #e8edf3; border-radius:14px; padding:18px 20px; position:relative; overflow:hidden; }
.kpi::before { content:''; position:absolute; top:0; left:0; width:4px; height:100%; }
.kpi.blue::before   { background:#185FA5; }
.kpi.green::before  { background:#15803d; }
.kpi.red::before    { background:#b91c1c; }
.kpi.amber::before  { background:#b45309; }
.kpi.purple::before { background:#6d28d9; }
.kpi-label { font-size:11px; font-weight:600; color:#94a3b8; text-transform:uppercase; letter-spacing:.06em; margin-bottom:6px; }
.kpi-value { font-size:28px; font-weight:700; color:#0f172a; line-height:1; }
.kpi-sub   { font-size:11px; color:#94a3b8; margin-top:4px; }

.section-hd {
    font-size:12px; font-weight:700; color:#64748b; text-transform:uppercase;
    letter-spacing:.08em; margin:24px 0 12px; padding-bottom:8px;
    border-bottom:2px solid #f1f5f9; display:flex; align-items:center; gap:8px;
}

/* Sidebar */
section[data-testid="stSidebar"] { background:#0f2942 !important; }
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stCaption { color:#fff !important; }
section[data-testid="stSidebar"] input { color:#0f172a !important; }

#MainMenu{visibility:hidden;} footer{visibility:hidden;}
.stDeployButton{display:none;}
header[data-testid="stHeader"]{display:none;}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in [("data", None), ("is_admin", False), ("last_update", None),
             ("sap_count", 0), ("mro_count", 0), ("quick_filter", "Todos")]:
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
        if 360 <= minutos < 840:    return "T1 (6am–2pm)"
        elif 840 <= minutos < 1290: return "T2 (2pm–9:30pm)"
        else:                       return "T3 (9:30pm–6am)"
    except:
        return "Sin turno"

def parse_num(s):
    try:
        return float(str(s).replace(",", "").replace("$", "").strip())
    except:
        return 0.0

def parse_date(s):
    try:
        return pd.to_datetime(s, dayfirst=False, errors='coerce')
    except:
        return pd.NaT

def fmt_mxn(v):
    return f"${abs(v):,.2f}"

def fmt_num(v):
    return f"{int(v):,}"

def process(sap_file, mro_file):
    sap = pd.read_excel(sap_file, dtype=str)
    sap.columns = sap.columns.str.strip()

    mov_col = next((c for c in sap.columns if "movement" in c.lower()), None)
    if mov_col:
        sap = sap[sap[mov_col].astype(str).str.strip() == "201"].copy()

    def fc(df, candidates):
        for cand in candidates:
            for col in df.columns:
                if cand.lower() == col.strip().lower():
                    return col
        for cand in candidates:
            for col in df.columns:
                if cand.lower() in col.strip().lower():
                    return col
        return df.columns[0]

    ref_col   = fc(sap, ["reference"])
    date_col  = fc(sap, ["document date"])
    time_col  = fc(sap, ["time of entry"])
    mat_col   = fc(sap, ["material"])
    qty_col   = fc(sap, ["qty in unit of entry", "qty in unit"])
    amt_col   = fc(sap, ["amount in loc. curr.", "amount in loc"])
    user_col  = fc(sap, ["user name"])
    plant_col = fc(sap, ["plant"])
    desc_col  = fc(sap, ["material description"])
    order_col = fc(sap, ["order"])

    sap_clean = pd.DataFrame({
        "Reference":   sap[ref_col].astype(str).str.strip(),
        "Fecha_dt":    sap[date_col].apply(parse_date),
        "Fecha":       sap[date_col].astype(str),
        "Hora":        sap[time_col].astype(str),
        "Material":    sap[mat_col].astype(str),
        "Descripcion": sap[desc_col].astype(str) if desc_col in sap.columns else "",
        "Cantidad":    sap[qty_col].apply(parse_num),
        "Monto_SAP":   sap[amt_col].apply(parse_num),
        "Usuario_SAP": sap[user_col].astype(str).str.strip(),
        "Planta":      sap[plant_col].astype(str).str.strip() if plant_col in sap.columns else "—",
        "Orden":       sap[order_col].astype(str).str.strip() if order_col in sap.columns else "—",
    })
    sap_clean["Turno"] = sap_clean["Hora"].apply(get_turno)

    mro = pd.read_excel(mro_file, dtype=str)
    mro.columns = mro.columns.str.strip()

    def fm(df, name):
        for col in df.columns:
            if col.strip().lower() == name.lower():
                return col
        return df.columns[0]

    mro_ref    = fm(mro, "reference")
    mro_status = fm(mro, "status")
    mro_user   = fm(mro, "user")
    mro_apr    = fm(mro, "approver")
    mro_req    = fm(mro, "requester")
    mro_cost   = fm(mro, "totalcost")
    mro_cc     = fm(mro, "costcenter")
    mro_part   = fm(mro, "partnumber")
    mro_qty    = fm(mro, "quantity")
    mro_folio  = fm(mro, "folio")
    mro_date   = fm(mro, "creationdate")
    mro_mat    = fm(mro, "materialdoc")

    mro_map = {}
    for _, row in mro.iterrows():
        key = str(row.get(mro_ref, "") or "").strip()
        if key:
            mro_map[key] = row

    ESTADOS_OK = {"approved","aprobada","aprobado","surtida","surtido","completed","completado","autorizado","autorizada"}

    rows = []
    for _, s in sap_clean.iterrows():
        ref = s["Reference"]
        m   = mro_map.get(ref)
        if m is not None:
            status_raw  = str(m.get(mro_status, "") or "").strip()
            status_norm = status_raw.lower()
            aprobado    = status_norm in ESTADOS_OK
            rows.append({
                "Folio":        str(m.get(mro_folio, "—") or "—").strip(),
                "Reference":    ref,
                "Orden":        s["Orden"],
                "Fecha_dt":     s["Fecha_dt"],
                "Fecha":        s["Fecha"],
                "Turno":        s["Turno"],
                "Material":     s["Material"],
                "Descripcion":  s["Descripcion"],
                "Cantidad":     s["Cantidad"],
                "Monto_SAP":    abs(s["Monto_SAP"]),
                "Usuario_SAP":  s["Usuario_SAP"],
                "Planta":       s["Planta"],
                "Status_MRO":   status_raw,
                "Aprobador":    str(m.get(mro_apr, "—") or "—").strip(),
                "Solicitante":  str(m.get(mro_req, "—") or "—").strip(),
                "CentroCosto":  str(m.get(mro_cc,  "—") or "—").strip(),
                "Monto_MRO":    abs(parse_num(m.get(mro_cost, 0))),
                "En_MRO":       True,
                "Aprobado":     aprobado,
                "Discrepancia": not aprobado,
            })
        else:
            rows.append({
                "Folio":        "—",
                "Reference":    ref,
                "Orden":        s["Orden"],
                "Fecha_dt":     s["Fecha_dt"],
                "Fecha":        s["Fecha"],
                "Turno":        s["Turno"],
                "Material":     s["Material"],
                "Descripcion":  s["Descripcion"],
                "Cantidad":     s["Cantidad"],
                "Monto_SAP":    abs(s["Monto_SAP"]),
                "Usuario_SAP":  s["Usuario_SAP"],
                "Planta":       s["Planta"],
                "Status_MRO":   "Sin registro MRO",
                "Aprobador":    "—",
                "Solicitante":  "—",
                "CentroCosto":  "—",
                "Monto_MRO":    0,
                "En_MRO":       False,
                "Aprobado":     False,
                "Discrepancia": True,
            })

    df = pd.DataFrame(rows)
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
                        st.session_state.quick_filter = "Todos"
                        st.success(f"✅ {len(st.session_state.data):,} registros")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    st.markdown("---")
    st.caption("Solo el admin puede actualizar datos.\nGerencia accede con el link.")

# ── LOGIN FALLBACK ────────────────────────────────────────────────────────────
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
sap_n = fmt_num(st.session_state.sap_count) if st.session_state.sap_count else "—"
mro_n = fmt_num(st.session_state.mro_count) if st.session_state.mro_count else "—"

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

df_all = st.session_state.data

# ── FILTROS GLOBALES (fechas + proyecto) ──────────────────────────────────────
st.markdown('<div class="section-hd">🎛 Filtros globales</div>', unsafe_allow_html=True)
fg1, fg2, fg3, fg4 = st.columns([1.2, 1.2, 1, 1])

with fg1:
    fechas_validas = df_all["Fecha_dt"].dropna()
    min_date = fechas_validas.min().date() if len(fechas_validas) else date(2024,1,1)
    max_date = fechas_validas.max().date() if len(fechas_validas) else date.today()
    rango = st.date_input("📅 Rango de fechas", value=(min_date, max_date),
                          min_value=min_date, max_value=max_date)

with fg2:
    plantas = ["Todos"] + sorted(df_all["Planta"].dropna().unique().tolist())
    planta_sel = st.selectbox("🏭 Planta / Proyecto", plantas)

with fg3:
    cc_opts = ["Todos"] + sorted([x for x in df_all["CentroCosto"].unique() if x != "—"])
    cc_sel = st.selectbox("💼 Centro de costo", cc_opts)

with fg4:
    turno_opts = ["Todos"] + sorted(df_all["Turno"].unique().tolist())
    turno_sel = st.selectbox("🕐 Turno", turno_opts)

# Aplica filtros globales
df = df_all.copy()
if isinstance(rango, (list, tuple)) and len(rango) == 2:
    fi, ff = pd.Timestamp(rango[0]), pd.Timestamp(rango[1])
    df = df[(df["Fecha_dt"] >= fi) & (df["Fecha_dt"] <= ff)]
if planta_sel != "Todos":
    df = df[df["Planta"] == planta_sel]
if cc_sel != "Todos":
    df = df[df["CentroCosto"] == cc_sel]
if turno_sel != "Todos":
    df = df[df["Turno"] == turno_sel]

# ── ALERTA UNIFICADA ──────────────────────────────────────────────────────────
total_df    = len(df)
sin_mro     = int((~df["En_MRO"]).sum())
disc_mro    = int((df["En_MRO"] & df["Discrepancia"]).sum())
total_disc  = int(df["Discrepancia"].sum())
monto_riesgo = df[df["Discrepancia"]]["Monto_SAP"].sum()
monto_sinmro = df[~df["En_MRO"]]["Monto_SAP"].sum()
monto_disc_mro = df[df["En_MRO"] & df["Discrepancia"]]["Monto_SAP"].sum()

if total_disc > 0:
    st.markdown(f"""
    <div class="alert-unified">
      <div class="alert-title">⚠️ {fmt_num(total_disc)} referencias SAP descargadas sin autorización válida — Monto total en riesgo: {fmt_mxn(monto_riesgo)}</div>
      <div class="alert-grid">
        <div class="alert-box">
          <div class="aval">{fmt_num(sin_mro)}</div>
          <div class="albl">Sin folio en MRO System</div>
          <div class="asub">{fmt_mxn(monto_sinmro)}</div>
        </div>
        <div class="alert-box">
          <div class="aval">{fmt_num(disc_mro)}</div>
          <div class="albl">Con folio pero no aprobado</div>
          <div class="asub">{fmt_mxn(monto_disc_mro)}</div>
        </div>
        <div class="alert-box">
          <div class="aval">{fmt_num(total_df)}</div>
          <div class="albl">Total mov. en rango</div>
          <div class="asub">{fmt_mxn(df['Monto_SAP'].sum())} total</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── FILTROS RÁPIDOS (botones) ─────────────────────────────────────────────────
st.markdown('<div class="section-hd">⚡ Vista rápida</div>', unsafe_allow_html=True)

QUICK_OPTS = [
    ("Todos",           "gray",   len(df)),
    ("Aprobados",       "green",  int(df["Aprobado"].sum())),
    ("Sin MRO",         "red",    sin_mro),
    ("No aprobado",     "amber",  disc_mro),
    ("T1 (6am–2pm)",    "blue",   int((df["Turno"]=="T1 (6am–2pm)").sum())),
    ("T2 (2pm–9:30pm)", "blue",   int((df["Turno"]=="T2 (2pm–9:30pm)").sum())),
    ("T3 (9:30pm–6am)", "purple", int((df["Turno"]=="T3 (9:30pm–6am)").sum())),
]

cols_btns = st.columns(len(QUICK_OPTS))
for i, (label, color, count) in enumerate(QUICK_OPTS):
    with cols_btns[i]:
        is_active = st.session_state.quick_filter == label
        btn_label = f"{label}\n{fmt_num(count)}"
        if st.button(btn_label, key=f"qf_{label}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.quick_filter = label
            st.rerun()

# Aplica filtro rápido
qf = st.session_state.quick_filter
if qf == "Aprobados":
    df = df[df["Aprobado"]]
elif qf == "Sin MRO":
    df = df[~df["En_MRO"]]
elif qf == "No aprobado":
    df = df[df["En_MRO"] & df["Discrepancia"]]
elif qf in ["T1 (6am–2pm)", "T2 (2pm–9:30pm)", "T3 (9:30pm–6am)"]:
    df = df[df["Turno"] == qf]

# ── KPIs (del filtro activo) ──────────────────────────────────────────────────
st.markdown('<div class="section-hd">📈 Resumen ejecutivo</div>', unsafe_allow_html=True)
total       = len(df)
monto_total = df["Monto_SAP"].sum()
aprobados   = int(df["Aprobado"].sum())
disc        = int(df["Discrepancia"].sum())
pct_apr     = aprobados / total * 100 if total else 0
monto_apr   = df[df["Aprobado"]]["Monto_SAP"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"""<div class="kpi blue"><div class="kpi-label">Descargas en vista</div>
    <div class="kpi-value">{fmt_num(total)}</div><div class="kpi-sub">Mov. 201 filtrados</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi green"><div class="kpi-label">Monto total</div>
    <div class="kpi-value" style="font-size:20px">{fmt_mxn(monto_total)}</div><div class="kpi-sub">Suma en moneda local</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi green"><div class="kpi-label">Aprobados MRO</div>
    <div class="kpi-value">{fmt_num(aprobados)}</div><div class="kpi-sub">{pct_apr:.1f}% · {fmt_mxn(monto_apr)}</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi red"><div class="kpi-label">Con discrepancia</div>
    <div class="kpi-value">{fmt_num(disc)}</div><div class="kpi-sub">{fmt_mxn(df[df['Discrepancia']]['Monto_SAP'].sum())} en riesgo</div></div>""", unsafe_allow_html=True)
with c5:
    avg = monto_total / total if total else 0
    st.markdown(f"""<div class="kpi purple"><div class="kpi-label">Ticket promedio</div>
    <div class="kpi-value" style="font-size:20px">{fmt_mxn(avg)}</div><div class="kpi-sub">Por movimiento</div></div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

# ── GRÁFICAS ROW 1 ────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">📊 Análisis de descargas</div>', unsafe_allow_html=True)
g1, g2, g3 = st.columns([1.2, 1, 1])

COLOR_MAP = {
    "approved":"#15803d","aprobado":"#15803d","aprobada":"#15803d","completed":"#15803d",
    "autorizado":"#15803d","autorizada":"#15803d",
    "rejected":"#b91c1c","rechazado":"#b91c1c","rechazada":"#b91c1c",
    "cancelled":"#b91c1c","cancelado":"#b91c1c","cancelada":"#b91c1c",
    "pending":"#b45309","pendiente":"#b45309",
    "sin registro mro":"#94a3b8",
}
TURNO_C = {"T1 (6am–2pm)":"#3b82f6","T2 (2pm–9:30pm)":"#22c55e","T3 (9:30pm–6am)":"#f59e0b","Sin turno":"#94a3b8"}

with g1:
    sc = df["Status_MRO"].value_counts().reset_index()
    sc.columns = ["Status","Cantidad"]
    colors_pie = [COLOR_MAP.get(s.lower(),"#7c3aed") for s in sc["Status"]]
    fig = go.Figure(go.Pie(
        labels=sc["Status"], values=sc["Cantidad"], hole=.58,
        marker=dict(colors=colors_pie, line=dict(color="#fff",width=2)),
        textinfo="label+percent", textfont=dict(size=11,family="Inter"),
    ))
    fig.add_annotation(text=f"<b>{fmt_num(total)}</b><br>mov.",
        x=0.5, y=0.5, showarrow=False, font=dict(size=14,family="Inter"))
    fig.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10),
        height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.markdown("**Estado MRO de descargas SAP**")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

with g2:
    td = df.groupby("Turno").agg(Movs=("Reference","count"), Monto=("Monto_SAP","sum")).reset_index()
    fig2 = go.Figure(go.Bar(
        x=td["Turno"], y=td["Movs"],
        marker=dict(color=[TURNO_C.get(t,"#7c3aed") for t in td["Turno"]], line=dict(width=0)),
        text=td["Movs"], textposition="outside", textfont=dict(size=11),
    ))
    fig2.update_layout(showlegend=False, margin=dict(t=10,b=20,l=10,r=10), height=280,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"))
    st.markdown("**Movimientos por turno**")
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

with g3:
    fig3 = go.Figure(go.Bar(
        x=td["Turno"], y=td["Monto"],
        marker=dict(color=[TURNO_C.get(t,"#7c3aed") for t in td["Turno"]], line=dict(width=0)),
        text=[fmt_mxn(v) for v in td["Monto"]], textposition="outside", textfont=dict(size=10),
    ))
    fig3.update_layout(showlegend=False, margin=dict(t=10,b=20,l=10,r=10), height=280,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickformat="$,.0f"))
    st.markdown("**Monto descargado por turno**")
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

# ── GRÁFICAS ROW 2 ────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">👤 Aprobadores y usuarios SAP</div>', unsafe_allow_html=True)
g4, g5 = st.columns(2)

with g4:
    apr_df = df[df["Aprobador"]!="—"].groupby("Aprobador").agg(
        Monto=("Monto_SAP","sum"), Movs=("Reference","count")).reset_index().sort_values("Monto",ascending=True).tail(10)
    if len(apr_df):
        fig4 = go.Figure(go.Bar(
            y=apr_df["Aprobador"], x=apr_df["Monto"], orientation="h",
            marker=dict(color="#185FA5", line=dict(width=0)),
            text=[fmt_mxn(v) for v in apr_df["Monto"]], textposition="outside", textfont=dict(size=10),
            customdata=apr_df["Movs"],
            hovertemplate="<b>%{y}</b><br>Monto: $%{x:,.0f}<br>Movimientos: %{customdata}<extra></extra>",
        ))
        fig4.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=90),
            height=max(260,len(apr_df)*38), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True,gridcolor="#f1f5f9",tickformat="$,.0f"),
            yaxis=dict(showgrid=False))
        st.markdown("**Top aprobadores MRO por monto**")
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})

with g5:
    usr_df = df[df["Usuario_SAP"]!="—"].groupby("Usuario_SAP").agg(
        Monto=("Monto_SAP","sum"), Movs=("Reference","count")).reset_index().sort_values("Monto",ascending=True).tail(10)
    if len(usr_df):
        fig5 = go.Figure(go.Bar(
            y=usr_df["Usuario_SAP"], x=usr_df["Monto"], orientation="h",
            marker=dict(color="#7c3aed", line=dict(width=0)),
            text=[fmt_mxn(v) for v in usr_df["Monto"]], textposition="outside", textfont=dict(size=10),
            customdata=usr_df["Movs"],
            hovertemplate="<b>%{y}</b><br>Monto: $%{x:,.0f}<br>Movimientos: %{customdata}<extra></extra>",
        ))
        fig5.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=90),
            height=max(260,len(usr_df)*38), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True,gridcolor="#f1f5f9",tickformat="$,.0f"),
            yaxis=dict(showgrid=False))
        st.markdown("**Usuarios SAP por monto descargado**")
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar":False})

# ── TOP MATERIALES ────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">🔩 Top materiales descargados</div>', unsafe_allow_html=True)
mat_df = df.groupby(["Material","Descripcion"]).agg(
    Cantidad=("Cantidad","sum"), Monto=("Monto_SAP","sum"), Movs=("Reference","count")
).reset_index().sort_values("Monto",ascending=False).head(12)

if len(mat_df):
    etiquetas = (mat_df["Material"] + " — " + mat_df["Descripcion"].str[:25]).tolist()
    fig6 = go.Figure(go.Bar(
        x=mat_df["Monto"], y=etiquetas, orientation="h",
        marker=dict(
            color=mat_df["Monto"],
            colorscale=[[0,"#bfdbfe"],[0.5,"#3b82f6"],[1,"#1e3a8a"]],
            line=dict(width=0), showscale=False,
        ),
        text=[fmt_mxn(v) for v in mat_df["Monto"]], textposition="outside", textfont=dict(size=10),
        customdata=list(zip(mat_df["Cantidad"], mat_df["Movs"])),
        hovertemplate="<b>%{y}</b><br>Monto: $%{x:,.2f}<br>Cantidad: %{customdata[0]:,.2f}<br>Movimientos: %{customdata[1]}<extra></extra>",
    ))
    fig6.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=100),
        height=max(320, len(mat_df)*36),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True,gridcolor="#f1f5f9",tickformat="$,.0f"),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)))
    st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar":False})

# ── TABLA DETALLE ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-hd">📋 Detalle de movimientos</div>', unsafe_allow_html=True)

fc1, fc2, fc3 = st.columns([2,1,1])
with fc1:
    q = st.text_input("🔍 Buscar referencia, folio, material, usuario, aprobador...", placeholder="Escribe para filtrar")
with fc2:
    status_opts = ["Todos"] + sorted(df["Status_MRO"].unique().tolist())
    f_status = st.selectbox("Estado MRO", status_opts)
with fc3:
    f_disc2 = st.selectbox("Discrepancia", ["Todos","Con discrepancia","Sin discrepancia"])

dff = df.copy()
if q:
    mask = (dff["Reference"].str.contains(q,case=False,na=False) |
            dff["Folio"].str.contains(q,case=False,na=False) |
            dff["Material"].str.contains(q,case=False,na=False) |
            dff["Usuario_SAP"].str.contains(q,case=False,na=False) |
            dff["Aprobador"].str.contains(q,case=False,na=False) |
            dff["Descripcion"].str.contains(q,case=False,na=False))
    dff = dff[mask]
if f_status != "Todos":
    dff = dff[dff["Status_MRO"]==f_status]
if f_disc2 == "Con discrepancia":
    dff = dff[dff["Discrepancia"]]
elif f_disc2 == "Sin discrepancia":
    dff = dff[~dff["Discrepancia"]]

st.caption(f"{fmt_num(len(dff))} registros · Monto en vista: {fmt_mxn(dff['Monto_SAP'].sum())}")

disp = dff[["Folio","Reference","Fecha","Turno","Material","Descripcion",
            "Cantidad","Monto_SAP","Usuario_SAP","Planta","Status_MRO",
            "Aprobador","Solicitante","CentroCosto","Discrepancia"]].copy()
disp["Monto_SAP"]  = disp["Monto_SAP"].apply(fmt_mxn)
disp["Cantidad"]   = disp["Cantidad"].apply(lambda x: f"{x:,.2f}")
disp["Discrepancia"] = disp["Discrepancia"].map({True:"⚠️ Sí", False:"✅ No"})
disp = disp.rename(columns={
    "Folio":"Folio MRO","Reference":"Referencia","Cantidad":"Cantidad",
    "Monto_SAP":"Monto","Usuario_SAP":"Usuario SAP","Status_MRO":"Estado MRO",
    "Aprobador":"Aprobador MRO","CentroCosto":"C. Costo",
})
st.dataframe(disp, use_container_width=True, hide_index=True, height=420)

# ── EXPORTAR ──────────────────────────────────────────────────────────────────
buf = io.BytesIO()
dff.drop(columns=["Fecha_dt"], errors="ignore").to_excel(buf, index=False, engine="openpyxl")
buf.seek(0)
st.download_button("⬇️ Exportar vista actual (.xlsx)", data=buf,
    file_name=f"SAP_MRO_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("""<div style='text-align:center;margin-top:40px;padding-top:16px;
border-top:1px solid #f1f5f9;font-size:11px;color:#cbd5e1'>
SAP × MRO Analytics · Dashboard Gerencial · Uso interno exclusivo</div>""",
unsafe_allow_html=True)

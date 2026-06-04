import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io, hashlib
from datetime import datetime, date

st.set_page_config(page_title="SAP × MRO | Gerencial", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

ADMIN_PASSWORD = hashlib.sha256("admin2024".encode()).hexdigest()

ESTADOS_OK = {
    "approved","aprobada","aprobado","surtida","surtido",
    "completed","completado","autorizado","autorizada",
    "supplied","open","released","liberado","liberada",
}

STATUS_COLOR = {
    "approved":      "#15803d",
    "aprobado":      "#15803d",
    "aprobada":      "#15803d",
    "completed":     "#15803d",
    "autorizado":    "#15803d",
    "autorizada":    "#15803d",
    "supplied":      "#0369a1",
    "open":          "#0369a1",
    "released":      "#0369a1",
    "liberado":      "#0369a1",
    "liberada":      "#0369a1",
    "surtida":       "#0369a1",
    "surtido":       "#0369a1",
    "rejected":      "#b91c1c",
    "rechazado":     "#b91c1c",
    "rechazada":     "#b91c1c",
    "cancelled":     "#b91c1c",
    "cancelado":     "#b91c1c",
    "cancelada":     "#b91c1c",
    "pending":       "#b45309",
    "pendiente":     "#b45309",
    "in review":     "#7c3aed",
    "en revision":   "#7c3aed",
    "sin registro mro": "#94a3b8",
}

def status_color(s): return STATUS_COLOR.get(str(s).lower().strip(), "#6366f1")

TURNO_C = {
    "T1 (6am–2pm)":    "#3b82f6",
    "T2 (2pm–9:30pm)": "#22c55e",
    "T3 (9:30pm–6am)": "#f59e0b",
    "Sin turno":        "#94a3b8",
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=DM+Sans:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}

/* ── HEADER ── */
.hdr{
  background:linear-gradient(135deg,#0a1f38 0%,#0f3460 60%,#16213e 100%);
  border-radius:20px;padding:30px 40px;margin-bottom:24px;
  display:flex;align-items:center;justify-content:space-between;
  border:1px solid rgba(255,255,255,.06);
  box-shadow:0 4px 24px rgba(0,0,0,.18);
}
.hdr h1{color:#fff;font-size:21px;font-weight:700;margin:0 0 5px;letter-spacing:-.3px;}
.hdr p{color:rgba(255,255,255,.45);font-size:12px;margin:0;}
.hdr-stats{display:flex;gap:32px;}
.hdr-stat .v{color:#fff;font-size:26px;font-weight:800;line-height:1;text-align:right;}
.hdr-stat .l{color:rgba(255,255,255,.4);font-size:10px;text-transform:uppercase;letter-spacing:.08em;margin-top:4px;text-align:right;}

/* ── KPIs ── */
.krow{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:24px;}
.kcard{
  background:#fff;border-radius:16px;padding:20px 22px;
  border:1px solid #eef2f7;position:relative;overflow:hidden;
  box-shadow:0 1px 8px rgba(15,41,66,.06);
}
.kcard::after{
  content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:3px 3px 0 0;
}
.kcard.blue::after{background:linear-gradient(90deg,#185FA5,#3b82f6);}
.kcard.green::after{background:linear-gradient(90deg,#15803d,#22c55e);}
.kcard.red::after{background:linear-gradient(90deg,#b91c1c,#f87171);}
.kcard.amber::after{background:linear-gradient(90deg,#b45309,#fbbf24);}
.kcard.purple::after{background:linear-gradient(90deg,#6d28d9,#a78bfa);}
.kcard-icon{font-size:22px;margin-bottom:10px;opacity:.8;}
.kcard-lbl{font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:5px;}
.kcard-val{font-size:26px;font-weight:800;color:#0f172a;line-height:1;}
.kcard-sub{font-size:11px;color:#94a3b8;margin-top:5px;}

/* ── SECTION HEADERS ── */
.shd{
  display:flex;align-items:center;gap:10px;
  font-size:11px;font-weight:700;color:#64748b;
  text-transform:uppercase;letter-spacing:.1em;
  margin:28px 0 14px;padding-bottom:10px;
  border-bottom:1.5px solid #f1f5f9;
}
.shd span{background:#f1f5f9;border-radius:6px;padding:3px 8px;font-size:10px;}

/* ── ALERT ── */
.alert-u{
  background:linear-gradient(135deg,#fff8f0,#fff);
  border:1px solid #fed7aa;border-left:5px solid #ea580c;
  border-radius:14px;padding:20px 24px;margin-bottom:20px;
  box-shadow:0 2px 12px rgba(234,88,12,.08);
}
.alert-title{font-size:14px;font-weight:700;color:#9a3412;margin-bottom:12px;display:flex;align-items:center;gap:8px;}
.alert-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.abox{background:#fff;border:1px solid #fed7aa;border-radius:10px;padding:14px 16px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.04);}
.abox .av{font-size:26px;font-weight:800;color:#ea580c;line-height:1;}
.abox .al{font-size:11px;color:#9a3412;margin-top:3px;}
.abox .as{font-size:12px;font-weight:600;color:#7c2d12;margin-top:5px;}

/* ── QUICK FILTER BUTTONS ── */
.stButton button{border-radius:10px!important;font-weight:600!important;font-size:12px!important;transition:all .2s!important;}

/* ── CHART CARDS ── */
.chart-card{
  background:#fff;border-radius:16px;border:1px solid #eef2f7;
  padding:18px 20px;box-shadow:0 1px 8px rgba(15,41,66,.05);
  margin-bottom:16px;
}
.chart-card-title{font-size:13px;font-weight:600;color:#1e293b;margin-bottom:2px;}
.chart-card-sub{font-size:11px;color:#94a3b8;margin-bottom:14px;}

/* ── DIAG BAR ── */
.diag-bar{
  background:#f0fdf4;border:1px solid #bbf7d0;border-left:4px solid #22c55e;
  border-radius:10px;padding:10px 18px;margin-bottom:14px;
  display:flex;gap:28px;align-items:center;flex-wrap:wrap;font-size:12px;color:#14532d;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"]{background:#0a1f38!important;}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stCaption{color:#e2e8f0!important;}
section[data-testid="stSidebar"] input{color:#0f172a!important;}
section[data-testid="stSidebar"] .stButton button{
  background:rgba(255,255,255,.1)!important;color:#fff!important;
  border:1px solid rgba(255,255,255,.2)!important;
}
section[data-testid="stSidebar"] .stButton button:hover{background:rgba(255,255,255,.2)!important;}

/* ── ACTIVE FILTER CHIP ── */
.active-chip{
  display:inline-flex;align-items:center;gap:6px;
  background:#dbeafe;color:#1e40af;border-radius:20px;
  padding:4px 12px;font-size:12px;font-weight:600;margin-bottom:12px;
}

#MainMenu{visibility:hidden;}footer{visibility:hidden;}
.stDeployButton{display:none;}header[data-testid="stHeader"]{display:none;}
div[data-testid="stDecoration"]{display:none;}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
defaults = {
    "data": None, "is_admin": False, "last_update": None,
    "sap_count": 0, "mro_count": 0, "quick_filter": "Todos",
    "matched": 0, "not_matched": 0, "sap_ref_col": "", "mro_ref_col": "",
    "click_filter": None,
    "click_type": None,
    "apr_toggle": "aprobador",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Invalida datos viejos que no tengan las columnas actuales
REQUIRED_COLS = {"Proyecto", "Fecha_dt", "Monto_SAP", "Turno", "Solicitante", "En_MRO", "Discrepancia"}
if st.session_state.data is not None:
    if not REQUIRED_COLS.issubset(set(st.session_state.data.columns)):
        st.session_state.data        = None
        st.session_state.last_update = None
        st.session_state.sap_count   = 0
        st.session_state.mro_count   = 0
        st.session_state.matched     = 0
        st.session_state.not_matched = 0

# ── HELPERS ────────────────────────────────────────────────────────────────────
def get_turno(t):
    try:
        if isinstance(t, str):
            parts = t.replace('.', ':').split(':')
            h = int(parts[0]); m = int(parts[1]) if len(parts) > 1 else 0
        elif hasattr(t, 'hour'):
            h, m = t.hour, t.minute
        else:
            return "Sin turno"
        mins = h * 60 + m
        if 360 <= mins < 840:    return "T1 (6am–2pm)"
        elif 840 <= mins < 1290: return "T2 (2pm–9:30pm)"
        else:                    return "T3 (9:30pm–6am)"
    except:
        return "Sin turno"

def parse_num(s):
    try:   return float(str(s).replace(",","").replace("$","").strip())
    except: return 0.0

def parse_date(s):
    try:   return pd.to_datetime(s, dayfirst=False, errors='coerce')
    except: return pd.NaT

def fmt_mxn(v): return f"${abs(v):,.0f}"
def fmt_mxn2(v): return f"${abs(v):,.2f}"
def fmt_num(v): return f"{int(v):,}"

def highlight_bar(values, selected, colors, dim="#dde3ec"):
    """Resalta la barra seleccionada, opaca las demás."""
    if selected is None:
        return colors
    return [c if v == selected else dim for v, c in zip(values, colors)]

# ── PROCESS ────────────────────────────────────────────────────────────────────
def process(sap_file, mro_file):
    sap = pd.read_excel(sap_file, dtype=str)
    sap.columns = sap.columns.str.strip()

    mov_col = next((c for c in sap.columns if "movement type" in c.lower()), None)
    if not mov_col:
        mov_col = next((c for c in sap.columns if "movement" in c.lower()), None)
    if mov_col:
        sap = sap[sap[mov_col].astype(str).str.strip() == "201"].copy()

    def fc(df, *exact):
        cl = {c.strip().lower(): c for c in df.columns}
        for e in exact:
            if e.lower() in cl: return cl[e.lower()]
        for e in exact:
            for k, v2 in cl.items():
                if e.lower() in k: return v2
        return None

    ref_col    = fc(sap, "Reference")
    date_col   = fc(sap, "Document Date")
    time_col   = fc(sap, "Time of Entry")
    mat_col    = fc(sap, "Material")
    qty_col    = fc(sap, "Qty in unit of entry", "Qty in unit")
    amt_col    = fc(sap, "Amount in Loc. Curr.", "Amount in Loc")
    user_col   = fc(sap, "User Name")
    plant_col  = fc(sap, "Plant")
    desc_col   = fc(sap, "Material Description")
    matgrp_col = fc(sap, "Material Group")

    def sc(col, default="—"):
        if col and col in sap.columns:
            return sap[col].astype(str).str.strip()
        return pd.Series([default] * len(sap), index=sap.index)

    sap_clean = pd.DataFrame({
        "Reference":   sc(ref_col, "SIN_REF"),
        "Fecha_dt":    sc(date_col, "").apply(parse_date),
        "Fecha":       sc(date_col, "—"),
        "Hora":        sc(time_col, "0"),
        "Material":    sc(mat_col, "—"),
        "Descripcion": sc(desc_col, "—"),
        "Cantidad":    sc(qty_col, "0").apply(parse_num),
        "Monto_SAP":   sc(amt_col, "0").apply(parse_num),
        "Usuario_SAP": sc(user_col, "—"),
        "Planta":      sc(plant_col, "—"),
        "Proyecto":    sc(matgrp_col, "—"),
    })
    sap_clean["Turno"]     = sap_clean["Hora"].apply(get_turno)
    sap_clean["Reference"] = sap_clean["Reference"].str.strip().str.upper()

    mro = pd.read_excel(mro_file, dtype=str)
    mro.columns = mro.columns.str.strip()

    def fm(df, *names):
        cl = {c.strip().lower(): c for c in df.columns}
        for n in names:
            if n.lower() in cl: return cl[n.lower()]
        return None

    mro_ref    = fm(mro, "reference")
    mro_status = fm(mro, "status")
    mro_apr    = fm(mro, "approver")
    mro_req    = fm(mro, "requester")
    mro_cost   = fm(mro, "totalcost")
    mro_cc     = fm(mro, "costcenter")
    mro_folio  = fm(mro, "folio")

    if not mro_ref:
        raise ValueError(f"No encontré 'Reference' en MRO. Columnas: {list(mro.columns)}")
    if not mro_status:
        raise ValueError(f"No encontré 'Status' en MRO. Columnas: {list(mro.columns)}")

    mro_map = {}
    for _, row in mro.iterrows():
        key = str(row[mro_ref] or "").strip().upper()
        if key and key not in ("NAN", ""):
            mro_map[key] = row

    matched = 0; not_matched = 0
    rows = []
    for _, s in sap_clean.iterrows():
        ref = s["Reference"]
        m   = mro_map.get(ref)
        if m is not None:
            matched += 1
            status_raw = str(m[mro_status] or "").strip()
            aprobado   = status_raw.lower().strip() in ESTADOS_OK
            rows.append({
                "Folio":       str(m[mro_folio] if mro_folio else "—").strip(),
                "Reference":   ref,
                "Fecha_dt":    s["Fecha_dt"],
                "Fecha":       s["Fecha"],
                "Turno":       s["Turno"],
                "Material":    s["Material"],
                "Descripcion": s["Descripcion"],
                "Proyecto":    s["Proyecto"],
                "Cantidad":    s["Cantidad"],
                "Monto_SAP":   abs(s["Monto_SAP"]),
                "Usuario_SAP": s["Usuario_SAP"],
                "Planta":      s["Planta"],
                "Status_MRO":  status_raw,
                "Aprobador":   str(m[mro_apr] if mro_apr else "—").strip(),
                "Solicitante": str(m[mro_req] if mro_req else "—").strip(),
                "CentroCosto": str(m[mro_cc]  if mro_cc  else "—").strip(),
                "Monto_MRO":   abs(parse_num(m[mro_cost] if mro_cost else 0)),
                "En_MRO":      True,
                "Aprobado":    aprobado,
                "Discrepancia":not aprobado,
            })
        else:
            not_matched += 1
            rows.append({
                "Folio":"—","Reference":ref,
                "Fecha_dt":s["Fecha_dt"],"Fecha":s["Fecha"],
                "Turno":s["Turno"],"Material":s["Material"],
                "Descripcion":s["Descripcion"],"Proyecto":s["Proyecto"],
                "Cantidad":s["Cantidad"],"Monto_SAP":abs(s["Monto_SAP"]),
                "Usuario_SAP":s["Usuario_SAP"],"Planta":s["Planta"],
                "Status_MRO":"Sin registro MRO",
                "Aprobador":"—","Solicitante":"—","CentroCosto":"—","Monto_MRO":0,
                "En_MRO":False,"Aprobado":False,"Discrepancia":True,
            })

    st.session_state.sap_count   = len(sap_clean)
    st.session_state.mro_count   = len(mro)
    st.session_state.matched     = matched
    st.session_state.not_matched = not_matched
    st.session_state.sap_ref_col = ref_col or "No encontrada"
    st.session_state.mro_ref_col = mro_ref or "No encontrada"
    return pd.DataFrame(rows)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔐 Admin")
    st.markdown("---")
    if not st.session_state.is_admin:
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Entrar", use_container_width=True, type="primary"):
            if hashlib.sha256(pwd.encode()).hexdigest() == ADMIN_PASSWORD:
                st.session_state.is_admin = True; st.rerun()
            else:
                st.error("Contraseña incorrecta")
    else:
        st.success("✅ Sesión admin activa")
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.is_admin = False; st.rerun()
        st.markdown("---")
        st.markdown("### 📂 Cargar archivos")
        sap_file = st.file_uploader("Archivo SAP (mov. 201)", type=["xlsx","xls","csv"])
        mro_file = st.file_uploader("Archivo MRO System",     type=["xlsx","xls","csv"])
        if sap_file and mro_file:
            if st.button("⚡ Procesar", use_container_width=True, type="primary"):
                with st.spinner("Cruzando datos SAP × MRO..."):
                    try:
                        st.session_state.data = process(sap_file, mro_file)
                        st.session_state.last_update = datetime.now()
                        st.session_state.quick_filter = "Todos"
                        st.session_state.click_filter = None
                        st.session_state.click_type   = None
                        st.success(f"✅ {len(st.session_state.data):,} registros")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    st.markdown("---")
    st.caption("Solo el admin puede actualizar.\nGerencia accede con el link.")

# ── LOGIN FALLBACK ─────────────────────────────────────────────────────────────
if not st.session_state.is_admin:
    with st.expander("🔐 Acceso Administrador", expanded=False):
        _, c2, _ = st.columns([1, 1, 1])
        with c2:
            p2 = st.text_input("Contraseña", type="password", key="pm")
            if st.button("Entrar", use_container_width=True, type="primary", key="bm"):
                if hashlib.sha256(p2.encode()).hexdigest() == ADMIN_PASSWORD:
                    st.session_state.is_admin = True; st.rerun()
                else:
                    st.error("Contraseña incorrecta")

# ── HEADER ─────────────────────────────────────────────────────────────────────
last_str = st.session_state.last_update.strftime("%d/%m/%Y %H:%M") if st.session_state.last_update else "Sin datos"
sap_n = fmt_num(st.session_state.sap_count) if st.session_state.sap_count else "—"
mro_n = fmt_num(st.session_state.mro_count) if st.session_state.mro_count else "—"

st.markdown(f"""
<div class="hdr">
  <div class="header-left">
    <h1>📊 SAP × MRO — Dashboard Gerencial</h1>
    <p>Movimientos tipo 201 · Cruce automático por Reference · Actualizado: {last_str}</p>
  </div>
  <div class="hdr-stats">
    <div class="hdr-stat"><div class="v">{sap_n}</div><div class="l">Mov. SAP 201</div></div>
    <div class="hdr-stat"><div class="v">{mro_n}</div><div class="l">Folios MRO</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.data is None:
    st.markdown("""<div style="text-align:center;padding:100px 0;color:#94a3b8">
      <div style="font-size:56px;margin-bottom:20px">📂</div>
      <div style="font-size:18px;font-weight:700;color:#475569;margin-bottom:8px">Sin datos cargados</div>
      <div style="font-size:13px">El administrador debe subir los archivos en el panel lateral izquierdo.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

df_all = st.session_state.data

# ── DIAGNÓSTICO ────────────────────────────────────────────────────────────────
if st.session_state.matched + st.session_state.not_matched > 0:
    tot_m = st.session_state.matched + st.session_state.not_matched
    pct   = st.session_state.matched / tot_m * 100
    st.markdown(f"""
    <div class="diag-bar">
      <span>🔗 <strong>Cruce SAP × MRO</strong></span>
      <span>Col. SAP: <strong>{st.session_state.sap_ref_col}</strong></span>
      <span>Col. MRO: <strong>{st.session_state.mro_ref_col}</strong></span>
      <span>Encontrados: <strong>{st.session_state.matched:,}</strong></span>
      <span>Sin match: <strong>{st.session_state.not_matched:,}</strong></span>
      <span>% cruce: <strong>{pct:.1f}%</strong></span>
    </div>""", unsafe_allow_html=True)

# ── FILTROS GLOBALES ───────────────────────────────────────────────────────────
st.markdown('<div class="shd">🎛 <span>Filtros globales</span></div>', unsafe_allow_html=True)
fg1, fg2, fg3, fg4 = st.columns([1.4, 1.2, 1, 1])

with fg1:
    fv = df_all["Fecha_dt"].dropna()
    mn = fv.min().date() if len(fv) else date(2024, 1, 1)
    mx = fv.max().date() if len(fv) else date.today()
    rango = st.date_input("📅 Rango de fechas", value=(mn, mx), min_value=mn, max_value=mx)
with fg2:
    proyectos = ["Todos"] + sorted([x for x in df_all["Proyecto"].dropna().unique()
                                    if x not in ("—","nan","NAN","")])
    proy_sel = st.selectbox("📦 Proyecto (Material Group)", proyectos)
with fg3:
    cc_opts = ["Todos"] + sorted([x for x in df_all["CentroCosto"].unique()
                                  if x not in ("—","nan","")])
    cc_sel = st.selectbox("💼 Centro de costo", cc_opts)
with fg4:
    turno_opts = ["Todos"] + sorted(df_all["Turno"].unique().tolist())
    turno_sel = st.selectbox("🕐 Turno", turno_opts)

# Aplica filtros globales
df = df_all.copy()
if isinstance(rango, (list, tuple)) and len(rango) == 2:
    df = df[(df["Fecha_dt"] >= pd.Timestamp(rango[0])) &
            (df["Fecha_dt"] <= pd.Timestamp(rango[1]))]
if proy_sel  != "Todos": df = df[df["Proyecto"]    == proy_sel]
if cc_sel    != "Todos": df = df[df["CentroCosto"] == cc_sel]
if turno_sel != "Todos": df = df[df["Turno"]       == turno_sel]

# ── ALERTA UNIFICADA ───────────────────────────────────────────────────────────
sin_mro    = int((~df["En_MRO"]).sum())
disc_mro   = int((df["En_MRO"] & df["Discrepancia"]).sum())
total_disc = int(df["Discrepancia"].sum())
m_riesgo   = df[df["Discrepancia"]]["Monto_SAP"].sum()
m_sinmro   = df[~df["En_MRO"]]["Monto_SAP"].sum()
m_discmro  = df[df["En_MRO"] & df["Discrepancia"]]["Monto_SAP"].sum()

if total_disc > 0:
    st.markdown(f"""
    <div class="alert-u">
      <div class="alert-title">⚠️ {fmt_num(total_disc)} referencias descargadas sin autorización válida
        <span style="font-weight:400;font-size:13px">— Monto en riesgo: <strong>{fmt_mxn2(m_riesgo)}</strong></span>
      </div>
      <div class="alert-grid">
        <div class="abox"><div class="av">{fmt_num(sin_mro)}</div>
          <div class="al">Sin folio en MRO System</div><div class="as">{fmt_mxn(m_sinmro)}</div></div>
        <div class="abox"><div class="av">{fmt_num(disc_mro)}</div>
          <div class="al">Folio MRO no aprobado</div><div class="as">{fmt_mxn(m_discmro)}</div></div>
        <div class="abox"><div class="av">{fmt_num(len(df))}</div>
          <div class="al">Total mov. en rango</div><div class="as">{fmt_mxn(df['Monto_SAP'].sum())} total</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

# ── FILTROS RÁPIDOS ────────────────────────────────────────────────────────────
st.markdown('<div class="shd">⚡ <span>Vista rápida</span></div>', unsafe_allow_html=True)
QUICK = [
    ("Todos",           len(df)),
    ("Aprobados",       int(df["Aprobado"].sum())),
    ("Sin MRO",         sin_mro),
    ("No aprobado",     disc_mro),
    ("T1 (6am–2pm)",    int((df["Turno"]=="T1 (6am–2pm)").sum())),
    ("T2 (2pm–9:30pm)", int((df["Turno"]=="T2 (2pm–9:30pm)").sum())),
    ("T3 (9:30pm–6am)", int((df["Turno"]=="T3 (9:30pm–6am)").sum())),
]
cols_b = st.columns(len(QUICK))
for i, (label, count) in enumerate(QUICK):
    with cols_b[i]:
        active = st.session_state.quick_filter == label
        if st.button(f"{label}\n{fmt_num(count)}", key=f"qf_{label}",
                     use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.quick_filter = label
            st.session_state.click_filter = None
            st.session_state.click_type   = None
            st.rerun()

# Aplica filtro rápido
qf = st.session_state.quick_filter
if qf == "Aprobados":       df = df[df["Aprobado"]]
elif qf == "Sin MRO":       df = df[~df["En_MRO"]]
elif qf == "No aprobado":   df = df[df["En_MRO"] & df["Discrepancia"]]
elif qf in ["T1 (6am–2pm)","T2 (2pm–9:30pm)","T3 (9:30pm–6am)"]:
    df = df[df["Turno"] == qf]

# ── CROSS-FILTER (click en gráficas) ─────────────────────────────────────────
cf_val  = st.session_state.click_filter
cf_type = st.session_state.click_type

if cf_val and cf_type:
    col_map = {
        "aprobador": "Aprobador",
        "usuario":   "Usuario_SAP",
        "status":    "Status_MRO",
        "turno":     "Turno",
        "material":  "Material",
    }
    col = col_map.get(cf_type)
    if col and col in df.columns:
        df = df[df[col] == cf_val]
    st.markdown(f"""<div class="active-chip">
      🔍 Filtro activo: <strong>{cf_val}</strong>
      &nbsp;&nbsp;<a href="?clear=1" style="color:#1e40af;text-decoration:none;font-size:11px"
      onclick="window.location.href=window.location.pathname">✕ Limpiar</a>
    </div>""", unsafe_allow_html=True)
    if st.button("✕ Limpiar filtro de gráfica", key="clear_cf"):
        st.session_state.click_filter = None
        st.session_state.click_type   = None
        st.rerun()

# ── KPIs ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="shd">📈 <span>Resumen ejecutivo</span></div>', unsafe_allow_html=True)
total   = len(df)
m_total = df["Monto_SAP"].sum()
apr_n   = int(df["Aprobado"].sum())
disc_n  = int(df["Discrepancia"].sum())
pct_apr = apr_n / total * 100 if total else 0
m_apr   = df[df["Aprobado"]]["Monto_SAP"].sum()
avg_t   = m_total / total if total else 0

c1,c2,c3,c4,c5 = st.columns(5)
kpis = [
    (c1,"blue","📦","Descargas en vista",fmt_num(total),"Movimientos tipo 201"),
    (c2,"green","💰","Monto total",fmt_mxn(m_total),"Suma en moneda local"),
    (c3,"green","✅","Aprobados MRO",fmt_num(apr_n),f"{pct_apr:.1f}% · {fmt_mxn(m_apr)}"),
    (c4,"red","⚠️","Con discrepancia",fmt_num(disc_n),f"{fmt_mxn(df[df['Discrepancia']]['Monto_SAP'].sum())} en riesgo"),
    (c5,"purple","📊","Ticket promedio",fmt_mxn(avg_t),"Por movimiento"),
]
for col, color, icon, lbl, val, sub in kpis:
    with col:
        st.markdown(f"""<div class="kcard {color}">
          <div class="kcard-icon">{icon}</div>
          <div class="kcard-lbl">{lbl}</div>
          <div class="kcard-val">{val}</div>
          <div class="kcard-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

# ── CHART HELPERS ──────────────────────────────────────────────────────────────
def bar_layout(height=300):
    return dict(
        showlegend=False, height=height,
        margin=dict(t=10, b=10, l=10, r=110),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans"),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickformat="$,.0f"),
        yaxis=dict(showgrid=False, tickfont=dict(size=11)),
    )

def bar_layout_v(height=280):
    return dict(
        showlegend=False, height=height,
        margin=dict(t=20, b=20, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans"),
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False),
    )

def make_hbar(y_vals, x_vals, colors, texts, customdata, hover, cf_col, height=300):
    sel = st.session_state.click_filter if st.session_state.click_type == cf_col else None
    bar_colors = highlight_bar(y_vals, sel, colors)
    fig = go.Figure(go.Bar(
        y=y_vals, x=x_vals, orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=texts, textposition="outside", textfont=dict(size=10),
        customdata=customdata, hovertemplate=hover,
    ))
    fig.update_layout(**bar_layout(height))
    return fig

# ── GRÁFICAS ROW 1: ESTADO + TURNOS ───────────────────────────────────────────
st.markdown('<div class="shd">📊 <span>Distribución de descargas</span></div>', unsafe_allow_html=True)
g1, g2, g3 = st.columns([1.3, 1, 1])

with g1:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-card-title">Estado MRO</div><div class="chart-card-sub">Distribución por status · haz clic para filtrar</div>', unsafe_allow_html=True)
    sc2 = df["Status_MRO"].value_counts().reset_index()
    sc2.columns = ["Status", "Cantidad"]
    colors_pie  = [status_color(s) for s in sc2["Status"]]
    fig_dona = go.Figure(go.Pie(
        labels=sc2["Status"], values=sc2["Cantidad"], hole=.60,
        marker=dict(colors=colors_pie, line=dict(color="#fff", width=2.5)),
        textinfo="label+percent", textfont=dict(size=11, family="DM Sans"),
        customdata=sc2["Status"],
        hovertemplate="<b>%{label}</b><br>Cantidad: %{value:,}<br>%{percent}<extra></extra>",
    ))
    fig_dona.add_annotation(
        text=f"<b>{fmt_num(total)}</b><br><span style='font-size:11px'>mov.</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(size=16, family="DM Sans"))
    fig_dona.update_layout(showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5, font=dict(size=10)),
        margin=dict(t=10, b=10, l=10, r=120), height=280,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    sel_dona = st.plotly_chart(fig_dona, use_container_width=True,
        config={"displayModeBar": False}, on_select="rerun", key="dona_status")
    if sel_dona and sel_dona.get("selection") and sel_dona["selection"].get("points"):
        pt = sel_dona["selection"]["points"][0]
        lbl = pt.get("label")
        if lbl and lbl != st.session_state.click_filter:
            st.session_state.click_filter = lbl
            st.session_state.click_type   = "status"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with g2:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-card-title">Movimientos por turno</div><div class="chart-card-sub">Cantidad de descargas</div>', unsafe_allow_html=True)
    td = df.groupby("Turno").agg(Movs=("Reference","count"), Monto=("Monto_SAP","sum")).reset_index()
    t_colors = [TURNO_C.get(t, "#6366f1") for t in td["Turno"]]
    sel_t = st.session_state.click_filter if st.session_state.click_type == "turno" else None
    t_bar_colors = highlight_bar(td["Turno"].tolist(), sel_t, t_colors)
    fig_t = go.Figure(go.Bar(
        x=td["Turno"], y=td["Movs"],
        marker=dict(color=t_bar_colors, line=dict(width=0)),
        text=td["Movs"], textposition="outside", textfont=dict(size=11),
        customdata=td["Turno"],
        hovertemplate="<b>%{x}</b><br>Movimientos: %{y:,}<extra></extra>",
    ))
    fig_t.update_layout(**bar_layout_v(260))
    sel_turno = st.plotly_chart(fig_t, use_container_width=True,
        config={"displayModeBar": False}, on_select="rerun", key="bar_turno")
    if sel_turno and sel_turno.get("selection") and sel_turno["selection"].get("points"):
        pt = sel_turno["selection"]["points"][0]
        lbl = pt.get("x") or pt.get("label")
        if lbl and lbl != st.session_state.click_filter:
            st.session_state.click_filter = lbl
            st.session_state.click_type   = "turno"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with g3:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-card-title">Monto por turno</div><div class="chart-card-sub">Suma en moneda local</div>', unsafe_allow_html=True)
    fig_mt = go.Figure(go.Bar(
        x=td["Turno"], y=td["Monto"],
        marker=dict(color=t_bar_colors, line=dict(width=0)),
        text=[fmt_mxn(v) for v in td["Monto"]], textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Monto: $%{y:,.0f}<extra></extra>",
    ))
    fig_mt.update_layout(**bar_layout_v(260))
    fig_mt.update_layout(yaxis=dict(tickformat="$,.0f", showgrid=True, gridcolor="#f1f5f9"))
    st.plotly_chart(fig_mt, use_container_width=True, config={"displayModeBar": False}, key="bar_monto_t")
    st.markdown('</div>', unsafe_allow_html=True)

# ── GRÁFICAS ROW 2: APROBADORES/REQUESTER + USUARIOS SAP ──────────────────────
st.markdown('<div class="shd">👤 <span>Aprobadores y usuarios SAP</span></div>', unsafe_allow_html=True)
g4, g5 = st.columns(2)

# ── Columna izquierda: toggle Aprobador / Requester ───────────────────────────
with g4:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)

    # Toggle buttons
    t_col1, t_col2, _ = st.columns([1, 1, 2])
    with t_col1:
        apr_active = st.session_state.get("apr_toggle", "aprobador") == "aprobador"
        if st.button("👤 Aprobador", key="toggle_apr",
                     type="primary" if apr_active else "secondary",
                     use_container_width=True):
            st.session_state.apr_toggle = "aprobador"
            # limpiar cross-filter si era del otro tipo
            if st.session_state.click_type in ("aprobador","requester"):
                st.session_state.click_filter = None
                st.session_state.click_type   = None
            st.rerun()
    with t_col2:
        req_active = st.session_state.get("apr_toggle", "aprobador") == "requester"
        if st.button("📋 Requester", key="toggle_req",
                     type="primary" if req_active else "secondary",
                     use_container_width=True):
            st.session_state.apr_toggle = "requester"
            if st.session_state.click_type in ("aprobador","requester"):
                st.session_state.click_filter = None
                st.session_state.click_type   = None
            st.rerun()

    modo = st.session_state.get("apr_toggle", "aprobador")

    if modo == "aprobador":
        st.markdown('<div class="chart-card-title" style="margin-top:10px">Top aprobadores MRO</div><div class="chart-card-sub">Por monto autorizado · haz clic para filtrar</div>', unsafe_allow_html=True)
        ad = df[df["Aprobador"] != "—"].groupby("Aprobador").agg(
            Monto=("Monto_SAP","sum"), Movs=("Reference","count")
        ).reset_index().sort_values("Monto", ascending=True).tail(10)
        cf_type_check = "aprobador"
        col_y = "Aprobador"
        data_df = ad
        bar_color_base = "#185FA5"
        empty_msg = "Sin datos de aprobadores en esta vista"
    else:
        st.markdown('<div class="chart-card-title" style="margin-top:10px">Top requesters / solicitantes</div><div class="chart-card-sub">Por monto solicitado · haz clic para filtrar</div>', unsafe_allow_html=True)
        ad = df[df["Solicitante"] != "—"].groupby("Solicitante").agg(
            Monto=("Monto_SAP","sum"), Movs=("Reference","count")
        ).reset_index().sort_values("Monto", ascending=True).tail(10)
        cf_type_check = "requester"
        col_y = "Solicitante"
        data_df = ad
        bar_color_base = "#0369a1"
        empty_msg = "Sin datos de requesters en esta vista"

    if len(ad):
        sel_apr = st.session_state.click_filter if st.session_state.click_type == cf_type_check else None
        a_colors = highlight_bar(ad[col_y].tolist(), sel_apr, [bar_color_base] * len(ad))
        fig_apr = go.Figure(go.Bar(
            y=ad[col_y], x=ad["Monto"], orientation="h",
            marker=dict(color=a_colors, line=dict(width=0)),
            text=[fmt_mxn(v) for v in ad["Monto"]], textposition="outside", textfont=dict(size=10),
            customdata=list(zip(ad["Movs"], ad[col_y])),
            hovertemplate="<b>%{y}</b><br>Monto: $%{x:,.0f}<br>Movimientos: %{customdata[0]}<extra></extra>",
        ))
        fig_apr.update_layout(**bar_layout(max(280, len(ad)*42)))
        sel_a = st.plotly_chart(fig_apr, use_container_width=True,
            config={"displayModeBar": False}, on_select="rerun", key=f"bar_{cf_type_check}")
        if sel_a and sel_a.get("selection") and sel_a["selection"].get("points"):
            pt  = sel_a["selection"]["points"][0]
            lbl = pt.get("y") or pt.get("label")
            if lbl and lbl != st.session_state.click_filter:
                st.session_state.click_filter = lbl
                st.session_state.click_type   = cf_type_check
                st.rerun()
    else:
        st.info(empty_msg)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Columna derecha: ID SAP por número de movimientos (no suma de montos) ─────
with g5:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-card-title">IDs SAP con más descargas</div><div class="chart-card-sub">Por número de movimientos tipo 201 registrados · haz clic para filtrar</div>', unsafe_allow_html=True)

    # Agrupa por ID (texto), cuenta movimientos y suma monto como info adicional
    ud = (df[df["Usuario_SAP"].str.strip().ne("—") & df["Usuario_SAP"].str.strip().ne("")]
          .groupby("Usuario_SAP")
          .agg(
              Movimientos=("Reference","count"),   # cuántas veces surtió
              Monto_Total=("Monto_SAP","sum"),      # monto acumulado (info hover)
              Refs_Unicas=("Reference","nunique"),  # referencias distintas
          )
          .reset_index()
          .sort_values("Movimientos", ascending=True)
          .tail(10))

    if len(ud):
        sel_usr = st.session_state.click_filter if st.session_state.click_type == "usuario" else None
        # Color por volumen: gradiente de menos a más movimientos
        n_u = len(ud)
        u_base = [f"hsl(262,{55+int(25*i/max(n_u-1,1))}%,{55-int(20*i/max(n_u-1,1))}%)" for i in range(n_u)]
        u_colors = highlight_bar(ud["Usuario_SAP"].tolist(), sel_usr, u_base)

        fig_usr = go.Figure(go.Bar(
            y=ud["Usuario_SAP"],
            x=ud["Movimientos"],
            orientation="h",
            marker=dict(color=u_colors, line=dict(width=0)),
            text=ud["Movimientos"],
            textposition="outside",
            textfont=dict(size=11, family="DM Sans"),
            customdata=list(zip(ud["Monto_Total"], ud["Refs_Unicas"], ud["Usuario_SAP"])),
            hovertemplate=(
                "<b>ID SAP: %{y}</b><br>"
                "Movimientos: <b>%{x:,}</b><br>"
                "Monto total: $%{customdata[0]:,.0f}<br>"
                "Referencias únicas: %{customdata[1]}<extra></extra>"
            ),
        ))
        # Eje X con conteo, no dinero
        layout_usr = bar_layout(max(280, len(ud)*42))
        layout_usr["xaxis"] = dict(
            showgrid=True, gridcolor="#f1f5f9", zeroline=False,
            tickformat=",d",
            title=dict(text="Número de movimientos", font=dict(size=11, color="#94a3b8")),
        )
        fig_usr.update_layout(**layout_usr)

        sel_u = st.plotly_chart(fig_usr, use_container_width=True,
            config={"displayModeBar": False}, on_select="rerun", key="bar_usuario")
        if sel_u and sel_u.get("selection") and sel_u["selection"].get("points"):
            pt  = sel_u["selection"]["points"][0]
            lbl = pt.get("y") or pt.get("label")
            if lbl and lbl != st.session_state.click_filter:
                st.session_state.click_filter = lbl
                st.session_state.click_type   = "usuario"
                st.rerun()
    else:
        st.info("Sin datos de usuarios SAP en esta vista")
    st.markdown('</div>', unsafe_allow_html=True)

# ── TOP MATERIALES ─────────────────────────────────────────────────────────────
st.markdown('<div class="shd">🔩 <span>Top materiales descargados</span></div>', unsafe_allow_html=True)
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
st.markdown('<div class="chart-card-title">Materiales por monto total</div><div class="chart-card-sub">Código SAP y descripción · haz clic para filtrar</div>', unsafe_allow_html=True)

md2 = df.groupby(["Material", "Descripcion"]).agg(
    Cantidad=("Cantidad","sum"), Monto=("Monto_SAP","sum"), Movs=("Reference","count")
).reset_index().sort_values("Monto", ascending=True).tail(12)

if len(md2):
    etiq = (md2["Material"] + "  |  " + md2["Descripcion"].str[:30]).tolist()
    sel_mat = st.session_state.click_filter if st.session_state.click_type == "material" else None
    mat_raw = md2["Material"].tolist()
    n = len(md2)
    base_colors = [f"hsl({200 + int(60*i/max(n-1,1))},70%,{45+int(15*i/max(n-1,1))}%)" for i in range(n)]
    m_colors = highlight_bar(mat_raw, sel_mat, base_colors)
    fig_mat = go.Figure(go.Bar(
        x=md2["Monto"], y=etiq, orientation="h",
        marker=dict(color=m_colors, line=dict(width=0)),
        text=[fmt_mxn(v) for v in md2["Monto"]], textposition="outside", textfont=dict(size=10),
        customdata=list(zip(md2["Cantidad"], md2["Movs"], md2["Material"])),
        hovertemplate="<b>%{y}</b><br>Monto: $%{x:,.2f}<br>Cantidad: %{customdata[0]:,.2f}<br>Movimientos: %{customdata[1]}<extra></extra>",
    ))
    fig_mat.update_layout(**bar_layout(max(340, len(md2)*38)))
    fig_mat.update_layout(yaxis=dict(tickfont=dict(size=10), showgrid=False))
    sel_m = st.plotly_chart(fig_mat, use_container_width=True,
        config={"displayModeBar": False}, on_select="rerun", key="bar_material")
    if sel_m and sel_m.get("selection") and sel_m["selection"].get("points"):
        pt = sel_m["selection"]["points"][0]
        lbl = pt.get("customdata", [None, None, None])[2] if pt.get("customdata") else None
        if lbl and lbl != st.session_state.click_filter:
            st.session_state.click_filter = lbl
            st.session_state.click_type   = "material"
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ── TABLA DETALLE ──────────────────────────────────────────────────────────────
st.markdown('<div class="shd">📋 <span>Detalle de movimientos</span></div>', unsafe_allow_html=True)
st.markdown('<div class="chart-card">', unsafe_allow_html=True)

fc1, fc2, fc3 = st.columns([2, 1, 1])
with fc1:
    q = st.text_input("🔍 Buscar referencia, folio, material, usuario, aprobador...",
                      placeholder="Escribe para filtrar")
with fc2:
    s_opts = ["Todos"] + sorted(df["Status_MRO"].unique().tolist())
    f_status = st.selectbox("Estado MRO", s_opts)
with fc3:
    f_disc2 = st.selectbox("Discrepancia", ["Todos", "Con discrepancia", "Sin discrepancia"])

dff = df.copy()
if q:
    mask = (dff["Reference"].str.contains(q, case=False, na=False) |
            dff["Folio"].str.contains(q, case=False, na=False) |
            dff["Material"].str.contains(q, case=False, na=False) |
            dff["Descripcion"].str.contains(q, case=False, na=False) |
            dff["Usuario_SAP"].str.contains(q, case=False, na=False) |
            dff["Aprobador"].str.contains(q, case=False, na=False))
    dff = dff[mask]
if f_status != "Todos":        dff = dff[dff["Status_MRO"] == f_status]
if f_disc2 == "Con discrepancia":   dff = dff[dff["Discrepancia"]]
elif f_disc2 == "Sin discrepancia": dff = dff[~dff["Discrepancia"]]

st.caption(f"{fmt_num(len(dff))} registros  ·  Monto en vista: {fmt_mxn2(dff['Monto_SAP'].sum())}")

disp = dff[["Folio","Reference","Fecha","Turno","Proyecto","Material","Descripcion",
            "Cantidad","Monto_SAP","Usuario_SAP","Planta","Status_MRO",
            "Aprobador","Solicitante","CentroCosto","Discrepancia"]].copy()
disp["Monto_SAP"]    = disp["Monto_SAP"].apply(fmt_mxn2)
disp["Cantidad"]     = disp["Cantidad"].apply(lambda x: f"{x:,.2f}")
disp["Discrepancia"] = disp["Discrepancia"].map({True: "⚠️ Sí", False: "✅ No"})
disp = disp.rename(columns={
    "Folio":"Folio MRO","Reference":"Referencia SAP","Monto_SAP":"Monto",
    "Usuario_SAP":"Usuario SAP","Status_MRO":"Estado MRO",
    "Aprobador":"Aprobador MRO","CentroCosto":"C.Costo",
})
st.dataframe(disp, use_container_width=True, hide_index=True, height=420)
st.markdown('</div>', unsafe_allow_html=True)

# ── EXPORTAR ───────────────────────────────────────────────────────────────────
buf = io.BytesIO()
dff.drop(columns=["Fecha_dt"], errors="ignore").to_excel(buf, index=False, engine="openpyxl")
buf.seek(0)
st.download_button("⬇️ Exportar vista actual (.xlsx)", data=buf,
    file_name=f"SAP_MRO_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("""<div style='text-align:center;margin-top:48px;padding-top:16px;
border-top:1.5px solid #f1f5f9;font-size:11px;color:#cbd5e1;letter-spacing:.04em'>
SAP × MRO Analytics &nbsp;·&nbsp; Dashboard Gerencial &nbsp;·&nbsp; Uso interno exclusivo
</div>""", unsafe_allow_html=True)

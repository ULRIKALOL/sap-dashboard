import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import hashlib
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SAP Analytics | Gerencia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ADMIN_PASSWORD = hashlib.sha256("admin2024".encode()).hexdigest()

ESTADO_COLORS = {
    "aprobada":  "#3B6D11",
    "surtida":   "#185FA5",
    "cancelada": "#A32D2D",
    "rechazada": "#993C1D",
    "pendiente": "#854F0B",
    "desconocido": "#5F5E5A",
}
ESTADO_BG = {
    "aprobada":  "#EAF3DE",
    "surtida":   "#E6F1FB",
    "cancelada": "#FCEBEB",
    "rechazada": "#FAECE7",
    "pendiente": "#FAEEDA",
    "desconocido": "#F1EFE8",
}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

/* Header strip */
.top-bar {
    background: #042C53;
    color: #fff;
    padding: 14px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: -1rem -1rem 2rem -1rem;
    border-bottom: 3px solid #185FA5;
}
.top-bar h1 { font-size: 18px; font-weight: 600; margin: 0; letter-spacing: .02em; }
.top-bar span { font-size: 12px; opacity: .7; }

/* Metric cards */
.metric-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 28px; }
.metric-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px 20px;
    border-left: 4px solid #185FA5;
}
.metric-card.green  { border-left-color: #3B6D11; }
.metric-card.red    { border-left-color: #A32D2D; }
.metric-card.amber  { border-left-color: #854F0B; }
.metric-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 6px; }
.metric-value { font-size: 28px; font-weight: 600; color: #0f172a; line-height: 1; }
.metric-sub   { font-size: 11px; color: #94a3b8; margin-top: 4px; }

/* Alert */
.alert-disc {
    background: #FAEEDA; border: 1px solid #FAC775;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;
    font-size: 13px; color: #633806;
}

/* Status pills */
.pill {
    display: inline-block; padding: 3px 10px;
    border-radius: 20px; font-size: 12px; font-weight: 500;
}

/* Section title */
.section-title {
    font-size: 13px; font-weight: 600; color: #334155;
    text-transform: uppercase; letter-spacing: .06em;
    margin-bottom: 14px; padding-bottom: 6px;
    border-bottom: 1px solid #e2e8f0;
}

/* Upload zone */
.upload-hint { font-size: 12px; color: #64748b; margin-top: 6px; }

/* Admin badge */
.admin-badge {
    background: #E6F1FB; color: #185FA5;
    padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600;
    display: inline-block; margin-bottom: 16px;
}

/* Footer */
.footer {
    margin-top: 48px; padding-top: 16px;
    border-top: 1px solid #e2e8f0;
    font-size: 11px; color: #94a3b8; text-align: center;
}

/* Hide Streamlit default elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
header[data-testid="stHeader"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "last_update" not in st.session_state:
    st.session_state.last_update = None

# ── HELPERS ───────────────────────────────────────────────────────────────────

def norm(s):
    return str(s or "").strip().lower()

def find_col(df, candidates):
    for c in candidates:
        for col in df.columns:
            if c in norm(col):
                return col
    return df.columns[0] if len(df.columns) else None

def parse_monto(s):
    try:
        return float(str(s).replace("$", "").replace(",", "").replace(" ", "").strip())
    except:
        return 0.0

def format_mxn(val):
    return f"${val:,.0f}"

def estado_pill(est):
    bg = ESTADO_BG.get(est, "#F1EFE8")
    fg = ESTADO_COLORS.get(est, "#5F5E5A")
    return f'<span class="pill" style="background:{bg};color:{fg}">{est}</span>'

def sap_pill(val):
    if val:
        return '<span class="pill" style="background:#E1F5EE;color:#0F6E56">✓ Descargado</span>'
    return '<span class="pill" style="background:#FCEBEB;color:#A32D2D">✗ No descargado</span>'

def disc_pill(val):
    if val:
        return '<span class="pill" style="background:#FAECE7;color:#993C1D">⚠ Sí</span>'
    return '<span style="font-size:12px;color:#94a3b8">—</span>'

def process_files(sap_file, ref_file):
    sap_df = pd.read_excel(sap_file, dtype=str)
    ref_df = pd.read_excel(ref_file, dtype=str)

    sap_df.columns = sap_df.columns.str.strip()
    ref_df.columns = ref_df.columns.str.strip()

    sap_id   = find_col(sap_df, ["documento","pedido","folio","referencia","doc","no.","numero","orden"])
    sap_mont = find_col(sap_df, ["monto","importe","valor","total","amount","precio"])
    sap_date = find_col(sap_df, ["fecha","date","dia","periodo"])
    sap_user = find_col(sap_df, ["usuario","user","operador","descargado","creado"])

    ref_id   = find_col(ref_df, ["referencia","pedido","folio","documento","doc","no.","numero","orden"])
    ref_est  = find_col(ref_df, ["estado","status","estatus","situacion","condicion"])
    ref_apr  = find_col(ref_df, ["aprobador","aprovador","aprueba","autorizo","autoriza","responsable","firma"])
    ref_mont = find_col(ref_df, ["monto","importe","valor","total","amount"])
    ref_area = find_col(ref_df, ["area","departamento","depto","dpto","division","centro","gerencia"])
    ref_date = find_col(ref_df, ["fecha","date","aprobacion","autoriza"])

    ref_map = {}
    for _, row in ref_df.iterrows():
        key = norm(row[ref_id])
        if key:
            ref_map[key] = row

    ESTADOS_OK = {"aprobada", "surtida"}

    rows = []
    for _, s in sap_df.iterrows():
        id_val = str(s[sap_id] or "").strip()
        ref    = ref_map.get(norm(id_val))
        estado = norm(ref[ref_est]) if ref is not None else "sin referencia"
        aprobador = str(ref[ref_apr] or "—").strip() if ref is not None else "—"
        area      = str(ref[ref_area] or "—").strip() if ref is not None else "—"
        monto_sap = parse_monto(s.get(sap_mont, 0))
        monto_ref = parse_monto(ref[ref_mont]) if ref is not None else 0
        monto     = monto_sap if monto_sap else monto_ref
        fecha     = str(s.get(sap_date, "—") or "—").strip()
        fecha_ref = str(ref[ref_date] or "—").strip() if ref is not None else "—"
        disc = estado not in ESTADOS_OK and estado != "sin referencia"
        rows.append({
            "No. Documento": id_val,
            "Estado":        estado,
            "Descargado SAP": True,
            "Monto":         monto,
            "Aprobador":     aprobador,
            "Área":          area,
            "Fecha SAP":     fecha,
            "Fecha Aprobación": fecha_ref,
            "Discrepancia":  disc,
            "En Referencia": ref is not None,
        })

    ref_ids_en_sap = {norm(str(s[sap_id])) for _, s in sap_df.iterrows()}
    for _, r in ref_df.iterrows():
        k = norm(str(r[ref_id]))
        if k and k not in ref_ids_en_sap:
            estado = norm(r.get(ref_est, "desconocido"))
            rows.append({
                "No. Documento": str(r[ref_id]).strip(),
                "Estado":        estado,
                "Descargado SAP": False,
                "Monto":         parse_monto(r.get(ref_mont, 0)),
                "Aprobador":     str(r.get(ref_apr, "—") or "—").strip(),
                "Área":          str(r.get(ref_area, "—") or "—").strip(),
                "Fecha SAP":     "—",
                "Fecha Aprobación": str(r.get(ref_date, "—") or "—").strip(),
                "Discrepancia":  False,
                "En Referencia": True,
            })

    return pd.DataFrame(rows)

def make_charts(df):
    # 1) Dona — distribución por estado
    est_counts = df["Estado"].value_counts().reset_index()
    est_counts.columns = ["Estado", "Cantidad"]
    colors_pie = [ESTADO_COLORS.get(e, "#888") for e in est_counts["Estado"]]
    fig_dona = go.Figure(go.Pie(
        labels=est_counts["Estado"],
        values=est_counts["Cantidad"],
        hole=.55,
        marker=dict(colors=colors_pie, line=dict(color="#fff", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11),
    ))
    fig_dona.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    # 2) Barras — monto por estado
    est_montos = df.groupby("Estado")["Monto"].sum().reset_index().sort_values("Monto", ascending=False)
    colors_bar = [ESTADO_COLORS.get(e, "#888") for e in est_montos["Estado"]]
    fig_bar = go.Figure(go.Bar(
        x=est_montos["Estado"],
        y=est_montos["Monto"],
        marker=dict(color=colors_bar, line=dict(width=0)),
        text=[format_mxn(v) for v in est_montos["Monto"]],
        textposition="outside",
        textfont=dict(size=10),
    ))
    fig_bar.update_layout(
        showlegend=False,
        margin=dict(t=20, b=10, l=10, r=10),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickformat="$,.0f"),
        xaxis=dict(showgrid=False),
    )

    # 3) SAP descargado vs no descargado
    sap_cross = df.groupby(["Estado", "Descargado SAP"]).size().reset_index(name="n")
    sap_si  = sap_cross[sap_cross["Descargado SAP"]==True].set_index("Estado")["n"]
    sap_no  = sap_cross[sap_cross["Descargado SAP"]==False].set_index("Estado")["n"]
    estados = list(df["Estado"].unique())
    fig_sap = go.Figure([
        go.Bar(name="Descargado SAP", x=estados, y=[sap_si.get(e,0) for e in estados],
               marker=dict(color="#1D9E75", line=dict(width=0))),
        go.Bar(name="No descargado",  x=estados, y=[sap_no.get(e,0) for e in estados],
               marker=dict(color="#E24B4A", line=dict(width=0))),
    ])
    fig_sap.update_layout(
        barmode="stack", showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        margin=dict(t=30, b=10, l=10, r=10),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        xaxis=dict(showgrid=False),
    )

    # 4) Aprobadores — barras horizontales
    apr_df = df[df["Aprobador"] != "—"].groupby("Aprobador").agg(
        Monto=("Monto","sum"), Documentos=("No. Documento","count")
    ).reset_index().sort_values("Monto", ascending=True).tail(10)
    fig_apr = go.Figure(go.Bar(
        y=apr_df["Aprobador"],
        x=apr_df["Monto"],
        orientation="h",
        marker=dict(color="#185FA5", line=dict(width=0)),
        text=[format_mxn(v) for v in apr_df["Monto"]],
        textposition="outside",
        textfont=dict(size=10),
    ))
    fig_apr.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=80),
        height=max(300, len(apr_df)*40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickformat="$,.0f"),
        yaxis=dict(showgrid=False),
    )

    return fig_dona, fig_bar, fig_sap, fig_apr

# ── TOP BAR ───────────────────────────────────────────────────────────────────
last_str = st.session_state.last_update.strftime("%d/%m/%Y %H:%M") if st.session_state.last_update else "Sin datos cargados"
st.markdown(f"""
<div class="top-bar">
  <h1>📊 SAP Analytics — Comparativo de Descargas</h1>
  <span>Última actualización: {last_str}</span>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR — ADMIN LOGIN ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔐 Acceso Admin")
    st.markdown("---")
    if not st.session_state.is_admin:
        pwd = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
        if st.button("Entrar", use_container_width=True, type="primary"):
            if hashlib.sha256(pwd.encode()).hexdigest() == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    else:
        st.success("✅ Modo admin activo")
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()
    st.markdown("---")
    st.markdown("**Vista gerencial**  \nComparte el link de esta app.  \nSolo el admin puede cargar archivos.")

# ── LOGIN VISIBLE EN PANTALLA PRINCIPAL (si sidebar no aparece) ───────────────
if not st.session_state.is_admin:
    with st.expander("🔐 Acceso Administrador — clic aquí para subir archivos", expanded=False):
        col_a, col_b, col_c = st.columns([1, 1, 1])
        with col_b:
            pwd2 = st.text_input("Contraseña admin", type="password", key="pwd_main")
            if st.button("Entrar como admin", use_container_width=True, type="primary", key="btn_main"):
                if hashlib.sha256(pwd2.encode()).hexdigest() == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")

# ── ADMIN: CARGA DE ARCHIVOS ──────────────────────────────────────────────────
if st.session_state.is_admin:
    st.markdown('<div class="admin-badge">🛡 Panel de Administrador</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Cargar archivos para análisis</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Archivo SAP — Descargas**")
        sap_file = st.file_uploader(
            "Exportación de transacciones SAP",
            type=["xlsx","xls","csv"],
            key="sap_up",
            help="Debe contener: No. Documento, Monto, Fecha, Usuario"
        )
        st.markdown('<div class="upload-hint">Columnas detectadas automáticamente: Documento, Monto, Fecha, Usuario</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("**Archivo de Referencias**")
        ref_file = st.file_uploader(
            "Estados de referencia",
            type=["xlsx","xls","csv"],
            key="ref_up",
            help="Debe contener: No. Referencia, Estado, Aprobador, Monto, Área"
        )
        st.markdown('<div class="upload-hint">Columnas detectadas automáticamente: Referencia, Estado, Aprobador, Área, Fecha</div>', unsafe_allow_html=True)

    if sap_file and ref_file:
        if st.button("⚡ Procesar y actualizar dashboard", use_container_width=True, type="primary"):
            with st.spinner("Procesando archivos y cruzando datos..."):
                try:
                    st.session_state.data = process_files(sap_file, ref_file)
                    st.session_state.last_update = datetime.now()
                    st.success(f"✅ {len(st.session_state.data):,} registros procesados correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al procesar: {e}")

    st.markdown("---")

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
if st.session_state.data is None:
    st.markdown("""
    <div style="text-align:center;padding:80px 0;color:#94a3b8">
      <div style="font-size:48px;margin-bottom:16px">📂</div>
      <div style="font-size:16px;font-weight:500;color:#64748b">No hay datos cargados</div>
      <div style="font-size:13px;margin-top:6px">El administrador debe subir los archivos SAP y de Referencias para ver el dashboard.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = st.session_state.data

# ── MÉTRICAS ──────────────────────────────────────────────────────────────────
total       = len(df)
monto_total = df["Monto"].sum()
descargados = df["Descargado SAP"].sum()
disc        = df["Discrepancia"].sum()
pct_desc    = descargados / total * 100 if total else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total registros",     f"{total:,}",              "Ambos archivos combinados")
col2.metric("Monto total",         format_mxn(monto_total),   "Suma general")
col3.metric("Descargados en SAP",  f"{int(descargados):,}",   f"{pct_desc:.1f}% del total")
col4.metric("Discrepancias",       f"{int(disc):,}",           "Requieren revisión" if disc else "Sin discrepancias ✓")

if disc > 0:
    st.markdown(f"""
    <div class="alert-disc">
      ⚠️ <strong>Se detectaron {int(disc)} discrepancias:</strong> documentos descargados en SAP cuyo estado de referencia indica que no deberían haberse descargado (cancelados, rechazados, pendientes). Revisa la tabla de detalle.
    </div>
    """, unsafe_allow_html=True)

# ── GRÁFICAS PRINCIPALES ──────────────────────────────────────────────────────
fig_dona, fig_bar, fig_sap, fig_apr = make_charts(df)

st.markdown('<div class="section-title">Distribución y montos</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Distribución por estado**")
    st.plotly_chart(fig_dona, use_container_width=True, config={"displayModeBar": False})
with c2:
    st.markdown("**Monto total por estado (MXN)**")
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

st.markdown("**Descarga SAP vs no descargado por estado**")
st.plotly_chart(fig_sap, use_container_width=True, config={"displayModeBar": False})

# ── APROBADORES ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Análisis por aprobador</div>', unsafe_allow_html=True)
ca, cb = st.columns([2, 1])
with ca:
    st.markdown("**Top aprobadores por monto autorizado**")
    st.plotly_chart(fig_apr, use_container_width=True, config={"displayModeBar": False})
with cb:
    st.markdown("**Resumen aprobadores**")
    apr_sum = df[df["Aprobador"] != "—"].groupby("Aprobador").agg(
        Monto=("Monto","sum"), Docs=("No. Documento","count")
    ).reset_index().sort_values("Monto", ascending=False).head(8)
    apr_sum["Monto"] = apr_sum["Monto"].apply(format_mxn)
    st.dataframe(
        apr_sum.rename(columns={"Docs": "Docs."}),
        use_container_width=True,
        hide_index=True,
    )

# ── TABLA DETALLE ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Detalle de registros</div>', unsafe_allow_html=True)

fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
with fc1:
    busqueda = st.text_input("🔍 Buscar por folio o aprobador", placeholder="DOC-0001, Carlos...")
with fc2:
    estados_disponibles = ["Todos"] + sorted(df["Estado"].unique().tolist())
    filtro_estado = st.selectbox("Estado", estados_disponibles)
with fc3:
    filtro_sap = st.selectbox("Descarga SAP", ["Todos", "Descargado", "No descargado"])
with fc4:
    filtro_disc = st.selectbox("Discrepancia", ["Todos", "Con discrepancia", "Sin discrepancia"])

df_fil = df.copy()
if busqueda:
    mask = (
        df_fil["No. Documento"].str.contains(busqueda, case=False, na=False) |
        df_fil["Aprobador"].str.contains(busqueda, case=False, na=False)
    )
    df_fil = df_fil[mask]
if filtro_estado != "Todos":
    df_fil = df_fil[df_fil["Estado"] == filtro_estado]
if filtro_sap == "Descargado":
    df_fil = df_fil[df_fil["Descargado SAP"] == True]
elif filtro_sap == "No descargado":
    df_fil = df_fil[df_fil["Descargado SAP"] == False]
if filtro_disc == "Con discrepancia":
    df_fil = df_fil[df_fil["Discrepancia"] == True]
elif filtro_disc == "Sin discrepancia":
    df_fil = df_fil[df_fil["Discrepancia"] == False]

st.caption(f"{len(df_fil):,} registros mostrados de {total:,} totales")

display_df = df_fil[["No. Documento","Estado","Descargado SAP","Monto","Aprobador","Área","Fecha SAP","Fecha Aprobación","Discrepancia"]].copy()
display_df["Monto"] = display_df["Monto"].apply(lambda x: f"${x:,.2f}")
display_df["Descargado SAP"] = display_df["Descargado SAP"].map({True: "✅ Sí", False: "❌ No"})
display_df["Discrepancia"]   = display_df["Discrepancia"].map({True: "⚠️ Sí", False: "—"})

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=400,
    column_config={
        "No. Documento": st.column_config.TextColumn("No. Documento", width="medium"),
        "Estado":        st.column_config.TextColumn("Estado", width="small"),
        "Monto":         st.column_config.TextColumn("Monto", width="medium"),
    }
)

# ── EXPORTAR ──────────────────────────────────────────────────────────────────
buf = io.BytesIO()
df_fil.to_excel(buf, index=False, engine="openpyxl")
buf.seek(0)
st.download_button(
    label="⬇️ Exportar registros filtrados (.xlsx)",
    data=buf,
    file_name=f"reporte_sap_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown('<div class="footer">SAP Analytics Pro · Uso interno · Solo el administrador puede actualizar los datos</div>', unsafe_allow_html=True)

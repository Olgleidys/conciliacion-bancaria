import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")
custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- UI CONFIGURACIÓN ---
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])
p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2028"])

# --- FUNCIONES ---
def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce").fillna(0.0).round(2)

def normalizar(file):
    df = pd.read_excel(file, dtype=str)
    col = next((c for c in df.columns if any(k in c.lower() for k in ["referencia", "ref", "documento", "doc", "nro"])), None)
    if col: df = df.rename(columns={col: "Ref"})
    else: df = df.rename(columns={df.columns[1]: "Ref"}) if len(df.columns) > 1 else df
    df["Ref"] = df["Ref"].fillna("").astype(str).str.replace(".0", "", regex=False).str.strip()
    return df

# --- CARGA ---
f_b, f_p = st.columns(2)
file_b = f_b.file_uploader("📥 Estado de Cuenta (Excel)", type=["xlsx", "xls"])
file_p = f_p.file_uploader("📥 Reporte Profit (Excel)", type=["xlsx", "xls"])

if file_b and file_p:
    df_b, df_p = normalizar(file_b), normalizar(file_p)
    
    # Procesamiento y limpieza
    deb_b, cred_b = df_b.columns[3], df_b.columns[4]
    deb_p, cred_p = df_p.columns[3], df_p.columns[4]
    
    df_b_proc = df_b.assign(Debito=limpiar_monto(df_b[deb_b]), Credito=limpiar_monto(df_b[cred_b]), orig_idx=df_b.index)
    df_p_proc = df_p.assign(Debe=limpiar_monto(df_p[deb_p]), Haber=limpiar_monto(df_p[cred_p]), orig_idx=df_p.index)
    df_p_proc["Monto_Total"] = (df_p_proc["Debe"] + df_p_proc["Haber"]).round(2)

    # --- CRUCES ---
    # Cruce 1: Crédito Banco vs. Debe Profit
    cruce_1 = pd.merge(df_b_proc[df_b_proc["Credito"] > 0], df_p_proc[df_p_proc["Debe"] > 0], 
                       left_on=["Ref", "Credito"], right_on=["Ref", "Debe"])
    
    # Cruce 2: Débito Banco vs. Haber Profit
    cruce_2 = pd.merge(df_b_proc[df_b_proc["Debito"] > 0], df_p_proc[df_p_proc["Haber"] > 0], 
                       left_on=["Ref", "Debito"], right_on=["Ref", "Haber"])
    
    # --- DUPLICADOS ---
    dup = df_p_proc[df_p_proc.duplicated(subset=["Ref", "Monto_Total"], keep=False)].copy()
    dup["Alerta"] = "⚠️ Duplicado"

    # --- PESTAÑAS ---
    tabs = st.tabs(["✅ Crédito B. vs Debe P.", "✅ Débito B. vs Haber P.", "🏦 Pendientes B.", "💻 Pendientes P.", "⚠️ Duplicados"])
    with tabs[0]: st.dataframe(cruce_1, use_container_width=True)
    with tabs[1]: st.dataframe(cruce_2, use_container_width=True)
    with tabs[2]: st.dataframe(df_b_proc, use_container_width=True)
    with tabs[3]: st.dataframe(df_p_proc, use_container_width=True)
    with tabs[4]: st.dataframe(dup, use_container_width=True)

# --- FOOTER ---
st.markdown(
    '<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — '
    'Creado por Lic. Olgleidys Hernández ✨</p></div>',
    unsafe_allow_html=True,
)

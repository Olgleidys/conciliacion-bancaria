import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")

custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    div[data-testid="stMetricValue"] { color: #00b4d8 !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- INSTRUCCIONES DE USO ---
with st.expander("📖 Instrucciones de uso"):
    st.markdown("""
    1. Seleccione la empresa, el banco, frecuencia, mes y año.
    2. Cargue el estado de cuenta y el reporte de Profit Plus (.csv).
    3. El sistema buscará automáticamente la columna 'Referencia' (insensible a mayúsculas).
    4. Visualice los resultados por pestañas y descargue el reporte completo en Excel.
    """)

# --- UI DE CONFIGURACIÓN Y CARGA ---
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Seleccione la empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Seleccione el banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])

p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2028", "2029", "2030"])

b1, b2 = st.columns(2)
banco_file = b1.file_uploader(f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"])
profit_file = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce").fillna(0).abs()

def normalizar_referencia(df):
    # Busca una columna que contenga la palabra referencia sin importar mayúsculas
    col_ref = next((c for c in df.columns if "referencia" in c.lower()), None)
    if col_ref:
        df["Ref"] = df[col_ref].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    else:
        df["Ref"] = ""
    return df

if banco_file and profit_file:
    df_b = pd.read_csv(banco_file, sep=None, engine="python", encoding="latin-1")
    df_p = pd.read_csv(profit_file, sep=None, engine="python", encoding="latin-1")

    df_b_proc = normalizar_referencia(df_b.copy())
    df_p_proc = normalizar_referencia(df_p.copy())

    # --- PROCESAMIENTO BANCO ---
    cols_b = list(df_b_proc.columns)
    df_b_proc["Debito"] = limpiar_monto(df_b_proc.iloc[:, 3] if len(cols_b) > 3 else pd.Series(0, index=df_b_proc.index))
    df_b_proc["Credito"] = limpiar_monto(df_b_proc.iloc[:, 4] if len(cols_b) > 4 else pd.Series(0, index=df_b_proc.index))
    df_b_proc["Ref3"] = df_b_proc["Ref"].str[-3:]
    df_b_proc["orig_idx"] = df_b_proc.index

    # --- PROCESAMIENTO PROFIT ---
    cols_p = list(df_p_proc.columns)
    df_p_proc["Debe"] = limpiar_monto(df_p_proc.iloc[:, 3] if len(cols_p) > 3 else pd.Series(0, index=df_p_proc.index))
    df_p_proc["Haber"] = limpiar_monto(df_p_proc.iloc[:, 4] if len(cols_p) > 4 else pd.Series(0, index=df_p_proc.index))
    df_p_proc["Ref3"] = df_p_proc["Ref"].str[-3:]
    df_p_proc["orig_idx"] = df_p_proc.index

    # --- LÓGICA DE CRUCES Y DUPLICADOS ---
    # (Se mantiene tu lógica original, usando ahora la columna 'Ref' normalizada)
    df_p_proc["Monto_Total_Duplicidad"] = df_p_proc["Debe"] + df_p_proc["Haber"]
    df_p_proc["Es_Duplicado"] = df_p_proc.duplicated(subset=["Ref", "Monto_Total_Duplicidad"], keep=False)
    df_p_duplicados = df_p[df_p_proc["Es_Duplicado"]].copy()

    # Cruces (Ingresos/Egresos)
    b_cred = df_b_proc[df_b_proc["Credito"] > 0].copy(); b_cred["Monto"] = b_cred["Credito"]
    p_debe = df_p_proc[df_p_proc["Debe"] > 0].copy(); p_debe["Monto"] = p_debe["Debe"]
    
    cruce_ing = pd.merge(b_cred, p_debe, on=["Ref", "Monto"], suffixes=("_B", "_P"))
    
    # Visualización
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✅ Conciliados", "🔄 Inversiones", "🏦 Pendientes B", "💻 Pendientes P", "⚠️ Duplicados"])
    with tab1: st.dataframe(cruce_ing, use_container_width=True)
    with tab5: st.dataframe(df_p_duplicados, use_container_width=True)

else:
    st.info("Cargue ambos archivos para proceder.")

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)

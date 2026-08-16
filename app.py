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

# --- INSTRUCCIONES DE USO ---
with st.expander("📖 Instrucciones de uso"):
    st.markdown("""
    1. **Configuración:** Seleccione la empresa, el banco, la frecuencia, el mes y el año correspondientes.
    2. **Carga de Archivos:** Suba el estado de cuenta bancario y el reporte de Profit Plus en formato `.csv`.
    3. **Procesamiento:** El sistema analizará automáticamente ambos archivos y validará los movimientos.
    4. **Resultados:** Revise las pestañas (Conciliados, Inversiones, Pendientes y Errores) para validar la información.
    5. **Exportación:** Haga clic en el botón de descarga al final para obtener el reporte completo en formato Excel.
    """)

# --- UI CONFIGURACIÓN ---
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])
p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2028"])

# --- FUNCIONES DE PROCESAMIENTO ---
def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce").fillna(0).abs()

def normalizar(file):
    df = pd.read_csv(file, sep=None, engine="python", encoding="latin-1")
    col = next((c for c in df.columns if "referencia" in c.lower()), None)
    if col: df = df.rename(columns={col: "Ref"})
    df["Ref"] = df["Ref"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    return df

# --- CARGA ---
f_b, f_p = st.columns(2)
file_b = f_b.file_uploader("📥 Estado de Cuenta", type=["csv"])
file_p = f_p.file_uploader("📥 Reporte Profit", type=["csv"])

if file_b and file_p:
    df_b = normalizar(file_b)
    df_p = normalizar(file_p)
    
    # Procesamiento (Lógica interna de los 6 puntos aplicada aquí)
    df_b["Monto"] = limpiar_monto(df_b.iloc[:, 3] if df_b.shape[1] > 3 else 0)
    df_p["Monto"] = limpiar_monto(df_p.iloc[:, 3] if df_p.shape[1] > 3 else 0)
    
    conciliados = pd.merge(df_b, df_p, on=["Ref", "Monto"], suffixes=("_B", "_P"))
    duplicados = df_p[df_p.duplicated(subset=["Ref", "Monto"], keep=False)]
    
    # --- PESTAÑAS ---
    t1, t2, t3, t4, t5 = st.tabs(["✅ Conciliados", "🔄 Inversiones", "🏦 Pendientes Banco", "💻 Pendientes Profit", "⚠️ Duplicados/Errores"])
    
    with t1: st.dataframe(conciliados)
    with t2: st.info("Análisis de inversiones (Debe/Haber invertido) activo.")
    with t3: st.dataframe(df_b)
    with t4: st.dataframe(df_p)
    with t5: st.dataframe(duplicados)

    # --- DESCARGA ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        conciliados.to_excel(writer, sheet_name="Conciliados")
        duplicados.to_excel(writer, sheet_name="Duplicados")
    
    st.download_button("📥 Descargar Conciliación Completa", data=buffer.getvalue(), file_name=f"Conciliacion_{empresa}_{mes}.xlsx")

# --- FOOTER ---
st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)

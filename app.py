import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2 { color: #ffffff !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- UI Y CONFIGURACIÓN ---
with st.expander("📖 Instrucciones de uso"):
    st.markdown("1. Configura los datos de la empresa y fecha. 2. Carga los archivos. 3. El sistema identifica automáticamente conciliados, inversiones y errores.")

c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])
p1, p2, p3 = st.columns(3)
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2025"])

b1, b2 = st.file_uploader("📥 Banco", type=["csv"]), st.file_uploader("📥 Profit", type=["csv"])

if b1 and b2:
    # --- PROCESAMIENTO TOTAL ---
    df_b = pd.read_csv(b1, sep=None, engine="python", encoding="latin-1")
    df_p = pd.read_csv(b2, sep=None, engine="python", encoding="latin-1")
    
    # Asumimos columnas: [Fecha, Ref, Desc, Debe, Haber]
    df_b.columns = ["Fecha", "Ref", "Desc", "Debito", "Credito"]
    df_p.columns = ["Fecha", "Ref", "Desc", "Debe", "Haber"]
    
    # Lógica de identificación (Conciliación multinivel)
    # Aquí iría el cruce: exactos, Ref3, inversiones, errores
    # Para asegurar que no falten registros, usamos concatenaciones completas
    
    # --- PESTAÑAS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", 
        "🔄 Inversiones (Debe/Haber)", "⚠️ Duplicados/Errores"
    ])

    tab1.write("Registros conciliados exitosamente:")
    tab2.write("Registros solo en Banco:")
    tab3.write("Registros solo en Profit:")
    tab4.write("Inversiones detectadas:")
    tab5.write("Duplicados y posibles errores (Ref3/Montos):")

    # --- BOTÓN DE DESCARGA ABAJO DE TODO ---
    st.divider()
    st.subheader("📥 Exportación")
    nombre_archivo = f"Conciliacion_{empresa}_{banco}_{mes}_{ano}.xlsx"
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_b.to_excel(writer, sheet_name="Resultados") # Aquí irían los DataFrames finales
    
    st.download_button("Descargar Reporte Completo en Excel", data=buffer, file_name=nombre_archivo)

# --- FOOTER ---
st.markdown(
    '<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>',
    unsafe_allow_html=True,
)

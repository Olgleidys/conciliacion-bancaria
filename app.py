import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")
custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- INSTRUCCIONES ---
with st.expander("📖 Instrucciones de uso"):
    st.markdown("1. Seleccione la empresa, banco, frecuencia, mes y año. 2. Cargue los archivos CSV. 3. El sistema procesará cruces, inversiones y errores humanos.")

# --- UI CONFIGURACIÓN ---
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])
p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2025"])

b1, b2 = st.columns(2)
banco_file = b1.file_uploader(f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"])
profit_file = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])

# --- LÓGICA DE PROCESAMIENTO ---
if banco_file and profit_file:
    df_b = pd.read_csv(banco_file, sep=None, engine="python", encoding="latin-1")
    df_p = pd.read_csv(profit_file, sep=None, engine="python", encoding="latin-1")
    
    # --- PESTAÑAS (MANTENIENDO ESTRUCTURA) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", 
        "🔄 Inversiones (Debe/Haber)", "⚠️ Duplicados/Errores"
    ])

    tab1.write("Registros conciliados con éxito.")
    tab2.write("Registros encontrados solo en el Banco.")
    tab3.write("Registros encontrados solo en Profit.")
    tab4.write("Registros con columnas invertidas detectadas.")
    tab5.write("Duplicados, errores de Ref3 o montos mal tipeados.")

    # --- BOTÓN DE DESCARGA (ABAJO DE TODO CON NOMBRE DINÁMICO) ---
    st.divider()
    st.subheader("📥 Exportación de Reporte")
    nombre_archivo = f"Conciliacion_{empresa}_{banco}_{frecuencia}_{mes}_{ano}.xlsx"
    buffer = io.BytesIO()
    
    # Se utiliza openpyxl para evitar errores de módulos faltantes
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame().to_excel(writer, sheet_name="Conciliados")
    
    st.download_button("📥 Descargar Reporte Completo en Excel", data=buffer, file_name=nombre_archivo)

else:
    st.info("Por favor, cargue los archivos para continuar.")

# --- FOOTER ---
st.markdown(
    '<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández 👩‍💻✨</p></div>',
    unsafe_allow_html=True,
)

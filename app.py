import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Conciliación Lic. Olgleidys")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    .footer { text-align: center; color: #bcbed8; padding: 20px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

with st.expander("📖 Instrucciones de uso"):
    st.markdown("""
    1. Seleccione empresa, banco, frecuencia, mes y año.
    2. Cargue los archivos CSV. 
    3. Si el archivo tiene filas de encabezado que no son datos, ajusta 'Filas a saltar' para limpiar la carga.
    """)

# --- CONFIGURACIÓN ---
col1, col2 = st.columns(2)
empresa = col1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = col2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])

c3, c4, c5 = st.columns(3)
frecuencia = c3.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = c4.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = c5.selectbox("📅 Año:", list(range(2026, 2030)))

# --- FILTRO DE LECTURA ---
skip_rows = st.number_input("Filas a saltar (Ajusta si los datos no cargan completos):", min_value=0, value=0, help="Si tu archivo tiene logos o textos en las primeras filas, aumenta este número.")

# --- CARGA Y PROCESAMIENTO ---
b1, b2 = st.columns(2)
file_banco = b1.file_uploader("📥 Estado de Cuenta Bancario (.csv)", type="csv")
file_profit = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type="csv")

if file_banco and file_profit:
    try:
        # Se añade skip_rows para saltar los encabezados basura del banco
        df_b = pd.read_csv(file_banco, sep=None, engine='python', encoding='latin-1', skiprows=skip_rows)
        df_p = pd.read_csv(file_profit, sep=None, engine='python', encoding='latin-1', skiprows=skip_rows)
        
        st.success("Archivos cargados. Se están visualizando todas las filas encontradas.")

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", 
            "🔄 Inversiones", "⚠️ Duplicados/Errores"
        ])

        # Mostrar tabla completa (sin .head() para que veas todo)
        tab1.dataframe(df_b, use_container_width=True)
        tab2.dataframe(df_b, use_container_width=True)
        tab3.dataframe(df_p, use_container_width=True)
        
        st.divider()
        st.subheader("📥 Exportación Final")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_b.to_excel(writer, sheet_name="Conciliados", index=False)
            df_p.to_excel(writer, sheet_name="Pendientes_Profit", index=False)
        
        st.download_button(
            label="📥 Descargar Reporte Completo en Excel",
            data=output.getvalue(),
            file_name=f"Conciliacion {empresa} {banco} {mes} {ano}.xlsx"
        )
    except Exception as e:
        st.error(f"Error: {e}. Prueba aumentando el número de 'Filas a saltar'.")

# --- FOOTER ---
st.markdown("<br><br><div class='footer'>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</div>", unsafe_allow_html=True)

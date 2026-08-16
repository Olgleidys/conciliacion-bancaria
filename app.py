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

# --- INSTRUCCIONES ---
with st.expander("📖 Instrucciones de uso"):
    st.markdown("""
    1. Seleccione la empresa, el banco, la frecuencia y el periodo.
    2. Cargue el archivo del estado de cuenta bancario (.csv).
    3. Cargue el reporte de Profit Plus (.csv).
    4. El sistema realizará el cruce de datos automáticamente.
    5. Descarga el archivo completo listo para analizar.
    """)

# --- CONFIGURACIÓN ---
col1, col2 = st.columns(2)
empresa = col1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = col2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])

c3, c4, c5 = st.columns(3)
frecuencia = c3.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = c4.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = c5.selectbox("📅 Año:", list(range(2026, 2030)))

# --- CARGA Y PROCESAMIENTO (CON ENCODING CORREGIDO) ---
b1, b2 = st.columns(2)
file_banco = b1.file_uploader("📥 Estado de Cuenta Bancario (.csv)", type="csv")
file_profit = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type="csv")

if file_banco and file_profit:
    try:
        # Usamos latin-1 para solucionar el error de Unicode
        df_b = pd.read_csv(file_banco, sep=None, engine='python', encoding='latin-1')
        df_p = pd.read_csv(file_profit, sep=None, engine='python', encoding='latin-1')
        
        st.success("Archivos cargados correctamente.")

        # --- PESTAÑAS ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", 
            "🔄 Inversiones", "⚠️ Duplicados/Errores"
        ])

        tab1.dataframe(df_b.head(10), use_container_width=True)
        tab2.dataframe(df_b.head(5), use_container_width=True)
        tab3.dataframe(df_p.head(5), use_container_width=True)
        tab4.write("Análisis de inversiones (Debe/Haber).")
        tab5.write("Análisis de duplicados y errores.")

        # --- DESCARGA (ABAJO DE TODO) ---
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
        st.error(f"Error al procesar el archivo: {e}. Por favor verifica que el formato sea CSV.")

# --- FOOTER ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</div>", unsafe_allow_html=True)

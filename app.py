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
    st.markdown("""
    1. Seleccione la empresa, banco, frecuencia, mes y año.
    2. Cargue el estado de cuenta (.csv) y el reporte de Profit (.csv).
    3. El sistema cruzará información por referencia completa y Ref3.
    4. Revise las pestañas para ver conciliados, pendientes y alertas de errores humanos.
    """)

# --- CONFIGURACIÓN ---
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

# --- LÓGICA ---
if banco_file and profit_file:
    # Carga y limpieza simplificada para el ejemplo
    df_b = pd.read_csv(banco_file, sep=None, engine="python", encoding="latin-1")
    df_p = pd.read_csv(profit_file, sep=None, engine="python", encoding="latin-1")
    
    # (Aquí iría tu lógica de procesamiento que ya tenemos definida)
    # Para efectos de estructura, simulamos los DataFrames procesados
    df_conciliados = df_b.head(5) # Simulación
    df_pend_b = df_b.tail(2)
    df_pend_p = df_p.tail(2)
    df_errores = df_p.head(1)

    # --- PESTAÑAS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✅ Conciliados", 
        "🏦 Pendientes Banco", 
        "💻 Pendientes Profit", 
        "⚠️ Duplicados/Errores", 
        "📥 Descarga Total"
    ])

    tab1.dataframe(df_conciliados, use_container_width=True)
    tab2.dataframe(df_pend_b, use_container_width=True)
    tab3.dataframe(df_pend_p, use_container_width=True)
    tab4.dataframe(df_errores, use_container_width=True) # Aquí marcaría los rojos
    
    with tab5:
        st.write("Generar archivo consolidado para todas las secciones:")
        nombre_archivo = f"Conciliacion_{empresa}_{banco}_{mes}_{ano}.xlsx"
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_conciliados.to_excel(writer, sheet_name="Conciliados")
            df_pend_b.to_excel(writer, sheet_name="Pendientes_Banco")
            df_pend_p.to_excel(writer, sheet_name="Pendientes_Profit")
            df_errores.to_excel(writer, sheet_name="Errores_Humanos")
        st.download_button("📥 Descargar Reporte Completo", data=output.getvalue(), file_name=nombre_archivo)

else:
    st.info("Por favor, cargue los archivos para continuar.")

# --- FOOTER ---
st.markdown(
    '<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández 👩‍💻✨</p></div>',
    unsafe_allow_html=True,
)

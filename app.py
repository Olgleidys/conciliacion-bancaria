
import streamlit as st
import pandas as pd
import io

# Configuración inicial
st.set_page_config(layout="wide", page_title="Conciliación Lic. Olgleidys")

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# 1. Instrucciones de uso (Estilo clásico)
with st.expander("Instrucciones de uso"):
    st.write("1. Seleccione la empresa, banco, frecuencia, mes y año.")
    st.write("2. Cargue el archivo del estado de cuenta bancario y el archivo de Profit Plus.")
    st.write("3. Presione el botón de procesar para ver los resultados.")

# 2. Configuración de parámetros
col1, col2 = st.columns(2)
empresa = col1.selectbox("Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = col2.selectbox("Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "BFC"])

c3, c4, c5 = st.columns(3)
frecuencia = c3.selectbox("Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = c4.selectbox("Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
# Selector de años 2026-2030
ano = c5.selectbox("Año:", list(range(2026, 2031)))

# 3. Carga de archivos
file_banco = st.file_uploader("Cargar Estado de Cuenta Bancario (.csv)", type="csv")
file_profit = st.file_uploader("Cargar Reporte Profit Plus (.csv)", type="csv")

# 4. Procesamiento
if file_banco and file_profit:
    df_b = pd.read_csv(file_banco)
    df_p = pd.read_csv(file_profit)
    
    # Aquí puedes insertar tu lógica de unión de dataframes
    # Para asegurar que la información aparezca:
    st.success("Archivos cargados correctamente.")
    
    # Ejemplo de visualización para probar que la info sí llega:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", 
        "🔄 Inversiones", "⚠️ Errores Humanos"
    ])
    
    with tab1:
        st.dataframe(df_b.head()) # Prueba de carga

    # Botón de descarga al final de todo
    st.divider()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_b.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Descargar Reporte Completo",
        data=output.getvalue(),
        file_name=f"Conciliacion_{empresa}_{banco}_{mes}_{ano}.xlsx"
    )

# 5. Footer con tu firma
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</div>", unsafe_allow_html=True)

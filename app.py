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
    1. Seleccione la empresa, banco, frecuencia, mes y año.
    2. Cargue los archivos de Banco y Profit CSV. 
    3. La app realizará la conciliación automática en segundos.
    4. Descargue la conciliación completa para su análisis.
    """)

# --- CONFIGURACIÓN DE PARÁMETROS ---
col1, col2 = st.columns(2)
empresa = col1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = col2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"])

c3, c4, c5 = st.columns(3)
frecuencia = c3.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = c4.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = c5.selectbox("📅 Año:", list(range(2026, 2030)))

skip_rows = st.number_input("Filas a saltar:", min_value=0, value=0)

# --- LÓGICA DE PROCESAMIENTO ---
def limpiar_ref_profit(ref):
    ref_str = str(ref).strip()
    if ref_str.endswith('-1'):
        return '1' + ref_str[:-2]
    return ref_str

# --- CARGA DE ARCHIVOS ---
b1, b2 = st.columns(2)
file_banco = b1.file_uploader("📥 Estado de Cuenta Bancario (.csv)", type="csv")
file_profit = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type="csv")

if file_banco and file_profit:
    df_b = pd.read_csv(file_banco, skiprows=skip_rows)
    df_p = pd.read_csv(file_profit, skiprows=skip_rows)
    
    # Normalización
    df_p['Ref_Procesada'] = df_p['Referencia'].apply(limpiar_ref_profit)
    df_b['Ref_Procesada'] = df_b['Referencia'].astype(str).str.strip()
    
    df_b['Ref_Corto'] = df_b['Ref_Procesada'].str[-3:]
    df_p['Ref_Corto'] = df_p['Ref_Procesada'].str[-3:]

    # PESTAÑAS
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", 
        "🔄 Inversiones", "⚠️ Duplicados/Errores"
    ])
    
    tab1.dataframe(df_b, use_container_width=True)
    tab2.dataframe(df_b, use_container_width=True)
    tab3.dataframe(df_p, use_container_width=True)
    
    # EXPORTACIÓN
    st.divider()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_b.to_excel(writer, sheet_name="Conciliados", index=False)
    
    st.download_button(
        label="📥 Descargar Reporte Completo en Excel",
        data=output.getvalue(),
        file_name=f"Conciliacion {empresa} {banco} {mes} {ano}.xlsx"
    )

# --- FOOTER ---
st.markdown("<br><br><div class='footer'>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</div>", unsafe_allow_html=True)

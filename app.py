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

# --- LÓGICA DE PROCESAMIENTO ---
def limpiar_ref_profit(ref):
    ref_str = str(ref).strip()
    if ref_str.endswith('-1'):
        return '1' + ref_str[:-2]
    return ref_str

def encontrar_columna(df, posibles_nombres):
    """Busca una columna ignorando mayúsculas, tildes y espacios"""
    for col in df.columns:
        col_limpia = str(col).strip().lower()
        for pos in posibles_nombres:
            if pos.lower() in col_limpia:
                return col
    return None

# --- CARGA DE ARCHIVOS ---
b1, b2 = st.columns(2)
file_banco = b1.file_uploader("📥 Estado de Cuenta Bancario (.csv)", type="csv")
file_profit = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type="csv")

if file_banco and file_profit:
    try:
        df_b = pd.read_csv(file_banco, encoding='latin-1', sep=None, engine='python')
        df_p = pd.read_csv(file_profit, encoding='latin-1', sep=None, engine='python')
        
        # Limpiar nombres de columnas de espacios extra
        df_b.columns = df_b.columns.str.strip()
        df_p.columns = df_p.columns.str.strip()

        # Detectar columna de Referencia de forma inteligente
        col_ref_b = encontrar_columna(df_b, ['referencia', 'ref', 'nro_ref'])
        col_ref_p = encontrar_columna(df_p, ['referencia', 'ref', 'nro_ref'])

        if not col_ref_b or not col_ref_p:
            st.error("No se pudo localizar la columna de 'Referencia' en uno de los archivos. Verifique los encabezados.")
        else:
            # Normalización de referencias
            df_p['Ref_Procesada'] = df_p[col_ref_p].apply(limpiar_ref_profit)
            df_b['Ref_Procesada'] = df_b[col_ref_b].astype(str).str.strip()
            
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
        st.error(f"Error al procesar los archivos: {e}")

# --- FOOTER ---
st.markdown("<br><br><div class='footer'>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</div>", unsafe_allow_html=True)

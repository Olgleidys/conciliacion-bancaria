import streamlit as st
import pandas as pd
import numpy as np
import re
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

# --- TÍTULO E INSTRUCCIONES ---
st.title("📊 Sistema Automatizado de Conciliación Bancaria")
with st.expander("📖 Instrucciones de uso"):
    st.markdown("""
    1. Seleccione empresa, banco, frecuencia, mes y año.
    2. Cargue los archivos CSV del Banco y de Profit Plus. 
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

# --- FUNCIONES ---
def limpiar_monto(val):
    if pd.isna(val) or val == "": return 0.0
    try:
        val_str = re.sub(r'[^0-9,.-]', '', str(val))
        if ',' in val_str and '.' in val_str: val_str = val_str.replace('.', '').replace(',', '.')
        else: val_str = val_str.replace(',', '.')
        return float(val_str)
    except: return 0.0

# --- LÓGICA DE PROCESAMIENTO ---
b1, b2 = st.columns(2)
file_banco = b1.file_uploader("📥 Estado de Cuenta Bancario (.csv)", type="csv")
file_profit = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type="csv")

if file_banco and file_profit:
    try:
        df_b = pd.read_csv(file_banco, encoding='latin-1', sep=None, engine='python')
        df_p = pd.read_csv(file_profit, encoding='latin-1', sep=None, engine='python')
        
        # Limpieza inicial
        df_b.columns = df_b.columns.str.strip()
        df_p.columns = df_p.columns.str.strip()
        
        # Normalización (Ajustar nombres de columnas según sus CSV reales si es necesario)
        df_b['Monto_Num'] = df_b.iloc[:, -1].apply(limpiar_monto)
        df_p['Monto_Num'] = df_p.iloc[:, -1].apply(limpiar_monto)
        df_b['Ref_Procesada'] = df_b.iloc[:, 0].astype(str).str.strip()
        df_p['Ref_Procesada'] = df_p.iloc[:, 0].astype(str).str.strip()
        df_b['Ref_Corto'] = df_b['Ref_Procesada'].str[-3:]
        df_p['Ref_Corto'] = df_p['Ref_Procesada'].str[-3:]

        # CRUCES DE CONCILIACIÓN
        cruce_A = pd.merge(df_b, df_p, on=['Ref_Procesada', 'Monto_Num'], how='inner')
        cruce_B = pd.merge(df_b, df_p, on=['Ref_Corto', 'Monto_Num'], how='inner')
        grupo_p = df_p.groupby('Ref_Corto')['Monto_Num'].sum().reset_index()
        cruce_C = pd.merge(df_b, grupo_p, on='Ref_Corto', suffixes=('', '_Sum'))
        cruce_C = cruce_C[cruce_C['Monto_Num'] == cruce_C['Monto_Num_Sum']]
        
        df_conciliados = pd.concat([cruce_A, cruce_B, cruce_C]).drop_duplicates()
        
        # PENDIENTES E INVERSIONES
        df_pend_banco = df_b[~df_b['Ref_Procesada'].isin(df_conciliados['Ref_Procesada'])]
        df_pend_profit = df_p[~df_p['Ref_Procesada'].isin(df_conciliados['Ref_Procesada'])]
        df_errores = df_p[df_p.duplicated(subset=['Ref_Procesada', 'Monto_Num'], keep=False)]

        # --- PESTAÑAS VISUALES ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", 
            "🔄 Inversiones", "⚠️ Duplicados/Errores"
        ])
        
        tab1.dataframe(df_conciliados, use_container_width=True)
        tab2.dataframe(df_pend_banco, use_container_width=True)
        tab3.dataframe(df_pend_profit, use_container_width=True)
        tab4.write("Análisis de inversiones Debe/Haber pendiente")
        tab5.dataframe(df_errores, use_container_width=True)

        # --- EXPORTACIÓN ---
        st.divider()
        st.subheader("📥 Exportación Final")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_conciliados.to_excel(writer, sheet_name="Conciliados", index=False)
            df_pend_banco.to_excel(writer, sheet_name="Pendientes_Banco", index=False)
            df_pend_profit.to_excel(writer, sheet_name="Pendientes_Profit", index=False)
            df_errores.to_excel(writer, sheet_name="Duplicados_Errores", index=False)
        
        st.download_button(
            label="📥 Descargar Reporte Completo en Excel",
            data=output.getvalue(),
            file_name=f"Conciliacion {empresa} {banco} {mes} {ano}.xlsx"
        )
    except Exception as e:
        st.error(f"Error al procesar: {e}")

# --- FOOTER ---
st.markdown("<br><br><div class='footer'>© 2026 | Sistema Conciliación — Lic. Olgleidys Hernández ✨</div>", unsafe_allow_html=True)

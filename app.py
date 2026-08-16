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

# --- FUNCIONES DE APOYO ---
def limpiar_ref_profit(ref):
    ref_str = str(ref).strip()
    if ref_str.endswith('-1'):
        return '1' + ref_str[:-2]
    return ref_str

def limpiar_monto(val):
    if pd.isna(val) or val == "": return 0.0
    try:
        val_str = re.sub(r'[^0-9,.-]', '', str(val))
        if ',' in val_str and '.' in val_str: 
            val_str = val_str.replace('.', '').replace(',', '.')
        else: 
            val_str = val_str.replace(',', '.')
        return float(val_str)
    except: return 0.0

def encontrar_columna(df, posibles):
    for col in df.columns:
        col_limpia = str(col).strip().lower()
        for p in posibles:
            if p.lower() in col_limpia:
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
        
        # Limpiar espacios en los nombres de las columnas
        df_b.columns = df_b.columns.str.strip()
        df_p.columns = df_p.columns.str.strip()
        
        # Detección inteligente de columnas
        col_ref_b = encontrar_columna(df_b, ['referencia', 'ref', 'nro_ref'])
        col_ref_p = encontrar_columna(df_p, ['referencia', 'ref', 'nro_ref'])
        
        # Detectar columnas de montos (Credito/Haber o Debito/Debe)
        col_monto_b = encontrar_columna(df_b, ['credito', 'haber', 'monto', 'debito', 'debe'])
        col_monto_p = encontrar_columna(df_p, ['haber', 'credito', 'monto', 'debe', 'debito'])

        if not col_ref_b or not col_ref_p or not col_monto_b or not col_monto_p:
            st.error("No se pudieron detectar automáticamente las columnas de 'Referencia' o 'Monto'. Verifique los nombres en sus CSV.")
        else:
            # Procesamiento de datos
            df_b['Ref_Procesada'] = df_b[col_ref_b].astype(str).str.strip()
            df_p['Ref_Procesada'] = df_p[col_ref_p].apply(limpiar_ref_profit)
            
            df_b['Ref_Corto'] = df_b['Ref_Procesada'].str[-3:]
            df_p['Ref_Corto'] = df_p['Ref_Procesada'].str[-3:]
            
            df_b['Monto_Num'] = df_b[col_monto_b].apply(limpiar_monto)
            df_p['Monto_Num'] = df_p[col_monto_p].apply(limpiar_monto)

            # --- CRUCES DE CONCILIACIÓN ---
            # A: Referencia Completa + Monto Exacto
            cruce_A = pd.merge(df_b, df_p, on=['Ref_Procesada', 'Monto_Num'], how='inner', suffixes=('_Banco', '_Profit'))
            cruce_A['Tipo_Cruce'] = 'A: Ref Completa y Monto'

            # B: Últimos 3 dígitos + Monto Exacto
            cruce_B = pd.merge(df_b, df_p, on=['Ref_Corto', 'Monto_Num'], how='inner', suffixes=('_Banco', '_Profit'))
            cruce_B = cruce_B[~cruce_B.index.isin(cruce_A.index)]
            cruce_B['Tipo_Cruce'] = 'B: Ref Corta y Monto'

            # C: Sumatoria Grupal en Profit == Monto del Banco
            grupo_p = df_p.groupby('Ref_Corto')['Monto_Num'].sum().reset_index()
            cruce_C = pd.merge(df_b, grupo_p, on='Ref_Corto', suffixes=('', '_Sum'))
            cruce_C = cruce_C[cruce_C['Monto_Num'] == cruce_C['Monto_Num_Sum']]
            cruce_C['Tipo_Cruce'] = 'C: Sumatoria Desglose Profit'

            df_conciliados = pd.concat([cruce_A, cruce_B, cruce_C], ignore_index=True).drop_duplicates()
            
            # PENDIENTES E INVERSIONES
            refs_conciliadas_b = df_conciliados['Ref_Procesada'].unique() if 'Ref_Procesada' in df_conciliados.columns else []
            df_pend_banco = df_b[~df_b['Ref_Procesada'].isin(refs_conciliadas_b)]
            df_pend_profit = df_p[~df_p['Ref_Procesada'].isin(refs_conciliadas_b)]
            df_errores = df_p[df_p.duplicated(subset=['Ref_Procesada', 'Monto_Num'], keep=False)]

            # --- PESTAÑAS VISUALES ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", 
                "🔄 Inversiones", "⚠️ Duplicados/Errores"
            ])
            
            with tab1:
                st.dataframe(df_conciliados, use_container_width=True)
            with tab2:
                st.dataframe(df_pend_banco, use_container_width=True)
            with tab3:
                st.dataframe(df_pend_profit, use_container_width=True)
            with tab4:
                st.write("Análisis de inversiones Debe/Haber")
            with tab5:
                st.dataframe(df_errores, use_container_width=True)

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
        st.error(f"Error al procesar los archivos: {e}")

# --- FOOTER ---
st.markdown("<br><br><div class='footer'>© 2026 | Sistema Conciliación — Lic. Olgleidys Hernández ✨</div>", unsafe_allow_html=True)

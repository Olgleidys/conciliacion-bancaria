import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")

st.title("⚖️ Conciliación Bancaria Profesional")

# Funciones de limpieza
def limpiar_df(df):
    df.columns = [c.lower().strip() for c in df.columns]
    # Limpieza de montos y referencias
    if 'monto' not in df.columns: # Asumimos columnas estándar
        # Intentar sumar debe/haber o debito/credito
        cols_monto = [c for c in df.columns if c in ['debe', 'haber', 'debito', 'credito']]
        for col in cols_monto:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    
    df['ref_clean'] = df['referencia'].astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
    df['ref_3'] = df['ref_clean'].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    return df

# Carga de archivos
col1, col2 = st.columns(2)
file_b = col1.file_uploader("Estado de Cuenta Banco", type=["xlsx"])
file_p = col2.file_uploader("Reporte Profit", type=["xlsx"])

if file_b and file_p:
    df_b = pd.read_excel(file_b)
    df_p = pd.read_excel(file_p)
    
    df_b = limpiar_df(df_b)
    df_p = limpiar_df(df_p)
    
    # Identificar montos reales (simplificamos la suma para el cruce)
    df_b['monto_final'] = df_b.get('debito', 0) + df_b.get('credito', 0)
    df_p['monto_final'] = df_p.get('debe', 0) + df_p.get('haber', 0)

    # 1. Detectar Duplicados en Profit (R4/R5)
    duplicados = df_p[df_p.duplicated(subset=['ref_clean', 'monto_final'], keep=False)]
    
    # 2. Conciliación Secuencial
    pend_b = df_b.copy()
    pend_p = df_p.copy()
    conciliados = pd.DataFrame()

    # R1: Exacto
    m1 = pd.merge(pend_b, pend_p, on=['ref_clean', 'monto_final'], suffixes=('_b', '_p'))
    conciliados = pd.concat([conciliados, m1])
    pend_b = pend_b.drop(m1.index) # Ojo: Ajustar según tu estructura real
    pend_p = pend_p.drop(m1.index)

    # Configuración de visualización para 2 decimales
    format_dict = {"monto_final": st.column_config.NumberColumn(format="%.2f")}

    # Pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", "⚠️ Duplicados Profit"])

    with tab1:
        st.dataframe(conciliados, column_config=format_dict, use_container_width=True)
    with tab2:
        st.dataframe(pend_b, column_config=format_dict, use_container_width=True)
    with tab3:
        st.dataframe(pend_p, column_config=format_dict, use_container_width=True)
    with tab4:
        st.dataframe(duplicados, column_config=format_dict, use_container_width=True)

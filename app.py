import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")

custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    div[data-testid="stMetricValue"] { color: #00b4d8 !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- UI DE CARGA ---
c1, c2 = st.columns(2)
banco_file = c1.file_uploader("📥 Estado de Cuenta", type=["csv"])
profit_file = c2.file_uploader("📥 Reporte Profit", type=["csv"])

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

if banco_file and profit_file:
    # Cargar archivos respetando encabezados originales
    df_b = pd.read_csv(banco_file, sep=None, engine='python', encoding="latin-1")
    df_p = pd.read_csv(profit_file, sep=None, engine='python', encoding="latin-1")
    
    # Identificar nombres de columnas para el proceso
    nom_b = list(df_b.columns)
    nom_p = list(df_p.columns)
    
    # Crear copias para procesar (normalizar nombres para cruce)
    df_b_proc = df_b.copy()
    df_p_proc = df_p.copy()
    
    for df in [df_b_proc, df_p_proc]:
        df.rename(columns={df.columns[0]: 'Fecha', df.columns[1]: 'Ref', df.columns[3]: 'Monto'}, inplace=True)
        df['Monto'] = limpiar_monto(df['Monto'])
        df['Ref'] = df['Ref'].fillna('').astype(str).str.strip()

    # --- LÓGICA DE CRUCE ---
    # Merge usando nombres normalizados
    cruce = pd.merge(df_b_proc, df_p_proc, on=['Ref', 'Monto'], suffixes=('_B', '_P'))
    
    # --- FILTRADO DE COLUMNAS PARA EL USUARIO ---
    # Queremos mostrar solo las columnas originales (ignorando Estado, Origen, etc.)
    # Seleccionamos las columnas del banco original + las del profit original que no sean Ref/Monto
    cols_finales = [c for c in cruce.columns if '_B' in c or '_P' in c]
    cols_limpias = [c for c in cols_finales if 'Estado' not in c and 'Origen' not in c and 'Monto_Limpio' not in c and 'Ref3' not in c]
    
    st.subheader("✅ Movimientos Conciliados")
    st.dataframe(cruce[cols_limpias], use_container_width=True)
    
    # --- DESCARGA ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        cruce[cols_limpias].to_excel(writer, index=False, sheet_name='Conciliados')
    
    st.download_button("📥 Descargar Reporte Limpio", data=output.getvalue(), file_name="Reporte_Conciliacion.xlsx")

else:
    st.info("Cargue ambos archivos para proceder con la conciliación.")

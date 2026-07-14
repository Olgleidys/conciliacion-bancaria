import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Conciliación Bancaria", layout="wide")

st.title("📊 Sistema de Conciliación Bancaria (Auditoría Total)")

col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader("📥 Estado de Cuenta (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader("📥 Reporte Profit (.csv)", type=["csv"])

def procesar(file):
    df = pd.read_csv(file, sep=';', encoding="latin-1", dtype=str)
    cols_ref = [c for c in df.columns if 'referencia' in c.lower()]
    ref_col = cols_ref[0] if cols_ref else df.columns[1]
    df = df[[df.columns[0], ref_col, df.columns[2], df.columns[3], df.columns[4]]]
    df.columns = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
    return df

def limpiar(valor):
    if pd.isna(valor): return ""
    v = str(valor)
    if 'E+' in v: v = str(int(float(v.replace(',', '.'))))
    return re.sub(r'[^0-9]', '', v)

if banco_file and profit_file:
    df_b = procesar(banco_file)
    df_p = procesar(profit_file)
    
    # Limpieza
    for df in [df_b, df_p]:
        df['Ref_Clean'] = df['Ref'].apply(limpiar)
        df['Monto'] = pd.to_numeric(df['Cred'].str.replace(',', '.'), errors='coerce').fillna(0)
    
    # --- LÓGICA DE CONCILIACIÓN SIN PÉRDIDA DE DATOS ---
    # Marcamos los de < 3 dígitos como "No conciliables"
    df_b['Tipo_Cruce'] = df_b['Ref_Clean'].apply(lambda x: 'Pendiente' if len(x) >= 3 else 'Ref Corta')
    df_p['Tipo_Cruce'] = df_p['Ref_Clean'].apply(lambda x: 'Pendiente' if len(x) >= 3 else 'Ref Corta')
    
    # 1. Intento Cruce Exacto
    df_b['Key1'] = df_b['Ref_Clean'] + "_" + df_b['Monto'].astype(str)
    df_p['Key1'] = df_p['Ref_Clean'] + "_" + df_p['Monto'].astype(str)
    
    # 2. Intento Cruce 3 dígitos
    df_b['Key2'] = df_b['Ref_Clean'].str[-3:] + "_" + df_b['Monto'].astype(str)
    df_p['Key2'] = df_p['Ref_Clean'].str[-3:] + "_" + df_p['Monto'].astype(str)
    
    # Realizamos merge para ver todo
    df_b = df_b.merge(df_p[['Key1', 'Key2', 'Ref', 'Fecha']], on='Key1', how='outer', suffixes=('', '_P'), indicator=True)
    
    # Mostrar resultados
    st.write("### 📋 Resultados Detallados")
    st.dataframe(df_b, use_container_width=True)
    
    st.info("💡 Si un movimiento no tiene pareja, verás columnas vacías o '_P' (Profit) al lado del Banco. Esto te permite ver exactamente qué falta.")

    # Descarga de todo el histórico
    output = io.BytesIO()
    df_b.to_excel(output, index=False)
    st.download_button("📥 Descargar Auditoría Completa", data=output.getvalue(), file_name="Auditoria_Conciliacion.xlsx")

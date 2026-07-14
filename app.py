import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Conciliación Bancaria", layout="wide")
st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# ... (Mantén tus selectores de empresa, banco, fecha, etc.) ...

col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader("📥 Estado de Cuenta (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader("📥 Reporte Profit (.csv)", type=["csv"])

def procesar_archivo(file):
    try:
        # Leemos forzando el separador ";"
        df = pd.read_csv(file, sep=';', encoding="latin-1", dtype=str)
        
        # BUSCADOR ESPECÍFICO: Busca la columna que contiene la palabra "referencia"
        columnas_ref = [c for c in df.columns if 'referencia' in c.lower()]
        
        if not columnas_ref:
            st.error("No encontré la columna 'referencia'. Revisa el archivo.")
            return None
            
        nombre_columna = columnas_ref[0]
        # Renombramos la columna encontrada a 'Ref_Fija' para trabajar cómodamente
        df.rename(columns={nombre_columna: 'Ref_Fija'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Error procesando archivo: {e}")
        return None

def limpiar(valor):
    if pd.isna(valor) or valor == '': return ""
    # Corrige notación científica E+ y quita todo lo que no sea número
    v = str(valor)
    if 'E+' in v:
        try: v = str(int(float(v)))
        except: pass
    return re.sub(r'[^0-9]', '', v)

if banco_file and profit_file:
    df_b = procesar_archivo(banco_file)
    df_p = procesar_archivo(profit_file)
    
    if df_b is not None and df_p is not None:
        # Limpieza usando la columna 'Ref_Fija'
        df_b['Ref_Clean'] = df_b['Ref_Fija'].apply(limpiar)
        df_p['Ref_Clean'] = df_p['Ref_Fija'].apply(limpiar)
        
        # Convertimos Cred/Haber a números para comparar
        df_b['Monto'] = pd.to_numeric(df_b.iloc[:,4].str.replace(',', '.'), errors='coerce').fillna(0)
        df_p['Monto'] = pd.to_numeric(df_p.iloc[:,4].str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Cruce
        df_b['Key'] = df_b['Ref_Clean'] + "_" + df_b['Monto'].astype(str)
        df_p['Key'] = df_p['Ref_Clean'] + "_" + df_p['Monto'].astype(str)
        
        cruces = df_b[df_b['Key'].isin(df_p['Key'])]
        solo_b = df_b[~df_b['Key'].isin(df_p['Key'])]
        solo_p = df_p[~df_p['Key'].isin(df_b['Key'])]

        # Mostrar tablas
        t1, t2, t3 = st.tabs(["✅ Cruces Exitosos", "🏦 Solo Banco", "💻 Solo Profit"])
        t1.dataframe(cruces, use_container_width=True)
        t2.dataframe(solo_b, use_container_width=True)
        t3.dataframe(solo_p, use_container_width=True)

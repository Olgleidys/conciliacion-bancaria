import streamlit as st
import pandas as pd
import io
import re

# Configuración de la página web
st.set_page_config(page_title="Conciliación Bancaria con KPIs", page_icon="📊", layout="wide")

# ESTILOS CSS
custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

def procesar_csv(file):
    try: 
        # Forzamos la lectura de la columna 'Ref' como cadena (dtype=str) desde el inicio
        return pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip", dtype={'Ref': str})
    except: return None

def limpiar_monto(serie):
    serie = serie.astype(str).str.replace(',', '.', regex=False)
    serie = serie.apply(lambda x: re.sub(r'[^0-9.]', '', x))
    return pd.to_numeric(serie, errors='coerce').fillna(0).round(2)

# Inputs
col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader("📥 Estado de Cuenta (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader("📥 Reporte Profit (.csv)", type=["csv"])

if banco_file and profit_file:
    df_banco = procesar_csv(banco_file)
    df_profit = procesar_csv(profit_file)
    
    if df_banco is not None and df_profit is not None:
        try:
            # Limpieza de nombres de columnas
            df_banco.columns = [str(c).strip() for c in df_banco.columns]
            df_profit.columns = [str(c).strip() for c in df_profit.columns]
            
            # Ajuste de columnas fijas
            df_banco = df_banco.iloc[:, :5]
            df_banco.columns = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
            df_profit = df_profit.iloc[:, :5]
            df_profit.columns = ['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']
            
            # --- LIMPIEZA EXTREMA Y SEGURA DE REFERENCIAS ---
            for df in [df_banco, df_profit]:
                df['Ref'] = df['Ref'].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lstrip('0')
            
            # Limpieza montos
            df_banco['Monto_Num'] = limpiar_monto(df_banco['Cred'])
            df_profit['Monto_Num'] = limpiar_monto(df_profit['Haber'])

            # LÓGICA DE CONCILIACIÓN
            df_banco['Key_Exacta'] = df_banco['Ref'] + "_" + df_banco['Monto_Num'].astype(str)
            df_profit['Key_Exacta'] = df_profit['Ref'] + "_" + df_profit['Monto_Num'].astype(str)
            
            # Cruce
            cruces_exactos = df_banco[df_banco['Key_Exacta'].isin(df_profit['Key_Exacta'])]
            pendientes_banco = df_banco[~df_banco['Key_Exacta'].isin(df_profit['Key_Exacta'])]
            pendientes_profit = df_profit[~df_profit['Key_Exacta'].isin(df_banco['Key_Exacta'])]
            
            # Cruce Secundario (últimos 3 dígitos)
            pb_valido = pendientes_banco[pendientes_banco['Ref'].str.len() >= 3].copy()
            pp_valido = pendientes_profit[pendientes_profit['Ref'].str.len() >= 3].copy()
            
            pb_valido['Key_Sec'] = pb_valido['Ref'].str[-3:] + "_" + pb_valido['Monto_Num'].astype(str)
            pp_valido['Key_Sec'] = pp_valido['Ref'].str[-3:] + "_" + pp_valido['Monto_Num'].astype(str)
            
            secundarios = pb_valido[pb_valido['Key_Sec'].isin(pp_valido['Key_Sec'])]
            
            # Resultados
            cruces_finales = pd.concat([cruces_exactos, secundarios])
            final_banco = pendientes_banco[~pendientes_banco.index.isin(secundarios.index)]
            final_profit = pendientes_profit[~pendientes_profit.index.isin(secundarios.index)]

            # Mostrar datos limpios (sin columnas técnicas)
            cols_b = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
            cols_p = ['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']
            
            t1, t2, t3 = st.tabs(["✅ Cruces", "🏦 Solo Banco", "💻 Solo Profit"])
            t1.dataframe(cruces_finales[cols_b], use_container_width=True)
            t2.dataframe(final_banco[cols_b], use_container_width=True)
            t3.dataframe(final_profit[cols_p], use_container_width=True)

        except Exception as e: 
            st.error(f"Error crítico en el procesamiento: {e}")
            st.write("Asegúrate de que tus archivos CSV no tengan filas mezcladas o encabezados extraños.")

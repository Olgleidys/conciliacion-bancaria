import streamlit as st
import pandas as pd
import io

# --- Configuración y CSS (mantenlo igual) ---
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")

# ... (Insertar aquí tu bloque custom_css)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- UI de Selección ---
empresa_seleccionada = st.selectbox("🏢 Seleccione la empresa:", ["Thermo Group", "Mystic", "Keravital"])
bancos_por_empresa = {"Thermo Group": ["Banesco", "Venezuela"], "Mystic": ["Banesco"], "Keravital": ["Banesco"]}
banco_seleccionado = st.selectbox("🏦 Seleccione el banco:", bancos_por_empresa[empresa_seleccionada])

col1, col2 = st.columns(2)
banco_file = col1.file_uploader(f"📥 Cargar {banco_seleccionado}", type=["csv"])
profit_file = col2.file_uploader(f"📥 Cargar Profit", type=["csv"])

# --- Funciones ---
def procesar_csv(file):
    return pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

def preparar_df(df, es_banco):
    df.columns = [str(c).strip() for c in df.columns]
    if 'Referencia' in df.columns: df.rename(columns={'Referencia': 'Ref'}, inplace=True)
    df['Ref'] = df['Ref'].fillna('').astype(str).str.strip()
    # Asignar columnas fijas para evitar errores de índice
    cols = ['Fecha', 'Ref', 'Desc', 'M1', 'M2']
    df.columns = cols
    df['Monto_Limpio'] = limpiar_monto(df['M1']) + limpiar_monto(df['M2'])
    return df

# --- Lógica Principal ---
if banco_file and profit_file:
    df_banco = preparar_df(procesar_csv(banco_file), True)
    df_profit = preparar_df(procesar_csv(profit_file), False)

    # 1. Cruce 100%
    cruce_1 = pd.merge(df_banco, df_profit, on=['Ref', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    # 2. Cruce por últimos 3 dígitos
    df_banco['Ref_3'] = df_banco['Ref'].str[-3:]
    df_profit['Ref_3'] = df_profit['Ref'].str[-3:]
    
    rest_b = df_banco[~df_banco.index.isin(cruce_1.index)]
    rest_p = df_profit[~df_profit.index.isin(cruce_1.index)]
    
    cruce_2 = pd.merge(rest_b, rest_p, on=['Ref_3', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    cruces_final = pd.concat([cruce_1, cruce_2])
    
    solo_banco = df_banco[~df_banco.index.isin(cruces_final.index)]
    solo_profit = df_profit[~df_profit.index.isin(cruces_final.index)]

    # --- Visualización ---
    tab1, tab2, tab3 = st.tabs(["✅ Conciliados", "🏦 Solo Banco", "💻 Solo Profit"])
    
    with tab1: st.dataframe(cruces_final[['Fecha_B', 'Ref_B', 'Desc_B', 'Monto_Limpio']], use_container_width=True)
    with tab2: st.dataframe(solo_banco[['Fecha', 'Ref', 'Desc', 'M1', 'M2']], use_container_width=True)
    with tab3: st.dataframe(solo_profit[['Fecha', 'Ref', 'Desc', 'M1', 'M2']], use_container_width=True)

import streamlit as st
import pandas as pd
import re
import io

# --- CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="Conciliación Lic. Olgleidys")

# --- FUNCIONES ---
def limpiar_monto(val):
    if pd.isna(val) or val == "": return 0.0
    try:
        val_str = re.sub(r'[^0-9,.-]', '', str(val))
        if ',' in val_str and '.' in val_str: val_str = val_str.replace('.', '').replace(',', '.')
        else: val_str = val_str.replace(',', '.')
        return float(val_str)
    except: return 0.0

def encontrar_columna(df, posibles):
    for col in df.columns:
        if any(p.lower() in col.lower() for p in posibles): return col
    return None

# --- UI ---
st.title("📊 Sistema Automatizado de Conciliación Bancaria")

b1, b2 = st.columns(2)
file_banco = b1.file_uploader("📥 Estado de Cuenta Bancario (.csv)", type="csv")
file_profit = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type="csv")

if file_banco and file_profit:
    try:
        df_b = pd.read_csv(file_banco, encoding='latin-1', sep=None, engine='python')
        df_p = pd.read_csv(file_profit, encoding='latin-1', sep=None, engine='python')
        
        # Detectar columnas dinámicamente
        ref_b, ref_p = encontrar_columna(df_b, ['referencia']), encontrar_columna(df_p, ['referencia'])
        monto_b = encontrar_columna(df_b, ['debito', 'debe', 'credito', 'haber'])
        monto_p = encontrar_columna(df_p, ['debito', 'debe', 'credito', 'haber'])
        
        df_b['Ref_P'] = df_b[ref_b].astype(str).str.strip()
        df_b['Ref_Corta'] = df_b['Ref_P'].str[-3:]
        df_b['Monto_N'] = df_b[monto_b].apply(limpiar_monto)
        
        df_p['Ref_P'] = df_p[ref_p].astype(str).str.strip()
        df_p['Ref_Corta'] = df_p['Ref_P'].str[-3:]
        df_p['Monto_N'] = df_p[monto_p].apply(limpiar_monto)

        # --- LÓGICA DE CRUCES ---
        # A: Ref completa y monto igual
        cruce_A = pd.merge(df_b, df_p, on=['Ref_P', 'Monto_N'], suffixes=('_B', '_P'))
        cruce_A['Tipo'] = 'A: Ref completa y monto'
        
        # B: Ref corta (3 dig) y monto igual
        cruce_B = pd.merge(df_b, df_p, on=['Ref_Corta', 'Monto_N'], suffixes=('_B', '_P'))
        cruce_B = cruce_B[~cruce_B.index.isin(cruce_A.index)]
        cruce_B['Tipo'] = 'B: Ref 3 dígitos y monto'
        
        # C: Sumatoria de desgloses (Profit suma == Banco)
        grupo_p = df_p.groupby('Ref_Corta')['Monto_N'].sum().reset_index()
        cruce_C = pd.merge(df_b, grupo_p, on='Ref_Corta', suffixes=('', '_Sum'))
        cruce_C = cruce_C[cruce_C['Monto_N'] == cruce_C['Monto_N_Sum']]
        cruce_C['Tipo'] = 'C: Sumatoria de desgloses'

        df_conciliados = pd.concat([cruce_A, cruce_B, cruce_C])

        # --- AUDITORÍA DE DUPLICADOS Y ERRORES ---
        # Duplicados exactos (Ref y Monto)
        df_errores = df_p[df_p.duplicated(subset=['Ref_P', 'Monto_N'], keep=False)].copy()
        df_errores['Observacion'] = '⚠️ Duplicado Exacto'
        
        # Alerta roja: Ref igual, montos distintos, pero coinciden 3 números
        def es_rojo(row, df):
            coincidencias = df[(df['Ref_P'] == row['Ref_P']) & (df['Monto_N'] != row['Monto_N'])]
            for _, m in coincidencias.iterrows():
                if any(str(row['Monto_N'])[i:i+3] in str(m['Monto_N']) for i in range(len(str(row['Monto_N']))-2)):
                    return True
            return False
            
        df_p['Es_Rojo'] = df_p.apply(lambda row: es_rojo(row, df_p), axis=1)
        df_rojo = df_p[df_p['Es_Rojo']]
        df_rojo['Observacion'] = '❌ ALERTA ROJA: Coincidencia 3 números'

        # --- PESTAÑAS Y EXPORTACIÓN ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["✅ Conciliados", "🏦 Pend. Banco", "💻 Pend. Profit", "🔄 Inversiones", "⚠️ Duplicados/Errores"])
        
        tab1.dataframe(df_conciliados, use_container_width=True)
        tab5.dataframe(pd.concat([df_errores, df_rojo]), use_container_width=True)
        
        # (Exportación se mantiene igual que la anterior)
        
    except Exception as e:
        st.error(f"Error técnico: {e}")

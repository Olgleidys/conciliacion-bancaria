import streamlit as st
import pandas as pd

st.set_page_config(page_title="Conciliación Bancaria y Detección de Inversiones", layout="wide")
st.title("⚖️ Conciliación Bancaria: Exactos, 3 Dígitos e Invertidos")

# --- FUNCIONES DE LIMPIEZA ---
def limpiar_banco(df):
    df.columns = [c.lower().strip() for c in df.columns]
    for col in ['debito', 'credito']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0.0)
    df['ref_clean'] = df['referencia'].astype(str).str.replace('.0', '', regex=False).str.lstrip('0').str.strip()
    df['ref_3'] = df['ref_clean'].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    return df

def limpiar_profit(df):
    df.columns = [c.lower().strip() for c in df.columns]
    for col in ['debe', 'haber']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0.0)
    df['ref_clean'] = df['referencia'].astype(str).str.replace('.0', '', regex=False).str.lstrip('0').str.strip()
    df['ref_3'] = df['ref_clean'].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    return df

# --- CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
file_b = col1.file_uploader("Estado de Cuenta Banco (Excel)", type=["xlsx"])
file_p = col2.file_uploader("Reporte Profit (Excel)", type=["xlsx"])

if file_b and file_p:
    df_b = limpiar_banco(pd.read_excel(file_b))
    df_p = limpiar_profit(pd.read_excel(file_p))

    # 1. DUPLICADOS EN PROFIT (Exactos por referencia y montos)
    duplicados_profit = df_p[df_p.duplicated(subset=['ref_clean', 'debe', 'haber'], keep=False)]

    # 2. CRUCES EXACTOS NORMALES
    # Egreso: Banco Debito == Profit Haber
    ex_norm_eg = pd.merge(df_b[df_b['debito'] > 0], df_p[df_p['haber'] > 0], left_on=['ref_clean', 'debito'], right_on=['ref_clean', 'haber'], suffixes=('_b', '_p'))
    ex_norm_eg['Regla'] = 'Exacto Normal (Egreso)'
    
    # Ingreso: Banco Credito == Profit Debe
    ex_norm_in = pd.merge(df_b[df_b['credito'] > 0], df_p[df_p['debe'] > 0], left_on=['ref_clean', 'credito'], right_on=['ref_clean', 'debe'], suffixes=('_b', '_p'))
    ex_norm_in['Regla'] = 'Exacto Normal (Ingreso)'

    # 3. CRUCES EXACTOS INVERTIDOS (Error de registro: Ej. Banco Debito cruzado con Profit Debe)
    ex_inv_1 = pd.merge(df_b[df_b['debito'] > 0], df_p[df_p['debe'] > 0], left_on=['ref_clean', 'debito'], right_on=['ref_clean', 'debe'], suffixes=('_b', '_p'))
    ex_inv_1['Regla'] = 'Invertido (Banco Debito / Profit Debe)'

    ex_inv_2 = pd.merge(df_b[df_b['credito'] > 0], df_p[df_p['haber'] > 0], left_on=['ref_clean', 'credito'], right_on=['ref_clean', 'haber'], suffixes=('_b', '_p'))
    ex_inv_2['Regla'] = 'Invertido (Banco Credito / Profit Haber)'

    # 4. CRUCES POR ÚLTIMOS 3 DÍGITOS (Normales)
    t3_eg = pd.merge(df_b[df_b['debito'] > 0], df_p[df_p['haber'] > 0], left_on=['ref_3', 'debito'], right_on=['ref_3', 'haber'], suffixes=('_b', '_p'))
    t3_eg['Regla'] = '3 Dígitos (Egreso)'

    t3_in = pd.merge(df_b[df_b['credito'] > 0], df_p[df_p['debe'] > 0], left_on=['ref_3', 'credito'], right_on=['ref_3', 'debe'], suffixes=('_b', '_p'))
    t3_in['Regla'] = '3 Dígitos (Ingreso)'

    # Unir resultados para visualización limpia
    df_exactos = pd.concat([ex_norm_eg, ex_norm_in])
    df_invertidos = pd.concat([ex_inv_1, ex_inv_2])
    df_tres_digitos = pd.concat([t3_eg, t3_in])

    # --- VISUALIZACIÓN EN PESTAÑAS ---
    tabs = st.tabs([
        "✅ Exactos Normales", 
        "🔀 Invertidos en Registro", 
        "🔍 Por 3 Dígitos", 
        "⚠️ Duplicados Profit"
    ])

    formatos = {"debito": "{:.2f}", "credito": "{:.2f}", "debe": "{:.2f}", "haber": "{:.2f}"}

    with tabs[0]:
        st.subheader("Operaciones con Referencia y Monto Exacto (Egresos e Ingresos)")
        st.dataframe(df_exactos, column_config=formatos, use_container_width=True)

    with tabs[1]:
        st.subheader("Operaciones con Inversión en el Registro (Débito/Crédito cruzados)")
        st.dataframe(df_invertidos, column_config=formatos, use_container_width=True)

    with tabs[2]:
        st.dataframe(df_tres_digitos, column_config=formatos, use_container_width=True)

    with tabs[3]:
        st.dataframe(duplicados_profit, column_config=formatos, use_container_width=True)

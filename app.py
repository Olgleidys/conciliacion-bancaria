import streamlit as st
import pandas as pd

st.set_page_config(page_title="Conciliación Bancaria", layout="wide")

st.title("⚖️ Conciliación Bancaria: Cero Diferencias")

# --- FUNCIONES DE LIMPIEZA ---
def limpiar_df(df):
    # Convertir todo a string, quitar espacios y convertir montos
    df = df.astype(str).apply(lambda x: x.str.strip())
    
    # Limpiar columnas numéricas
    for col in ['debito', 'credito', 'debe', 'haber']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0.0)
    
    # Limpiar referencias
    df['ref_clean'] = df['referencia'].str.replace('.0', '', regex=False).str.lstrip('0')
    df['ref_3'] = df['ref_clean'].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    return df

# --- CARGA ---
col1, col2 = st.columns(2)
file_b = col1.file_uploader("Estado de Cuenta Banco (Excel)", type=["xlsx"])
file_p = col2.file_uploader("Reporte Profit (Excel)", type=["xlsx"])

if file_b and file_p:
    df_b = pd.read_excel(file_b).rename(columns={c: c.lower().strip() for c in pd.read_excel(file_b).columns})
    df_p = pd.read_excel(file_p).rename(columns={c: c.lower().strip() for c in pd.read_excel(file_p).columns})
    
    df_b = limpiar_df(df_b)
    df_p = limpiar_df(df_p)

    # --- IDENTIFICAR DUPLICADOS PROFIT (R4/R5) ---
    duplicados = df_p[df_p.duplicated(subset=['ref_clean', 'debe', 'haber'], keep=False)]

    # --- CONCILIACIÓN ---
    # Separamos ingresos (Credito banco / Debe Profit) y egresos (Debito Banco / Haber Profit)
    # Aquí vamos a conciliar buscando exactitud en monto y referencia
    
    # Copias para trabajar
    pend_b = df_b.copy()
    pend_p = df_p.copy()
    conciliados = pd.DataFrame()

    # R1: Cruce Exacto (Ref + Monto)
    # Cruzamos Debito Banco con Haber Profit (Egresos)
    m1_egresos = pd.merge(pend_b, pend_p, left_on=['ref_clean', 'debito'], right_on=['ref_clean', 'haber'], suffixes=('_b', '_p'))
    m1_egresos['Regla'] = 'Exacta (Ref+Monto)'
    
    # Cruzamos Credito Banco con Debe Profit (Ingresos)
    m1_ingresos = pd.merge(pend_b, pend_p, left_on=['ref_clean', 'credito'], right_on=['ref_clean', 'debe'], suffixes=('_b', '_p'))
    m1_ingresos['Regla'] = 'Exacta (Ref+Monto)'

    conciliados = pd.concat([conciliados, m1_egresos, m1_ingresos])

    # R2: 3 Digitos (Ref + Monto) - Excluyendo ya conciliados
    # (Filtrado simple para evitar duplicados en la lista de conciliados)
    
    # --- RESULTADOS ---
    tabs = st.tabs(["✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", "⚠️ Duplicados Profit"])
    
    format_dict = {"debito": "{:.2f}", "credito": "{:.2f}", "debe": "{:.2f}", "haber": "{:.2f}"}

    with tabs[0]:
        st.dataframe(conciliados, use_container_width=True)
    with tabs[1]:
        st.dataframe(pend_b, use_container_width=True)
    with tabs[2]:
        st.dataframe(pend_p, use_container_width=True)
    with tabs[3]:
        st.dataframe(duplicados, use_container_width=True)

    # Descarga
    csv = conciliados.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar Conciliados", csv, "conciliados.csv")

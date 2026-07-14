import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN DE PÁGINA Y CSS (MANTENIDO) ---
st.set_page_config(page_title="Conciliación Bancaria con KPIs", page_icon="📊", layout="wide")

custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    div[data-testid="stMetricValue"] { color: #00b4d8 !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- UI Y LÓGICA ---
st.title("📊 Sistema Automatizado de Conciliación Bancaria")

empresa = st.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
bancos = {"Thermo Group": ["Banesco", "Venezuela"], "Mystic": ["Banesco"], "Keravital": ["Banesco"]}
banco = st.selectbox("🏦 Banco:", bancos[empresa])

c1, c2 = st.columns(2)
banco_file = c1.file_uploader("📥 Estado de Cuenta", type=["csv"])
profit_file = c2.file_uploader("📥 Reporte Profit", type=["csv"])

def preparar_df(file, es_banco):
    df = pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    df.columns = [str(c).strip() for c in df.columns]
    if 'Referencia' in df.columns: df.rename(columns={'Referencia': 'Ref'}, inplace=True)
    df['Ref'] = df['Ref'].fillna('').astype(str).str.strip()
    # Identificar columnas clave (asumiendo orden: Fecha, Ref, Desc, Debe, Haber)
    cols = list(df.columns)
    df = df.rename(columns={cols[0]: 'Fecha', cols[1]: 'Ref', cols[2]: 'Desc', cols[3]: 'M1', cols[4]: 'M2'})
    df['Monto_Limpio'] = pd.to_numeric(df['M1'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0) + \
                         pd.to_numeric(df['M2'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    return df[['Fecha', 'Ref', 'Desc', 'M1', 'M2', 'Monto_Limpio']]

if banco_file and profit_file:
    df_b = preparar_df(banco_file, True)
    df_p = preparar_df(profit_file, False)

    # Lógica de Conciliación
    # 1. Cruce 100%
    cruce_1 = pd.merge(df_b, df_p, on=['Ref', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    # 2. Cruce últimos 3 dígitos
    df_b['Ref_3'] = df_b['Ref'].str[-3:]
    df_p['Ref_3'] = df_p['Ref'].str[-3:]
    
    res_b = df_b[~df_b.index.isin(cruce_1.index)]
    res_p = df_p[~df_p.index.isin(cruce_1.index)]
    
    cruce_2 = pd.merge(res_b, res_p, on=['Ref_3', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    cruces = pd.concat([cruce_1, cruce_2])
    solo_b = df_b[~df_b.index.isin(cruces.index)]
    solo_p = df_p[~df_p.index.isin(cruces.index)]

    # --- PESTAÑAS Y VISUALIZACIÓN ---
    tab1, tab2, tab3 = st.tabs(["✅ Conciliados", "🏦 Solo Banco", "💻 Solo Profit"])
    
    with tab1: st.dataframe(cruces[['Fecha_B', 'Ref_B', 'Desc_B', 'M1_B', 'M2_B']], use_container_width=True)
    with tab2: st.dataframe(solo_b[['Fecha', 'Ref', 'Desc', 'M1', 'M2']], use_container_width=True)
    with tab3: st.dataframe(solo_p[['Fecha', 'Ref', 'Desc', 'M1', 'M2']], use_container_width=True)
    
    st.success("¡Conciliación procesada manteniendo toda tu estética y datos intactos!")

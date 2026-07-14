import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN Y ESTILOS (Mantenidos) ---
st.set_page_config(page_title="Conciliación Bancaria con KPIs", page_icon="📊", layout="wide")

custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    div[data-testid="stMetricValue"] { color: #00b4d8 !important; font-size: 28px !important; font-weight: bold !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; border-radius: 8px !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- HEADER Y CONFIGURACIÓN ---
st.title("📊 Sistema Automatizado de Conciliación Bancaria")
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Seleccione la empresa:", ["Thermo Group", "Mystic", "Keravital"])
bancos = {"Thermo Group": ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"], "Mystic": ["Banesco", "Venezuela", "Banplus", "Banplus Mazal"], "Keravital": ["Banesco", "Venezuela"]}
banco = c2.selectbox("🏦 Seleccione el banco:", bancos[empresa])

p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2025"])

# --- CARGA DE ARCHIVOS ---
b1, b2 = st.columns(2)
banco_file = b1.file_uploader(f"📥 Estado de Cuenta {banco}", type=["csv"])
profit_file = b2.file_uploader("📥 Reporte Profit Plus", type=["csv"])

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

def procesar_df(file, es_banco):
    df = pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    df.columns = [str(c).strip() for c in df.columns]
    if 'Referencia' in df.columns: df.rename(columns={'Referencia': 'Ref'}, inplace=True)
    
    # Estandarizar nombres (ajustado a tu estructura)
    cols = list(df.columns)
    df = df.rename(columns={cols[0]: 'Fecha', cols[1]: 'Ref', cols[2]: 'Desc', cols[3]: 'M1', cols[4]: 'M2'})
    df['Ref'] = df['Ref'].fillna('').astype(str).str.strip().str.lstrip('0')
    df['Monto_Limpio'] = limpiar_monto(df['M1']) + limpiar_monto(df['M2'])
    return df

if banco_file and profit_file:
    df_b = procesar_df(banco_file, True)
    df_p = procesar_df(profit_file, False)

    # Lógica: 1. Cruce Exacto | 2. Cruce últimos 3 dígitos
    cruce_1 = pd.merge(df_b, df_p, on=['Ref', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    df_b['Ref3'] = df_b['Ref'].str[-3:]
    df_p['Ref3'] = df_p['Ref'].str[-3:]
    
    rest_b = df_b[~df_b.index.isin(cruce_1.index)]
    rest_p = df_p[~df_p.index.isin(cruce_1.index)]
    cruce_2 = pd.merge(rest_b, rest_p, on=['Ref3', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    cruces_final = pd.concat([cruce_1, cruce_2])
    solo_b = df_b[~df_b.index.isin(cruces_final.index)]
    solo_p = df_p[~df_p.index.isin(cruces_final.index)]

    # --- PESTAÑAS Y RESULTADOS ---
    tab1, tab2, tab3, tab4 = st.tabs(["✅ Cruces Exitosos", "🏦 Pendiente Banco", "💻 Pendiente Profit", "📈 Indicadores"])
    
    with tab1: st.dataframe(cruces_final[['Fecha_B', 'Ref_B', 'Desc_B', 'M1_B', 'M2_B']], use_container_width=True)
    with tab2: st.dataframe(solo_b[['Fecha', 'Ref', 'Desc', 'M1', 'M2']], use_container_width=True)
    with tab3: st.dataframe(solo_p[['Fecha', 'Ref', 'Desc', 'M1', 'M2']], use_container_width=True)
    
    with tab4:
        st.metric("🎯 Tasa de Conciliación", f"{(len(cruces_final)/len(df_b)*100):.1f}%")
        st.bar_chart(pd.DataFrame({'Categoría': ['Conciliados', 'Solo Banco', 'Solo Profit'], 'Movimientos': [len(cruces_final), len(solo_b), len(solo_p)]}).set_index('Categoría'))

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Olgleidys Hernández 👩‍💻✨</p></div>', unsafe_allow_html=True)

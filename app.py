import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN Y ESTILOS ---
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

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# Configuración (Período y Empresa)
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])

p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2025"])

# Definición de archivos (Deben estar antes de cualquier lógica)
banco_file = st.file_uploader(f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"])
profit_file = st.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

# --- LÓGICA SOLO SI EXISTEN ARCHIVOS ---
if banco_file is not None and profit_file is not None:
    df_b = pd.read_csv(banco_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    df_p = pd.read_csv(profit_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    
    nombres_orig_b = list(df_b.columns)
    nombres_orig_p = list(df_p.columns)
    
    for df in [df_b, df_p]:
        df.columns = [str(c).strip() for c in df.columns]
        if 'Referencia' in df.columns: df.rename(columns={'Referencia': 'Ref'}, inplace=True)
        cols = list(df.columns)
        df.rename(columns={cols[0]: 'Fecha', cols[1]: 'Ref', cols[2]: 'Desc', cols[3]: 'M1', cols[4]: 'M2'}, inplace=True)
        df['Ref'] = df['Ref'].fillna('').astype(str).str.strip()
        df['Monto_Limpio'] = limpiar_monto(df['M1']) + limpiar_monto(df['M2'])

    # Conciliación
    cruce_1 = pd.merge(df_b, df_p, on=['Ref', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    df_b['Ref3'] = df_b['Ref'].str[-3:]
    df_p['Ref3'] = df_p['Ref'].str[-3:]
    
    rest_b = df_b[~df_b.index.isin(cruce_1.index)]
    rest_p = df_p[~df_p.index.isin(cruce_1.index)]
    cruce_2 = pd.merge(rest_b, rest_p, on=['Ref3', 'Monto_Limpio'], suffixes=('_B', '_P'))
    cruces_final = pd.concat([cruce_1, cruce_2])
    
    # Preparar visualización limpiando columnas técnicas
    cols_a_mostrar_b = nombres_orig_b[:5]
    cols_a_mostrar_p = nombres_orig_p[:5]
    
    df_b_show = df_b.rename(columns={'Fecha': nombres_orig_b[0], 'Ref': nombres_orig_b[1], 'Desc': nombres_orig_b[2], 'M1': nombres_orig_b[3], 'M2': nombres_orig_b[4]})
    df_p_show = df_p.rename(columns={'Fecha': nombres_orig_p[0], 'Ref': nombres_orig_p[1], 'Desc': nombres_orig_p[2], 'M1': nombres_orig_p[3], 'M2': nombres_orig_p[4]})
    
    # Cruces (Renombrados correctamente)
    cruces_show = cruces_final.rename(columns={
        'Fecha_B': nombres_orig_b[0], 'Ref_B': nombres_orig_b[1], 'Desc_B': nombres_orig_b[2], 'M1_B': nombres_orig_b[3], 'M2_B': nombres_orig_b[4]
    })[cols_a_mostrar_b]

    # Tabs
    tab1, tab2, tab3 = st.tabs(["✅ Cruces Exitosos", "🏦 Pendiente Banco", "💻 Pendiente Profit"])
    with tab1: st.dataframe(cruces_show, use_container_width=True)
    with tab2: st.dataframe(df_b_show.loc[~df_b.index.isin(cruces_final.index), cols_a_mostrar_b], use_container_width=True)
    with tab3: st.dataframe(df_p_show.loc[~df_p.index.isin(cruces_final.index), cols_a_mostrar_p], use_container_width=True)

    # Descarga
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        cruces_show.to_excel(writer, sheet_name='Conciliados', index=False)
        df_b_show.loc[~df_b.index.isin(cruces_final.index), cols_a_mostrar_b].to_excel(writer, sheet_name='Solo_Banco', index=False)
        df_p_show.loc[~df_p.index.isin(cruces_final.index), cols_a_mostrar_p].to_excel(writer, sheet_name='Solo_Profit', index=False)
    st.download_button("📥 Descargar Conciliación Limpia", data=output.getvalue(), file_name="Conciliacion_Final.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)

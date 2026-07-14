import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Conciliación Bancaria", page_icon="📊", layout="wide")
custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; border-radius: 8px !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

c1, c2 = st.columns(2)
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])
banco_file = st.file_uploader(f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"])
profit_file = st.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

if banco_file and profit_file:
    # Leer archivos
    df_b = pd.read_csv(banco_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    df_p = pd.read_csv(profit_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    
    # Capturamos los nombres reales de las columnas actuales
    cols_b = list(df_b.columns)
    cols_p = list(df_p.columns)
    
    # Procesamiento (usamos las primeras 5 columnas)
    df_b_proc = df_b.iloc[:, :5].copy()
    df_p_proc = df_p.iloc[:, :5].copy()
    
    # Renombramos temporalmente para la lógica de conciliación
    for df in [df_b_proc, df_p_proc]:
        df.columns = ['Fecha', 'Ref', 'Desc', 'M1', 'M2']
        df['Ref'] = df['Ref'].fillna('').astype(str).str.strip()
        df['Monto_Limpio'] = limpiar_monto(df['M1']) + limpiar_monto(df['M2'])
        df['Ref3'] = df['Ref'].str[-3:]

    # Conciliación
    df_b['Estado'] = 'Pendiente'
    df_p['Estado'] = 'Pendiente'
    
    matches = pd.merge(df_b_proc.reset_index(), df_p_proc.reset_index(), on=['Ref', 'Monto_Limpio'], suffixes=('_B', '_P'))
    df_b.loc[matches['index_B'], 'Estado'] = 'Conciliado'
    df_p.loc[matches['index_P'], 'Estado'] = 'Conciliado'

    pend_b = df_b_proc[df_b['Estado'] == 'Pendiente']
    pend_p = df_p_proc[df_p['Estado'] == 'Pendiente']
    matches3 = pd.merge(pend_b.reset_index(), pend_p.reset_index(), on=['Ref3', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    df_b.loc[matches3['index_B'], 'Estado'] = 'Conciliado'
    df_p.loc[matches3['index_P'], 'Estado'] = 'Conciliado'

    # Preparar visualización usando los nombres originales capturados al inicio
    df_b_vis = df_b.iloc[:, :5].copy()
    df_b_vis['Estado'] = df_b['Estado']
    
    df_p_vis = df_p.iloc[:, :5].copy()
    df_p_vis['Estado'] = df_p['Estado']

    st.subheader("Todos los movimientos conciliados")
    tab1, tab2, tab3 = st.tabs(["✅ Todos los movimientos", "🏦 Pendientes Banco", "💻 Pendientes Profit"])
    
    with tab1: st.dataframe(pd.concat([df_b_vis.assign(Origen='Banco'), df_p_vis.assign(Origen='Profit')]), use_container_width=True)
    with tab2: st.dataframe(df_b_vis[df_b_vis['Estado'] == 'Pendiente'], use_container_width=True)
    with tab3: st.dataframe(df_p_vis[df_p_vis['Estado'] == 'Pendiente'], use_container_width=True)

    # Descarga
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.concat([df_b_vis.assign(Origen='Banco'), df_p_vis.assign(Origen='Profit')]).to_excel(writer, sheet_name='Todos_Movimientos', index=False)
    st.download_button("📥 Descargar conciliación completa (Excel)", data=output.getvalue(), file_name="Conciliacion_Completa.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)

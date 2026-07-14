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

# Configuración
c1, c2 = st.columns(2)
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])
banco_file = st.file_uploader(f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"])
profit_file = st.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace(r'[^0-9,.-]', '', regex=True).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)

if banco_file and profit_file:
    df_b = pd.read_csv(banco_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    df_p = pd.read_csv(profit_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    
    # Preparamos los DataFrames finales con los nombres deseados
    # Asumiendo que tus columnas de interés están en las primeras 5 posiciones
    columnas_finales = ['Fecha', 'Referencia', 'Descripción', 'Debito', 'Credito']
    
    def procesar_df(df):
        df_proc = df.iloc[:, :5].copy()
        df_proc.columns = columnas_finales
        df_proc['Monto_Limpio'] = limpiar_monto(df_proc['Debito']) + limpiar_monto(df_proc['Credito'])
        df_proc['Ref3'] = df_proc['Referencia'].astype(str).str.strip().str[-3:]
        df_proc['Estado'] = 'Pendiente'
        return df_proc

    df_b_final = procesar_df(df_b)
    df_p_final = procesar_df(df_p)

    # Lógica de conciliación
    matches = pd.merge(df_b_final.reset_index(), df_p_final.reset_index(), on=['Referencia', 'Monto_Limpio'], suffixes=('_B', '_P'))
    df_b_final.loc[matches['index_B'], 'Estado'] = 'Conciliado'
    df_p_final.loc[matches['index_P'], 'Estado'] = 'Conciliado'

    # Conciliación por últimos 3 dígitos
    pend_b = df_b_final[df_b_final['Estado'] == 'Pendiente']
    pend_p = df_p_final[df_p_final['Estado'] == 'Pendiente']
    matches3 = pd.merge(pend_b.reset_index(), pend_p.reset_index(), on=['Ref3', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    df_b_final.loc[matches3['index_B'], 'Estado'] = 'Conciliado'
    df_p_final.loc[matches3['index_P'], 'Estado'] = 'Conciliado'

    # --- VISUALIZACIÓN ---
    # Unimos y seleccionamos solo las columnas resaltadas
    full_df = pd.concat([df_b_final, df_p_final])
    cols_a_mostrar = columnas_finales + ['Estado']
    
    st.subheader("Todos los movimientos conciliados")
    st.dataframe(full_df[cols_a_mostrar], use_container_width=True)

    tab_p1, tab_p2 = st.tabs(["🏦 Pendientes Banco", "💻 Pendientes Profit"])
    with tab_p1: st.dataframe(df_b_final[df_b_final['Estado'] == 'Pendiente'][cols_a_mostrar], use_container_width=True)
    with tab_p2: st.dataframe(df_p_final[df_p_final['Estado'] == 'Pendiente'][cols_a_mostrar], use_container_width=True)

    # --- DESCARGA ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        full_df[cols_a_mostrar].to_excel(writer, sheet_name='Todos_Movimientos', index=False)
        
    st.download_button("📥 Descargar conciliación completa (Excel)", data=output.getvalue(), file_name="Conciliacion_Completa.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria</p></div>', unsafe_allow_html=True)

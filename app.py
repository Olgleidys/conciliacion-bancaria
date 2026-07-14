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

# Instrucciones de uso
with st.expander("📖 Instrucciones de uso"):
    st.write("""
    1. **Selecciona** la empresa, banco y periodo correspondiente.
    2. **Carga** el archivo CSV del estado de cuenta bancario y el reporte de Profit Plus.
    3. **Visualiza** los resultados en las pestañas (Todos, Pendientes Banco, Pendientes Profit).
    4. **Descarga** el archivo Excel final haciendo clic en el botón inferior.
    """)

# Configuración (Período y Empresa)
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Banco:", ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "Banco Fondo Común"])

p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2025"])

banco_file = st.file_uploader(f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"])
profit_file = st.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

if banco_file and profit_file:
    df_b = pd.read_csv(banco_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    df_p = pd.read_csv(profit_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    
    # --- PROCESAMIENTO ---
    df_b_proc = df_b.iloc[:, :5].copy()
    df_p_proc = df_p.iloc[:, :5].copy()
    
    nombres_cols = ['Fecha', 'Referencia', 'Descripción', 'Debito', 'Credito']
    df_b_proc.columns = nombres_cols
    df_p_proc.columns = nombres_cols
    
    for df in [df_b_proc, df_p_proc]:
        df['Referencia'] = df['Referencia'].astype(str).str.strip()
        df['Monto_Limpio'] = limpiar_monto(df['Debito']) + limpiar_monto(df['Credito'])
        df['Ref3'] = df['Referencia'].str[-3:]

    df_b_proc['Estado'] = 'Pendiente'
    df_p_proc['Estado'] = 'Pendiente'
    
    matches = pd.merge(df_b_proc.reset_index(), df_p_proc.reset_index(), on=['Referencia', 'Monto_Limpio'], suffixes=('_B', '_P'))
    df_b_proc.loc[matches['index_B'], 'Estado'] = 'Conciliado'
    df_p_proc.loc[matches['index_P'], 'Estado'] = 'Conciliado'

    pend_b = df_b_proc[df_b_proc['Estado'] == 'Pendiente']
    pend_p = df_p_proc[df_p_proc['Estado'] == 'Pendiente']
    matches3 = pd.merge(pend_b.reset_index(), pend_p.reset_index(), on=['Ref3', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    df_b_proc.loc[matches3['index_B'], 'Estado'] = 'Conciliado'
    df_p_proc.loc[matches3['index_P'], 'Estado'] = 'Conciliado'

    # --- VISUALIZACIÓN ---
    st.subheader("Todos los movimientos conciliados")
    full_df = pd.concat([df_b_proc.assign(Origen='Banco'), df_p_proc.assign(Origen='Profit')])
    cols_a_mostrar = ['Fecha', 'Referencia', 'Descripción', 'Debito', 'Credito', 'Estado', 'Origen']
    
    tab1, tab2, tab3 = st.tabs(["✅ Todos los movimientos", "🏦 Pendientes Banco", "💻 Pendientes Profit"])
    with tab1: st.dataframe(full_df[cols_a_mostrar], use_container_width=True)
    with tab2: st.dataframe(df_b_proc[df_b_proc['Estado'] == 'Pendiente'][cols_a_mostrar[:-1]], use_container_width=True)
    with tab3: st.dataframe(df_p_proc[df_p_proc['Estado'] == 'Pendiente'][cols_a_mostrar[:-1]], use_container_width=True)

    # --- DESCARGA ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        full_df[cols_a_mostrar].to_excel(writer, sheet_name='Todos_Movimientos', index=False)
        df_b_proc[df_b_proc['Estado'] == 'Pendiente'][cols_a_mostrar[:-1]].to_excel(writer, sheet_name='Pendientes_Banco', index=False)
        df_p_proc[df_p_proc['Estado'] == 'Pendiente'][cols_a_mostrar[:-1]].to_excel(writer, sheet_name='Pendientes_Profit', index=False)
        
    st.download_button("📥 Descargar conciliación completa (Excel)", data=output.getvalue(), file_name="Conciliacion_Completa.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)

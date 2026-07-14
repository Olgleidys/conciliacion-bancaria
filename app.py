import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Conciliación Bancaria", page_icon="📊", layout="wide")
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

banco_file = st.file_uploader(f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"])
profit_file = st.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

if banco_file and profit_file:
    df_b = pd.read_csv(banco_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    df_p = pd.read_csv(profit_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    
    # Preservar nombres originales
    nombres_orig_b = list(df_b.columns)
    nombres_orig_p = list(df_p.columns)
    
    # Crear copias de trabajo para la lógica
    df_b_proc = df_b.copy()
    df_p_proc = df_p.copy()
    
    for df in [df_b_proc, df_p_proc]:
        df.columns = [str(c).strip() for c in df.columns]
        if 'Referencia' in df.columns: df.rename(columns={'Referencia': 'Ref'}, inplace=True)
        cols = list(df.columns)
        df.rename(columns={cols[0]: 'Fecha', cols[1]: 'Ref', cols[2]: 'Desc', cols[3]: 'M1', cols[4]: 'M2'}, inplace=True)
        df['Ref'] = df['Ref'].fillna('').astype(str).str.strip()
        df['Monto_Limpio'] = limpiar_monto(df['M1']) + limpiar_monto(df['M2'])
        df['Ref3'] = df['Ref'].str[-3:]

    # Conciliación (etiquetado sin eliminar nada)
    df_b['Estado'] = 'Pendiente'
    df_p['Estado'] = 'Pendiente'
    
    # Lógica de cruce y asignación de ID de conciliación
    # 1. 100%
    matches = pd.merge(df_b_proc.reset_index(), df_p_proc.reset_index(), on=['Ref', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    # Marcar estados en los originales
    df_b.loc[matches['index_B'], 'Estado'] = 'Conciliado'
    df_p.loc[matches['index_P'], 'Estado'] = 'Conciliado'

    # 2. Cruces últimos 3 (solo donde Estado sea Pendiente)
    pend_b = df_b_proc[df_b['Estado'] == 'Pendiente']
    pend_p = df_p_proc[df_p['Estado'] == 'Pendiente']
    matches3 = pd.merge(pend_b.reset_index(), pend_p.reset_index(), on=['Ref3', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    df_b.loc[matches3['index_B'], 'Estado'] = 'Conciliado'
    df_p.loc[matches3['index_P'], 'Estado'] = 'Conciliado'

    # Mostrar resultados: Todo sigue ahí, solo filtrado por estado
    tab1, tab2, tab3 = st.tabs(["✅ Todos los movimientos", "🏦 Pendientes Banco", "💻 Pendientes Profit"])
    
    with tab1: st.dataframe(pd.concat([df_b.assign(Origen='Banco'), df_p.assign(Origen='Profit')]), use_container_width=True)
    with tab2: st.dataframe(df_b[df_b['Estado'] == 'Pendiente'], use_container_width=True)
    with tab3: st.dataframe(df_p[df_p['Estado'] == 'Pendiente'], use_container_width=True)

    # Descarga
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.concat([df_b.assign(Origen='Banco'), df_p.assign(Origen='Profit')]).to_excel(writer, sheet_name='Todos_Movimientos', index=False)
    st.download_button("📥 Descargar Conciliación Completa (Con Estados)", data=output.getvalue(), file_name="Conciliacion_Completa.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>', unsafe_allow_html=True)

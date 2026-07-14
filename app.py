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

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# Configuración (Mantenida)
c1, c2 = st.columns(2)
empresa = c1.selectbox("🏢 Seleccione la empresa:", ["Thermo Group", "Mystic", "Keravital"])
banco = c2.selectbox("🏦 Seleccione el banco:", ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"])

p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2025"])

banco_file = st.file_uploader(f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"])
profit_file = st.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

if banco_file and profit_file:
    # Cargar y preparar
    df_b = pd.read_csv(banco_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    df_p = pd.read_csv(profit_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    
    # Estandarizar nombre Referencia a Ref
    for df in [df_b, df_p]:
        df.columns = [str(c).strip() for c in df.columns]
        if 'Referencia' in df.columns: df.rename(columns={'Referencia': 'Ref'}, inplace=True)
        # Asegurar columnas (asumimos las 5 primeras de tu archivo)
        cols = list(df.columns)
        df.rename(columns={cols[0]: 'Fecha', cols[1]: 'Ref', cols[2]: 'Desc', cols[3]: 'Deb', cols[4]: 'Cred'}, inplace=True)
        df['Ref'] = df['Ref'].fillna('').astype(str).str.strip()
        df['Monto_Limpio'] = limpiar_monto(df['Deb']) + limpiar_monto(df['Cred'])

    # LÓGICA SIN ELIMINAR FILAS
    # Marcamos estados iniciales
    df_b['Estado'] = 'Pendiente'
    df_p['Estado'] = 'Pendiente'
    
    # Cruce 1: 100%
    merge_1 = pd.merge(df_b, df_p, on=['Ref', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    # Cruce 2: Últimos 3 dígitos
    df_b['Ref3'] = df_b['Ref'].str[-3:]
    df_p['Ref3'] = df_p['Ref'].str[-3:]
    merge_2 = pd.merge(df_b[df_b['Estado']=='Pendiente'], df_p[df_p['Estado']=='Pendiente'], on=['Ref3', 'Monto_Limpio'], suffixes=('_B', '_P'))

    # Visualización y Descarga
    tab1, tab2, tab3 = st.tabs(["✅ Conciliados", "🏦 Solo Banco", "💻 Solo Profit"])
    
    # Mostrar resultados
    with tab1: st.dataframe(pd.concat([merge_1, merge_2]), use_container_width=True)
    with tab2: st.dataframe(df_b, use_container_width=True) # Muestra todo el original
    with tab3: st.dataframe(df_p, use_container_width=True)
    
    # EXPORTACIÓN A EXCEL (Corregida)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.concat([merge_1, merge_2]).to_excel(writer, sheet_name='Conciliados', index=False)
        df_b.to_excel(writer, sheet_name='Todo_Banco', index=False)
        df_p.to_excel(writer, sheet_name='Todo_Profit', index=False)
    
    st.download_button("📥 Descargar Conciliación Completa (Excel)", data=output.getvalue(), file_name="Conciliacion_Completa.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Olgleidys Hernández 👩‍💻✨</p></div>', unsafe_allow_html=True)

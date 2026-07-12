import streamlit as st
import pandas as pd
import io

# Configuración de la página web corporativa
st.set_page_config(page_title="Conciliación Bancaria Multi-Empresa", page_icon="📊", layout="wide")

# ESTILOS CSS PERSONALIZADOS: Look Azul Corporativo Oscuro / Premium
custom_css = """
    <style>
    /* Fondo principal de la app */
    .stApp {
        background-color: #0d1b2a;
        color: #e0e1dd;
    }
    
    /* Títulos principales */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Etiquetas de los selectores y cajas de carga */
    .stSelectbox label, .stFileUploader label {
        color: #e0e1dd !important;
        font-weight: bold !important;
    }
    
    /* Tarjetas de Métricas */
    div[data-testid="stMetricValue"] {
        color: #00b4d8 !important;
        font-size: 28px !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #ffffff !important;
    }
    
    /* Botón de descarga de Excel */
    .stDownloadButton button {
        background-color: #0077b6 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: bold !important;
        transition: background-color 0.3s ease;
    }
    .stDownloadButton button:hover {
        background-color: #00b4d8 !important;
        color: #0d1b2a !important;
    }

    /* Pie de página elegante fijo abajo */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0b132b;
        color: #bcbed8;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        font-weight: 500;
        border-top: 2px solid #0077b6;
        z-index: 100;
    }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Render del pie de página autoral
footer_html = """
    <div class="footer">
        <p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Olgleidys Hernández 👩‍💻✨</p>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)

# TÍTULO PRINCIPAL
st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# FILA 1: Configuración de Empresa y Banco
c1, c2 = st.columns(2)

with c1:
    empresa_seleccionada = st.selectbox(
        "🏢 Seleccione la empresa a conciliar:",
        ["Thermo Group", "Mystic", "Keravital"]
    )

# Diccionario de bancos por empresa
bancos_por_empresa = {
    "Thermo Group": ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"],
    "Mystic": ["Banesco", "Venezuela", "Banplus", "Banplus Mazal"],
    "Keravital": ["Banesco", "Venezuela"] # Recuerda expandir esta lista cuando gustes
}

with c2:
    bancos_disponibles = bancos_por_empresa[empresa_seleccionada]
    banco_seleccionado = st.selectbox(
        "🏦 Seleccione el banco a conciliar:",
        bancos_disponibles
    )

# FILA 2: Configuración del Período de Auditoría (Frecuencia, Mes y Año)
st.markdown("### 📅 Configuración del Período")
p1, p2, p3 = st.columns(3)

with p1:
    frecuencia = st.selectbox(
        "⏱️ Frecuencia del control:",
        ["Semanal", "Quincenal", "Mensual"]
    )

with p2:
    mes = st.selectbox(
        "📆 Mes correspondiente:",
        ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    )

with p3:
    ano = st.selectbox(
        "📅 Año:",
        ["2026", "2027", "2025"]
    )

st.markdown("---")
st.markdown(f"### Panel de Control: **{empresa_seleccionada}**")
st.info(f"⚙️ **Configuración activa:** Banco *{banco_seleccionado}* | Control *{frecuencia}* | Período: *{mes} {ano}*")

# Zona de carga de archivos en dos columnas
col1, col2 = st.columns(2)

with col1:
    banco_file = st.file_uploader(f"📥 Cargar Estado de Cuenta de {banco_seleccionado} (.csv)", type=["csv"])
with col2:
    profit_file = st.file_uploader(f"📥 Cargar Reporte de Profit Plus para {empresa_seleccionada} (.csv)", type=["csv"])

def procesar_csv(file):
    try:
        df = pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

if banco_file and profit_file:
    df_banco = procesar_csv(banco_file)
    df_profit = procesar_csv(profit_file)
    
    if df_banco is not None and df_profit is not None:
        try:
            df_banco.columns = [str(c).strip() for c in df_banco.columns]
            df_profit.columns = [str(c).strip() for c in df_profit.columns]

            while len(df_banco.columns) < 5:
                df_banco[f'Comodin_B_{len(df_banco.columns)}'] = ""
            while len(df_profit.columns) < 5:
                df_profit[f'Comodin_P_{len(df_profit.columns)}'] = 0

            cols_banco = list(df_banco.columns)
            cols_banco[0], cols_banco[1], cols_banco[2], cols_banco[3], cols_banco[4] = 'Fecha', 'Ref', 'Desc', 'Deb', 'Cred'
            df_banco.columns = cols_banco

            cols_profit = list(df_profit.columns)
            cols_profit[0], cols_profit[1], cols_profit[2], cols_profit[3], cols_profit[4] = 'Fecha', 'Ref', 'Desc', 'Debe', 'Haber'
            df_profit.columns = cols_profit
            
            df_banco['Ref'] = df_banco['Ref'].fillna('').astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
            df_profit['Ref'] = df_profit['Ref'].fillna('').astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
            
            df_banco = df_banco[df_banco['Ref'] != '']
            df_profit = df_profit[df_profit['Ref'] != '']
            
            refs_profit = set(df_profit['Ref'].unique())
            refs_banco = set(df_banco['Ref'].unique())
            
            cruces_df = df_banco[df_banco['Ref'].isin(refs_profit)]
            solo_banco_df = df_banco[~df_banco['Ref'].isin(refs_profit)]
            solo_profit_df = df_profit[~df_profit['Ref'].isin(refs_banco)]
            
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Cruces Exitosos", f"{len(cruces_df)} mov.")
            m2.metric(f"Pendientes en {banco_seleccionado}", f"{len(solo_banco_df)} mov.")
            m3.metric("Pendientes en Profit", f"{len(solo_profit_df)} mov.")
            
            tab1, tab2, tab3 = st.tabs(["✅ Cruces Exitosos", f"🏦 Solo en {banco_seleccionado}", f"💻 Solo en Profit ({empresa_seleccionada})"])
            
            with tab1:
                st.subheader("Transacciones Conciliadas Correctamente")
                st.dataframe(cruces_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']], use_container_width=True)
                
            with tab2:
                st.subheader(f"Movimientos en {banco_seleccionado} pendientes por registrar")
                st.dataframe(solo_banco_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']], use_container_width=True)
                
            with tab3:
                st.subheader(f"Movimientos en Profit pendientes por pasar por {banco_seleccionado}")
                st.dataframe(solo_profit_df[['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']], use_container_width=True)
            
            st.markdown("---")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                cruces_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']].to_excel(writer, sheet_name='Cruces_Exitosos', index=False)
                solo_banco_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']].to_excel(writer, sheet_name='Solo_en_Banco', index=False)
                solo_profit_df[['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']].to_excel(writer, sheet_name='Solo_en_Profit', index=False)
            
            # Formato de nombre automatizado e inteligente para tus archivos
            emp_nom = empresa_seleccionada.replace(" ", "_")
            bnc_nom = banco_seleccionado.replace(" ", "_")
            nombre_archivo_excel = f"Conciliacion_{emp_nom}_{bnc_nom}_{frecuencia}_{mes}_{ano}.xlsx"
            
            st.download_button(
                label=f"📥 Descargar Conciliación Completa (Excel)",
                data=output.getvalue(),
                file_name=nombre_archivo_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success(f"¡Conciliación de {empresa_seleccionada} procesada con éxito para el período {mes} {ano}!")
            
        except Exception as e:
            st.error(f"Ocurrió un error al procesar los datos: {e}")

# Espacio estético final
st.markdown("<br><br><br>", unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import io

# Configuración de la página web corporativa
st.set_page_config(page_title="Conciliación Bancaria Multi-Empresa", page_icon="📊", layout="wide")

# PIE DE PÁGINA: Derechos de autor y firma fijos al fondo de la pantalla
footer = """
    <style>
    .reportview-container .main .footer {color: rgba(49, 51, 63, 0.6);}
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f0f2f6;
        color: #31333f;
        text-align: center;
        padding: 8px;
        font-size: 14px;
        font-weight: 500;
        border-top: 1px solid #e0e0e0;
        z-index: 100;
    }
    </style>
    <div class="footer">
        <p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Olgleidys Hernández 👩‍💻✨</p>
    </div>
"""
st.markdown(footer, unsafe_allow_html=True)

# TÍTULO PRINCIPAL
st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# SECTOR DE SELECCIÓN DE TU GRUPO DE EMPRESAS
empresa_seleccionada = st.selectbox(
    "🏢 Seleccione la empresa a conciliar:",
    ["Thermo Group", "Mystic", "Keravital"]
)

st.markdown(f"### Panel de Control: **{empresa_seleccionada}**")
st.markdown("Carga tus archivos mensuales en formato CSV para procesar la auditoría de forma inmediata.")

# Zona de carga de archivos en dos columnas
col1, col2 = st.columns(2)

with col1:
    banco_file = st.file_uploader("📥 Cargar Estado de Cuenta del Banco (.csv)", type=["csv"])
with col2:
    profit_file = st.file_uploader("📥 Cargar Reporte de Profit Plus (.csv)", type=["csv"])

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
            m2.metric("Pendientes en Banco", f"{len(solo_banco_df)} mov.")
            m3.metric("Pendientes en Profit", f"{len(solo_profit_df)} mov.")
            
            tab1, tab2, tab3 = st.tabs(["✅ Cruces Exitosos", "🏦 Solo en Banco", "💻 Solo en Profit"])
            
            with tab1:
                st.subheader("Transacciones Conciliadas Correctamente")
                st.dataframe(cruces_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']], use_container_width=True)
                
            with tab2:
                st.subheader("Movimientos en Banco pendientes por registrar")
                st.dataframe(solo_banco_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']], use_container_width=True)
                
            with tab3:
                st.subheader("Movimientos en Profit pendientes por pasar por el Banco")
                st.dataframe(solo_profit_df[['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']], use_container_width=True)
            
            st.markdown("---")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                cruces_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']].to_excel(writer, sheet_name='Cruces_Exitosos', index=False)
                solo_banco_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']].to_excel(writer, sheet_name='Solo_en_Banco', index=False)
                solo_profit_df[['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']].to_excel(writer, sheet_name='Solo_en_Profit', index=False)
            
            # Nombre dinámico para el archivo Excel descargado
            nombre_archivo_excel = f"Conciliacion_{empresa_seleccionada}.xlsx"
            
            st.download_button(
                label=f"📥 Descargar Conciliación de {empresa_seleccionada} (Excel)",
                data=output.getvalue(),
                file_name=nombre_archivo_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success(f"¡Conciliación de {empresa_seleccionada} procesada con éxito!")
            
        except Exception as e:
            st.error(f"Ocurrió un error al procesar los datos: {e}")

# Espacio estético final
st.markdown("<br><br><br>", unsafe_allow_html=True)

# ... (Dentro de tu bloque donde cargas los archivos)

    # Cargar datos
    df_b = pd.read_csv(banco_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    df_p = pd.read_csv(profit_file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    
    # GUARDAMOS LOS NOMBRES ORIGINALES ANTES DE CAMBIAR NADA
    cols_b_original = list(df_b.columns)
    cols_p_original = list(df_p.columns)
    
    # Preparar DataFrames (logica interna)
    for df in [df_b, df_p]:
        df.columns = [str(c).strip() for c in df.columns]
        if 'Referencia' in df.columns: df.rename(columns={'Referencia': 'Ref'}, inplace=True)
        cols = list(df.columns)
        # Renombramos temporalmente para el cálculo
        df.rename(columns={cols[0]: 'Fecha', cols[1]: 'Ref', cols[2]: 'Desc', cols[3]: 'TempM1', cols[4]: 'TempM2'}, inplace=True)
        df['Ref'] = df['Ref'].fillna('').astype(str).str.strip()
        df['Monto_Limpio'] = limpiar_monto(df['TempM1']) + limpiar_monto(df['TempM2'])

    # ... (Realizas la lógica de cruce igual que antes)

    # AL MOSTRAR, RENOMBRAMOS PARA QUE EL USUARIO VEA LOS NOMBRES ORIGINALES
    df_b_show = df_b.rename(columns={'TempM1': cols_b_original[3], 'TempM2': cols_b_original[4]})
    df_p_show = df_p.rename(columns={'TempM1': cols_p_original[3], 'TempM2': cols_p_original[4]})
    cruces_show = cruces_final.rename(columns={'TempM1_B': cols_b_original[3], 'TempM2_B': cols_b_original[4], 
                                               'TempM1_P': cols_p_original[3], 'TempM2_P': cols_p_original[4]})

    # Ahora usas estos DataFrames "_show" para st.dataframe y el Excel

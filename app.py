# Función para procesar las alternativas basadas en los productos 
def procesar_alternativas(Codart_df, inventario_api_df):
    # Convertir los nombres de las columnas a minúsculas
    Codart_df.columns = Codart_df.columns.str.lower().str.strip()

    # Verificar si el archivo de Codart contiene las columnas requeridas
    if not {'cur', 'codart', 'embalaje'}.issubset(Codart_df.columns):
        st.error("El archivo debe contener las columnas: 'codart', 'cur' y 'embalaje'")
        return pd.DataFrame()  # Devuelve un DataFrame vacío si faltan columnas

    # Filtrar el inventario solo por los artículos que están en el archivo de Codart
    cur_Codart = Codart_df['cur'].unique()
    alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_Codart)]

    # Verificar si las columnas necesarias existen en el inventario
    columnas_necesarias = ['codart', 'cur', 'nomart', 'cum', 'carta', 'opcion', 'emb']
    for columna in columnas_necesarias:
        if columna not in alternativas_inventario_df.columns:
            st.error(f"La columna '{columna}' no se encuentra en el inventario. Verifica el archivo de origen.")
            st.stop()

    # Convertir la columna 'opcion' a enteros
    alternativas_inventario_df['opcion'] = alternativas_inventario_df['opcion'].fillna(0).astype(int)

    # Seleccionar las columnas requeridas
    alternativas_disponibles_df = alternativas_inventario_df[columnas_necesarias]

    # Combinar los Codart con las alternativas disponibles
    alternativas_disponibles_df = pd.merge(
        Codart_df[['cur', 'codart', 'embalaje']],
        alternativas_disponibles_df,
        on=['cur', 'codart'],
        how='inner'
    )

    return alternativas_disponibles_df

# Subir archivo de Codart
uploaded_file = st.file_uploader("Sube un archivo con los productos (contiene 'codart', 'cur' y 'embalaje')", type=["xlsx", "csv"])

if uploaded_file:
    # Leer el archivo subido
    if uploaded_file.name.endswith('xlsx'):
        Codart_df = pd.read_excel(uploaded_file)
    else:
        Codart_df = pd.read_csv(uploaded_file)

    # Cargar el inventario
    inventario_api_df = load_inventory_file()

    # Procesar alternativas
    alternativas_disponibles_df = procesar_alternativas(Codart_df, inventario_api_df)

    # Mostrar las alternativas
    if not alternativas_disponibles_df.empty:
        st.write("Alternativas disponibles para los productos:")
        st.dataframe(alternativas_disponibles_df)

        # Permitir seleccionar opciones
        opciones_disponibles = alternativas_disponibles_df['opcion'].unique()
        opciones_seleccionadas = st.multiselect(
            "Selecciona las opciones que deseas ver (puedes elegir varias):",
            options=sorted(opciones_disponibles)
        )

        # Filtrar según las opciones seleccionadas
        if opciones_seleccionadas:
            alternativas_filtradas = alternativas_disponibles_df[alternativas_disponibles_df['opcion'].isin(opciones_seleccionadas)]
            st.write(f"Mostrando alternativas para las opciones seleccionadas: {', '.join(map(str, opciones_seleccionadas))}")
            st.dataframe(alternativas_filtradas)

            # Generar archivo Excel para descargar
            excel_file = generar_excel(alternativas_filtradas)
            st.download_button(
                label="Descargar archivo Excel con las opciones seleccionadas",
                data=excel_file,
                file_name="alternativas_filtradas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No has seleccionado ninguna opción para mostrar.")
    else:
        st.write("No se encontraron alternativas para los códigos ingresados.")


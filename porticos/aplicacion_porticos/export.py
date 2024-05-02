import openpyxl
from openpyxl.utils import get_column_letter

class Exportar:
    def __init__(self, listas_datos):
        self.listas_datos = listas_datos

    def exportar_excel(self, nombre_archivo):
        # Crear un nuevo libro de Excel
        libro = openpyxl.Workbook()

        # Escribir cada arreglo de datos en una hoja de Excel separada
        for idx, datos in enumerate(self.listas_datos, start=1):
            hoja = libro.create_sheet(title=f'Hoja {idx}')
            self._escribir_datos_en_hoja(hoja, datos)

        # Eliminar la hoja inicial predeterminada
        libro.remove(libro['Sheet'])

        # Guardar el archivo Excel
        libro.save(nombre_archivo)

    def _escribir_datos_en_hoja(self, hoja, datos):
        # Escribir los encabezados de las columnas
        encabezados = list(datos[0].keys())
        for idx, encabezado in enumerate(encabezados, start=1):
            hoja.cell(row=1, column=idx, value=encabezado)

        # Escribir los datos en las filas siguientes
        for fila, dato in enumerate(datos, start=2):
            for columna, valor in enumerate(dato.values(), start=1):
                hoja.cell(row=fila, column=columna, value=valor)
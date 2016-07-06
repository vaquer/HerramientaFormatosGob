import os
import xlrd
import csv
import json
from django.conf import settings


def encode_row(row, txt_convert=False):
    """ Funcion que valida el encoding de un valor 
    para manejo del utf-8 en la clase csv
    """
    for item in row:
        if txt_convert:
            yield item.encode('utf-8') if type(item) == type(u'') else str(item)
        else:
            yield item.encode('utf-8') if type(item) == type(u'') else item


class XLSConverter:
    """ Clase interfaz
    para acceder a los convertidores y sus propiedades estaticas
    """
    @staticmethod
    def get_converter(format, memory_file):
        """ Funcion que retorna la instancia del convertidor
        dependiendo del formato y asociada al archivo en memoria
        Tipo de Retorno: XLSConverter or None
        """
        for decoder in XLSConverterBase.__subclasses__():
            if decoder.format_extension == format:
                return decoder(memory_file=memory_file)
        return None

    @staticmethod
    def get_mime_type_of_file(format):
        """ Funcion que retorna el MIME type 
        dependiendo del formato de archivo
        Tipo de Retorno: String
        """
        for decoder in XLSConverterBase.__subclasses__():
            if decoder.format_extension == format:
                return decoder.get_mime_type()

class XLSConverterBase(object):
    """ Clase base de los convertidores
    contiene metodos comunes de todos los convertidores
    """
    def __init__(self, *args, **kwargs):
        """ Constructor de la clase:
        Agrega como parametro el archivo en memoria (xls, xlsx)
        Obtiene la hoja de trabajo principal
        """
        self.memory_file = kwargs.get('memory_file', None)
        self.xls_file = xlrd.open_workbook(file_contents=self.memory_file.read(), encoding_override="cp1252")
        self.principal_sheet = self.xls_file.sheet_by_index(0)

    def get_rows_of_xls(self):
        """ Funcion que devuelve una funcion generadora
        para recorrer todas las filas de la hoja de trabajo
        Tipo de Retorno: Function
        """
        if not self.xls_file:
            return []

        def xls_row_generator():
            for index_row in xrange(self.principal_sheet.nrows):
               yield self.principal_sheet.row_values(index_row)

        return xls_row_generator

    def get_name_file(self):
        """ Funcion que devuelve una funcion generadora
        para recorrer todas las filas de la hoja de trabajo
        Tipo de Retorno: Function
        """
        return '{0}.{1}'.format(self.get_clean_name_file(), self.format_extension)

    def get_clean_name_file(self):
        """ Funcion que devuelve una funcion generadora
        para recorrer todas las filas de la hoja de trabajo
        Tipo de Retorno: Function
        """
        name = self.memory_file.name.replace('.xls', '').replace('xlsx', '')
        return name

    def get_path_file(self):
        """ Funcion el path donde se encuentra temporalmente alojado
        el archivo resultante del proceso de conversion
        Tipo de Retorno: String
        """
        base_path = os.path.join(settings.TEMPORAL_FILES_ROOT, self.format_extension)
        return os.path.join(base_path, self.get_name_file())

    def convert(self):
        """ Funcion que convierte el archivo xls
        al tipo especifico del convertidor, genera un archivo temporal
        y retorna un link de descarga
        Tipo de Retorno: URL
        """
        pass

    @staticmethod
    def get_mime_type():
        """ Funcion que devuelve el MIME type del convertidor
        dependiendo del tipo de archivo que maneja
        Tipo de Retorno: String
        """
        pass


class XLSToCSVConverter(XLSConverterBase):
    """ Clase Convertidor especializada
    en la transformacion de formatos xls y xlsx a csv
    """
    format_extension = 'csv'

    def __init__(self, *args, **kwargs):
        super(XLSToCSVConverter, self).__init__(*args, **kwargs)

    def convert(self):
        def converter_generator():
            with open(self.get_path_file(), 'w') as json_file:
                self.csv_writer = csv.writer(json_file)
                for row in self.get_rows_of_xls()():
                    self.csv_writer.writerow(list(encode_row(row)))

            return '{0}converter/{1}/{2}'.format(settings.FQDN, self.format_extension, self.get_name_file())

        return converter_generator()

    @staticmethod
    def get_mime_type():
        return 'text/csv'


class XLSToJSONConverter(XLSConverterBase):
    """ Clase Convertidor especializada
    en la transformacion de formatos xls y xlsx a json
    """
    format_extension = 'json'
    def __init__(self, *args, **kwargs):
        super(XLSToJSONConverter, self).__init__(*args, **kwargs)
        self.json_object = {
            'name': self.get_clean_name_file(),
            'count_rows': self.principal_sheet.nrows,
            'rows': []
        }

    def convert(self):
        def converter_generator():
            index_row = 0
            separator = ''

            with open(self.get_path_file(), 'w') as json_file:
                json_file.write("{{name: \"{0}\", count_rows: {1}, rows: [".format(self.get_clean_name_file(), self.principal_sheet.nrows))

                for row in self.get_rows_of_xls()():
                    json_file.write("{0}{1}".format(separator, json.dumps({'row': index_row, 'values': list(encode_row(row))})))

                    if index_row == 0:
                        separator = ','

                    index_row += 1

                if self.principal_sheet.nrows == index_row:
                    json_file.write("]}")

            return '{0}converter/{1}/{2}'.format(settings.FQDN, self.format_extension, self.get_name_file())

        return converter_generator()

    @staticmethod
    def get_mime_type():
        return 'application/json'


class XLSToTxtConverter(XLSConverterBase):
    """ Clase Convertidor especializada
    en la transformacion de formatos xls y xlsx a txt
    """
    format_extension = 'txt'

    def __init__(self, *args, **kwargs):
        super(XLSToTxtConverter, self).__init__(*args, **kwargs)

    def convert(self):
        def convert_generator():
            with open(self.get_path_file(), 'w') as txt_file:
                for row in self.get_rows_of_xls()():
                    txt_file.write('{0}\n'.format(';'.join(list(encode_row(row, txt_convert=True)))))

            return '{0}converter/{1}/{2}'.format(settings.FQDN, self.format_extension, self.get_name_file())

        return convert_generator()

    @staticmethod
    def get_mime_type():
        return 'text/plain'


class XLSToXMLConverter(XLSConverterBase):
    """ Clase Convertidor especializada
    en la transformacion de formatos xls y xlsx a xml
    """
    format_extension = 'xml'

    def __init__(self, *args, **kwargs):
        super(XLSToXMLConverter, self).__init__(*args, **kwargs)

    def convert(self):
        def convert_generator():
            with open(self.get_path_file(), 'w') as xml_file:
                xml_file.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?><rows>")
                for row in self.get_rows_of_xls()():
                    xml_file.write("<row>")
                    for field in encode_row(row, txt_convert=True):
                        xml_file.write("<field>{0}</field>".format(field))
                    xml_file.write("</row>")
                xml_file.write("</rows>")

            return '{0}converter/{1}/{2}'.format(settings.FQDN, self.format_extension, self.get_name_file())

        return convert_generator()

    @staticmethod
    def get_mime_type():
        return 'application/xml'


class XLSToHTMLConverter(XLSConverterBase):
    """ Clase Convertidor especializada
    en la transformacion de formatos xls y xlsx a HTML
    """
    format_extension = 'html'

    def __init__(self, *args, **kwargs):
        super(XLSToHTMLConverter, self).__init__(*args, **kwargs)

    def convert(self):
        def convert_generator():
            with open(self.get_path_file(), 'w') as html_file:
                html_file.write("<meta charset='utf-8'><table attr-name='{0}'>".format(self.get_clean_name_file()))
                for row in self.get_rows_of_xls()():
                    html_file.write("<tr>")
                    for field in encode_row(row, txt_convert=True):
                        html_file.write("<td>{0}</td>".format(field))
                    html_file.write("</tr>")
                html_file.write("</table>")

            return '{0}converter/{1}/{2}'.format(settings.FQDN, self.format_extension, self.get_name_file())

        return convert_generator()

    @staticmethod
    def get_mime_type():
        return 'text/html'
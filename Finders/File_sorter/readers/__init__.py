from Finders.File_sorter.readers.xlsx_reader import XlsxReader
from Finders.File_sorter.readers.xlsm_reader import XlsmReader
from Finders.File_sorter.readers.xls_reader import XlsReader
from Finders.File_sorter.readers.csv_reader import CsvReader

READERS = {
    ".xlsx": XlsxReader,
    ".xlsm": XlsmReader,
    ".xls": XlsReader,
    ".csv": CsvReader,
}

import csv
from io import StringIO
from itertools import groupby
import re
from . import settings


def parse_waybill_creation_file(input_string):
    return {'customer_code': get_first_regex_group_stripped(settings.CUSTOMER_CODE_REGEX, input_string),
            'customer_name': get_first_regex_group_stripped(settings.CUSTOMER_NAME_REGEX, input_string),
            'customer_city': get_first_regex_group_stripped(settings.CUSTOMER_CITY_REGEX, input_string),
            'customer_state': get_first_regex_group_stripped(settings.CUSTOMER_STATE_REGEX, input_string),
            'number': get_first_regex_group_stripped(settings.WAYBILL_NUMBER_REGEX, input_string),
            'products': parse_waybill_creation_file_products(input_string)}


def get_first_regex_group_stripped(regex, input_string):
    return re.search(regex, input_string).group(1).strip()


def parse_waybill_creation_file_products(input_string):
    results = []
    for match in re.finditer(settings.PRODUCT_REGEX, input_string):
        results.append((match.group(1).strip(), match.group(2).strip()))
    return results


def parse_waybill_closing_file(input_string):
    csv_file = StringIO(input_string)
    reader = csv.reader(csv_file, delimiter=';', quotechar='"')
    rows = list(reader)
    filtered_rows = filter(is_row_installer_product, rows)
    result = dict()
    for waybill_number, product_rows in groupby(filtered_rows, key=lambda x: x[settings.WAYBILL_NUMBER_COLUMN]):
        if is_waybill_invoiced(waybill_number, rows):
            result[waybill_number] = sum(map(get_waybill_closing_file_row_price, product_rows))
    return result


def is_waybill_invoiced(waybill_number, rows):
    filtered_rows = [row for row in rows if row[settings.WAYBILL_NUMBER_COLUMN] == waybill_number]
    return filtered_rows[0][4] == "1"


def get_waybill_closing_file_row_price(row):
    return parse_float(row[settings.QUANTITY_COLUMN]) * parse_float(row[settings.PRICE_COLUMN])


def parse_float(string: str):
    string = string.replace(',', '.')
    return float(string)


def is_row_installer_product(row):
    return row[settings.PRODUCT_CODE_COLUMN].startswith(settings.INSTALLER_PRODUCT_CODE_HEADER)

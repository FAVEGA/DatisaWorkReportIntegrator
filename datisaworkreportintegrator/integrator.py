import os.path
from time import sleep
import traceback

from watchdog.events import FileSystemEventHandler

from . import db
from . import settings
from . import parser


class Integrator:
    def __init__(self, path):
        self.path = path
        self.files = set()

    def run(self):
        while True:
            files = {f for f in os.listdir(self.path)
                     if os.path.isfile(os.path.join(self.path, f))}
            self.files |= files
            for path in self.files:
                handle_file(path)
            sleep(1)


class Handler(FileSystemEventHandler):
    def __init__(self, integrator):
        self.integrator = integrator

    def on_modified(self, event):
        """
        Called whenever a file is modified in the watched directory
        TODO: Move this somewhere else.
        :param event:
        :return:
        """
        self.integrator.files.add(event.src_path)


# noinspection PyBroadException
def handle_file(path):
    try:
        lines = read_file(path)
        if path.endswith(settings.WAYBILL_CREATION_FILE_EXTENSION):
            handle_new_waybill(lines)
        elif path.endswith(settings.WAYBILL_CLOSING_FILE_EXTENSION):
            handle_closing_waybill(lines)
        os.remove(path)
    except Exception:
        traceback.print_exc()
    finally:
        db.Session.remove()


def read_file(path):
    if os.path.exists(path):
        with open(path) as file:
            lines = "".join([line for line in file.readlines() if line])
        return lines
    raise RuntimeError("Unable to read file " + path)


def handle_closing_waybill(lines):
    print('Handling closing waybill file...')
    modified_reports = set()
    for waybill_number, price in parser.parse_waybill_closing_file(lines).items():
        report = db.get_report_for_waybill_number(waybill_number)
        if report is None or report.reviewed:
            continue
        waybill = db.get_waybill(waybill_number)
        if waybill is None:
            waybill = db.Waybill(number=waybill_number, report=report)
        waybill.sold_for = price
        db.add(waybill)
        modified_reports.add(report)
    check_modified_reports(modified_reports)


def check_modified_reports(modified_reports):
    for report in modified_reports:
        report_cost = 0
        for waybill_number in report.waybill_numbers:
            waybill = db.get_waybill(waybill_number)
            if waybill is None:
                print('Report is missing waybill price for waybill number ' + waybill_number)
                break
            report_cost += waybill.sold_for
        else:
            print('Finishing report ' + str(report.id))
            report.finished = True
            report.sold_for = report_cost
            db.add(report)


def handle_new_waybill(lines):
    print('Handling new waybill file...')
    waybill = parser.parse_waybill_creation_file(lines)
    report = db.get_first_open_report_for_customer(waybill['customer_code'])
    if waybill['number'] in db.get_waybill_numbers():
        print('Waybill {} is already in database'.format(waybill['number']))
        return
    if report is not None:
        if waybill['number'] not in report.waybill_numbers:
            update_old_report_with_waybill(report, waybill)
        else:
            print('Waybill already existed in a report.')
    else:
        create_new_report_for_waybill(waybill)


def update_old_report_with_waybill(report, waybill):
    db.add_waybill_number_to_report(report.id, waybill['number'])
    db.Session().add(report)
    db.Session().commit()
    print('Updated old report for waybill number', waybill['number'])


def create_new_report_for_waybill(waybill):
    report = db.Report()
    report.sold_for = 0
    report.creator__id = settings.USER_ID
    report.customer_name = waybill['customer_name']
    report.customer_number = waybill['customer_code']
    report.state = waybill['customer_state']
    report.city = waybill['customer_city']
    report.finished = False
    report.reviewed = False
    report.observations = ''
    report.workers = []
    db.Session.add(report)
    db.Session.commit()
    db.add_waybill_number_to_report(report.id, waybill['number'])
    print('Created new report for waybill number', waybill['number'])

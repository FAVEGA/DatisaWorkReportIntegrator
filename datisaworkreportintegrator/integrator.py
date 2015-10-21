import os.path
import traceback

from watchdog.events import FileSystemEventHandler

from . import db
from . import settings
from . import parser


class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        try:
            if os.path.exists(event.src_path):
                with open(event.src_path, 'r') as file:
                    lines = "".join([line for line in file.readlines() if line])
                os.remove(event.src_path)
                if event.src_path.endswith(settings.WAYBILL_CREATION_FILE_EXTENSION):
                    handle_new_waybill(lines)
                elif event.src_path.endswith(settings.WAYBILL_CLOSING_FILE_EXTENSION):
                    handle_closing_waybill(lines)
                db.Session.remove()
        except Exception:
            print('Error with file ' + event.src_path)
            traceback.print_exc()


def handle_closing_waybill(lines):
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
                print('Report is mising waybill price for waybill number ' + waybill_number)
                break
            report_cost += waybill.sold_for
        else:
            print('Finishing report ' + str(report.id))
            report.finished = True
            report.cost = report_cost
            db.add(report)


def handle_new_waybill(lines):
    waybill = parser.parse_waybill_creation_file(lines)
    report = db.get_first_open_report_for_customer(waybill['customer_code'])
    if report is not None:
        if waybill['number'] not in report.waybill_numbers:
            update_old_report_with_waybill(report, waybill)
    else:
        create_new_report_for_waybill(waybill)


def update_old_report_with_waybill(report, waybill):
    db.add_waybill_number_to_report(report.id, waybill['number'])
    db.Session().add(report)
    db.Session().commit()


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

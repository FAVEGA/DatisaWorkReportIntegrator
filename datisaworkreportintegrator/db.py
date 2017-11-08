# coding: utf-8
import os

from sqlalchemy import BigInteger, Boolean, Column, Float, ForeignKey, Integer, LargeBinary, String, Table, \
    create_engine, Sequence, insert, select, event, exc
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine(os.environ.get("CONNECTION_STRING"), pool_size=5)
Base = declarative_base(bind=engine)
metadata = Base.metadata
Session = scoped_session(sessionmaker(bind=engine))


@event.listens_for(engine, "engine_connect")
def ping_connection(connection, branch):
    if branch:
        return
    try:
        connection.scalar(select([1]))
    except exc.DBAPIError as err:
        if err.connection_invalidated:
            connection.scalar(select([1]))
        else:
            raise


class Job(Base):
    __tablename__ = 'job'

    id = Column(String(255), primary_key=True)
    date = Column(LargeBinary)
    description = Column(String(255))
    price = Column(Float(53))
    work_hours = Column('workhours', String(255))
    report_id = Column(ForeignKey('report.id'))
    worker__id = Column(ForeignKey('users._id'))

    report = relationship('Report')
    worker_ = relationship('User')


class Notification(Base):
    __tablename__ = 'notification'

    id = Column(BigInteger, primary_key=True)
    date = Column(LargeBinary)
    seen = Column(Boolean)
    text = Column(String(255))
    sender__id = Column(ForeignKey('users._id'))

    sender_ = relationship('User')
    users_s = relationship('User', secondary='notification_users')


t_notification_users = Table(
    'notification_users', metadata,
    Column('notification_id', ForeignKey('notification.id'), primary_key=True, nullable=False),
    Column('users__id', ForeignKey('users._id'), primary_key=True, nullable=False)
)

report_users = Table(
    'report_users', metadata,
    Column('report_id', ForeignKey('report.id'), primary_key=True, nullable=False),
    Column('workerlist__id', ForeignKey('users._id'), primary_key=True, nullable=False)
)

t_report_waybillnum = Table(
    'report_waybillnum', metadata,
    Column('report_id', ForeignKey('report.id')),
    Column('waybillnum', String(255))
)


class Waybill(Base):
    __tablename__ = 'waybill'

    id = Column(BigInteger, Sequence('user_seq'), primary_key=True)
    number = Column(String(255))
    sold_for = Column(Float(53))

    report_id = Column(ForeignKey('report.id'))
    report = relationship('Report')


class Report(Base):
    __tablename__ = 'report'

    id = Column(BigInteger, Sequence('user_seq'), primary_key=True)
    city = Column(String(255))
    cost = Column(Float(53))
    customer_name = Column('customername', String(255))
    customer_number = Column('customernum', String(255))
    date = Column(LargeBinary)
    finished = Column(Boolean)
    observations = Column(String(255))
    reviewed = Column(Boolean)
    sold_for = Column('soldfor', Float(53))
    state = Column(String(255))
    workers = relationship('User', secondary=report_users)

    creator__id = Column(ForeignKey('users._id'))
    creator = relationship('User')

    @property
    def waybill_numbers(self):
        return [pair[1] for pair in Session().query(t_report_waybillnum) if pair[0] == self.id]

    @waybill_numbers.setter
    def waybill_numbers(self, value):
        t_report_waybillnum()


class User(Base):
    __tablename__ = 'users'

    _id = Column(BigInteger, primary_key=True)
    closed_date = Column('closeddate', LargeBinary)
    login = Column(String(255))
    password = Column(String(255))
    permissions = Column(Integer)


def get_first_open_report_for_customer(customer_code):
    f = Session().query(Report).filter(Report.finished == False, Report.customer_number == customer_code)
    return f.first()


def add_waybill_number_to_report(report_id, waybill_number):
    Session().execute(insert(t_report_waybillnum).values(report_id=report_id, waybillnum=waybill_number))
    Session().commit()


def get_report_for_waybill_number(waybill_number):
    reports = [pair[0] for pair in Session().query(t_report_waybillnum) if pair[1] == waybill_number]
    if len(reports) == 0:
        return None
    return Session().query(Report).filter(Report.id == reports[0]).first()


def get_waybill_numbers():
    return [pair[1] for pair in Session().query(t_report_waybillnum)]


def get_waybill(number):
    return Session().query(Waybill).filter(Waybill.number == number).first()


def add(item):
    Session().add(item)
    Session().commit()

import datetime
import parsedatetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import twilio
from twilio.rest import TwilioRestClient
import sensi
import time
from settings import MINUTES, ACCOUNT_SID, ACCOUNT_TOKEN

engine = create_engine('sqlite:///db/data.db', echo=True)

Base = declarative_base()

WAIT = 0.5


class Reading(Base):
    __tablename__ = 'Readings'

    id = Column(Integer, primary_key=True)
    from_api_string = Column(String)
    desired_temperature = Column(String)
    current_temperature = Column(String)
    mode = Column(String)
    active = Column(Boolean)
    notified = Column(Boolean, default=False)
    assumed_date = Column(DateTime())
    created_date = Column(DateTime(), default=datetime.datetime.utcnow())

    def __repr__(self):
        return "<User(name='%s', fullname='%s', password='%s')>" % (
            self.name, self.fullname, self.password)


Base.metadata.create_all(engine)


def parse_sensi_time_format(time_string):

    hours, minutes, seconds = [int(unit.decode("utf8")) for unit in time_string.decode("utf8").split(":")]

    td = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

    return td


def get_data():
    from_api_string = sensi.get_duration()
    time.sleep(WAIT)
    desired_temperature = sensi.get_desiredTemperature()
    time.sleep(WAIT)
    current_temperature = sensi.get_temperature()
    time.sleep(WAIT)
    mode = sensi.get_mode()
    assumed_date = datetime.datetime.utcnow() - parse_sensi_time_format(from_api_string)
    active = True
    return active, assumed_date, current_temperature, desired_temperature, from_api_string, mode


def add_reading(active, assumed_date, current_temperature, desired_temperature, from_api_string, mode):
    reading = Reading(
        from_api_string=from_api_string,
        desired_temperature=desired_temperature,
        current_temperature=current_temperature,
        mode=mode,
        active=active,
        assumed_date=assumed_date
    )

    print("Adding reading as follows: {reading.from_api_string}, {reading.current_temperature}, {reading.assumed_date},"
          "".format(reading=reading))

    return reading


def run():
    active, assumed_date, current_temperature, desired_temperature, from_api_string, mode = get_data()

    if from_api_string == "00:00:00":
        print("No run session happening")

    Session = sessionmaker(bind=engine)
    session = Session()

    last_reading = session.query(Reading).filter_by(active=True).first()

    # If there is an active reading we're monitoring
    if last_reading:

        # If the active reading we're monitoring has a longer duration than the new one, it must be trumped.
        if parse_sensi_time_format(last_reading.from_api_string) > parse_sensi_time_format(from_api_string):

            # Delete last reading
            session.delete(last_reading)

            # Delete the other ones
            deletes = session.query(Reading).filter_by(active=False)

            for item in deletes:
                session.delete(item)
            print("Monitoring a new running session.")

        else:
            last_reading.active = False
            print("Continuing monitoring a run session.")

        reading = add_reading(active, assumed_date, current_temperature, desired_temperature, from_api_string, mode)

        session.add(reading)
        session.commit()
    else:
        reading = add_reading(active, assumed_date, current_temperature, desired_temperature, from_api_string, mode)

        session.add(reading)
        session.commit()
        print("Starting a fresh db.")

    threshold = datetime.timedelta(minutes=MINUTES)

    # If we are past a threshold
    duration = datetime.datetime.utcnow() - assumed_date
    if duration > threshold:
        if last_reading:
            if last_reading.notified:
                print("Run session running too long, but User was already notified")
                return
            else:
                last_reading.notified = True
        else:
            reading.notified = True

        unit = "Heater" if mode.lower() == "heat" else "AC"
        if MINUTES > 60:
            hours = duration.hours
        else:
            hours = 2

        body = "Hi. This is Sensi. Your {0} has been running for over {1} hours without affecting the temperature. " \
               "Please consider calling a service professional".format(unit, hours)

        account_sid = ACCOUNT_SID
        auth_token = ACCOUNT_TOKEN
        client = TwilioRestClient(account_sid, auth_token)

        sms = client.sms.messages.create(body=body,
                                         to="+13146402087",
                                         from_="+13148992442")

        print(sms.sid)

        session.commit()
    else:
        print("Not notifying because it has not been long enough: "+str(duration))

if __name__ == "__main__":
    run()

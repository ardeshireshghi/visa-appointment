import requests
from pyquery import PyQuery as pq
from web_page import WebPage
from web_form import WebForm
from email_notif import send_email
import json
import sys
import os
import urllib
import datetime
import re

UKVISA_BASE_URL = 'https://www.visa4uk.fco.gov.uk'
USER_EMAIL = ''
USER_PASSWORD = ''
LOGIN_PATH = '/Account/login'
USER_APPLICATIONS_PATH = '/User/UserApplications'
APPOINTMENT_LOCATION_PATH = '/Appointment/AppointmentLocation'
APPOINTMENT_AVAILIBILITY_PATH = '/Appointment/GetAppointmentAvailability'
APPOINTMENT_TIMESLOTS_PATH = '/Appointment/GetTimeSlots'
APPOINTMENT_SCHEDULE_PATH = '/Appointment/AppointmentSchedule'

visa_uri_paths = dict(
    login=LOGIN_PATH,
    application=USER_APPLICATIONS_PATH,
    appointment_location=APPOINTMENT_LOCATION_PATH,
    appointment_availibility=APPOINTMENT_AVAILIBILITY_PATH,
    appointment_schedule=APPOINTMENT_SCHEDULE_PATH,
    appointment_timeslots=APPOINTMENT_TIMESLOTS_PATH
)

post_visa_type_ids = dict(
    tehran=1330,
    uae_abudhabi=984
)

enrolment_station_ids = dict(
    tehran='bf977c96-66d9-e511-bb32-0050569253ba',
    uae_abudhabi='587e0007-67d9-e511-95ad-005056922509'
)

VISA_CENTRE = 'tehran'

APPOINTMENT_LOCATION_FIXED_FIELDS = dict()

s = requests.Session()
s.headers.update(
    {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML,' +
     ' like Gecko) Chrome/52.0.2743.116 Safari/537.36'})


def get_login_form_data(login_page_content):
    d = pq(login_page_content)
    form_el = d('#frmLogin')
    form_data = dict(
        Email=USER_EMAIL,
        Password=USER_PASSWORD
    )
    for input_el in form_el.find('input'):
        field_name = d(input_el).attr('name')
        if not field_name in ['Email', 'Password'] and field_name != None:
            form_data[field_name] = d(input_el).val()

    return form_data


def get_book_appointment_page_url():
    user_applications_page = WebPage(
        url="%s%s" % (UKVISA_BASE_URL, USER_APPLICATIONS_PATH),
        handler=s
    )

    d = pq(user_applications_page.content())
    return "%s%s" % (UKVISA_BASE_URL, d('a').attr('href').replace('..', ''))


def get_appointment_loc_form_data(book_appointment_page_content):
    d = pq(book_appointment_page_content)
    form_el = d('form[action*="/Appointment"]')

    form_data = {d(el).attr('name'): d(el).val() for el in form_el(
        'input, select') if not d(el).attr('name') in APPOINTMENT_LOCATION_FIXED_FIELDS.keys()}

    form_data.update(APPOINTMENT_LOCATION_FIXED_FIELDS)
    return form_data


def get_appointment_schedule_form_data(appointment_loc_page_content):
    d = pq(appointment_loc_page_content)
    schedule_appointment_form_el = d('#frmAppointmentSchedule')
    form_data = {d(el).attr('name'): d(el).val() for el in schedule_appointment_form_el(
        'input, select') if d(el).attr('name') != ''}
    return form_data


def create_login_form(form_data):
    return WebForm(
        action_url="%s%s" % (UKVISA_BASE_URL, LOGIN_PATH),
        form_data=form_data,
        handler=s
    )


def get_available_dates():
    res = s.get(
        url='%s%s' % (
            UKVISA_BASE_URL, visa_uri_paths.get('appointment_availibility')),
        params='id=%s&count=%s&selectedPostVisaTypeId=%s' % (enrolment_station_ids[VISA_CENTRE], '%0A++++-1%0A++',
            post_visa_type_ids[VISA_CENTRE])
    )

    return sorted(set((json.loads(res.text))))

def submit_schedule_appointment_form(form_data):
  schedule_appointment_form = WebForm(
    action_url="%s%s" % (UKVISA_BASE_URL, visa_uri_paths['appointment_schedule']),
    form_data=form_data,
    handler=s
  )

  return schedule_appointment_form.submit().response()

def str_to_datetime(date_string):
  return datetime.datetime.strptime(date_string, "%d-%m-%Y")

def get_available_time_slots(post_id, appointment_date):
  re_pattern = r"value=(\d{8}\|\d{0,2}\:\d{0,2})>"
  res = s.get(
      url='%s%s' % (
          UKVISA_BASE_URL, visa_uri_paths.get('appointment_timeslots')),
      params='id=%s&count=%s&postId=%s&selectedPostVisaTypeId=%s' % (urllib.quote(appointment_date.encode("utf-8")),
          '%0A++++-1%0A++', post_id, post_visa_type_ids[VISA_CENTRE])
  )

  decoded_res = res.text.decode("unicode-escape")
  matches = re.finditer(re_pattern, decoded_res)
  results = [match.group(1) for match in matches]
  return results

def create_message(appointment_data):
  message = ''
  for date, times in appointment_data.items():
    message += '\nDate: ' + date
    message += '\n================\n'
    for time in times:
      message += 'Time slot: ' + time.split('|')[1] + '\n'

  message += '\nEarliest available date: ' + appointment_data.keys()[0];
  return message;

def start_check():
    try:
        # 1. Open login page
        login_page = WebPage(
            url="%s%s" % (UKVISA_BASE_URL, LOGIN_PATH),
            handler=s
        )

        login_form_data = get_login_form_data(login_page.content())

        # 2. Post login form and login :)
        login_form = create_login_form(login_form_data)
        res = login_form.submit().response()

        # 3. Open book appointment page
        book_appointment_page = WebPage(
            url=get_book_appointment_page_url(),
            handler=s
        )

        get_appointment_location_form = WebForm(
            action_url="%s%s" % (UKVISA_BASE_URL, APPOINTMENT_LOCATION_PATH),
            form_data=get_appointment_loc_form_data(
                book_appointment_page.content()),
            handler=s
        )

        res = get_appointment_location_form.submit().response()

        schedule_appointment_form_data = get_appointment_schedule_form_data(
            res.text)

        post_id = schedule_appointment_form_data['EnrolmentStationId']

        available_dates = get_available_dates()
        
        print("\n" + datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
        if len(available_dates) > 0:
          appointment_data = {date: get_available_time_slots(
            post_id = post_id,
            appointment_date = date
          ) for date in available_dates[:7]}
          print('Available dates found, generating message to be emailed')
          send_email(create_message(appointment_data))
        else:
          print('No available dates for %s...' % (VISA_CENTRE))

        #TODO: Need to figure out the captcha after submitting the form
        # submit_schedule_appointment_form(schedule_appointment_form_data);

    except Exception as e:
        print('Error checking visa appointment', e)

def main():
    global USER_EMAIL
    global USER_PASSWORD
    global VISA_CENTRE
    global APPOINTMENT_LOCATION_FIXED_FIELDS 
    
    USER_EMAIL = os.environ['USER_NAME'] if 'USER_NAME' in os.environ else None
    USER_PASSWORD = os.environ['PASSWORD'] if 'PASSWORD' in os.environ else None 
    VISA_CENTRE = os.environ['VISA_CENTRE'] if 'VISA_CENTRE' in os.environ else VISA_CENTRE 
    
    APPOINTMENT_LOCATION_FIXED_FIELDS = dict(
      VisaAppointmentTypeId=post_visa_type_ids[VISA_CENTRE],
      EnrolmentStationId=enrolment_station_ids[VISA_CENTRE],
      PostRegionId='8bf48b88-66d9-e511-bf7d-005056921cc8'
    )
 
    if not (USER_EMAIL or USER_PASSWORD):
      raise Exception('Can not check visa appointment without visa application credentials')
    
    start_check()
 

if __name__ == '__main__':
    try:
      main()
    except Exception as e:
     print('Error: ' + e.message)

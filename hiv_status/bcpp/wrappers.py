import pytz
from datetime import datetime
from django.conf import settings

from edc_constants.constants import POS, YES

from hiv_status.status import ResultWrapper

tz = pytz.timezone(settings.TIME_ZONE)


"""
from hiv_status import Status
from hiv_status.bcpp.wrappers import Current, Documented, Indirect, Verbal
from apps.bcpp_subject.models import (
    HivResult, HivTestReview, HivTestingHistory, HivResultDocumentation,
    SubjectConsent, SubjectReferral, SubjectVisit)

for subject_referral in SubjectReferral.objects.filter(
        subject_visit__household_member__household_structure__survey__survey_slug='bcpp-year-1'
        ).order_by('subject_identifier'):
    visit = subject_referral.subject_visit
    options={'subject_visit': visit}
    try:
        current = Current(HivResult, options)
    except HivResult.DoesNotExist:
        current = None
    try:
        documented = Documented(HivTestReview, options)
    except HivTestReview.DoesNotExist:
        documented = None
    try:
        indirect = Indirect(HivResultDocumentation, options)
    except HivTestingHistory.DoesNotExist:
        indirect = None
    try:
        verbal = Verbal(HivTestingHistory, options)
    except HivTestingHistory.DoesNotExist:
        verbal = None

    status = Status(
        visit.appointment.registered_subject,
        current=current,
        documented=documented,
        indirect=indirect,
        verbal=verbal,
        visit_code=visit.appointment.visit_definition.code)
    if str(status) != subject_referral.hiv_result:
        print('{} ** {}!={}.'.format(status.subject.subject_identifier, str(status), subject_referral.hiv_result))
    else:
        print(status.subject.subject_identifier)

"""


class Current:
    """Wrapper for model bhp066.bcpp_subject.HivResult."""

    def __init__(self, model_cls, visit):
        instance = model_cls.objects.get(subject_visit=visit)
        try:
            self.result_value = instance.hiv_result
            self.result_datetime = tz.localize(instance.hiv_result_datetime)
            self.visit = instance.subject_visit
        except AttributeError:
            self.result_value = None
            self.result_datetime = None
            self.visit = None


class Documented:
    """Wrapper for model bhp066.bcpp_subject.HivTestReview."""

    def __init__(self, model_cls, visit, current_model_cls=None):
        try:
            instance = current_model_cls.objects.filter(hiv_result=POS).exclude(
                subject_visit__report_datetime__lte=visit.report_datetime).earliest()
        except current_model_cls.DoesNotExist:
            instance = model_cls.objects.get(subject_visit=visit)
        try:
            self.result_value = instance.recorded_hiv_result
            self.result_datetime = tz.localize(
                datetime(instance.hiv_test_date.year, instance.hiv_test_date.month, instance.hiv_test_date.day))
            self.visit = instance.subject_visit
        except AttributeError:
            self.result_value = None
            self.result_datetime = None
            self.visit = None


class Indirect:
    """Wrapper for model bhp066.bcpp_subject.HivTestingHistory."""
    def __init__(self, model_cls, options):
        instance = model_cls.objects.get(**options)
        self.result_value = instance.result_recorded
        try:
            self.result_datetime = tz.localize(
                datetime(instance.result_date.year, instance.result_date.month, instance.result_date.day))
            self.visit = instance.subject_visit
        except AttributeError:
            self.result_datetime = None
            self.visit = None


class Verbal:
    """Wrapper for model bhp066.bcpp_subject.HivTestingHistory."""
    def __init__(self, model_cls, options):
        instance = model_cls.objects.get(**options)
        if instance.has_tested == YES:
            self.result_value = instance.verbal_hiv_result
        else:
            self.result_value = None
        try:
            self.result_datetime = tz.localize(instance.hiv_test_date)
            self.visit = instance.subject_visit
        except AttributeError:
            self.result_datetime = None
            self.visit = None

from django.test import TestCase
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from edc_constants.constants import POS, NEG, UNK

from hiv_status.status import Status
from hiv_status.models import HivResult, Subject, Visit


class TestStatus(TestCase):

    def setUp(self):
        self.subject = Subject.objects.create(subject_identifier='123456789')

    def create_visits(self, count, visit_code=None, base_datetime=None):
        visit_code = visit_code or '1000'
        base_datetime = base_datetime or timezone.now()
        for m in range(0, count):
            Visit.objects.create(
                subject=self.subject,
                visit_code=visit_code,
                encounter=m,
                visit_datetime=base_datetime + relativedelta(months=m)
            )

    def test_returns_status(self):
        status = Status(subject=self.subject, current=HivResult)
        self.assertIn(status.result.result_value, [POS, NEG, UNK, None])

    def test_prefers_pos_result(self):
        """Returns the most recent result -- which is POS."""
        self.create_visits(3)
        for visit in Visit.objects.order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.all().latest()
        # set most recent to POS
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, current=HivResult)
        self.assertEqual(status, POS)

    def test_prefers_pos_result2(self):
        """Returns the second most recent result -- which is POS."""
        self.create_visits(3)
        for visit in Visit.objects.all().order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.all().order_by('result_datetime')[1]
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, current=HivResult)
        self.assertEqual(status, POS)

    def test_first_pos_result(self):
        """Returns the second most recent result -- which is POS."""
        self.create_visits(6)
        for visit in Visit.objects.all().order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.all().order_by('result_datetime')[5]
        hiv_result.result_value = POS
        hiv_result.save()
        hiv_result = HivResult.objects.all().order_by('result_datetime')[1]
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, current=HivResult)
        self.assertEqual(status, POS)
        self.assertEqual(status.result.visit, hiv_result.visit)

    def test_status_as_of_visit_code(self):
        self.create_visits(3, visit_code='1000', base_datetime=timezone.now() - relativedelta(years=2))
        self.create_visits(3, visit_code='2000', base_datetime=timezone.now() - relativedelta(years=1))
        for visit in Visit.objects.all().order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        status = Status(subject=self.subject, current=HivResult, visit_code='2000', result_list=[POS, NEG])
        self.assertEqual(status, None)
        status = Status(subject=self.subject, current=HivResult, visit_code='2000', result_list=[NEG])
        self.assertEqual(status, NEG)
        hiv_result = HivResult.objects.filter(visit__visit_code='2000').order_by('result_datetime')[1]
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, current=HivResult, visit_code='1000', result_list=[POS, NEG])
        self.assertEqual(status, None)
        status = Status(subject=self.subject, current=HivResult, visit_code='1000', result_list=[NEG])
        self.assertEqual(status, NEG)
        status = Status(subject=self.subject, current=HivResult, visit_code='2000', result_list=[POS, NEG])
        self.assertEqual(status, POS)
        self.assertEqual(status.result.visit, hiv_result.visit)

    def test_result_as_of_visit_code_and_encounter(self):
        self.create_visits(3, visit_code='1000', base_datetime=timezone.now() - relativedelta(years=2))
        self.create_visits(3, visit_code='2000', base_datetime=timezone.now() - relativedelta(years=1))
        for visit in Visit.objects.all().order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.get(visit__visit_code='2000', visit__encounter=1)
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, current=HivResult, visit_code='2000', encounter=1)
        self.assertEqual(status, POS)
        self.assertEqual(status.result.visit, hiv_result.visit)

    def test_result_as_of_visit_code_and_encounter2(self):
        self.create_visits(3, visit_code='1000', base_datetime=timezone.now() - relativedelta(years=2))
        self.create_visits(3, visit_code='2000', base_datetime=timezone.now() - relativedelta(years=1))
        for visit in Visit.objects.all().order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.get(visit__visit_code='1000', visit__encounter=1)
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, current=HivResult, visit_code='2000', encounter=1)
        self.assertEqual(status, None)

    def test_result_no_result(self):
        self.create_visits(3, visit_code='1000', base_datetime=timezone.now() - relativedelta(years=2))
        status = Status(subject=self.subject, current=HivResult)
        self.assertIsNone(status.result.result_value)

    def test_result_wrapper(self):
        status = Status(subject=self.subject, current=None)
        self.assertIsNone(status.current.result_value)
        self.assertIsNone(status.documented.result_value)
        self.assertIsNone(status.indirect.result_value)
        self.assertIsNone(status.verbal.result_value)

    def test_current_neg_documented_pos(self):
        status = Status(subject=self.subject, current=NEG, documented=POS)
        self.assertEqual(status, NEG)

    def test_current_none_documented_pos(self):
        status = Status(subject=self.subject, current=None, documented=NEG)
        self.assertEqual(status, None)

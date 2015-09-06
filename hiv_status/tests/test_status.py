from datetime import datetime
from django.test import TestCase
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from edc_constants.constants import POS, NEG, UNK

from hiv_status.status import Status
from hiv_status.models import HivResult, Subject, Visit, HivStatusReview


class TestSimple(TestCase):
    """Test status does not change base class if results are passed as strings."""

    def setUp(self):
        self.subject = Subject.objects.create(subject_identifier='123456789')

    def test_returns_status(self):
        """Asserts excepts string instead of model."""
        status = Status(subject=self.subject, tested=HivResult)
        self.assertIn(status.result, [POS, NEG, UNK, None])
        self.assertIn(str(status.result), [POS, NEG, UNK, ''])
        self.assertFalse(status.newly_positive)
        self.assertFalse(status.subject_aware)

    def test_returns_all(self):
        """Asserts excepts string instead of model."""
        status = Status(subject=self.subject, tested=POS, documented=NEG, indirect=NEG, verbal=POS)
        self.assertEqual(status.tested, POS)
        self.assertEqual(status.previous, '')
        self.assertEqual(status.documented, NEG)
        self.assertEqual(status.indirect, NEG)
        self.assertEqual(status.verbal, POS)
        self.assertEqual(status.result, POS)
        self.assertTrue(status.newly_positive)
        self.assertFalse(status.subject_aware)

    def test_returns_status1(self):
        """Asserts excepts string instead of model."""
        status = Status(subject=self.subject, tested=POS)
        self.assertEqual(status.result, POS)
        self.assertTrue(status.newly_positive)
        self.assertFalse(status.subject_aware)

    def test_returns_status2(self):
        """Asserts excepts string instead of model."""
        status = Status(subject=self.subject, tested=POS, documented=NEG)
        self.assertEqual(status.result, POS)
        self.assertEqual(str(status.documented), NEG)
        self.assertTrue(status.newly_positive)
        self.assertFalse(status.subject_aware)

    def test_returns_status3(self):
        """Asserts excepts string instead of model."""
        status = Status(subject=self.subject, indirect=POS)
        self.assertEqual(status.result, POS)
        self.assertFalse(status.newly_positive)
        self.assertTrue(status.subject_aware)

    def test_returns_status4(self):
        """Asserts excepts string instead of model."""
        status = Status(subject=self.subject, indirect=NEG)
        self.assertEqual(status.result, '')
        self.assertEqual(status.result, None)
        self.assertIsNotNone(status.result)
        self.assertFalse(status.newly_positive)
        self.assertFalse(status.subject_aware)


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
                visit_datetime=base_datetime - relativedelta(months=m)
            )

    def test_previous(self):
        self.create_visits(3)
        for visit in Visit.objects.order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.all().latest()
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, tested=HivResult)
        self.assertEqual(status.previous, NEG)
        self.assertEqual(status.documented, NEG)

    def test_previous2(self):
        self.create_visits(3)
        for visit in Visit.objects.order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.all().latest()
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, tested=HivResult, documented=POS)
        self.assertEqual(status.previous, NEG)
        self.assertEqual(status.documented, POS)

    def test_previous3(self):
        self.create_visits(3)
        for visit in Visit.objects.order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.all().latest()
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, tested=HivResult, documented=HivStatusReview)
        self.assertEqual(status.previous, NEG)
        self.assertEqual(status.documented, NEG)

    def test_previous4(self):
        self.create_visits(3)
        for visit in Visit.objects.order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.all().latest()
        hiv_result.result_value = POS
        hiv_result.save()
        visit = Visit.objects.all().order_by('visit_datetime')[1]
        d = visit.visit_datetime
        HivStatusReview.objects.create(
            visit=visit,
            documented_result=POS,
            documented_result_date=datetime(d.year, d.month, d.day)
        )
        status = Status(subject=self.subject, tested=HivResult, documented=HivStatusReview)
        self.assertEqual(status.previous, NEG)
        self.assertEqual(status.documented, POS)

    def test_prefers_pos_result(self):
        """Returns the most recent result -- which is POS."""
        self.create_visits(3)
        for visit in Visit.objects.order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.all().latest()
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, tested=HivResult)
        self.assertEqual(status, POS)
        self.assertTrue(status.newly_positive)
        self.assertFalse(status.subject_aware)

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
        status = Status(subject=self.subject, tested=HivResult)
        self.assertEqual(status, POS)
        self.assertTrue(status.newly_positive)  # relative to this result
        self.assertFalse(status.subject_aware)

    def test_first_pos_result(self):
        """Returns the second most recent result -- which is POS."""
        self.create_visits(6)
        for visit in Visit.objects.all().order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.all().order_by('result_datetime')[1]
        hiv_result.result_value = POS
        hiv_result.save()
        hiv_result = HivResult.objects.all().order_by('result_datetime')[5]
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, tested=HivResult)
        self.assertEqual(status, POS)
        self.assertEqual(status.result.visit, hiv_result.visit)
        self.assertEqual(status.previous, POS)
        self.assertFalse(status.newly_positive)
        self.assertTrue(status.subject_aware)

    def test_status_as_of_visit_code(self):
        self.create_visits(3, visit_code='1000', base_datetime=timezone.now() - relativedelta(years=2))
        self.create_visits(3, visit_code='2000', base_datetime=timezone.now() - relativedelta(years=1))
        for visit in Visit.objects.all().order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        status = Status(subject=self.subject, tested=HivResult, visit_code='2000', result_list=[POS, NEG])
        self.assertEqual(status, None)
        status = Status(subject=self.subject, tested=HivResult, visit_code='2000', result_list=[NEG])
        self.assertEqual(status, NEG)
        hiv_result = HivResult.objects.filter(visit__visit_code='2000').order_by('result_datetime')[1]
        hiv_result.result_value = POS
        hiv_result.save()
        status = Status(subject=self.subject, tested=HivResult, visit_code='1000', result_list=[POS, NEG])
        self.assertEqual(status, None)
        status = Status(subject=self.subject, tested=HivResult, visit_code='1000', result_list=[NEG])
        self.assertEqual(status, NEG)
        status = Status(subject=self.subject, tested=HivResult, visit_code='2000', result_list=[POS, NEG])
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
        status = Status(subject=self.subject, tested=HivResult, visit_code='2000', encounter=1)
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
        status = Status(subject=self.subject, tested=HivResult, visit_code='2000', encounter=1)
        self.assertEqual(status, None)

    def test_result_no_result(self):
        self.create_visits(3, visit_code='1000', base_datetime=timezone.now() - relativedelta(years=2))
        status = Status(subject=self.subject, tested=HivResult)
        self.assertEquals(status.result.result_value, '')
        self.assertEquals(status.result, None)
        self.assertFalse(status.newly_positive)
        self.assertFalse(status.subject_aware)

    def test_result_wrapper(self):
        status = Status(subject=self.subject, tested=None)
        self.assertEqual(status.tested.result_value, '')
        self.assertEqual(status.documented.result_value, '')
        self.assertEqual(status.indirect.result_value, '')
        self.assertEqual(status.verbal.result_value, '')

    def test_tested_neg_documented_pos(self):
        status = Status(subject=self.subject, tested=NEG, documented=POS)
        self.assertEqual(status, NEG)
        self.assertFalse(status.newly_positive)
        self.assertFalse(status.subject_aware)

    def test_tested_none_documented_pos(self):
        status = Status(subject=self.subject, tested=None, documented=NEG)
        self.assertEqual(status, None)
        self.assertFalse(status.newly_positive)
        self.assertFalse(status.subject_aware)

    def test_indirect_none(self):
        status = Status(subject=self.subject, indirect=None)
        self.assertEqual(status, None)
        self.assertFalse(status.newly_positive)
        self.assertFalse(status.subject_aware)

    def test_indirect_pos(self):
        status = Status(subject=self.subject, indirect=POS)
        self.assertEqual(status, POS)
        self.assertFalse(status.newly_positive)
        self.assertTrue(status.subject_aware)

    def test_indirect_neg(self):
        status = Status(subject=self.subject, indirect=NEG)
        self.assertEqual(status, None)

    def test_subject_aware(self):
        status = Status(subject=self.subject, tested=POS)
        self.assertFalse(status.subject_aware)
        status = Status(subject=self.subject, documented=POS)
        self.assertTrue(status.subject_aware)
        status = Status(subject=self.subject, tested=POS, documented=NEG)
        self.assertFalse(status.subject_aware)
        status = Status(subject=self.subject, tested=NEG, documented=NEG)
        self.assertTrue(status.subject_aware)
        status = Status(subject=self.subject, documented=NEG)
        self.assertFalse(status.subject_aware)
        status = Status(subject=self.subject, tested=POS, indirect=POS)
        self.assertTrue(status.subject_aware)

    def test_newly_positive(self):
        status = Status(subject=self.subject, tested=POS)
        self.assertTrue(status.newly_positive)
        status = Status(subject=self.subject, documented=POS)
        self.assertFalse(status.newly_positive)
        status = Status(subject=self.subject, tested=POS, documented=NEG)
        self.assertTrue(status.newly_positive)

#     def test_longitudinal(self):
#         self.create_visits(3)
#         visit = Visit.objects.all()[0]
#         status = LongitudinalStatus(subject=self.subject, visit=visit, tested=HivResult, documented=HivStatusReview)

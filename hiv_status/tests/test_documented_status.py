from datetime import date
from edc_constants.constants import POS, NEG

from hiv_status.models import HivResult, Visit
from hiv_status.result_wrapper import ResultWrapper
from hiv_status.status import Status

from .test_status import TestStatus


class TestDocumentedStatus(TestStatus):

    def test_returns_result(self):
        status = Status(self.subject, HivResult)
        self.assertEqual(status.result.result_value, '')

    def test_returns_pos_or_none(self):
        status = Status(self.subject, documented=NEG)
        self.assertEqual(status.result.result_value, '')
        status = Status(self.subject, indirect=NEG)
        self.assertEqual(status.result.result_value, '')
        status = Status(self.subject, verbal=NEG)
        self.assertEqual(status.result.result_value, '')

    def test_returns_pos_or_none2(self):
        status = Status(self.subject, documented=POS)
        self.assertEqual(status, POS)
        status = Status(self.subject, indirect=POS)
        self.assertEqual(status, POS)
        status = Status(self.subject, verbal=POS)
        self.assertEqual(status.result.result_value, '')
        status = Status(self.subject, verbal=POS, include_verbal=True)
        self.assertEqual(status, POS)

    def test_returns_result_if_documented(self):
        status = Status(self.subject, documented=NEG)
        self.assertEqual(status.result.result_value, '')
        status = Status(self.subject, documented=POS)
        self.assertEqual(status, POS)

    def test_returns_result_ignores_verbal(self):
        status = Status(self.subject, documented=NEG, verbal=POS)
        self.assertEqual(status.result.result_value, '')
        status = Status(self.subject, documented=POS, verbal=NEG)
        self.assertEqual(status, POS)

    def test_returns_result_ignores_verbal_if_direct(self):
        status = Status(
            self.subject, documented=NEG, verbal=POS, include_verbal=True)
        self.assertEqual(status.result.result_value, '')
        status = Status(
            self.subject, documented=POS, verbal=NEG, include_verbal=True)
        self.assertEqual(status, POS)

    def test_date_positive(self):
        self.create_visits(3)
        for visit in Visit.objects.order_by('visit_datetime'):
            HivResult.objects.create(
                visit=visit,
                result_value=NEG,
                result_datetime=visit.visit_datetime)
        hiv_result = HivResult.objects.all().latest()
        hiv_result.result = POS
        hiv_result.save()
        status = Status(
            self.subject, documented=ResultWrapper(POS))
        self.assertEqual(status, POS)
        self.assertEqual(status.result.name, 'documented')
        self.assertEqual(status.result.result_datetime.date(), date.today())

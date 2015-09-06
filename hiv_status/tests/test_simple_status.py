import unittest

from edc_constants.constants import POS, NEG, UNK

from hiv_status.status import SimpleStatus, ResultWrapper


class TestWrapper(unittest.TestCase):

    def test_wrapper(self):
        a = ResultWrapper('POS')
        b = ResultWrapper('POS')
        self.assertEqual(a, b)
        self.assertFalse(a is b)

    def test_wrapper2(self):
        a = ResultWrapper('POS')
        b = ResultWrapper('NEG')
        self.assertNotEqual(a, b)

    def test_wrapper3(self):
        a = ResultWrapper(None)
        b = ResultWrapper(None)
        self.assertEqual(a, b)

    def test_wrapper4(self):
        a = ResultWrapper(None)
        self.assertEqual(a, '')

    def test_wrapper_name(self):
        a = ResultWrapper(None, name='tested')
        self.assertEqual(a.name, 'tested')


class TestSimpleStatus(unittest.TestCase):

    def test_returns_simple_status(self):
        status = SimpleStatus(tested=NEG)
        self.assertIn(status.result, [POS, NEG, UNK, None])

    def test_returns_simple_status_pos(self):
        status = SimpleStatus(tested=POS)
        self.assertEqual(status, POS)

    def test_returns_simple_status2(self):
        """Asserts tested result always overrides previous info."""
        status = SimpleStatus(tested=POS, documented=NEG)
        self.assertEqual(status, POS)

    def test_returns_simple_status3(self):
        status = SimpleStatus(tested=None, documented=POS)
        self.assertEqual(status, POS)

    def test_returns_simple_status4(self):
        status = SimpleStatus(tested=None, documented=None, indirect=POS)
        self.assertEqual(status, POS)

    def test_returns_simple_status5(self):
        status = SimpleStatus(tested=None, documented=None, indirect=None, verbal=POS)
        self.assertEqual(status, None)
        self.assertIsNone(status.result)

    def test_returns_simple_status6(self):
        """Asserts tested result always overrides previous info."""
        status = SimpleStatus(tested=NEG, documented=POS, indirect=None, verbal=POS)
        self.assertEqual(status, NEG)

    def test_returns_simple_status7(self):
        """Asserts tested result always overrides previous info."""
        status = SimpleStatus(tested=NEG, documented=POS, indirect=POS, verbal=POS)
        self.assertEqual(status, NEG)

    def test_returns_simple_status8(self):
        """Asserts tested result always overrides previous info."""
        status = SimpleStatus(tested=POS, documented=NEG, indirect=None, verbal=None)
        self.assertEqual(status, POS)

    def test_returns_simple_status9(self):
        """Asserts NEG status must be confirmed with a currrent result."""
        status = SimpleStatus(tested=None, documented=None, indirect=NEG)
        self.assertEqual(status, None)
        self.assertIsNone(status.result)

    def test_returns_simple_status10(self):
        """Asserts NEG status must be confirmed with a currrent result."""
        status = SimpleStatus(tested=None, documented=NEG, indirect=None)
        self.assertEqual(status, None)
        self.assertIsNone(status.result)

    def test_accepts_wrapped_result1(self):
        tested = ResultWrapper(POS)
        documented = ResultWrapper(NEG)
        status = SimpleStatus(tested=tested, documented=documented, indirect=None, verbal=None)
        self.assertEqual(status, POS)
        self.assertEqual(status.result, POS)
        self.assertEqual(status.result.result_value, POS)

    def test_accepts_wrapped_result2(self):
        tested = ResultWrapper(None)
        documented = ResultWrapper(POS)
        self.assertEqual(str(tested), '')
        self.assertEqual(str(documented), POS)
        status = SimpleStatus(tested=tested, documented=documented, indirect=None, verbal=None)
        self.assertEqual(status, POS)

if __name__ == '__main__':
    unittest.main()

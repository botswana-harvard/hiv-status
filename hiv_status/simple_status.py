from edc_constants.constants import POS


class SimpleStatus:

    """
    Returns the earliest HIV POS result or the tested result.

    tested result: result from a test run now/today
    documented result: a documented result other than today's result
    indirect result: documented evidence of HIV POS status, e.g prescription, medical record
    """

    def __init__(self, tested=None, documented=None, indirect=None, verbal=None, include_verbal=None,
                 result_list=None):
        self.simple_result = None
        if str(tested or ''):
            self.simple_result = tested
        else:
            if str(documented or '') == POS:
                self.simple_result = documented
            elif str(indirect or '') == POS:
                self.simple_result = indirect
            elif str(verbal or '') == POS and include_verbal:
                if (str(documented or '') or str(indirect or '')):
                    self.simple_result = None
                else:
                    self.simple_result = verbal
            else:
                self.simple_result = None

    @property
    def result(self):
        return self.simple_result

    def __repr__(self):
        return '{}(\'{}\')'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if self.simple_result:
            return str(self.simple_result)
        else:
            return ''

    def __eq__(self, other):
        if not other:
            other = ''
        return str(self) == str(other)

    def __ne__(self, other):
        if not other:
            other = ''
        return str(self) != str(other)

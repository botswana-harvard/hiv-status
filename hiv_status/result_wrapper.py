from datetime import date

class ResultWrapper:
    """
    >>> a = ResultWrapper('POS')
    >>> a
    ResultWrapper('POS')
    >>> b = ResultWrapper('POS')
    >>> b
    ResultWrapper('POS')
    >>> a == b
    True
    >>> a is b
    False
    """
    def __init__(self, result_value, result_datetime=None, visit_code=None, encounter=None,
                 visit=None, name=None, instance=None):
        self.result_value = result_value or ''
        self.result_datetime = result_datetime
        if result_datetime:
            self.result_date = date(result_datetime.year, result_datetime.month, result_datetime.day)
        else:
            self.result_date = None
        self.visit_code = visit_code
        self.encounter = encounter
        self.visit = visit
        self.name = name
        self.instance = instance

    def __repr__(self):
        return '{}(\'{}\')'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if self.result_value:
            return str(self.result_value)
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

from collections import namedtuple

from edc_constants.constants import POS
from django.core.exceptions import ObjectDoesNotExist

ResultWrapper = namedtuple('ResultWrapper', 'result_value result_datetime, visit_code encounter visit')
SubjectWrapper = namedtuple('SubjectWrapper', 'id, subject_identifier')


class Status:

    """
    Returns the earliest HIV POS result.

    current result: result from a test run now
    documented result: a documented result other than today's result
    indirect result: documented evidence of HIV POS status, e.g prescription, medical record
    """

    def __init__(self, subject, current=None, visit_code=None, encounter=None, result_list=None,
                 documented=None, indirect=None,
                 verbal=None, include_verbal=None, result_wrapper=None, subject_wrapper=None):
        self.new_pos = False
        self.result_wrapper = result_wrapper or self._result_wrapper
        self.subject_wrapper = subject_wrapper or self._subject_wrapper
        self.subject = self.subject_wrapper(subject)
        if result_list is None:
            self.result_list = [POS]
        else:
            self.result_list = [POS] if POS in result_list else result_list
        self.current = self.result_wrapper(current, visit_code, encounter)
        self.documented = self.result_wrapper(documented, visit_code, encounter)
        self.indirect = self.result_wrapper(indirect, visit_code, encounter)
        self.verbal = self.result_wrapper(verbal, visit_code, encounter)
        self.include_verbal = include_verbal
        if self.current.result_value:
            self.result = self.current
        else:
            if self.documented.result_value == POS:
                self.result = self.documented
            elif self.indirect.result_value == POS:
                self.result = self.indirect
            elif self.verbal.result_value == POS and self.include_verbal:
                if (self.documented.result_value or self.indirect.result_value):
                    self.result = self.str_result_wrapper(None)
                else:
                    self.result = self.verbal
            else:
                self.result = self.str_result_wrapper(None)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.subject.subject_identifier)

    def __str__(self):
        return str(self.result.result_value)

    def __eq__(self, other):
        try:
            return self.result.result_value == other
        except AttributeError:
            return None is other

    def __ne__(self, other):
        return self.result.result_value != other

    def _result_wrapper(self, result, visit_code, encounter):
        """Wraps a result which might be a model, instance, string or some custom class."""
        try:
            return ResultWrapper(
                result.result_value, result.result_datetime, visit_code, encounter, result.visit)
        except AttributeError:
            try:
                result = result.objects.filter(
                    visit__subject__id=self.subject.id, result_value__in=self.result_list,
                    **self.visit_options(visit_code, encounter)).earliest()
                return ResultWrapper(
                    result.result_value, result.result_datetime, visit_code, encounter, result.visit)
            except ObjectDoesNotExist:
                return self.str_result_wrapper(None)
            except AttributeError as e:
                if 'object has no attribute \'objects\'' in str(e):
                    return self.str_result_wrapper(result)
                else:
                    raise AttributeError(e)
        return None

    @classmethod
    def str_result_wrapper(cls, result):
        """Wraps a string result."""
        return ResultWrapper(result, None, None, None, None)

    def _subject_wrapper(self, subject):
        return SubjectWrapper(subject.id, subject.subject_identifier)

    def visit_options(self, visit_code, encounter):
        visit_options = {}
        if visit_code and encounter:
            visit_options.update(visit__visit_code=visit_code, visit__encounter=encounter)
        elif visit_code:
            visit_options.update(visit__visit_code=visit_code)
        else:
            pass
        return visit_options

import pytz
from collections import namedtuple
from datetime import date, datetime
from django.conf import settings
from django.utils import timezone
from edc_constants.constants import POS, NEG

from .result_wrapper import ResultWrapper
from .simple_status import SimpleStatus
from django.core.exceptions import ObjectDoesNotExist

tz = pytz.timezone(settings.TIME_ZONE)

SubjectWrapper = namedtuple('SubjectWrapper', 'id, subject_identifier')


class Status:

    SUBJECT_LOOKUP = 0
    RESULT_LOOKUP = 1
    VISIT_CODE_LOOKUP = 2
    ENCOUNTER_LOOKUP = 3

    RESULT_VALUE_ATTR = 0
    RESULT_DATETIME_ATTR = 1
    VISIT_ATTR = 2

    lookup_options = {
        'default': ['visit__subject__id', 'result_value__in', 'visit__visit_code', 'visit__encounter'],
        'tested': [],
        'documented': ['visit__subject__id', 'documented_result__in', 'visit__visit_code', 'visit__encounter'],
        'indirect': [],
        'verbal': []
    }

    field_attr = {
        'default': ['result_value', 'result_datetime', 'visit'],
        'tested': [],
        'documented': ['documented_result', 'documented_result_date', 'visit'],
        'indirect': [],
        'verbal': []
    }

    def __init__(self, subject, tested=None, documented=None, indirect=None, verbal=None,
                 visit_code=None, encounter=None, visit=None, visit_model=None, result_list=None,
                 reference_date=None, include_verbal=None):
        self.subject = subject
        self.visit_code = visit_code
        self.encounter = encounter
        self.visit = visit
        self.reference_datetime = self.zero_time(reference_date)
        if result_list is None:
            self.result_list = [POS]
        else:
            self.result_list = [POS] if POS in result_list else result_list
        self.tested = self.lookup_latest(tested, name='tested')
        self.previous = self.lookup_previous(tested, name='previous')
        self.documented = self.lookup_latest(documented, name='documented')
        if self.documented.result_value and self.previous.result_value:
            if self.previous.result_date > self.documented.result_date:
                self.documented = SimpleStatus(tested=self.previous, documented=self.documented).result
            else:
                self.documented = SimpleStatus(tested=self.documented, documented=self.previous).result
        elif self.previous.result_value:
            self.documented = self.previous
        self.indirect = self.lookup_latest(indirect, name='indirect')
        self.verbal = self.lookup_latest(verbal, name='verbal')
        self.result = SimpleStatus(
            tested=self.tested, documented=self.documented,
            indirect=self.indirect, verbal=self.verbal, include_verbal=include_verbal).result
        if self.result is None:
            self.result = ResultWrapper(None)

    def __repr__(self):
        return '{}(\'{}\')'.format(self.__class__.__name__, str(self))

    def __str__(self):
        try:
            if self.result:
                return str(self.result)
        except AttributeError:
            pass
        return ''

    def __eq__(self, other):
        if not other:
            other = ''
        return str(self) == str(other)

    def __ne__(self, other):
        if not other:
            other = ''
        return str(self) != str(other)

    def lookup_latest(self, result, name):
        result_value = None
        result_datetime = None
        instance = None
        visit = None
        if result:
            try:
                try:
                    options = self.options(name)
                    options.update(self.visit_options(name))
                    instance = result.objects.filter(**options).latest()
                    result_value_attr, result_datetime_attr, visit_attr = self.attrs(name)
                    result_value = getattr(instance, result_value_attr)
                    result_datetime = getattr(instance, result_datetime_attr)
                    visit = getattr(instance, visit_attr)
                except ObjectDoesNotExist:
                    result_value = None
            except AttributeError as e:
                if ('object has no attribute \'DoesNotExist\'' in str(e) or
                        'object has no attribute \'objects\'' in str(e)):
                    result_value = result
                    result_datetime = timezone.now()
                else:
                    raise AttributeError(e)
        if result_value:
            return ResultWrapper(
                result_value, result_datetime=result_datetime, visit=visit, name=name, instance=instance)
        else:
            return ResultWrapper(None)

    def lookup_previous(self, result, name):
        """Lookup previous result relative to the reference date but return None if same as "tested"."""
        result_value = None
        result_datetime = None
        instance = None
        visit = None
        if result:
            try:
                try:
                    result_value_attr, result_datetime_attr, visit_attr = self.attrs(name)
                    try:
                        options = self.options(name, result_list=[POS])
                        options.update({'{}__lte'.format(result_datetime_attr): self.reference_datetime})
                        instance = result.objects.filter(**options).earliest()
                    except ObjectDoesNotExist:
                        options = self.options(name, result_list=[NEG])
                        options.update({'{}__lte'.format(result_datetime_attr): self.reference_datetime})
                        instance = result.objects.filter(**options).earliest()
                    if getattr(instance, result_datetime_attr).date() == self.tested.result_datetime.date():
                        result_value = None
                    else:
                        result_value = getattr(instance, result_value_attr)
                        result_datetime = getattr(instance, result_datetime_attr)
                        visit = getattr(instance, visit_attr)
                except result.DoesNotExist:
                    result_value = None
            except AttributeError:
                result_value = None
        if result_value:
            return ResultWrapper(
                result_value, result_datetime=result_datetime, visit=visit, name=name, instance=instance)
        else:
            return ResultWrapper(None)

    def visit_options(self, name):
        """Returns the filter lookup of name or the default for the visit based on the
        values available of visit, visit_code and encounter."""
        visit_options = {}
        if self.lookup_options[name]:
            lookup = self.lookup_options[name]
        else:
            lookup = self.lookup_options['default']
        if self.visit_code and self.encounter:
            visit_options.update({
                lookup[self.VISIT_CODE_LOOKUP]: self.visit_code,
                lookup[self.ENCOUNTER_LOOKUP]: self.encounter})
        elif self.visit_code:
            visit_options.update({
                lookup[self.VISIT_CODE_LOOKUP]: self.visit_code})
        elif self.visit:
            try:
                attrs = self.field_attr[name]
            except KeyError:
                attrs = self.field_attr['default']
            visit_options.update({attrs[self.VISIT_ATTR]: self.visit})
        else:
            pass
        return visit_options

    def subject_wrapper(self, subject):
        return SubjectWrapper(subject.id, subject.subject_identifier)

    @property
    def subject_aware(self):
        """Returns True is subject is considered aware of their status.

        A subject is NOT aware if a documented NEG
        is not confirmed (tested=NEG) as well if a documented POS or indirect POS
        is contradicted (tested=POS)."""

        if self.indirect.result_value == POS and self.tested.result_value == POS:
            return True
        elif self.documented.result_value == POS and self.tested.result_value == POS:
            return True
        elif self.documented.result_value == NEG and self.tested.result_value == NEG:
            return True
        elif self.documented.result_value == NEG and self.tested.result_value == POS:
            return False
        elif self.documented.result_value == POS and self.tested.result_value == NEG:
            return False
        elif self.indirect.result_value == POS and self.tested.result_value == NEG:
            return False
        elif self.documented.result_value == POS:
            return True
        elif self.indirect.result_value == POS:
            return True
        else:
            return False

    @property
    def newly_positive(self):
        """Returns True if the subject is considered newly diagnosed positive."""
        if self.tested.result_value == POS:
            if not self.documented.result_value and not self.indirect.result_value:
                return True
            elif self.documented.result_value == NEG:
                return True
        return False

    def options(self, name, result_list=None):
        """Returns model filter lookups for 'name' or the default."""
        result_list = result_list or self.result_list
        try:
            name = 'tested' if name == 'previous' else name
            options = {
                self.lookup_options[name][self.SUBJECT_LOOKUP]: self.subject.id,
                self.lookup_options[name][self.RESULT_LOOKUP]: result_list,
            }
        except IndexError:
            options = {
                self.lookup_options['default'][self.SUBJECT_LOOKUP]: self.subject.id,
                self.lookup_options['default'][self.RESULT_LOOKUP]: result_list,
            }
        return options

    def attrs(self, name):
        """Returns model attributes of 'name' or the default for attributes
        result_value, result_datetime, visit."""
        try:
            name = 'tested' if name == 'previous' else name
            result_value = self.field_attr[name][self.RESULT_VALUE_ATTR]
            result_datetime = self.field_attr[name][self.RESULT_DATETIME_ATTR]
            visit = self.field_attr[name][self.VISIT_ATTR]
        except IndexError:
            result_value = self.field_attr['default'][self.RESULT_VALUE_ATTR]
            result_datetime = self.field_attr['default'][self.RESULT_DATETIME_ATTR]
            visit = self.field_attr['default'][self.VISIT_ATTR]
        return result_value, result_datetime, visit

    def zero_time(self, d=None):
        """Returns a datetime with time(0)."""
        d = d or date.today()
        d = datetime(d.year, d.month, d.day)
        return tz.localize(d)

from hiv_status.status import Status as BaseStatus


class Status(BaseStatus):

    """
        HivResult: tested
        HivTestReview: documented
        HivResultDocumentation: Indirect
        HivResultDocumentation: Verbal
    """

    lookup_options = {
        'default': [
            'subject_visit__appointment__registered_subject__id',
            'result_value__in',
            'subject_visit__appointment__visitdefinition__visit_code',
            'subject_visit__appointment__visitdefinition__visit_instance'],
        'tested': [
            'subject_visit__appointment__registered_subject__id',
            'hiv_result__in',
            'subject_visit__appointment__visitdefinition__visit_code',
            'subject_visit__appointment__visitdefinition__visit_instance'],
        'documented': [
            'subject_visit__appointment__registered_subject__id',
            'recorded_hiv_result__in',
            'subject_visit__appointment__visitdefinition__visit_code',
            'subject_visit__appointment__visitdefinition__visit_instance'],
        'indirect': [
            'subject_visit__appointment__registered_subject__id',
            'result_recorded__in',
            'subject_visit__appointment__visitdefinition__visit_code',
            'subject_visit__appointment__visitdefinition__visit_instance'],
        'verbal': [
            'subject_visit__appointment__registered_subject__id',
            'verbal_hiv_result__in',
            'subject_visit__appointment__visitdefinition__visit_code',
            'subject_visit__appointment__visitdefinition__visit_instance'],
    }

    field_attr = {
        'default': ['result_value', 'result_datetime', 'subject_visit'],
        'tested': ['hiv_result', 'hiv_result_datetime', 'subject_visit'],
        'documented': ['recorded_hiv_result', 'hiv_test_date', 'subject_visit'],
        'indirect': ['result_recorded', 'result_date', 'subject_visit'],
        'verbal': ['verbal_hiv_result', '', 'subject_visit'],
    }

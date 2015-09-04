# hiv-status

Determine HIV(+) status based on a combination of documented, indirect and verbal information

Class `Status` expects to be working with longitudinal data or at least subject specific data.

`Status` determines the "best" result to use. The choice in order is: a current test (current), a documented test (documented), some evidence of HIV(+) status such as a prescription or medical record (indirect). Verbal information may be used if deliberately set to do so (verbal, include_verbal=True).

`Status` represents HIV(+) as a string 'POS'. See module `edc-constants`.

The parameters `current, documented, indirect, verbal` all accept a string ('POS', 'NEG' IND', 'UNK'), a model class, or some class with the attributes `result_value`, `result_datetime`, and `visit`. If you pass a string, `Status` will wrap the string result. You can write and pass your own wrappers for both the result parameters and the `subject` parameter as long as they add the same attributes as `hiv_status.ResultWrapper` and `hiv_status.SubjectWrapper`.

Usage
-----

Take a look through the tests, but here are some simple examples.

	>>> subject = Subject.objects.create(subject_identifier='12345678')
	>>> status = Status(subject)
	>>> str(status)
	'None'
	>>> status.result.value
	'None'
	>>> status.result.result_datetime
	'None'

	>>> status = Status(subject, current='POS')
	>>> str(status)
	'POS'

	>>> status = Status(subject, documented='POS')
	>>> str(status)
	'POS'

	>>> status = Status(subject, documented='NEG')
	>>> str(status)
	'None'

	>>> status = Status(subject, current='POS', documented='NEG')
	>>> str(status)
	'POS'

	>>> status = Status(subject, current='NEG', documented='POS')
	>>> str(status)
	'None'

	>>> status = Status(subject, indirect='POS')
	>>> str(status)
	'POS'

	>>> status = Status(subject, verbal='POS')
	>>> str(status)
	'None'

	>>> status = Status(subject, verbal='POS', include_verbal=True)
	>>> str(status)
	'POS'

	>>> status = Status(subject, , verbal='POS')
	>>> str(status)
	'None'
	
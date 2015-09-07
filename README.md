[![Build Status](https://travis-ci.org/botswana-harvard/hiv-status.svg)](https://travis-ci.org/botswana-harvard/hiv-status)
[![Coverage Status](https://coveralls.io/repos/botswana-harvard/hiv-status/badge.svg?branch=develop&service=github)](https://coveralls.io/github/botswana-harvard/hiv-status?branch=develop)

# hiv-status

Determine HIV(+) status based on a combination of documented, indirect and verbal information

Class `SimpleStatus` works with string results.

	>>> status = Status(subject, tested='POS', documented='POS')
	>>> str(status)
	'POS'

Class `Status` adds additional handling of model classes with results instead of string results.

    >>> from .models import HivResult, HivStatusReview, Subject
    >>> subject = Subject.objects.create(subject_identifier='12345678')
    >>> status = Status(
        subject=subject, tested=HivResult,
        documented=HivStatusReview)
    >>> status.tested
    'POS'
    >>> status.previous
    'NEG'
    >>> status.documented
    'POS'
    >>> status.newly_positive
    False
    >>> status.subject_aware
    True

You can add information about a visit to determine values relative to a timepoint. Assume you administer an HIV test over six timepoints where the 2nd and 5th are POS, the others are NEG.  

        >>> HivResult.objects.all().count()
        6
        >>> [obj.hiv_result for obj in HivResult.objects.all().order_by('result_datetime')]
        ['NEG', 'POS', 'NEG', 'NEG', 'POS', 'NEG'] 
        >>> status = Status(subject=self.subject, tested=HivResult)
        >>> status.result.result_value
        POS
        >>> status.previous
        POS
        >>> status.newly_positive
        False
        >>> status.subject_aware
        True
        >>> status.visit
        (datetime for the 2nd timepoint)

If there is only one POS result:

        >>> HivResult.objects.all().count()
        6
        >>> [obj.hiv_result for obj in HivResult.objects.all().order_by('result_datetime')]
        ['NEG', 'NEG', 'NEG', 'NEG', 'NEG', 'POS'] 
        >>> status = Status(subject=self.subject, tested=HivResult)
        >>> status.result.result_value
        POS
        >>> status.previous
        NEG
        >>> status.newly_positive
        True
        >>> status.subject_aware
        False
        >>> status.visit
        (datetime for the 6th timepoint)

Determining if a subject is `newly_positive` and aware of their status, `subject_aware`, also takes into account `documented` and `indirect`.

`Status` and `SimpleStatus` determine the "best" result to use. The choice in order is:

* today's test (tested);
* a documented test (documented);
* some evidence of HIV(+) status such as a prescription or medical record (indirect);
* Verbal information may be used if deliberately set to do so (verbal, include_verbal=True).

`Status` and `SimpleStatus` represents HIV(+) as a string 'POS'. See module `edc-constants`.

For both classes, `SimpleStatus` and `Status`, the parameters `tested, documented, indirect, verbal` all accept a string ('POS', 'NEG' IND', 'UNK'), a model class, or some class with the attributes `result_value`, `result_datetime`, and `visit`. `Status` wraps the string result into a class for consistency (`ResultWrapper`).

Take a look through the tests, but here are some simple examples to demonstrate the logic. These examples work for both classes.

	>>> subject = Subject.objects.create(subject_identifier='12345678')
	>>> status = Status(subject)
	>>> str(status)
	''
	>>> status.result.value
	''
	>>> status.result.result_datetime
	''
	>>> status == None
	True

Subject is tested for HIV today:

	>>> status = Status(subject, tested='POS')
	>>> str(status)
	'POS'

Subject shows documentation of HIV(+) status, such as a test result. `Status` returns 'POS':

	>>> status = Status(subject, documented='POS')
	>>> str(status)
	'POS'

Subject shows documentation of HIV(-) status, such as a test result. `Status` returns None since a HIV(+) status cannot be eliminated unless the subject gets tested today:

	>>> status = Status(subject, documented='NEG')
	>>> str(status)
	''

Subject shows documentation of HIV(-) status but tests POS today, `Status` returns 'POS':

	>>> status = Status(subject, tested='POS', documented='NEG')
	>>> str(status)
	'POS'	
	
Subject shows documentation of HIV(+) status but tests NEG today, `Status` returns 'NEG':

	>>> status = Status(subject, tested='NEG', documented='POS')
	>>> str(status)
	'NEG'

Subject claims HIV(-) status but has a prescription for ART, `Status` returns 'POS':

	>>> status = Status(subject, indirect='POS', verbal='NEG', include_verbal=True)
	>>> str(status)
	'POS'

Subject claims HIV(+) status but there is no direct or indirect documentation to support this, `Status` returns None:

	>>> status = Status(subject, verbal='POS')
	>>> str(status)
	''

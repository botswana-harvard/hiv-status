from django.db import models

from edc_constants.choices import HIV_RESULT


class Subject(models.Model):

    subject_identifier = models.CharField(max_length=25, unique=True)

    class Meta:
        app_label = 'hiv_status'


class Visit(models.Model):

    subject = models.ForeignKey(Subject)

    visit_datetime = models.DateTimeField()

    visit_code = models.CharField(max_length=10)

    encounter = models.IntegerField()

    def __str__(self):
        return self.visit_datetime.strftime('%Y-%m-%d')

    class Meta:
        app_label = 'hiv_status'
        unique_together = (('subject', 'visit_datetime'), ('visit_code', 'encounter'))
        ordering = ('-visit_datetime', 'visit_code', 'encounter')
        get_latest_by = 'visit_datetime'


class HivResult(models.Model):

    """A models completed by the user to record the result of a test run "today"."""

    visit = models.ForeignKey(Visit)

    result_value = models.CharField(
        verbose_name="Today\'s HIV test result",
        max_length=50,
        choices=HIV_RESULT,
        help_text="If participant declined HIV testing, please select a reason below.",
    )

    result_datetime = models.DateTimeField(
        verbose_name="Today\'s HIV test result date and time",
        null=True,
        blank=True,
    )

    why_not_tested = models.CharField(
        verbose_name=("What was the main reason why you did not want HIV testing"
                      " as part of today's visit?"),
        max_length=65,
        null=True,
        blank=True,
        help_text="Note: Only asked of individuals declining HIV testing during this visit.",
    )

    class Meta:
        app_label = 'hiv_status'
        get_latest_by = 'result_datetime'


class HivStatusReview(models.Model):

    subject = models.ForeignKey(Subject)

    report_datetime = models.DateTimeField()

    documented_result = models.CharField(max_length=10, null=True)

    documented_result_date = models.DateField(null=True)

    indirect_documentation = models.CharField(max_length=10, null=True)

    indirect_documentation_date = models.DateField(null=True)

    verbal_result = models.CharField(max_length=10, null=True)

    class Meta:
        app_label = 'hiv_status'
        get_latest_by = 'report_datetime'

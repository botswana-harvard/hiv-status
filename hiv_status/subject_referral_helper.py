from copy import copy
from collections import namedtuple

from django.db.models import get_model

from edc.constants import NOT_REQUIRED, KEYED
from edc.entry_meta_data.models import ScheduledEntryMetaData
from edc.map.classes import site_mappers
from edc.data_manager.models import TimePointStatus
from edc.constants import CLOSED, POS, NEG

from apps.bcpp_household_member.models import EnrollmentChecklist
from apps.bcpp_household.constants import BASELINE_SURVEY_SLUG
from apps.bcpp_subject.constants import ANNUAL_CODES

from ..choices import REFERRAL_CODES
from ..models import (SubjectConsent, ResidencyMobility, Circumcision, ReproductiveHealth, SubjectLocator)
from ..constants import BASELINE_CODES
from ..utils import convert_to_nullboolean

from .subject_status_helper import SubjectStatusHelper
from .subject_referral_appt_helper import SubjectReferralApptHelper


class SubjectReferralHelper(object):
    """A class that calculates the referral code or returns a blank string.

    See property :func:`referral_code`"""

    BASELINE = 'baseline'
    ANNUAL = 'annual'

    def __init__(self, subject_referral=None):
        self._circumcised = None
        self._enrollment_checklist_instance = None
        self._pregnant = None
        self._referral_clinic = None
        self._referral_code = None
        self._referral_code_list = []
        self._subject_consent_instance = None
        self._subject_referral = None
        self._subject_referral_dict = {}
        self._subject_status_helper = None
        self.community_code = site_mappers.get_current_mapper().map_code
        # self.models dict is also used in the signal
        self.models = copy(SubjectStatusHelper.models)
        self.models[self.BASELINE].update({
            'subject_locator': SubjectLocator,
            'circumcision': Circumcision,
            'reproductive_health': ReproductiveHealth,
            'residency_mobility': ResidencyMobility,
            'subject_consent': SubjectConsent,
            })
        self.models[self.ANNUAL].update({
            'subject_locator': SubjectLocator,
            'circumcision': Circumcision,
            'reproductive_health': ReproductiveHealth,
            'residency_mobility': ResidencyMobility,
            'subject_consent': SubjectConsent,
            })
        self.models[self.BASELINE].update({'subject_requisition': get_model('bcpp_lab', 'SubjectRequisition')})
        self.models[self.ANNUAL].update({'subject_requisition': get_model('bcpp_lab', 'SubjectRequisition')})
        self.previous_subject_referrals = []
        if subject_referral:
            self.subject_referral = subject_referral

    def __repr__(self):
        return 'SubjectStatusHelper({0.subject_referral!r})'.format(self)

    def __str__(self):
        return '({0.subject_referral!r})'.format(self)

    @property
    def timepoint_key(self):
        """Returns a dictionary key of either baseline or annual base in the visit code."""
        if self.subject_referral.subject_visit.appointment.visit_definition.code in BASELINE_CODES:
            return self.BASELINE
        return self.ANNUAL

    @property
    def subject_referral(self):
        return self._subject_referral

    @subject_referral.setter
    def subject_referral(self, subject_referral):
        SubjectReferral = get_model('bcpp_subject', 'SubjectReferral')
        if self._subject_referral:
            # reset every attribute
            self._subject_referral = None
            self.__init__()
        self._subject_referral = subject_referral
        # prepare a queryset of visits previous to visit_instance
        self.previous_subject_referrals = SubjectReferral.objects.filter(
            subject_visit__household_member__internal_identifier=\
            subject_referral.subject_visit.household_member.internal_identifier,
            report_datetime__lt=subject_referral.report_datetime).order_by('report_datetime')

    @property
    def subject_status_helper(self):
        if not self._subject_status_helper:
            self._subject_status_helper = SubjectStatusHelper(copy(self.subject_visit))
        return self._subject_status_helper

    @property
    def gender(self):
        return self.subject_referral.subject_visit.appointment.registered_subject.gender

    @property
    def household_member(self):
        return self.subject_referral.subject_visit.household_member

    @property
    def subject_identifier(self):
        return self.subject_referral.subject_visit.appointment.registered_subject.subject_identifier

    @property
    def subject_visit(self):
        return self.subject_referral.subject_visit

    def visit_code(self):
        return self.subject_referral.subject_visit.appointment.visit_definition.code

    @property
    def survey(self):
        return self.subject_referral.subject_visit.household_member.household_structure.survey

    @property
    def hiv_result(self):
        return self.subject_status_helper.hiv_result

    @property
    def on_art(self):
        """Returns None if hiv_result==NEG otherwise True if hiv_result==POS and on ART or False if not."""
        return self.subject_status_helper.on_art

    @property
    def missing_data(self):
        """Returns the model name of the first model used in the referral algorithm
        with meta data that is NOT set to KEYED or NOT_REQUIRED.

        If time-point status instance exists with status=CLOSED, the check is skipped."""
        first_model_cls = None
        internal_identifier = self.subject_visit.household_member.internal_identifier
        if not SubjectLocator.objects.filter(
                subject_visit__household_member__internal_identifier=internal_identifier).exists():
            first_model_cls = SubjectLocator  # required no matter what
        else:
            try:
                TimePointStatus.objects.get(appointment=self.subject_visit.appointment, status=CLOSED)
            except TimePointStatus.DoesNotExist:
                for model_cls in self.models[self.timepoint_key].values():
                    try:
                        scheduled_entry_meta_data = ScheduledEntryMetaData.objects.get(
                            appointment=self.subject_visit.appointment,
                            entry__app_label=model_cls._meta.app_label,
                            entry__model_name=model_cls._meta.object_name)
                        if scheduled_entry_meta_data.entry_status not in [KEYED, NOT_REQUIRED]:
                            first_model_cls = model_cls
                            break
                    except ScheduledEntryMetaData.DoesNotExist:
                        pass
                    except AttributeError:  # NoneType?
                        pass
        return first_model_cls

    @property
    def subject_referral_dict(self):
        """Returns a dictionary of the attributes {name: value, ...}
        from this class that match, by name, field attributes in the
        SubjectReferral model."""
        if not self._subject_referral_dict:
            self._subject_referral_dict = {}
            for attr in self.subject_referral.__dict__:
                if attr in dir(self) and not attr.startswith('_'):
                    self._subject_referral_dict.update({attr: getattr(self, attr)})
            self._subject_referral_dict.update({'subject_identifier': getattr(self, 'subject_identifier')})
        return self._subject_referral_dict

    @property
    def subject_referral_tuple(self):
        """Returns a dictionary of the attributes {name: value, ...}
        from this class that match, by name, field attributes in the
        SubjectReferral model."""
        Tpl = namedtuple('SubjectReferralTuple', 'subject_visit ' + '  '.join(self.subject_referral.keys()))
        self._subject_referral_tuple = Tpl(self.subject_visit, *self.subject_referral.values())
        return self._subject_referral_tuple

    @property
    def referral_code_list(self):
        """Returns a list of referral codes by reviewing the conditions for referral."""
        if not self._referral_code_list:
            if not self.hiv_result:
                if self.gender == 'M':
                    if self.circumcised:
                        self._referral_code_list.append('TST-HIV')  # refer if status unknown
                    else:
                        if self.circumcised is False:
                            self._referral_code_list.append('SMC-UNK')  # refer if status unknown
                        else:
                            self._referral_code_list.append('SMC?UNK')  # refer if status unknown
                elif self.pregnant:
                    self._referral_code_list.append('UNK?-PR')
                else:
                    self._referral_code_list.append('TST-HIV')
            else:
                if self.hiv_result == 'IND':
                    # do not set referral_code_list to IND
                    pass
                elif self.hiv_result == NEG:
                    if self.gender == 'F' and self.pregnant:  # only refer F if pregnant
                        self._referral_code_list.append('NEG!-PR')
                    elif self.gender == 'M' and self.circumcised is False:  # only refer M if not circumcised
                        self._referral_code_list.append('SMC-NEG')
                    elif self.gender == 'M' and self.circumcised is None:  # only refer M if not circumcised
                        self._referral_code_list.append('SMC?NEG')
                elif self.hiv_result == POS:
                    if self.gender == 'F' and self.pregnant and self.on_art:
                        self._referral_code_list.append('POS#-AN')
                    elif self.gender == 'F' and self.pregnant and not self.on_art:
                        self._referral_code_list.append(
                            'POS!-PR') if self.new_pos else self._referral_code_list.append('POS#-PR')
                    elif not self.on_art:
                        if not self.cd4_result:
                            self._referral_code_list.append('TST-CD4')
                        elif self.cd4_result > 350:
                            self._referral_code_list.append(
                                'POS!-HI') if self.new_pos else self._referral_code_list.append('POS#-HI')
                        elif self.cd4_result <= 350:
                            self._referral_code_list.append(
                                'POS!-LO') if self.new_pos else self._referral_code_list.append('POS#-LO')
                    elif self.on_art:
                        self._referral_code_list.append('MASA-CC')
                        if self.defaulter:
                            self._referral_code_list = ['MASA-DF' for item in self._referral_code_list if item == 'MASA-CC']
                        if self.pregnant:
                            self._referral_code_list = ['POS#-AN' for item in self._referral_code_list if item == 'MASA-CC']
                        if self.visit_code in ANNUAL_CODES:  # do not refer to MASA-CC except if BASELINE
                            try:
                                self._referral_code_list.remove('MASA-CC')
                            except ValueError:
                                pass
                else:
                    self._referral_code_list.append('TST-HIV')
            # refer if on art and known positive to get VL, and o get outsiders to transfer care
            # referal date is the next appointment date if on art
            if self._referral_code_list:
                self._referral_code_list = list(set((self._referral_code_list)))
                self._referral_code_list.sort()
                for code in self._referral_code_list:
                    if code not in self.valid_referral_codes:
                        raise ValueError('{0} is not a valid referral code.'.format(code))
        return self._referral_code_list

    @property
    def referral_code(self):
        """Returns a string of referral codes as a join of the
        list of referral codes delimited by ","."""
        if self._referral_code is None:
            self._referral_code = ','.join(self.referral_code_list)
            self._referral_code = self.remove_smc_in_annual_ecc(self._referral_code)
        return self._referral_code

    def remove_smc_in_annual_ecc(self, referral_code):
        """Removes any SMC referral codes if in the ECC during an ANNUAL survey."""
        if (not site_mappers.current_mapper().intervention and
                self.subject_visit.household_member.household_structure.survey.survey_slug != \
                BASELINE_SURVEY_SLUG):
            referral_code = referral_code.replace('SMC-NEG', '').replace('SMC?NEG', '').replace('SMC-UNK', '').replace('SMC?UNK', '')
        return referral_code

    @property
    def valid_referral_codes(self):
        return [code for code, _ in REFERRAL_CODES if not code == 'pending']

    @property
    def arv_clinic(self):
        try:
            clinic_receiving_from = self._subject_status_helper.hiv_care_adherence_instance.clinic_receiving_from
        except AttributeError:
            clinic_receiving_from = None
        return clinic_receiving_from

    @property
    def circumcised(self):
        """Returns None if female otherwise True if circumcised or False if not."""
        if self._circumcised is None:
            if self.gender == 'M':
                circumcised = None
                if self.previous_subject_referrals:
                    # save current visit
#                     current_subject_referral = copy(self.subject_referral)
                    previous_subject_referrals = copy(self.previous_subject_referrals)
                    for subject_referral in previous_subject_referrals:
                        # check for CIRCUMCISED result from previous data
#                         self.subject_referral = subject_referral
                        circumcised = subject_referral.circumcised
                        if circumcised:
                            break
#                     self.subject_referral = current_subject_referral
                if not circumcised:
                    try:
                        circumcision_instance = self.models[self.timepoint_key].get(
                            'circumcision').objects.get(subject_visit=self.subject_visit)
                        circumcised = convert_to_nullboolean(circumcision_instance.circumcised)
                    except self.models[self.timepoint_key].get('circumcision').DoesNotExist:
                        circumcised = None
                self._circumcised = circumcised
        return self._circumcised

    @property
    def citizen(self):
        citizen = None
        try:
            citizen = (self.enrollment_checklist_instance.citizen == 'Yes'
                       and self.subject_consent_instance.identity is not None)
        except AttributeError:
            citizen = None
        return citizen

    @property
    def citizen_spouse(self):
        citizen_spouse = None
        try:
            citizen_spouse = (self.enrollment_checklist_instance.legal_marriage == 'Yes' and
                              self.subject_consent_instance.identity is not None)
        except AttributeError:
            citizen_spouse = None
        return citizen_spouse

    @property
    def next_arv_clinic_appointment_date(self):
        next_appointment_date = None
        try:
            next_appointment_date = self._subject_status_helper.hiv_care_adherence_instance.next_appointment_date
        except AttributeError:
            pass
        return next_appointment_date

    @property
    def part_time_resident(self):
        """Returns True if part_time_resident as stated on enrollment_checklist."""
        try:
            #Note: Reading the question in EnrollmentChecklist, you should interpret in the following way,
            # Yes => not part_time_resident, No => part_time_resident.
            part_time_resident = not convert_to_nullboolean(self.enrollment_checklist_instance.part_time_resident)
        except AttributeError:
            part_time_resident = None
        return part_time_resident

    @property
    def permanent_resident(self):
        """Returns True if permanent resident as stated on ResidencyMobility."""
        try:
            residency_mobility_instance = self.models[self.timepoint_key].get('residency_mobility').objects.get(
                subject_visit=self.subject_visit)
            permanent_resident = convert_to_nullboolean(residency_mobility_instance.permanent_resident)
        except self.models[self.timepoint_key].get('residency_mobility').DoesNotExist:
            permanent_resident = None
        return permanent_resident

    @property
    def pregnant(self):
        """Returns None if male otherwise True if pregnant or False if not."""
        if self.gender == 'F':
            if not self._pregnant:
                try:
                    reproductive_health = self.models[self.timepoint_key].get('reproductive_health').objects.get(
                        subject_visit=self.subject_visit)
                    self._pregnant = convert_to_nullboolean(reproductive_health.currently_pregnant)
                except self.models[self.timepoint_key].get('reproductive_health').DoesNotExist:
                    self._pregnant = None
        return self._pregnant

    @property
    def tb_symptoms(self):
        """Returns the tb_symptoms list as a convenience.

        Not necessary for determining the referral code."""
        return self.subject_referral.tb_symptoms

    @property
    def urgent_referral(self):
        """Compares the referral_codes to the "urgent" referrals
        list and sets to true on a match."""
        URGENT_REFERRALS = ['MASA-DF', 'POS!-LO', 'POS#-LO', 'POS#-PR', 'POS!-PR']
        return True if [code for code in self.referral_code_list if code in URGENT_REFERRALS] else False

    @property
    def enrollment_checklist_instance(self):
        # Can have multiple enrollment checklists for one each household_member__internal_identifier,
        # but only one of them will be associated with a consented member. Thats the 1 we want to pull here.
        if not self._enrollment_checklist_instance:
            self._enrollment_checklist_instance = EnrollmentChecklist.objects.get(
                household_member__internal_identifier=self.subject_visit.household_member.internal_identifier,
                household_member__is_consented=True)
        return self._enrollment_checklist_instance

    @property
    def subject_consent_instance(self):
        if not self._subject_consent_instance:
            try:
                self._subject_consent_instance = self.models[self.timepoint_key].get('subject_consent').objects.get(
                    household_member__internal_identifier=self.household_member.internal_identifier)
            except self.models[self.timepoint_key].get('subject_consent').DoesNotExist:
                self._subject_consent_instance = None
        return self._subject_consent_instance

    @property
    def subject_referral_appt_helper(self):
        return SubjectReferralApptHelper(
            self.referral_code,
            base_date=self.subject_referral.report_datetime,
            scheduled_appt_date=self.subject_referral.scheduled_appt_date,
            )

    @property
    def referral_appt_datetime(self):
        return self.subject_referral_appt_helper.referral_appt_datetime

    @property
    def referral_clinic_type(self):
        return self.subject_referral_appt_helper.referral_clinic_type

    @property
    def referral_clinic(self):
        return self.subject_referral_appt_helper.community_name

    @property
    def original_scheduled_appt_date(self):
        return self.subject_referral_appt_helper.original_scheduled_appt_date

    @property
    def new_pos(self):
        return self.subject_status_helper.new_pos

    @property
    def hiv_result_datetime(self):
        return self.subject_status_helper.hiv_result_datetime

    @property
    def last_hiv_result_date(self):
        return self.subject_status_helper.last_hiv_result_date

    @property
    def verbal_hiv_result(self):
        return self.subject_status_helper.verbal_hiv_result

    @property
    def last_hiv_result(self):
        return self.subject_status_helper.last_hiv_result

    @property
    def indirect_hiv_documentation(self):
        return self.subject_status_helper.indirect_hiv_documentation

    @property
    def direct_hiv_documentation(self):
        return self.subject_status_helper.direct_hiv_documentation

    @property
    def defaulter(self):
        return self.subject_status_helper.defaulter

    @property
    def cd4_result(self):
        return self.subject_status_helper.cd4_result

    @property
    def vl_sample_drawn(self):
        return self.subject_status_helper.vl_sample_drawn

    @property
    def vl_sample_drawn_datetime(self):
        return self.subject_status_helper.vl_sample_drawn_datetime

    @property
    def arv_documentation(self):
        return self.subject_status_helper.arv_documentation

    @property
    def cd4_result_datetime(self):
        return self.subject_status_helper.cd4_result_datetime

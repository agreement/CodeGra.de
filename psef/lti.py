"""This module contains the code used for all LTI functionality.

:license: AGPLv3, see LICENSE for details. This does not include code copied
    from https://github.com/ucfopen/lti-template-flask-oauth-tokens
"""
# This file contains large pieces of code from this github repository:
# https://github.com/ucfopen/lti-template-flask-oauth-tokens

import typing as t
import datetime

import flask
import oauth2
import dateutil
import flask_jwt_extended as flask_jwt
from lxml import etree, objectify

import psef
import psef.auth as auth
import psef.models as models
import psef.helpers as helpers
from psef import LTI_ROLE_LOOKUPS, app, current_user
from psef.auth import _user_active
from psef.errors import APICodes, APIException
from psef.models import db


def init_app(_: t.Any) -> None:
    pass


# TODO: This class has so many public methods as they are properties. A lot of
# them can be converted to private properties which should be done.
class LTI:  # pylint: disable=too-many-public-methods
    """The base LTI class.
    """

    def __init__(
        self,
        params: t.Mapping[str, str],
        lti_provider: models.LTIProvider = None
    ) -> None:
        self.launch_params = params

        if lti_provider is not None:
            self.lti_provider = lti_provider
        else:
            lti_id = params['lti_provider_id']
            self.lti_provider = helpers.get_or_404(
                models.LTIProvider,
                lti_id,
            )

        self.key = self.lti_provider.key
        self.secret = self.lti_provider.secret

    # TODO support more than just flask
    @classmethod
    def create_from_request(cls: t.Type['LTI'], req: flask.Request) -> 'LTI':
        """Create an instance from a flask request.

        The request should have a ``form`` variable that has all the right
        parameters. So this request should be from an LTI launch.

        :param req: The request to create the LTI instance from.
        :returns: A fresh LTI instance.
        """
        params = req.form.copy()

        lti_provider = models.LTIProvider.query.filter_by(
            key=params['oauth_consumer_key']
        ).first()
        if lti_provider is None:
            lti_provider = models.LTIProvider(key=params['oauth_consumer_key'])
            db.session.add(lti_provider)
            db.session.commit()

        params['lti_provider_id'] = lti_provider.id

        # This is semi sensitive information so it should not end up in the JWT
        # token.
        launch_params = {}
        for key, value in params.items():
            if not key.startswith('oauth'):
                launch_params[key] = value

        self = cls(launch_params, lti_provider)

        auth.ensure_valid_oauth(self.key, self.secret, req)

        return self

    @property
    def user_id(self) -> str:
        """The unique id of the current LTI user.
        """
        return self.launch_params['user_id']

    @property
    def user_email(self) -> str:
        """The email of the current LTI user.
        """
        return self.launch_params['lis_person_contact_email_primary']

    @property
    def full_name(self) -> str:
        """The name of the current LTI user.
        """
        return self.launch_params['lis_person_name_full']

    @property
    def username(self) -> str:  # pragma: no cover
        """The username of the current LTI user.
        """
        return self.launch_params['user_id']

    @property
    def course_id(self) -> str:  # pragma: no cover
        """The course id of the current LTI course.
        """
        return self.launch_params['context_id']

    @property
    def course_name(self) -> str:  # pragma: no cover
        """The name of the current LTI course.
        """
        return self.launch_params['context_title']

    @property
    def assignment_id(self) -> str:  # pragma: no cover
        """The id of the current LTI assignment.
        """
        raise NotImplementedError

    @property
    def assignment_name(self) -> str:  # pragma: no cover
        """The name of the current LTI assignment.
        """
        raise NotImplementedError

    @property
    def outcome_service_url(self) -> str:  # pragma: no cover
        """The url used to passback grades to Canvas.
        """
        raise NotImplementedError

    @property
    def result_sourcedid(self) -> str:  # pragma: no cover
        """The sourcedid of the current user for the current assignment.
        """
        raise NotImplementedError

    @property
    def assignment_state(self) -> models._AssignmentStateEnum:  # pylint: disable=protected-access
        """The state of the current LTI assignment.
        """
        raise NotImplementedError  # pragma: no cover

    @property
    def roles(self) -> t.Iterable[str]:  # pragma: no cover
        """The normalized roles of the current LTI user.
        """
        raise NotImplementedError

    def get_assignment_deadline(
        self, default: datetime.datetime = None
    ) -> datetime.datetime:  # pragma: no cover
        """Get the deadline of the current LTI assignment.

        :param default: The value to be returned of the assignment has no
            deadline. If ``default.__bool__`` is ``False`` the current date
            plus 365 days is used.
        :returns: The deadline of the assignment as a datetime.
        """
        raise NotImplementedError

    def ensure_lti_user(
        self
    ) -> t.Tuple[models.User, t.Optional[str], t.Optional[str]]:
        """Make sure the current LTI user is logged in as a psef user.

        This is done by first checking if we know a user with the current LTI
        user_id, if this is the case this is the user we log in and return.

        Otherwise we check if a user is logged in and this user has no LTI
        user_id, if this is the case we link the current LTI user_id to the
        current logged in user and return this user.

        Otherwise we create a new user and link this user to current LTI
        user_id.

        :returns: A tuple containing the items in order: the user found as
            described above, optionally a new token for the user to login with,
            optionally the updated email of the user as a string, this is
            ``None`` if the email was not updated.
        """
        is_logged_in = _user_active()
        token = None
        user = None

        lti_user = models.User.query.filter_by(lti_user_id=self.user_id
                                               ).first()

        if is_logged_in and current_user.lti_user_id == self.user_id:
            # The currently logged in user is now using LTI
            user = current_user

        elif lti_user is not None:
            # LTI users are used before the current logged user.
            token = flask_jwt.create_access_token(
                identity=lti_user.id,
                fresh=True,
            )
            user = lti_user
        elif is_logged_in and current_user.lti_user_id is None:
            # TODO show some sort of screen if this linking is wanted
            current_user.lti_user_id = self.user_id
            db.session.flush()
            user = current_user
        else:
            # New LTI user id is found and no user is logged in or the current
            # user has a different LTI user id. A new user is created and
            # logged in.
            i = 0

            def _get_username() -> str:
                return self.username + (f' ({i})' if i > 0 else '')

            while db.session.query(
                models.User.query.filter_by(username=_get_username()).exists()
            ).scalar():  # pragma: no cover
                i += 1

            user = models.User(
                lti_user_id=self.user_id,
                name=self.full_name,
                email=self.user_email,
                active=True,
                password=None,
                username=_get_username(),
            )
            db.session.add(user)
            db.session.flush()

            token = flask_jwt.create_access_token(
                identity=user.id,
                fresh=True,
            )

        updated_email = None
        if user.reset_email_on_lti:
            user.email = self.user_email
            updated_email = self.user_email
            user.reset_email_on_lti = False

        return user, token, updated_email

    def get_course(self) -> models.Course:
        """Get the current LTI course as a psef course.
        """
        course = models.Course.query.filter_by(lti_course_id=self.course_id
                                               ).first()
        if course is None:
            course = models.Course(
                name=self.course_name, lti_course_id=self.course_id
            )
            db.session.add(course)

        course.lti_provider = self.lti_provider
        db.session.flush()

        return course

    def get_assignment(self, user: models.User) -> models.Assignment:
        """Get the current LTI assignment as a psef assignment.
        """
        assignment = models.Assignment.query.filter_by(
            lti_assignment_id=self.assignment_id
        ).first()
        if assignment is None:
            course = self.get_course()
            assignment = models.Assignment(
                name=self.assignment_name,
                state=self.assignment_state,
                course_id=course.id,
                deadline=self.get_assignment_deadline(),
                lti_assignment_id=self.assignment_id,
                description=''
            )
            db.session.add(assignment)
            db.session.flush()

        if self.has_result_sourcedid():
            if assignment.id in user.assignment_results:
                user.assignment_results[assignment.id
                                        ].sourcedid = self.result_sourcedid
            else:
                assig_res = models.AssignmentResult(
                    sourcedid=self.result_sourcedid,
                    user_id=user.id,
                    assignment_id=assignment.id
                )
                db.session.add(assig_res)

        assignment.lti_outcome_service_url = self.outcome_service_url

        if not assignment.is_done:
            assignment.state = self.assignment_state

        assignment.deadline = self.get_assignment_deadline(
            default=assignment.deadline
        )

        db.session.flush()

        return assignment

    def set_user_role(self, user: models.User) -> None:
        """Set the role of the given user if the user has no role.

        The role is determined according to :py:data:`.LTI_ROLE_LOOKUPS`.

        .. note::
            If the role could not be matched the ``DEFAULT_ROLE`` configured
            in the config of the app is used.

        :param models.User user: The user to set the role for.
        :returns: Nothing
        :rtype: None
        """
        if user.role is None:
            for role in self.roles:
                if role not in LTI_ROLE_LOOKUPS:
                    continue
                role_lookup = LTI_ROLE_LOOKUPS[role]
                if role_lookup['course_role']:  # This is a course role
                    continue
                user.role = models.Role.query.filter_by(
                    name=role_lookup['role']
                ).one()
                return
            user.role = models.Role.query.filter_by(
                name=app.config['DEFAULT_ROLE']
            ).one()

    def set_user_course_role(self, user: models.User,
                             course: models.Course) -> t.Union[str, bool]:
        """Set the course role for the given course and user if there is no
        such role just yet.

        The mapping is done using :py:data:`.LTI_ROLE_LOOKUPS`. If no role
        could be found a new role is created with the default permissions.

        :param models.User user: The user to set the course role  for.
        :param models.Course course: The course to connect to user to.
        :returns: True if a new role was created.
        """
        if course.id not in user.courses:
            unkown_roles = []
            for role in self.roles:
                if role not in LTI_ROLE_LOOKUPS:
                    unkown_roles.append(role)
                    continue
                role_lookup = LTI_ROLE_LOOKUPS[role]
                if not role_lookup['course_role']:  # This is not a course role
                    continue

                crole = models.CourseRole.query.filter_by(
                    course_id=course.id, name=role_lookup['role']
                ).one()
                user.courses[course.id] = crole
                return False

            if not psef.app.config['FEATURES']['AUTOMATIC_LTI_ROLE']:
                raise APIException(
                    'The given LTI role was not valid found, please '
                    'ask your instructor or site admin.',
                    f'No role in "{list(self.roles)}" is a known LTI role',
                    APICodes.INVALID_STATE, 400
                )

            # Add a new course role
            new_created: t.Union[bool, str] = False
            new_role = (unkown_roles + ['New LTI Role'])[0]
            existing_role = models.CourseRole.query.filter_by(
                course_id=course.id, name=new_role
            ).first()
            if existing_role is None:
                existing_role = models.CourseRole(course=course, name=new_role)
                db.session.add(existing_role)
                new_created = new_role
            user.courses[course.id] = existing_role
            return new_created
        return False

    def has_result_sourcedid(self) -> bool:  # pragma: no cover
        """Check if the current LTI request has a ``sourcedid`` field.

        :returns: A boolean indicating if a ``sourcedid`` field was found.
        """
        raise NotImplementedError

    @staticmethod
    def generate_xml() -> str:  # pragma: no cover
        """Generate a config XML for this LTI consumer.
        """
        raise NotImplementedError

    @staticmethod
    def passback_grade(
        key: str,
        secret: str,
        grade: t.Union[float, None, bool, str, int],
        service_url: str,
        sourcedid: str,
        url: str = None,
    ) -> 'OutcomeResponse':
        """Do a LTI grade passback.

        :param key: The oauth key to use.
        :param secret: The oauth secret to use.
        :param grade: The grade to pass back, between 0 and
            10. If it is `None` the grade will be deleted, if it is a ``bool``
            no grade information will be send.
        :param service_url: The url used for grade passback.
        :param sourcedid: The ``sourcedid`` used in the grade passback.
        :param url: The url used as general feedback to the student which will
            probably be clickable.
        :returns: The response of the LTI consumer.
        """
        req = OutcomeRequest(
            consumer_key=key,
            consumer_secret=secret,
            lis_outcome_service_url=service_url,
            lis_result_sourcedid=sourcedid
        )
        opts = None
        if url is not None:
            opts = {'url': url}

        if grade is None:
            return req.post_delete_result()
        else:
            if isinstance(grade, bool):
                grade = None
            elif not isinstance(grade, str):
                grade = str(grade / 10)
            return req.post_replace_result(grade, result_data=opts)


class CanvasLTI(LTI):
    """The LTI class used for the Canvas LMS.
    """

    @property
    def username(self) -> str:
        return self.launch_params['custom_canvas_user_login_id']

    @property
    def course_name(self) -> str:
        return self.launch_params['custom_canvas_course_name']

    @property
    def course_id(self) -> str:
        return self.launch_params['custom_canvas_course_id']

    @property
    def assignment_id(self) -> str:
        return self.launch_params['custom_canvas_assignment_id']

    @property
    def assignment_name(self) -> str:
        return self.launch_params['custom_canvas_assignment_title']

    @property
    def outcome_service_url(self) -> str:
        return self.launch_params['lis_outcome_service_url']

    @property
    def result_sourcedid(self) -> str:
        return self.launch_params['lis_result_sourcedid']

    def has_result_sourcedid(self) -> bool:
        return 'lis_result_sourcedid' in self.launch_params

    @staticmethod
    def generate_xml() -> str:  # pragma: no cover
        """Generate a config XML for this LTI consumer.

        .. todo:: Implement this function
        """
        raise NotImplementedError

    @property
    def assignment_state(self) -> models._AssignmentStateEnum:
        # pylint: disable=protected-access
        if self.launch_params['custom_canvas_assignment_published'] == 'true':
            return models._AssignmentStateEnum.open
        else:
            return models._AssignmentStateEnum.hidden

    @property
    def roles(self) -> t.Iterable[str]:
        for role in self.launch_params['roles'].split(','):
            yield role.split('/')[-1].lower()

    def get_assignment_deadline(
        self, default: datetime.datetime = None
    ) -> datetime.datetime:
        try:
            deadline = dateutil.parser.parse(
                self.launch_params['custom_canvas_assignment_due_at']
            )
            deadline = deadline.astimezone(datetime.timezone.utc)
            return deadline.replace(tzinfo=None)
        except (KeyError, ValueError, OverflowError):
            return (datetime.datetime.utcnow() + datetime.timedelta(days=365)
                    ) if default is None else default


# This part is largely copied from https://github.com/tophatmonocle/ims_lti_py

REPLACE_REQUEST = 'replaceResult'
DELETE_REQUEST = 'deleteResult'
READ_REQUEST = 'readResult'


# TODO: Actually cover this in some way using unit tests
class OutcomeRequest:  # pragma: no cover, pylint: disable=protected-access,invalid-name,too-many-arguments,missing-docstring
    '''
    Class for consuming & generating LTI Outcome Requests.

    Outcome Request documentation:
        http://www.imsglobal.org/LTI/v1p1/ltiIMGv1p1.html#_Toc319560472

    This class can be used both by Tool Providers and Tool Consumers, though
    they each use it differently. The TP will use it to POST an OAuth-signed
    request to the TC. A TC will use it to parse such a request from a TP.
    '''

    def __init__(
        self,
        operation: str = None,
        score: str = None,
        result_data: t.Mapping[str, str] = None,
        message_identifier: str = None,
        lis_outcome_service_url: str = None,
        lis_result_sourcedid: str = None,
        consumer_key: str = None,
        consumer_secret: str = None,
        post_request: t.Any = None
    ) -> None:
        self.operation = operation
        self.score = score
        self.result_data = result_data
        self.outcome_response = None  # type: t.Optional['OutcomeResponse']
        self.message_identifier = message_identifier
        self.lis_outcome_service_url = lis_outcome_service_url
        self.lis_result_sourcedid = lis_result_sourcedid
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.post_request = post_request

    @staticmethod
    def from_post_request(post_request: t.Any) -> 'OutcomeRequest':
        '''
        Convenience method for creating a new OutcomeRequest from a request
        object.

        post_request is assumed to be a Django HttpRequest object
        '''
        request = OutcomeRequest()
        request.post_request = post_request
        request.process_xml(post_request.data)
        return request

    def post_replace_result(
        self, score: str, result_data: t.Mapping[str, str] = None
    ) -> 'OutcomeResponse':
        '''
        POSTs the given score to the Tool Consumer with a replaceResult.

        OPTIONAL:
            result_data must be a dictionary
            Note: ONLY ONE of these values can be in the dict at a time,
            due to the Canvas specification.

        :param str text: text
        :param str url: url
        :param str launchUrl: The lti launch url
        '''
        self.operation = REPLACE_REQUEST
        self.score = score
        self.result_data = result_data
        if result_data is not None:
            if len(result_data) > 1:
                error_msg = (
                    'Dictionary result_data can only have one entry. '
                    '{0} entries were found.'.format(len(result_data))
                )
                raise ValueError(error_msg)
            elif any(a in result_data for a in ['url', 'text', 'launchUrl']):
                return self.post_outcome_request()
            else:
                error_msg = (
                    'Dictionary result_data can only have the key '
                    '"text" or the key "url".'
                )
                raise ValueError(error_msg)
        else:
            return self.post_outcome_request()

    def post_delete_result(self) -> 'OutcomeResponse':
        '''
        POSTs a deleteRequest to the Tool Consumer.
        '''
        self.operation = DELETE_REQUEST
        return self.post_outcome_request()

    def post_read_result(self) -> 'OutcomeResponse':
        '''
        POSTS a readResult to the Tool Consumer.
        '''
        self.operation = READ_REQUEST
        return self.post_outcome_request()

    def is_replace_request(self) -> bool:
        '''
        Check whether this request is a replaceResult request.
        '''
        return self.operation == REPLACE_REQUEST

    def is_delete_request(self) -> bool:
        '''
        Check whether this request is a deleteResult request.
        '''
        return self.operation == DELETE_REQUEST

    def is_read_request(self) -> bool:
        '''
        Check whether this request is a readResult request.
        '''
        return self.operation == READ_REQUEST

    def was_outcome_post_successful(self) -> bool:
        return (
            self.outcome_response is not None and
            self.outcome_response.is_success()
        )

    def post_outcome_request(self) -> 'OutcomeResponse':
        '''
        POST an OAuth signed request to the Tool Consumer.
        '''
        if not self.has_required_attributes():
            raise ValueError(
                'OutcomeRequest does not have all required attributes'
            )

        consumer = oauth2.Consumer(
            key=self.consumer_key, secret=self.consumer_secret
        )

        client = oauth2.Client(consumer)
        # monkey_patch_headers ensures that Authorization
        # header is NOT lower cased
        monkey_patch_headers = True
        monkey_patch_function = None
        if monkey_patch_headers:
            import httplib2
            http = httplib2.Http

            normalize = http._normalize_headers

            def __my_normalize(self: t.Any, headers: t.Sequence) -> t.Sequence:
                ret = normalize(self, headers)
                if 'authorization' in ret:
                    ret['Authorization'] = ret.pop('authorization')
                return ret

            http._normalize_headers = __my_normalize
            monkey_patch_function = normalize

        response, content = client.request(
            self.lis_outcome_service_url,
            'POST',
            body=self.generate_request_xml(),
            headers={'Content-Type': 'application/xml'}
        )

        if monkey_patch_headers and monkey_patch_function:
            http = httplib2.Http
            http._normalize_headers = monkey_patch_function

        self.outcome_response = OutcomeResponse.from_post_response(
            response, content
        )
        return self.outcome_response

    def process_xml(self, xml: str) -> None:
        '''
        Parse Outcome Request data from XML.
        '''
        root = t.cast(t.Mapping, objectify.fromstring(xml))
        self.message_identifier = str(
            root['imsx_POXHeader']['imsx_POXRequestHeaderInfo']
            ['imsx_messageIdentifier']
        )
        try:
            result = root['imsx_POXBody']['replaceResultRequest']
            self.operation = REPLACE_REQUEST

            # Get result sourced id from resultRecord
            record = result.resultRecord
            self.lis_result_sourcedid = record.sourcedGUID.sourcedId

            self.score = str(result.resultRecord.result.resultScore.textString)
        except (KeyError, TypeError, AttributeError):
            pass

        try:
            result = root['imsx_POXBody']['deleteResultRequest']
            self.operation = DELETE_REQUEST
            # Get result sourced id from resultRecord
            self.lis_result_sourcedid = result['resultRecord']['sourcedGUID'
                                                               ]['sourcedId']
        except (KeyError, TypeError):
            pass

        try:
            result = root['imsx_POXBody']['readResultRequest']
            self.operation = READ_REQUEST
            # Get result sourced id from resultRecord
            self.lis_result_sourcedid = result['resultRecord']['sourcedGUID'
                                                               ]['sourcedId']
        except (KeyError, TypeError):
            pass

    def has_required_attributes(self) -> bool:
        return (
            self.consumer_key is not None and
            self.consumer_secret is not None and
            self.lis_outcome_service_url is not None and
            self.lis_result_sourcedid is not None and
            self.operation is not None
        )

    def generate_request_xml(self) -> t.Union[bytes, str]:
        root = etree.Element(
            'imsx_POXEnvelopeRequest',
            xmlns='http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0'
        )

        header = etree.SubElement(root, 'imsx_POXHeader')
        header_info = etree.SubElement(header, 'imsx_POXRequestHeaderInfo')
        version = etree.SubElement(header_info, 'imsx_version')
        version.text = 'V1.0'
        message_identifier = etree.SubElement(
            header_info, 'imsx_messageIdentifier'
        )
        message_identifier.text = self.message_identifier
        body = etree.SubElement(root, 'imsx_POXBody')
        request = etree.SubElement(body, f'{self.operation}Request')
        record = etree.SubElement(request, 'resultRecord')

        guid = etree.SubElement(record, 'sourcedGUID')

        sourcedid = etree.SubElement(guid, 'sourcedId')
        sourcedid.text = self.lis_result_sourcedid

        if self.score is not None or self.result_data:
            result = etree.SubElement(record, 'result')

        if self.score is not None:
            result_score = etree.SubElement(result, 'resultScore')
            language = etree.SubElement(result_score, 'language')
            language.text = 'en'
            text_string = etree.SubElement(result_score, 'textString')
            text_string.text = self.score.__str__()

        if self.result_data:
            resultData = etree.SubElement(result, 'resultData')
            if 'text' in self.result_data:
                resultDataText = etree.SubElement(resultData, 'text')
                resultDataText.text = self.result_data['text']
            elif 'url' in self.result_data:
                resultDataURL = etree.SubElement(resultData, 'url')
                resultDataURL.text = self.result_data['url']
            elif 'launchUrl' in self.result_data:
                resultDataLaunchURL = etree.SubElement(
                    resultData, 'ltiLaunchUrl'
                )
                resultDataLaunchURL.text = self.result_data['launchUrl']

        return etree.tostring(root, xml_declaration=True, encoding='utf-8')


CODE_MAJOR_CODES = ['success', 'processing', 'failure', 'unsupported']

SEVERITY_CODES = ['status', 'warning', 'error']


# TODO: Actually cover this in some way using unit tests
class OutcomeResponse:  # pragma: no cover
    '''
    This class consumes & generates LTI Outcome Responses.

    Response documentation:
        http://www.imsglobal.org/LTI/v1p1/ltiIMGv1p1.html#_Toc319560472

    Error code documentation:
        http://www.imsglobal.org/gws/gwsv1p0/imsgws_baseProfv1p0.html#1639667

    This class can be used by both Tool Providers and Tool Consumers, though
    each will use it differently. TPs will use it to partse the result of an
    OutcomeRequest to the TC. A TC will use it to generate proper response XML
    to send back to a TP.
    '''

    def __init__(  # pylint: disable=too-many-arguments
        self,
        request_type: str = None,
        score: str = None,
        message_identifier: str = None,
        response_code: str = None,
        post_response: str = None,
        code_major: str = None,
        severity: str = None,
        description: str = None,
        operation: str = None,
        message_ref_identifier: str = None
    ) -> None:
        self.request_type = request_type
        self.score = score
        self.message_identifier = message_identifier
        self.response_code = response_code

        self.post_response = post_response
        self.code_major = code_major
        self.severity = severity
        self.description = description
        self.operation = operation

        self.message_ref_identifier = message_ref_identifier

    @staticmethod
    def from_post_response(
        post_response: t.Any, content: str
    ) -> 'OutcomeResponse':
        '''
        Convenience method for creating a new OutcomeResponse from a response
        object.
        '''
        response = OutcomeResponse()
        response.post_response = post_response
        response.response_code = post_response.status
        response.process_xml(content)
        return response

    def is_success(self) -> bool:
        return self.code_major == 'success'

    def is_processing(self) -> bool:
        return self.code_major == 'processing'

    def is_failure(self) -> bool:
        return self.code_major == 'failure'

    def is_unsupported(self) -> bool:
        return self.code_major == 'unsupported'

    def has_warning(self) -> bool:
        return self.severity == 'warning'

    def has_error(self) -> bool:
        return self.severity == 'error'

    def process_xml(self, xml: str) -> None:
        '''
        Parse OutcomeResponse data form XML.
        '''
        try:
            root = t.cast(t.Mapping, objectify.fromstring(xml))
            # Get message idenifier from header info
            self.message_identifier = root['imsx_POXHeader'][
                'imsx_POXResponseHeaderInfo'
            ]['imsx_messageIdentifier']

            status_node = root['imsx_POXHeader']['imsx_POXResponseHeaderInfo'
                                                 ]['imsx_statusInfo']

            # Get status parameters from header info status
            self.code_major = status_node.imsx_codeMajor
            self.severity = status_node.imsx_severity
            self.description = status_node.imsx_description
            self.message_ref_identifier = str(
                status_node.imsx_messageRefIdentifier
            )
            self.operation = status_node.imsx_operationRefIdentifier

            try:
                # Try to get the score
                self.score = str(
                    root['imsx_POXBody']['readResultResponse']['result']
                    ['resultScore.textString']
                )
            except AttributeError:
                # Not a readResult, just ignore!
                pass
        except Exception:  # pylint: disable=broad-except
            pass

    def generate_response_xml(self) -> str:
        '''
        Generate XML based on the current configuration.
        '''
        root = etree.Element(
            'imsx_POXEnvelopeResponse',
            xmlns='http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0'
        )

        header = etree.SubElement(root, 'imsx_POXHeader')
        header_info = etree.SubElement(header, 'imsx_POXResponseHeaderInfo')
        version = etree.SubElement(header_info, 'imsx_version')
        version.text = 'V1.0'
        message_identifier = etree.SubElement(
            header_info, 'imsx_messageIdentifier'
        )
        message_identifier.text = str(self.message_identifier)
        status_info = etree.SubElement(header_info, 'imsx_statusInfo')
        code_major = etree.SubElement(status_info, 'imsx_codeMajor')
        code_major.text = str(self.code_major)
        severity = etree.SubElement(status_info, 'imsx_severity')
        severity.text = str(self.severity)
        description = etree.SubElement(status_info, 'imsx_description')
        description.text = str(self.description)
        message_ref_identifier = etree.SubElement(
            status_info, 'imsx_messageRefIdentifier'
        )
        message_ref_identifier.text = str(self.message_ref_identifier)
        operation_ref_identifier = etree.SubElement(
            status_info, 'imsx_operationRefIdentifier'
        )
        operation_ref_identifier.text = str(self.operation)

        body = etree.SubElement(root, 'imsx_POXBody')
        response = etree.SubElement(
            body, '%s%s' % (self.operation, 'Response')
        )

        if self.score:
            result = etree.SubElement(response, 'result')
            result_score = etree.SubElement(result, 'resultScore')
            language = etree.SubElement(result_score, 'language')
            language.text = 'en'
            text_string = etree.SubElement(result_score, 'textString')
            text_string.text = str(self.score)

        return '<?xml version="1.0" encoding="UTF-8"?>{}'.format(
            etree.tostring(root)
        )

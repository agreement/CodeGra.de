# This file contains large pieces of code from this github repository:
# https://github.com/ucfopen/lti-template-flask-oauth-tokens

import datetime
import traceback
from collections import defaultdict

import flask
import oauth2
import dateutil
from lxml import etree, objectify
from flask_login import login_user, login_fresh, current_user

import psef.models as models
from psef import LTI_ROLE_LOOKUPS, db, app
from psef.auth import ensure_valid_oauth


class LTI:
    # TODO support more than just flask
    def __init__(self, req):
        self.launch_params = req.form.copy()
        self.lti_provider = models.LTIProvider.query.filter_by(
            key=self.launch_params['oauth_consumer_key']).first()
        if self.lti_provider is None:
            self.lti_provider = models.LTIProvider(
                key=self.launch_params['oauth_consumer_key'])
            db.session.add(self.lti_provider)

        self.key = self.lti_provider.key
        self.secret = self.lti_provider.secret

        ensure_valid_oauth(self.key, self.secret, req)

    @property
    def user_id(self):
        return self.launch_params['user_id']

    @property
    def user_email(self):
        return self.launch_params['lis_person_contact_email_primary']

    @property
    def user_name(self):
        return self.launch_params['lis_person_name_full']

    @property
    def course_id(self):
        return self.launch_params['context_id']

    @property
    def course_name(self):
        return self.launch_params['context_title']

    def ensure_lti_user(self):
        is_logged_in = login_fresh() and current_user.is_authenticated
        if is_logged_in and current_user.lti_user_id == self.user_id:
            # The currently logged in user is now using LTI
            return current_user

        lti_user = models.User.query.filter_by(
            lti_user_id=self.user_id).first()

        if lti_user is not None:
            # LTI users are used before the current logged user.
            login_user(lti_user)
            return lti_user
        elif is_logged_in and current_user.lti_user_id is None:
            # TODO show some sort of screen if this coupling is wanted
            current_user.lti_user_id = self.user_id
            return current_user
        else:
            # New LTI user id is found and no user is logged in or the current
            # user has a different LTI user id. A new user is created and
            # logged in.
            user = models.User(
                lti_user_id=self.user_id,
                name=self.user_name,
                email=self.user_email,
                active=True,
                password=None)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return user

    def get_course(self):
        course = models.Course.query.filter_by(
            lti_course_id=self.course_id).first()
        if course is None:
            course = models.Course(
                name=self.course_name, lti_course_id=self.course_id)
            db.session.add(course)
        elif course.lti_provider is None:
            course.ensure_default_roles()

        course.lti_provider = self.lti_provider
        db.session.commit()

        return course

    def get_assignment(self):
        assignment = models.Assignment.query.filter_by(
            lti_assignment_id=self.assignment_id).first()
        if assignment is None:
            course = self.get_course()
            assignment = models.Assignment(
                name=self.assignment_name,
                state=self.assignment_state,
                course_id=course.id,
                deadline=self.assignment_deadline,
                lti_assignment_id=self.assignment_id,
                description='')
            db.session.add(assignment)

        if self.has_result_sourcedid():
            if assignment.id in current_user.assignment_results:
                current_user.assignment_results[
                    assignment.id].sourcedid = self.result_sourcedid
            else:
                assig_res = models.AssignmentResult(
                    sourcedid=self.result_sourcedid,
                    user_id=current_user.id,
                    assignment_id=assignment.id)
                db.session.add(assig_res)

        assignment.lti_outcome_service_url = self.outcome_service_url
        assignment.state = self.assignment_state

        db.session.commit()

        return assignment

    def set_user_role(self, user):
        if user.role is None:
            for role in self.roles:
                if role not in LTI_ROLE_LOOKUPS:
                    continue
                role_lookup = LTI_ROLE_LOOKUPS[role]
                if role_lookup['course_role']:
                    continue
                user.role = models.Role.query.filter_by(
                    name=role_lookup['role']).one()
                return
            user.role = models.Role.query.filter_by(
                name=app.config['DEFAULT_ROLE']).one()

    def set_user_course_role(self, user, course):
        if course.id not in user.courses:
            for role in self.roles:
                role_lookup = LTI_ROLE_LOOKUPS[role]
                if not role_lookup['course_role']:
                    continue
                crole = models.CourseRole.query.filter_by(
                    course_id=course.id, name=role_lookup['role']).one()
                user.courses[course.id] = crole
                return
            raise ValueError('Got an unkown or no course roles')

    def has_result_sourcedid(self):
        return False

    @staticmethod
    def generate_xml():
        raise NotImplementedError()

    @staticmethod
    def passback_grade(key,
                       secret,
                       grade,
                       service_url,
                       sourcedid,
                       text=None,
                       url=None):
        req = OutcomeRequest(opts={
            'consumer_key': key,
            'consumer_secret': secret,
            'lis_outcome_service_url': service_url,
            'lis_result_sourcedid': sourcedid,
        })
        opts = None
        if text is not None and url is not None:
            raise ValueError('Only text or url can be passed, not both')
        elif text is not None:
            opts = {'text': text}
        elif url is not None:
            opts = {'url': url}
        return req.post_replace_result(str(grade), result_data=opts)


class CanvasLTI(LTI):
    def __init__(self, *args, **kwargs):
        super(CanvasLTI, self).__init__(*args, **kwargs)

    @property
    def course_name(self):
        return self.launch_params['custom_canvas_course_name']

    @property
    def course_id(self):
        return self.launch_params['custom_canvas_course_id']

    @property
    def assignment_id(self):
        return self.launch_params['custom_canvas_assignment_id']

    @property
    def assignment_name(self):
        return self.launch_params['custom_canvas_assignment_title']

    @property
    def outcome_service_url(self):
        return self.launch_params['lis_outcome_service_url']

    @property
    def result_sourcedid(self):
        return self.launch_params['lis_result_sourcedid']

    def has_result_sourcedid(self):
        return 'lis_result_sourcedid' in self.launch_params

    @property
    def assignment_deadline(self):
        try:
            return dateutil.parser.parse(
                self.launch_params['custom_canvas_assignment_due_at'])
        except:
            return datetime.datetime.utcnow() + datetime.timedelta(days=365)

    @property
    def assignment_state(self):
        if self.launch_params['custom_canvas_assignment_published'] == 'true':
            return models._AssignmentStateEnum.open
        else:
            return models._AssignmentStateEnum.hidden

    @property
    def roles(self):
        for role in self.launch_params['roles'].split(','):
            yield role.split('/')[-1].lower()


@app.route('/lti/launch', methods=['POST'])
def launch_lti():
    lti = CanvasLTI(flask.request)
    user = lti.ensure_lti_user()
    course = lti.get_course()
    assig = lti.get_assignment()
    lti.set_user_role(user)
    lti.set_user_course_role(user, course)
    db.session.commit()
    return flask.redirect(
        '{}/courses/{}/assignments/{}/submissions?lti=true'.format(
            app.config['EXTERNAL_URL'], course.id, assig.id))


# This part is largely copied from https://github.com/tophatmonocle/ims_lti_py

REPLACE_REQUEST = 'replaceResult'
DELETE_REQUEST = 'deleteResult'
READ_REQUEST = 'readResult'

accessors = [
    'operation', 'score', 'result_data', 'outcome_response',
    'message_identifier', 'lis_outcome_service_url', 'lis_result_sourcedid',
    'consumer_key', 'consumer_secret', 'post_request'
]


class OutcomeRequest():
    '''
    Class for consuming & generating LTI Outcome Requests.

    Outcome Request documentation:
        http://www.imsglobal.org/LTI/v1p1/ltiIMGv1p1.html#_Toc319560472

    This class can be used both by Tool Providers and Tool Consumers, though
    they each use it differently. The TP will use it to POST an OAuth-signed
    request to the TC. A TC will use it to parse such a request from a TP.
    '''

    def __init__(self, opts=defaultdict(lambda: None)):
        # Initialize all our accessors to None
        for accessor in accessors:
            setattr(self, accessor, None)

        # Store specified options in our accessors
        for key, val in opts.items():
            setattr(self, key, val)

    @staticmethod
    def from_post_request(post_request):
        '''
        Convenience method for creating a new OutcomeRequest from a request
        object.

        post_request is assumed to be a Django HttpRequest object
        '''
        request = OutcomeRequest()
        request.post_request = post_request
        request.process_xml(post_request.data)
        return request

    def post_replace_result(self, score, result_data=None):
        '''
        POSTs the given score to the Tool Consumer with a replaceResult.

        OPTIONAL:
            result_data must be a dictionary
            Note: ONLY ONE of these values can be in the dict at a time,
            due to the Canvas specification.

            'text' : str text
            'url' : str url
        '''
        self.operation = REPLACE_REQUEST
        self.score = score
        self.result_data = result_data
        if result_data is not None:
            if len(result_data) > 1:
                error_msg = (
                    'Dictionary result_data can only have one entry. '
                    '{0} entries were found.'.format(len(result_data)))
                raise ValueError(error_msg)
            elif 'text' not in result_data and 'url' not in result_data:
                error_msg = ('Dictionary result_data can only have the key '
                             '"text" or the key "url".')
                raise ValueError(error_msg)
            else:
                return self.post_outcome_request()
        else:
            return self.post_outcome_request()

    def post_delete_result(self):
        '''
        POSTs a deleteRequest to the Tool Consumer.
        '''
        self.operation = DELETE_REQUEST
        return self.post_outcome_request()

    def post_read_result(self):
        '''
        POSTS a readResult to the Tool Consumer.
        '''
        self.operation = READ_REQUEST
        return self.post_outcome_request()

    def is_replace_request(self):
        '''
        Check whether this request is a replaceResult request.
        '''
        return self.operation == REPLACE_REQUEST

    def is_delete_request(self):
        '''
        Check whether this request is a deleteResult request.
        '''
        return self.operation == DELETE_REQUEST

    def is_read_request(self):
        '''
        Check whether this request is a readResult request.
        '''
        return self.operation == READ_REQUEST

    def was_outcome_post_successful(self):
        return self.outcome_response and self.outcome_response.is_success()

    def post_outcome_request(self):
        '''
        POST an OAuth signed request to the Tool Consumer.
        '''
        if not self.has_required_attributes():
            raise ValueError(
                'OutcomeRequest does not have all required attributes')

        consumer = oauth2.Consumer(
            key=self.consumer_key, secret=self.consumer_secret)

        client = oauth2.Client(consumer)
        # monkey_patch_headers ensures that Authorization
        # header is NOT lower cased
        monkey_patch_headers = True
        monkey_patch_function = None
        if monkey_patch_headers:
            import httplib2
            http = httplib2.Http

            normalize = http._normalize_headers

            def my_normalize(self, headers):
                ret = normalize(self, headers)
                if 'authorization' in ret:
                    ret['Authorization'] = ret.pop('authorization')
                return ret

            http._normalize_headers = my_normalize
            monkey_patch_function = normalize

        response, content = client.request(
            self.lis_outcome_service_url,
            'POST',
            body=self.generate_request_xml(),
            headers={'Content-Type': 'application/xml'})

        if monkey_patch_headers and monkey_patch_function:
            import httplib2
            http = httplib2.Http
            http._normalize_headers = monkey_patch_function

        self.outcome_response = OutcomeResponse.from_post_response(
            response, content)
        return self.outcome_response

    def process_xml(self, xml):
        '''
        Parse Outcome Request data from XML.
        '''
        root = objectify.fromstring(xml)
        self.message_identifier = str(
            root.imsx_POXHeader.imsx_POXRequestHeaderInfo.
            imsx_messageIdentifier)
        try:
            result = root.imsx_POXBody.replaceResultRequest
            self.operation = REPLACE_REQUEST
            # Get result sourced id from resultRecord
            self.lis_result_sourcedid = result.resultRecord.\
                sourcedGUID.sourcedId
            self.score = str(result.resultRecord.result.resultScore.textString)
        except:
            pass

        try:
            result = root.imsx_POXBody.deleteResultRequest
            self.operation = DELETE_REQUEST
            # Get result sourced id from resultRecord
            self.lis_result_sourcedid = result.resultRecord.\
                sourcedGUID.sourcedId
        except:
            pass

        try:
            result = root.imsx_POXBody.readResultRequest
            self.operation = READ_REQUEST
            # Get result sourced id from resultRecord
            self.lis_result_sourcedid = result.resultRecord.\
                sourcedGUID.sourcedId
        except:
            pass

    def has_required_attributes(self):
        return self.consumer_key is not None\
            and self.consumer_secret is not None\
            and self.lis_outcome_service_url is not None\
            and self.lis_result_sourcedid is not None\
            and self.operation is not None

    def generate_request_xml(self):
        root = etree.Element(
            'imsx_POXEnvelopeRequest',
            xmlns='http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0')

        header = etree.SubElement(root, 'imsx_POXHeader')
        header_info = etree.SubElement(header, 'imsx_POXRequestHeaderInfo')
        version = etree.SubElement(header_info, 'imsx_version')
        version.text = 'V1.0'
        message_identifier = etree.SubElement(header_info,
                                              'imsx_messageIdentifier')
        message_identifier.text = self.message_identifier
        body = etree.SubElement(root, 'imsx_POXBody')
        request = etree.SubElement(body, '%s%s' % (self.operation, 'Request'))
        record = etree.SubElement(request, 'resultRecord')

        guid = etree.SubElement(record, 'sourcedGUID')

        sourcedid = etree.SubElement(guid, 'sourcedId')
        sourcedid.text = self.lis_result_sourcedid

        if self.score is not None:
            result = etree.SubElement(record, 'result')
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

        return etree.tostring(root, xml_declaration=True, encoding='utf-8')


CODE_MAJOR_CODES = ['success', 'processing', 'failure', 'unsupported']

SEVERITY_CODES = ['status', 'warning', 'error']

accessors = [
    'request_type', 'score', 'message_identifier', 'response_code',
    'post_response', 'code_major', 'severity', 'description', 'operation',
    'message_ref_identifier'
]


class OutcomeResponse():
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

    def __init__(self, **kwargs):
        # Initialize all class accessors to None
        for opt in accessors:
            setattr(self, opt, None)

        # Store specified options in our options member
        for (key, val) in kwargs.items():
            setattr(self, key, val)

    @staticmethod
    def from_post_response(post_response, content):
        '''
        Convenience method for creating a new OutcomeResponse from a response
        object.
        '''
        response = OutcomeResponse()
        response.post_response = post_response
        response.response_code = post_response.status
        response.process_xml(content)
        return response

    def is_success(self):
        return self.code_major == 'success'

    def is_processing(self):
        return self.code_major == 'processing'

    def is_failure(self):
        return self.code_major == 'failure'

    def is_unsupported(self):
        return self.code_major == 'unsupported'

    def has_warning(self):
        return self.severity == 'warning'

    def has_error(self):
        return self.severity == 'error'

    def process_xml(self, xml):
        '''
        Parse OutcomeResponse data form XML.
        '''
        try:
            root = objectify.fromstring(xml)
            # Get message idenifier from header info
            self.message_identifier = root.imsx_POXHeader.\
                imsx_POXResponseHeaderInfo.\
                imsx_messageIdentifier

            status_node = root.imsx_POXHeader.\
                imsx_POXResponseHeaderInfo.\
                imsx_statusInfo

            # Get status parameters from header info status
            self.code_major = status_node.imsx_codeMajor
            self.severity = status_node.imsx_severity
            self.description = status_node.imsx_description
            self.message_ref_identifier = str(
                status_node.imsx_messageRefIdentifier)
            self.operation = status_node.imsx_operationRefIdentifier

            try:
                # Try to get the score
                self.score = str(root.imsx_POXBody.readResultResponse.result.
                                 resultScore.textString)
            except AttributeError:
                # Not a readResult, just ignore!
                pass
        except:
            pass

    def generate_response_xml(self):
        '''
        Generate XML based on the current configuration.
        '''
        root = etree.Element(
            'imsx_POXEnvelopeResponse',
            xmlns='http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0')

        header = etree.SubElement(root, 'imsx_POXHeader')
        header_info = etree.SubElement(header, 'imsx_POXResponseHeaderInfo')
        version = etree.SubElement(header_info, 'imsx_version')
        version.text = 'V1.0'
        message_identifier = etree.SubElement(header_info,
                                              'imsx_messageIdentifier')
        message_identifier.text = str(self.message_identifier)
        status_info = etree.SubElement(header_info, 'imsx_statusInfo')
        code_major = etree.SubElement(status_info, 'imsx_codeMajor')
        code_major.text = str(self.code_major)
        severity = etree.SubElement(status_info, 'imsx_severity')
        severity.text = str(self.severity)
        description = etree.SubElement(status_info, 'imsx_description')
        description.text = str(self.description)
        message_ref_identifier = etree.SubElement(status_info,
                                                  'imsx_messageRefIdentifier')
        message_ref_identifier.text = str(self.message_ref_identifier)
        operation_ref_identifier = etree.SubElement(
            status_info, 'imsx_operationRefIdentifier')
        operation_ref_identifier.text = str(self.operation)

        body = etree.SubElement(root, 'imsx_POXBody')
        response = etree.SubElement(body, '%s%s' % (self.operation,
                                                    'Response'))

        if self.score:
            result = etree.SubElement(response, 'result')
            result_score = etree.SubElement(result, 'resultScore')
            language = etree.SubElement(result_score, 'language')
            language.text = 'en'
            text_string = etree.SubElement(result_score, 'textString')
            text_string.text = str(self.score)

        return '<?xml version="1.0" encoding="UTF-8"?>' + etree.tostring(root)

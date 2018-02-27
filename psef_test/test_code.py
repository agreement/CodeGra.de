import os
import uuid
import datetime

import pytest

import psef.models as m

perm_error = pytest.mark.perm_error
data_error = pytest.mark.data_error
late_error = pytest.mark.late_error


@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        'Student1',
        perm_error(error=401)('NOT_LOGGED_IN'),
        perm_error(error=403)('admin'),
        perm_error(error=403)('Student3'),
    ],
    indirect=True
)
@pytest.mark.parametrize('filename', ['test_flake8.tar.gz'], indirect=True)
def test_get_code_metadata(
    named_user, assignment_real_works, test_client, request, error_template,
    ta_user, logged_in
):
    assignment, work = assignment_real_works
    work_id = work['id']

    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': [{
                    'id': int,
                    'name': 'test.py'
                }],
                'id': int,
                'name': 'test_flake8'
            }
        )

    with logged_in(named_user):
        test_client.req(
            'get',
            f'/api/v1/code/{res["id"]}',
            error if error else 200,
            result=error_template if error else {
                'name': 'test_flake8',
                'is_directory': True,
                'id': int,
            },
            query={
                'type': 'metadata'
            }
        )

        test_client.req(
            'get',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            error if error else 200,
            result=error_template if error else {
                'name': 'test.py',
                'is_directory': False,
                'id': int,
            },
            query={
                'type': 'metadata'
            }
        )


@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        'Student1',
        perm_error(error=401)('NOT_LOGGED_IN'),
        perm_error(error=403)('admin'),
        perm_error(error=403)('Student3'),
    ],
    indirect=True
)
@pytest.mark.parametrize(
    'filename,content', [
        ('test_flake8.tar.gz', 'def a(b):\n\tprint ( 5 )\n'),
        data_error(error=410)(
            (
                '../test_submissions/single_symlink_archive.tar.gz',
                'SHOULD ERROR!'
            )
        ),
        data_error(error=400)(
            ('../test_submissions/nested_dir_archive.tar.gz', 'SHOULD_ERROR')
        ),
        ('../test_submissions/pdf_in_dir_archive.tar.gz', False),
    ],
    indirect=['filename']
)
def test_get_code_plaintext(
    named_user, assignment_real_works, test_client, request, error_template,
    ta_user, logged_in, content
):
    assignment, work = assignment_real_works
    work_id = work['id']

    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error')
    if perm_err:
        error = perm_err.kwargs['error']
    elif data_err:
        error = data_err.kwargs['error']
    else:
        error = False

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )

    with logged_in(named_user):
        if error:
            test_client.req(
                'get',
                f'/api/v1/code/{res["entries"][0]["id"]}',
                error,
                result=error_template,
            )
        else:
            res = test_client.get(f'/api/v1/code/{res["entries"][0]["id"]}')
            assert res.status_code == 200
            if content:
                assert res.get_data(as_text=True) == content
            else:
                with pytest.raises(UnicodeDecodeError):
                    res.get_data(as_text=True)
                res.get_data()


@pytest.mark.parametrize(
    'filename', ['../test_submissions/single_dir_archive.zip']
)
def test_get_code_plaintext_revisions(
    assignment_real_works, test_client, request, error_template, ta_user,
    student_user, logged_in
):
    assignment, work = assignment_real_works
    assignment_id = assignment.id
    work_id = work['id']

    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment_id}',
            204,
            data={'state': 'done'},
        )

        files = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
        )
        student_file_id = files['entries'][0]['id']

        res = test_client.req(
            'patch',
            f'/api/v1/code/{student_file_id}',
            200,
            real_data='test',
        )
        teacher_file_id = res['id']
        assert teacher_file_id != student_file_id

    with logged_in(student_user):
        res = test_client.get(f'/api/v1/code/{student_file_id}', )
        assert res.status_code == 200

        res = test_client.get(f'/api/v1/code/{teacher_file_id}', )
        assert res.status_code == 200

    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment_id}',
            204,
            data={'state': 'open'},
        )

    with logged_in(student_user):
        res = test_client.get(f'/api/v1/code/{student_file_id}', )
        assert res.status_code == 200

        res = test_client.get(f'/api/v1/code/{teacher_file_id}', )
        assert res.status_code == 403


@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        'Student1',
        perm_error(error=401)('NOT_LOGGED_IN'),
        perm_error(error=403)('admin'),
        perm_error(error=403)('Student3'),
    ],
    indirect=True
)
@pytest.mark.parametrize(
    'filename,mimetype', [
        ('../test_submissions/pdf_in_dir_archive.tar.gz', 'application/pdf'),
        ('../test_submissions/img_in_dir_archive.tar.gz', 'image/png'),
    ],
    indirect=['filename']
)
@pytest.mark.parametrize('query_type', ['pdf', 'file-url'])
def test_get_file_url(
    named_user, assignment_real_works, test_client, request, error_template,
    ta_user, logged_in, mimetype, query_type
):
    assignment, work = assignment_real_works
    work_id = work['id']

    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )
        file_id = res["entries"][0]["id"]

    with logged_in(named_user):
        if error:
            test_client.req(
                'get',
                f'/api/v1/code/{file_id}',
                error,
                query={'type': query_type},
                result=error_template
            )
        else:
            res = test_client.req(
                'get',
                f'/api/v1/code/{file_id}',
                200,
                query={'type': query_type},
                result={'name': str},
            )
            res = test_client.get(
                f'/api/v1/files/{res["name"]}',
                query_string={
                    'mime': mimetype
                }
            )
            assert res.status_code == 200
            assert res.headers['Content-Type'] == mimetype


@pytest.mark.parametrize(
    'filename', ['../test_submissions/multiple_dir_archive.zip'],
    indirect=True
)
def test_delete_code_as_ta(
    assignment_real_works, test_client, request, error_template, ta_user,
    logged_in, session
):
    assignment, work = assignment_real_works
    work_id = work['id']

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )
        assert len(res['entries']) == 2

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["entries"][0]["id"]}',
            403,
            result=error_template,
        )

        assignment.deadline = datetime.datetime.utcnow(
        ) - datetime.timedelta(days=1)
        session.commit()

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']
        assert len(ents) == 2, 'It should not delete after an error'

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            400,
            result=None,
        )
        for ent in res['entries'][0]['entries'][:-1]:
            test_client.req(
                'delete',
                f'/api/v1/code/{ent["id"]}',
                204,
                result=None,
            )
            test_client.req(
                'delete',
                f'/api/v1/code/{res["entries"][0]["id"]}',
                400,
                result=None,
            )
        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["entries"][-1]["id"]}',
            204,
            result=None,
        )
        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            204,
            result=None,
        )

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
        )['entries']

        assert len(ents) == 2, 'Only teacher files should be affected'

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']

        assert len(ents) == 1, 'The teacher files should have a file less'


@pytest.mark.parametrize(
    'filename', ['../test_submissions/single_dir_archive.zip'], indirect=True
)
def test_delete_code_as_student(
    assignment_real_works,
    test_client,
    request,
    error_template,
    ta_user,
    logged_in,
    session,
    student_user,
):
    assignment, work = assignment_real_works
    work_id = work['id']

    with logged_in(student_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )
        assert len(res['entries']) == 2

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            204,
            result=None,
        )

        assignment.state = m._AssignmentStateEnum.done
        session.commit()

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            403,
            result=error_template,
        )

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
        )['entries']

        assert len(ents) == 1

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']

        assert len(ents) == 2

        with logged_in(ta_user):
            test_client.req(
                'delete',
                f'/api/v1/code/{res["entries"][0]["id"]}',
                204,
                result=None,
            )

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']
        assert len(ents) == 1


@pytest.mark.parametrize(
    'filename', ['../test_submissions/single_dir_archive.zip'], indirect=True
)
def test_delete_code_twice(
    assignment_real_works, test_client, request, error_template, ta_user,
    logged_in, session
):
    assignment, work = assignment_real_works
    work_id = work['id']

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )
        assert len(res['entries']) == 2

        assignment.deadline = datetime.datetime.utcnow(
        ) - datetime.timedelta(days=1)
        session.commit()

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            204,
            result=None,
        )

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']

        assert len(ents) == 1, 'The teacher files should have a file less'

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            403,
            result=error_template,
        )

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']

        assert len(ents) == 1, 'The teacher files should have a file less'


@pytest.mark.parametrize(
    'filename', ['../test_submissions/multiple_dir_archive.zip'],
    indirect=True
)
def test_delete_code_with_comment(
    assignment_real_works, test_client, request, error_template, ta_user,
    logged_in, session
):
    assignment, work = assignment_real_works
    work_id = work['id']

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )
        assignment.deadline = datetime.datetime.utcnow() - datetime.timedelta(
            days=1,
        )
        session.commit()

        f = res['entries'][0]['entries'][0]
        print(f)
        new_f = test_client.req(
            'patch',
            f'/api/v1/code/{f["id"]}',
            200,
            query={'operation': 'content'},
            result={'name': f['name'],
                    'id': int,
                    'is_directory': False},
            real_data='WOWSERS123',
        )

        assert new_f['id'] != f['id'], 'Should have a new file'

        test_client.req(
            'put',
            f'/api/v1/code/{new_f["id"]}/comments/0',
            204,
            data={'comment': 'GOED!'},
        )

        req = test_client.get(f'/api/v1/code/{new_f["id"]}')
        assert req.status_code == 200, 'Request had no errors'
        assert req.get_data(
            as_text=True
        ) == 'WOWSERS123', 'The teacher revision was used'

        test_client.req(
            'delete',
            f'/api/v1/code/{new_f["id"]}',
            400,
            result=error_template,
        )


@pytest.mark.parametrize(
    'filename', ['../test_submissions/single_dir_archive.zip'], indirect=True
)
def test_update_code(
    assignment_real_works, test_client, request, error_template, ta_user,
    logged_in, session, student_user
):
    assignment, work = assignment_real_works
    work_id = work['id']

    def get_code_data(code_id):
        r = test_client.get(f'/api/v1/code/{code_id}')
        assert r.status_code == 200
        try:
            return r.get_data(as_text=True)
        except:
            return r.get_data()

    def adjust_code(code_id, status, data=None):
        if data is None:
            data = str(uuid.uuid4())
        with logged_in(ta_user):
            old = get_code_data(code_id)

        res = test_client.req(
            'patch',
            f'/api/v1/code/{code_id}',
            status,
            real_data=data,
            result=error_template if status >= 400 else None
        )
        if status >= 400:
            with logged_in(ta_user):
                assert get_code_data(code_id) == old
            return

        assert get_code_data(res['id']) == data
        return res['id']

    with logged_in(ta_user):
        code_id = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )['entries'][0]['id']

    with logged_in(student_user):
        assert adjust_code(code_id, 200) == code_id
        assert adjust_code(code_id, 200) == code_id

        m.Assignment.query.filter_by(id=assignment.id).update(
            {
                'state': m._AssignmentStateEnum.done
            }
        )

        adjust_code(code_id, 403)

    with logged_in(ta_user):
        old = get_code_data(code_id)
        new_id = adjust_code(code_id, 200)
        assert new_id != code_id
        # Make sure id only changes once
        assert adjust_code(new_id, 200) == new_id
        assert old == get_code_data(code_id)

        # You cannot change the student rev more than once
        adjust_code(code_id, 403)

        # Make sure you cannot upload to large strings
        adjust_code(new_id, 400, b'0' * 2 * 2 ** 20)

    # Cannot change code if state is done
    with logged_in(student_user):
        adjust_code(code_id, 403)

    m.Assignment.query.filter_by(id=assignment.id).update(
        {
            'state': m._AssignmentStateEnum.open
        }
    )
    # Cannot adjust teacher rev as student
    with logged_in(student_user):
        adjust_code(new_id, 403)

    m.Assignment.query.filter_by(id=assignment.id).update(
        {
            'state':
                m._AssignmentStateEnum.open,
            'deadline':
                datetime.datetime.utcnow() - datetime.timedelta(days=1),
        }
    )
    # Cannot change code after deadline as student
    with logged_in(student_user):
        adjust_code(code_id, 403, 'AAH_CON')

    role = m.CourseRole.query.filter_by(
        course_id=assignment.course_id, name='Student'
    ).one()
    role.set_permission(
        m.Permission.query.filter_by(name='can_upload_after_deadline').one(),
        True
    )
    session.commit()
    # CAN change code after deadline as student if you have the permission for
    # this.
    with logged_in(ta_user):
        old = get_code_data(new_id)
    with logged_in(student_user):
        adjust_code(code_id, 200)
    with logged_in(ta_user):
        assert old == get_code_data(new_id)

    # Make sure invalid utf-8 can be uploaded
    with logged_in(student_user):
        data = b'\x00' + os.urandom(12) + b'\xff'
        # Make sure we sent a string that is not valid utf-8
        with pytest.raises(UnicodeDecodeError):
            data.decode('utf-8')
        adjust_code(code_id, 200, data)
        assert data == get_code_data(code_id)


@pytest.mark.parametrize(
    'filename', ['../test_submissions/multiple_dir_archive.zip'],
    indirect=True
)
def test_rename_code(
    assignment_real_works, test_client, request, error_template, ta_user,
    logged_in, session, student_user
):
    assignment, work = assignment_real_works
    work_id = work['id']

    def get_code_data(code_id):
        with logged_in(ta_user):
            r = test_client.get(f'/api/v1/code/{code_id}')
            assert r.status_code == 200
            return r.get_data(as_text=True)

    def adjust_code(code_id, status, data=None):
        if data is None:
            data = str(uuid.uuid4())
        with logged_in(ta_user):
            old = get_code_data(code_id)

        res = test_client.req(
            'patch',
            f'/api/v1/code/{code_id}',
            status,
            real_data=data,
            result=error_template if status >= 400 else None
        )
        if status >= 400:
            assert get_code_data(code_id) == old
            return

        assert get_code_data(res['id']) == data
        return res['id']

    def create_file(path):
        return test_client.req(
            'post',
            f'/api/v1/submissions/{work_id}/files/?path={path}',
            200,
        )['id']

    def rename(code_id, new_name, status):
        if status < 400:
            test_client.req(
                'patch',
                f'/api/v1/code/{code_id}?operation=rename',
                400,
                result=error_template
            )
        res = test_client.req(
            'patch',
            f'/api/v1/code/{code_id}?operation=rename&new_path={new_name}',
            status,
            result=error_template if status >= 400 else None
        )
        if status < 400:
            return res['id']

    def get_file_tree():
        return test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/?owner=auto',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )

    with logged_in(ta_user):
        files = get_file_tree()
        assert files['name'] == 'multiple_dir_archive'
        assert len(files['entries']) == 2
        assert 'dir' == files['entries'][0]['name']
        assert 'dir2' == files['entries'][1]['name']
        old_data0 = get_code_data(files['entries'][0]['entries'][0]['id'])
        code_id = files['entries'][0]['entries'][0]['id']

    with logged_in(student_user):
        assert old_data0 == get_code_data(code_id)
        assert adjust_code(code_id, 200, 'new_data--\n') == code_id
        assert adjust_code(code_id, 200, 'new_data\n') == code_id
        assert get_code_data(code_id) == 'new_data\n'

        assert rename(
            code_id, '/multiple_dir_archive/dir///NEW_NAME///', 200
        ) == code_id
        assert 'new_data\n' == get_code_data(code_id)
        assert get_file_tree()['entries'][0]['entries'][0]['name'
                                                           ] == 'NEW_NAME'

        assert rename(
            files['entries'][0]['id'], '/multiple_dir_archive/dir3/', 200
        )
        assert 'new_data\n' == get_code_data(code_id)
        files = get_file_tree()
        assert files['entries'][1]['name'] == 'dir3'
        assert files['entries'][0]['name'] == 'dir2'
        assert len(files['entries'][1]['entries']) == 2
        assert files['entries'][1]['entries'][0]['id'] == code_id

        added_file = adjust_code(
            create_file('/multiple_dir_archive/dir3/sub_dir/file'),
            200,
            'CONTENT',
        )

        rename(files['entries'][0]['id'], '/multiple_dir_archive/dir3', 400)

        m.Assignment.query.filter_by(id=assignment.id).update(
            {
                'state': m._AssignmentStateEnum.done
            }
        )
        rename(files['entries'][0]['id'], '/multiple_dir_archive/dir3', 403)
        rename(files['entries'][0]['id'], '/multiple_dir_archive/dir4', 403)

    role = m.CourseRole.query.filter_by(
        course_id=assignment.course_id, name='Student'
    ).one()
    role.set_permission(
        m.Permission.query.filter_by(name='can_upload_after_deadline').one(),
        True
    )
    session.commit()

    with logged_in(student_user):
        added_file2 = adjust_code(
            create_file('/multiple_dir_archive/dir3/sub_dir/file2'),
            200,
            'CONTENT',
        )
        added_file3 = adjust_code(
            create_file('/multiple_dir_archive/dir3/sub_dir/file3'),
            200,
            'CONTENT',
        )

    with logged_in(ta_user):
        added_file4 = adjust_code(
            create_file('/multiple_dir_archive/dir3/sub_dir/file4'),
            200,
            'CONTENT',
        )

        files = get_file_tree()
        ff = files['entries'][1]['entries']
        assert len(ff) == 3
        assert ff[-1]['name'] == 'sub_dir'
        assert ff[-1]['entries'][0]['id'] == added_file
        assert ff[-1]['entries'][1]['id'] == added_file4
        assert len(ff[-1]['entries']) == 2
        del ff

        rename(files['entries'][1]['id'], '/multiple_dir_archive/dir4', 200)
        files = get_file_tree()

        assert len(files['entries']) == 2

        assert files['entries'][0]['name'] == 'dir2'
        assert files['entries'][1]['name'] == 'dir4'

        ff = files['entries'][1]['entries']
        assert len(ff) == 3
        assert ff[-1]['name'] == 'sub_dir'
        assert ff[-1]['entries'][0]['id'] != added_file
        assert ff[-1]['entries'][1]['id'] == added_file4
        assert len(ff[-1]['entries']) == 2
        del ff

        assert len(files['entries'][0]['entries']) == 2

    with logged_in(student_user):
        files = get_file_tree()

        assert len(files['entries']) == 2

        assert files['entries'][0]['name'] == 'dir2'
        assert files['entries'][1]['name'] == 'dir3'

        ff = files['entries'][1]['entries']
        assert len(ff) == 3
        assert ff[-1]['name'] == 'sub_dir'
        assert ff[-1]['entries'][0]['id'] == added_file
        assert ff[-1]['entries'][1]['id'] == added_file2
        assert ff[-1]['entries'][2]['id'] == added_file3
        assert len(ff[-1]['entries']) == 3
        del ff

        assert len(files['entries'][0]['entries']) == 2

    with logged_in(ta_user):
        files = get_file_tree()
        rename(
            files['entries'][0]['id'],
            '/multiple_dir_archive/dir4/sub_dir/dir', 200
        )
        files = get_file_tree()
        assert len(files['entries']) == 1
        assert len(files['entries'][0]['entries']) == 3

    with logged_in(student_user):
        files = get_file_tree()

        assert len(files['entries']) == 2

        assert files['entries'][0]['name'] == 'dir2'
        assert files['entries'][1]['name'] == 'dir3'

        ff = files['entries'][1]['entries']
        assert len(ff) == 3
        assert ff[-1]['name'] == 'sub_dir'
        assert ff[-1]['entries'][0]['id'] == added_file
        assert ff[-1]['entries'][1]['id'] == added_file2
        assert ff[-1]['entries'][2]['id'] == added_file3
        assert len(ff[-1]['entries']) == 3
        del ff

        assert len(files['entries'][0]['entries']) == 2

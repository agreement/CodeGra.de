#!/usr/bin/env python3
import os
import tempfile
import uuid

import patoolib
from flask import jsonify, make_response, request
from psef import app


@app.route("/api/v1/code/<id>")
def get_code(id):
    if id == "0":
        return jsonify({
            "lang": "python",
            "code": "def id0func0():\n\treturn 0\n\n\ndef id0func1():\n\t" +
                    "return 1",
            "feedback": {
                "0": "wtf",
            }
        })
    else:
        return jsonify({
            "lang": "c",
            "code": "void\nsome_func(void) {}\n\nvoid other_func(int x)" +
                    "{\n\treturn 2 * x;\n}",
            "feedback": {
                "1": "slechte naam voor functie",
                "3": "niet veel beter..."
            }
        })


@app.route("/api/v1/dir/<path>")
def get_dir_contents(path):
    return jsonify(dir_contents(path))


def dir_contents(path):
    return {
        "name": path,
        "entries": [
            {
                "name": "a",
                "entries": [
                    {"name": "a_1", "id": 0, },
                    {"name": "a_2", "id": 1, },
                    {
                        "name": "a_3",
                        "entries": [
                            {"name": "a_3_1", "id": 2},
                        ],
                    },
                ],
            },
            {"name": "b", "id": 3},
            {"name": "c", "id": 4},
            {"name": "d", "id": 5},
        ]
    }


@app.route("/api/v1/submission/<submission_id>")
def get_submission(submission_id):
    return jsonify({
        "title": "Assignment 1",
        "fileTree": dir_contents("abc"),
    })


@app.route("/api/v1/submission/<submission_id>/general-feedback",
           methods=['GET', 'PUT'])
def get_general_feedback(submission_id):
    if request.method == 'GET':
        if id == 0:
            return jsonify({
                "grade": 8.5,
                "feedback": "test feedback voor id nul"
            })
        else:
            return jsonify({
                "grade": 6.5,
                "feedback": "test feedback"
            })
    elif request.method == 'PUT':
        content = request.get_json()

        # Here you should connect to the database
        print(content)

        resp = make_response("grade and feedback submitted", 204)
        return resp


def random_file_path():
    "Generates a new random file path in the upload directory."
    while True:
        candidate = os.path.join(app.config['UPLOAD_DIR'], str(uuid.uuid4()))
        if os.path.exists(candidate):
            continue
        else:
            break
    return candidate


def is_archive(file):
    "Checks whether file ends with a known archive file extension."
    return file.filename.endswith(('.zip', '.tar.gz', '.tgz', '.tbz',
                                   '.tar.bz2'))


def extract(archive):
    "Extracts all files in archive with random name to uploads folder."
    tmpmode, tmparchive = tempfile.mkstemp()
    tmpdir = tempfile.mkdtemp()
    archive.save(tmparchive)
    try:
        patoolib.test_archive(tmparchive, verbosity=-1, interactive=False)
        patoolib.extract_archive(tmparchive, verbosity=-1, outdir=tmpdir,
                                 interactive=False)
        for root, _, filenames in os.walk(tmpdir):
            rel_path = os.path.relpath(root, start=tmpdir)
            for filename in filenames:
                os.rename(os.path.join(root, filename), random_file_path())
        return True
    except:
        return False


@app.route("/api/v1/works/<int:work_id>/file", methods=['POST'])
def upload_file(work_id):
    """
    Saves the files on the server if the request is valid.

    For a request to be valid there needs to be:
        - at least one file under key 'file' in the request files
        - all files must be named
    """

    # Check if a valid submission was made
    files = []
    try:
        if (request.content_length and
                request.content_length > app.config['MAX_UPLOAD_SIZE']):
            raise ValueError('Request is bigger than maximum upload size.')
        if len(request.files) == 0:
            raise KeyError
        for key in request.files:
            if not key.startswith('file'):
                raise ValueError(
                    "There was some file in the http request with key {:s}, "
                    "expected file[idx].".format(key))

            file = request.files[key]
            if file.filename == '':
                raise ValueError(
                    "The name of the file with key '{:s}' in the http request "
                    "was an empty string.".format(key))

            files.append(file)
    except KeyError as e:
        return make_response(jsonify({
            "message": "No file in HTTP request.",
            "description": "There was no file in the HTTP request.",
            "code": None
        }), 400)
    except ValueError as e:
        return make_response(jsonify({
            "message": "Invalid file in HTTP request.",
            "description": str(e),
            "code": None
        }), 400)

    # Save files under random name
    # TODO: Add entries to database
    for file in files:
        # Unpack archives
        if is_archive(file) and extract(file):
            pass
        else:
            file.save(random_file_path())

    return make_response(jsonify({
        "message": "Files were successfully uploaded",
        "description": "The files were uploaded and are stored in the uploads "
                       "folder",
        "code": None
    }), 200)



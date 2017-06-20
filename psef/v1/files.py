from flask import jsonify

import psef.models as models
from psef import db
from . import api


@api.route("/file/metadata/<int:file_id>", methods=['GET'])
def get_file_metadata(file_id):
    file = db.session.query(models.File).filter(
        models.File.id == file_id).first()

    return jsonify({"name": file.name, "extension": file.extension})


from flask.ext.sqlalchemy import SQLAlchemy
from psef import app

db = SQLAlchemy(app)



class User (db.Model):
    __tablename__ = "User"
    id = db.Column('id', db.Integer, primary_key = True)
    name = db.Column('name', db.Unicode)
    role = db.Column('role', db.Integer)

class Course (db.Model):
    __tablename__ = "Course"
    id = db.Column('id', db.Integer, primary_key = True)
    name = db.Column('name', db.Unicode)

class Work (db.Model):
    __tablename__ = "Work"
    id = db.Column('id', db.Integer, primary_key = True)
    assignment_id = db.Column('Assignment_id', db.Integer, db.ForeignKey('Assignment.id'))
    user_id = db.Column('User_id', db.Integer, db.ForeignKey('User.id'))
    state = db.Column('state', db.Integer)
    edit = db.Column('edit', db.Integer)

    assignment = db.relationship('Assignment', foreign_keys=assignment_id)
    user = db.relationship('User', foreign_keys=user_id)

class File (db.Model):
    __tablename__ = "File"
    id = db.Column('id', db.Integer, primary_key = True)
    work_id = db.Column('Work_id', db.Integer, db.ForeignKey('Work.id'))
    extension = db.Column('extension', db.Unicode)
    description = db.Column('description', db.Unicode)

    work = db.relationship('Work', foreign_keys=work_id)

class Comment (db.Model):
    __tablename__ = "Comment"
    id = db.Column('id', db.Integer, primary_key = True)
    file_id = db.Column('File_id', db.Integer, db.ForeignKey('File.id'))
    user_id = db.Column('User_id', db.Integer, db.ForeignKey('User.id'))
    line = db.Column('line', db.Integer)
    comment = db.Column('comment', db.Unicode)

    file = db.relationship('File', foreign_keys=file_id)
    user = db.relationship('User', foreign_keys=user_id)

class Assignment (db.Model):
    __tablename__ = "Assignment"
    id = db.Column('id', db.Integer, primary_key = True)
    description = db.Column('description', db.Unicode)
    course_id = db.Column('Course_id', db.Integer, db.ForeignKey('Course.id'))

    course = db.relationship('Course', foreign_keys=course_id)


from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)


class Student (db.Model):
    __tablename__ = "Student"
    id = db.Column('id', db.Integer, primary_key = True)
    name = db.Column('name', db.Unicode)

class Enrolled (db.Model):
    __tablename__ = "Enrolled"
    id = db.Column('id', db.Integer, primary_key = True)
    student_id = db.Column('Student_id', db.Integer, db.ForeignKey('Student.id'))
    course_id = db.Column('Course_id', db.Integer, db.ForeignKey('Course.id'))

    student = db.relationship('Student', foreign_keys=student_id)
    course = db.relationship('Course', foreign_keys=course_id)

class Staff (db.Model):
    __tablename__ = "Staff"
    id = db.Column('id', db.Integer, primary_key = True)
    name = db.Column('name', db.Unicode)

class Course (db.Model):
    __tablename__ = "Course"
    id = db.Column('id', db.Integer, primary_key = True)
    staff_id = db.Column('Staff_id', db.Integer, db.ForeignKey('Staff.id'))
    name = db.Column('name', db.Unicode)

    staff = db.relationship('Staff', foreign_keys=staff_id)

class Work (db.Model):
    __tablename__ = "Work"
    id = db.Column('id', db.Integer, primary_key = True)
    enrolled_id = db.Column('Enrolled_id', db.Integer, db.ForeignKey('Enrolled.id'))
    assignment_id = db.Column('Assignment_id', db.Integer, db.ForeignKey('Assignment.id'))
    state = db.Column('state', db.Integer)
    edit = db.Column('edit', db.Integer)

    enrolled = db.relationship('Enrolled', foreign_keys=enrolled_id)
    assignment = db.relationship('Assignment', foreign_keys=assignment_id)

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
    staff_id = db.Column('Staff_id', db.Integer, db.ForeignKey('Staff.id'))
    work_id = db.Column('Work_id', db.Integer, db.ForeignKey('Work.id'))
    line = db.Column('line', db.Integer)
    comment = db.Column('comment', db.Unicode)

    file = db.relationship('File', foreign_keys=file_id)
    staff = db.relationship('Staff', foreign_keys=staff_id)
    work = db.relationship('Work', foreign_keys=work_id)

class Assignment (db.Model):
    __tablename__ = "Assignment"
    id = db.Column('id', db.Integer, primary_key = True)
    description = db.Column('description', db.Unicode)

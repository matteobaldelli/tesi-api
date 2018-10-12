from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Medical(db.Model):
    __tablename__ = 'medical'

    id = db.Column(db.Integer, primary_key=True)
    metric = db.Column(db.String(255))
    value = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    visit_id = db.Column(db.Integer, db.ForeignKey('visit.id'), nullable=False)
    visit = db.relationship('Visit', backref=db.backref('medicals', lazy=True))

    def __init__(self, metric, value, visit):
        self.metric = metric
        self.value = value
        self.visit = visit

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Medical.query.all()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Visit(db.Model):
    __tablename__ = 'visit'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('visits', lazy=True))

    def __init__(self, name, user):
        self.name = name
        self.user = user

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Visit.query.all()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    def __init__(self, username):
        self.username = username

    def save(self):
        db.session.add(self)
        db.session.commit()

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

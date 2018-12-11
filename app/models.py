from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Exam(db.Model):
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    visit = db.relationship('Visit', back_populates='exams')
    metric_id = db.Column(db.Integer, db.ForeignKey('metrics.id'), nullable=False)
    metric = db.relationship('Metric', back_populates='exams')

    def __init__(self, metric, value, visit):
        self.metric = metric
        self.value = value
        self.visit = visit

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Exam.query.all()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Visit(db.Model):
    __tablename__ = 'visits'

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
    exams = db.relationship('Exam', back_populates='visit', cascade='all, delete-orphan')

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
    username = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.String(128))
    gender = db.Column(db.String(255))
    birth_date = db.Column(db.DateTime)
    admin = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    def __init__(self, username, email, gender, birth_date):
        self.username = username
        self.email = email
        self.gender = gender
        self.birth_date = birth_date

    def save(self):
        db.session.add(self)
        db.session.commit()

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_all():
        return User.query.order_by(User.username).all()


class Metric(db.Model):
    __tablename__ = 'metrics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    weight = db.Column(db.Integer)
    unit_label = db.Column(db.String(255))
    total_range_min = db.Column(db.Integer)
    total_range_max = db.Column(db.Integer)
    healthy_range_min = db.Column(db.Integer)
    healthy_range_max = db.Column(db.Integer)
    gender = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    category = db.relationship('Category', back_populates='metrics')
    exams = db.relationship('Exam', back_populates='metric', cascade='all, delete-orphan')

    def __init__(self, name, weight, unit_label, total_range_min, total_range_max, healthy_range_min,
                 healthy_range_max, gender):
        self.name = name
        self.weight = weight
        self.unit_label = unit_label
        self.total_range_min = total_range_min
        self.total_range_max = total_range_max
        self.healthy_range_min = healthy_range_min
        self.healthy_range_max = healthy_range_max
        self.gender = gender

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Metric.query.all()


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    metrics = db.relationship('Metric', back_populates='category', cascade='save-update')

    def __init__(self, name):
        self.name = name

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Category.query.all()

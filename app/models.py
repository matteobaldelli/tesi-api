from app import db


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

    # def __repr__(self):
    #     return "<Medical: {}>".format(self.name)


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

    def __init__(self, name):
        self.name = name

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Visit.query.all()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

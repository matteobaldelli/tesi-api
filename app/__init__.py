import datetime

import jwt
from jwt import DecodeError, ExpiredSignatureError
from six import wraps

from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy
from flask import request, jsonify, abort
from flask_cors import CORS
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func


from werkzeug.exceptions import BadRequest

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# local import
from instance.config import app_config

db = SQLAlchemy()


def create_app(config_name):
    from app.models import Exam, Visit, User, Metric, Category

    sentry_sdk.init(
        dsn=app_config[config_name].SENTRY_URL,
        integrations=[FlaskIntegration()]
    )

    app = FlaskAPI(__name__, instance_relative_config=True)
    cors = CORS(app, resources={r"/*": {"origins": "*"}})
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):

            if 'Authorization' not in request.headers:
                return jsonify({'message': 'Token is missing!'}), 401

            token = request.headers['Authorization']

            try:
                data = jwt.decode(token, app.config['SECRET'])
                current_user = User.query.filter_by(id=data['id']).first()
            except DecodeError:
                return jsonify({'message': 'Token is invalid!'}), 401
            except NoResultFound:
                return jsonify({'message': 'Token is invalid!'}), 401
            except ExpiredSignatureError:
                return jsonify({'message': 'Token is invalid!'}), 401

            return f(current_user, *args, **kwargs)

        return decorated

    @app.route('/exams', methods=['POST', 'GET'])
    @token_required
    def exam(user):
        if request.method == 'POST':
            try:
                metric_id = request.data['metricId']
                visit_id = request.data['visitId']
                value = request.data['value']
            except KeyError:
                return {}, 400

            metric = Metric.query.filter_by(id=metric_id)
            visit = Visit.query.filter_by(id=visit_id)

            if not user.admin:
                metric = metric.filter_by(gender=user.gender)
                visit = visit.filter_by(user=user)

            metric = metric.first()
            visit = visit.first()
            if visit is None or metric is None:
                return {}, 400

            exam = Exam(value=value, metric=metric, visit=visit)
            exam.save()
            visit.date_modified = exam.date_modified
            visit.save()
            response = jsonify({
                'id': exam.id,
                'value': exam.value,
                'dateCreated': exam.date_created,
                'dateModified': exam.date_modified,
                'visitId': exam.visit.id,
                'metricId': exam.metric.id,
                'metricName': exam.metric.name
            })
            response.status_code = 201
            return response
        else:
            try:
                visit_id = request.values['visitId']
            except KeyError:
                if user.admin:
                    exams = Exam.get_all()
                else:
                    visit_ids = Visit.query.filter_by(user=user).with_entities(Visit.id)
                    exams = Exam.query.filter(Exam.visit_id.in_(visit_ids))
            else:
                visit = Visit.query.filter_by(id=visit_id)
                if not user.admin:
                    visit = visit.filter_by(user=user)
                visit = visit.first()
                exams = Exam.query.filter_by(visit=visit).order_by(Exam.metric_id)
            results = []
            for exam in exams:
                obj = {
                    'id': exam.id,
                    'value': exam.value,
                    'dateCreated': exam.date_created,
                    'dateModified': exam.date_modified,
                    'visitId': exam.visit.id,
                    'metricId': exam.metric.id,
                    'metricName': exam.metric.name
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/exams/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    @token_required
    def exam_details(user, id, **kwargs):
        if user.admin:
            exam = Exam.query.get_or_404(id)
        else:
            visit_ids = Visit.query.filter_by(user=user).with_entities(Visit.id)
            exam = Exam.query.filter(Exam.visit_id.in_(visit_ids)).filter_by(id=id,).first()
            if not exam:
                abort(404)

        if request.method == 'DELETE':
            visit = exam.visit
            visit.date_modified = datetime.datetime.now()
            visit.save()
            exam.delete()
            return {
                       "message": "exam {} deleted successfully".format(exam.id)
                   }, 200

        elif request.method == 'PUT':
            exam.value = request.data.get('value', exam.value)
            # No control for authorization
            # metric_id = request.data.get('metricId', exam.metric.id)
            # visit_id = request.data.get('visitId', exam.visit.id)
            # exam.metric = Metric.query.get(metric_id)
            # exam.visit = Visit.query.get(visit_id)
            exam.save()
            response = jsonify({
                'id': exam.id,
                'value': exam.value,
                'dateCreated': exam.date_created,
                'dateModified': exam.date_modified,
                'metricId': exam.metric.id,
                'visitId': exam.visit.id
            })
            visit = exam.visit
            visit.date_modified = exam.date_modified
            visit.save()
            response.status_code = 200
            return response
        else:
            # GET
            response = jsonify({
                'id': exam.id,
                'value': exam.value,
                'dateCreated': exam.date_created,
                'dateModified': exam.date_modified,
                'metricId': exam.metric.id,
                'visitId': exam.visit.id
            })
            response.status_code = 200
            return response

    @app.route('/exams/statistics', methods=['GET'])
    @token_required
    def exam_statistics(user):
        if user.admin:
            visit_id = request.args.getlist('visits[]', type=int)
            if not len(visit_id):
                params = request.values.to_dict()
                gender = params.pop('gender')
                filter_age = params.pop('age').split(',')
                visits = Visit.get_all()
                visit_id = []
                for visit in visits:
                    age = (datetime.datetime.now() - visit.user.birth_date).days // 365.2425
                    if visit.user.gender != gender:
                        continue
                    if age < int(filter_age[0]) or age > int(filter_age[1]):
                        continue

                    exams = visit.exams
                    good_visit = True
                    for key, value in params.items():
                        values = value.split(',')
                        for exam in exams:
                            if exam.metric.name == key:
                                if exam.value < int(values[0]) or exam.value > int(values[1]):
                                    good_visit = False
                                    break
                    if good_visit:
                        visit_id.append(visit.id)
                    if not params:
                        visit_id.append(visit.id)
        else:
            visit_id = []
            visits = Visit.query.filter_by(user=user)
            for visit in visits:
                visit_id.append(visit.id)

        avgs = Exam.query.with_entities(
            Exam.metric_id, func.avg(Exam.value).label('avg')
        ).filter(Exam.visit_id.in_(visit_id)).group_by(Exam.metric_id).all()

        results = []
        for avg in avgs:
            metric = Metric.query.filter_by(id=avg[0]).first()
            obj = {
                'metricName': metric.name,
                'value': int(avg[1])
            }
            results.append(obj)
        response = jsonify(results)
        response.status_code = 200
        return response

    @app.route('/visits', methods=['POST', 'GET'])
    @token_required
    def visit(user):
        if request.method == 'POST':
            try:
                name = str(request.data['name'])
            except KeyError:
                return {}, 400

            visit = Visit(
                name=name,
                user=user
            )
            visit.save()
            response = jsonify({
                'id': visit.id,
                'name': visit.name,
                'dateCreated': visit.date_created,
                'dateModified': visit.date_modified,
                'userUsername': visit.user.username
            })
            response.status_code = 201
            return response
        else:
            if user.admin:
                filter_user = request.values.get('user')
                if filter_user is None:
                    visits = Visit.query.filter_by()
                else:
                    visits = Visit.query.filter_by(user_id=filter_user)
            else:
                visits = Visit.query.filter_by(user=user)

            visits = visits.order_by(Visit.date_created)
            results = []
            for visit in visits:
                obj = {
                    'id': visit.id,
                    'name': visit.name,
                    'dateCreated': visit.date_created,
                    'dateModified': visit.date_modified,
                    'userUsername': visit.user.username,
                    'userGender': visit.user.gender
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/visits/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    @token_required
    def visit_details(user, id, **kwargs):
        visit = Visit.query.filter_by(id=id)
        if not user.admin:
            visit = visit.filter_by(user=user)
        visit = visit.first()
        if not visit:
            return {}, 404

        if request.method == 'DELETE':
            visit.delete()
            return {
                       "message": "visit {} deleted successfully".format(visit.id)
                   }, 200

        elif request.method == 'PUT':
            visit.name = str(request.data.get('name', visit.name))
            visit.save()
            response = jsonify({
                'id': visit.id,
                'name': visit.name,
                'dateCreated': visit.date_created,
                'dateModified': visit.date_modified,
                'userUsername': visit.user.username,
                'userGender': visit.user.gender
            })
            response.status_code = 200
            return response
        else:
            # GET
            response = jsonify({
                'id': visit.id,
                'name': visit.name,
                'dateCreated': visit.date_created,
                'dateModified': visit.date_modified,
                'userUsername': visit.user.username,
                'userGender': visit.user.gender
            })
            response.status_code = 200
            return response

    @app.route('/visits/exams', methods=['POST', 'GET'])
    @token_required
    def exam_group(user):
        if not user.admin:
            return {}, 403
        user_id = request.values.get('userId', user.id)
        visits = Visit.query.filter_by(user_id=user_id).order_by(Visit.date_modified)

        results = []
        for visit in visits:
            result = {
                'id': visit.id,
                'name': visit.name,
                'dateCreated': visit.date_created,
                'dateModified': visit.date_modified,
                'userUsername': visit.user.username,
                'userGender': visit.user.gender,
                'exams': []
            }
            for exam in visit.exams:
                obj = {
                    'id': exam.id,
                    'value': exam.value,
                    'dateCreated': exam.date_created,
                    'dateModified': exam.date_modified,
                    'visitId': exam.visit.id,
                    'metricId': exam.metric.id,
                    'metricName': exam.metric.name
                }
                result['exams'].append(obj)
            results.append(result)
        response = jsonify(results)
        response.status_code = 200
        return response

    @app.route('/metrics', methods=['POST', 'GET'])
    @token_required
    def metric(user):
        if request.method == 'POST':
            if not user.admin:
                return {}, 403
            category_id = request.data.get('categoryId', None)

            metric = Metric(
                name=str(request.data['name']),
                weight=request.data['weight'],
                unit_label=str(request.data['unitLabel']),
                total_range_min=request.data['totalRangeMin'],
                total_range_max=request.data['totalRangeMax'],
                healthy_range_min=request.data['healthyRangeMin'],
                healthy_range_max=request.data['healthyRangeMax'],
                gender=str(request.data['gender']),
            )
            try:
                category = Category.query.get(category_id)
                metric.category = category
            except:
                db.session.rollback()
            metric.save()
            response = jsonify({
                'id': metric.id,
                'name': metric.name,
                'weight': metric.weight,
                'unitLabel': metric.unit_label,
                'totalRangeMin': metric.total_range_min,
                'totalRangeMax': metric.total_range_max,
                'healthyRangeMin': metric.healthy_range_min,
                'healthyRangeMax': metric.healthy_range_max,
                'gender': metric.gender,
                'categoryId': None if metric.category is None else metric.category.id,
                'categoryName': None if metric.category is None else metric.category.name
            })
            response.status_code = 201
            return response
        else:
            gender = request.values.get('gender', None)
            if gender is None:
                metrics = Metric.get_all()
            else:
                metrics = Metric.query.filter_by(gender=gender)
            results = []

            for metric in metrics:
                obj = {
                    'id': metric.id,
                    'name': metric.name,
                    'weight': metric.weight,
                    'unitLabel': metric.unit_label,
                    'totalRangeMin': metric.total_range_min,
                    'totalRangeMax': metric.total_range_max,
                    'healthyRangeMin': metric.healthy_range_min,
                    'healthyRangeMax': metric.healthy_range_max,
                    'gender': metric.gender,
                    'categoryId': None if metric.category is None else metric.category.id,
                    'categoryName': None if metric.category is None else metric.category.name
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/metrics/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    @token_required
    def metric_details(user, id, **kwargs):
        if not user.admin:
            return {}, 403
        metric = Metric.query.get_or_404(id)

        if request.method == 'DELETE':
            metric.delete()
            return {
                       "message": "metric {} deleted successfully".format(metric.id)
                   }, 200

        elif request.method == 'PUT':
            metric.name = str(request.data.get('name', metric.name))
            metric.weight = request.data.get('weight', metric.weight)
            metric.unit_label = str(request.data.get('unitLabel', metric.unit_label))
            metric.total_range_min = request.data.get('totalRangeMin', metric.total_range_min)
            metric.total_range_max = request.data.get('totalRangeMax', metric.total_range_max)
            metric.healthy_range_min = request.data.get('healthyRangeMin', metric.healthy_range_min)
            metric.healthy_range_max = request.data.get('healthyRangeMax', metric.healthy_range_max)
            metric.gender = request.data.get('gender', metric.gender)
            metric.save()
            response = jsonify({
                'id': metric.id,
                'name': metric.name,
                'weight': metric.weight,
                'unitLabel': metric.unit_label,
                'totalRangeMin': metric.total_range_min,
                'totalRangeMax': metric.total_range_max,
                'healthyRangeMin': metric.healthy_range_min,
                'healthyRangeMax': metric.healthy_range_max,
                'gender': metric.gender,
                'categoryId': None if metric.category is None else metric.category.id,
                'categoryName': None if metric.category is None else metric.category.name
            })
            response.status_code = 200
            return response
        else:
            response = jsonify({
                'id': metric.id,
                'name': metric.name,
                'weight': metric.weight,
                'unitLabel': metric.unit_label,
                'totalRangeMin': metric.total_range_min,
                'totalRangeMax': metric.total_range_max,
                'healthyRangeMin': metric.healthy_range_min,
                'healthyRangeMax': metric.healthy_range_max,
                'gender': metric.gender,
                'categoryId': None if metric.category is None else metric.category.id,
                'categoryName': None if metric.category is None else metric.category.name
            })
            response.status_code = 200
            return response

    @app.route('/metrics/data', methods=['GET'])
    @token_required
    def metric_data(user):
        results = []
        gender = request.values.get('gender', user.gender)
        categories = Category.get_all()
        for category in categories:
            obj_category = {
                'name': category.name,
                'details': []
            }
            for metric in category.metrics:
                if metric.gender == gender:
                    obj = {
                        'name': metric.name,
                        'weight': metric.weight,
                        'unit_label': metric.unit_label,
                        'features': {
                            'totalrange': [
                                metric.total_range_min,
                                metric.total_range_max
                            ],
                            'healthyrange': [
                                metric.healthy_range_min,
                                metric.healthy_range_max
                            ]
                        }
                    }
                    obj_category['details'].append(obj)
            if obj_category['details']:
                results.append(obj_category)

        metrics = Metric.query.filter_by(gender=gender, category=None)

        for metric in metrics:
            obj = {
                'name': metric.name,
                'weight': metric.weight,
                'unit_label': metric.unit_label,
                'features': {
                    'totalrange': [
                        metric.total_range_min,
                        metric.total_range_max
                    ],
                    'healthyrange': [
                        metric.healthy_range_min,
                        metric.healthy_range_max
                    ]
                }
            }
            results.append(obj)

        response = jsonify(results)
        response.status_code = 200
        return response

    @app.route('/categories', methods=['POST', 'GET'])
    @token_required
    def category(user):
        if not user.admin:
            return {}, 403
        if request.method == 'POST':
            try:
                name = str(request.data['name'])
            except KeyError:
                return {}, 400

            category = Category(name=name)
            category.save()
            response = jsonify({
                'id': category.id,
                'name': category.name
            })
            response.status_code = 201
            return response
        else:
            categories = Category.get_all()
            results = []

            for category in categories:
                obj = {
                    'id': category.id,
                    'name': category.name
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/categories/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    @token_required
    def category_details(user, id, **kwargs):
        if not user.admin:
            return {}, 403
        category = Category.query.get_or_404(id)

        if request.method == 'DELETE':
            category.delete()
            return {
                       "message": "category {} deleted successfully".format(category.id)
                   }, 200

        elif request.method == 'PUT':
            category.name = str(request.data.get('name', category.name))
            category.save()
            response = jsonify({
                'id': category.id,
                'name': category.name
            })
            response.status_code = 200
            return response
        else:
            response = jsonify({
                'id': category.id,
                'name': category.name,
            })
            response.status_code = 200
            return response

    @app.route('/users', methods=['POST', 'GET'])
    def user():
        if request.method == 'POST':
            try:
                username = request.json['username']
                email = request.json['email']
                password = request.json['password']
                gender = request.json['gender']
                birth_date = request.json['birthDate']
            except BadRequest:
                return {}, 400

            username = username.lower()
            email = email.lower()

            if User.query.filter_by(username=username).first() is not None:
                return {}, 400
            if User.query.filter_by(email=email).first() is not None:
                return {}, 400
            user = User(username=username, gender=gender, birth_date=birth_date, email=email)
            user.hash_password(password)
            user.save()
            return jsonify({
                'username': user.username,
                'email': user.email,
                'gender': user.gender,
                'birthDate': user.birth_date,
                'dateCreated': user.date_created,
                'dateModified': user.date_modified
            }), 201
        else:
            users = User.get_all()
            results = []

            for user in users:
                obj = {
                    'id': user.id,
                    'username': user.username,
                    'gender': user.gender,
                    'birthDate': user.birth_date,
                    'dateCreated': user.date_created
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/login', methods=['POST'])
    def login():
        try:
            username = request.json['username']
            password = request.json['password']
        except BadRequest:
            return {}, 400

        user = User.query.filter_by(username=username.lower()).first()

        if not user:
            return {}, 400

        if user.check_password(password):
            token = jwt.encode(
                payload={
                    'id': user.id,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
                    'admin': user.admin
                },
                key=app.config['SECRET']
            )

            return jsonify({'access_token': token.decode('UTF-8')})

        return {}, 403

    return app


import datetime
import jwt
from jwt import DecodeError, ExpiredSignatureError
from six import wraps

from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy
from flask import request, jsonify, abort
from flask_cors import CORS
from sqlalchemy.orm.exc import NoResultFound

from werkzeug.exceptions import BadRequest

# local import
from instance.config import app_config

db = SQLAlchemy()


def create_app(config_name):
    from app.models import Exam, Visit, User, Metric, Category

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
            exam = Exam(
                value=request.data.get('value', 0),
                metric=Metric.query.filter_by(id=request.data['metricId']).first(),
                visit=Visit.query.filter_by(id=request.data['visitId']).first()
            )
            exam.save()
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
            # GET
            exams = Exam.query.filter_by(visit_id=request.values.get('visitId', ''))

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
    def exam_details(id, **kwargs):
        exam = Exam.query.filter_by(id=id).first()
        if not exam:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        if request.method == 'DELETE':
            exam.delete()
            return {
                       "message": "exam {} deleted successfully".format(exam.id)
                   }, 200

        elif request.method == 'PUT':
            exam.value = request.data.get('value', exam.value)
            exam.metric = Metric.query.filter_by(id=request.data.get('metricId', exam.metric.id)).first()
            exam.visit = Visit.query.filter_by(id=request.data.get('visitId', exam.visit.id)).first()
            exam.save()
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

    @app.route('/visits', methods=['POST', 'GET'])
    @token_required
    def visit(user):
        if request.method == 'POST':
            visit = Visit(
                name=str(request.data.get('name', 'visit')),
                user=user
            )
            visit.save()
            response = jsonify({
                'id': visit.id,
                'name': visit.name,
                'dateCreated': visit.date_created,
                'dateModified': visit.date_modified
            })
            response.status_code = 201
            return response
        else:
            # GET
            visits = Visit.query.filter_by(user=user)
            results = []

            for visit in visits:
                obj = {
                    'id': visit.id,
                    'name': visit.name,
                    'dateCreated': visit.date_created,
                    'dateModified': visit.date_modified
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/visits/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def visit_details(id, **kwargs):
        visit = Visit.query.filter_by(id=id).first()
        if not visit:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

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
                'dateModified': visit.date_modified
            })
            response.status_code = 200
            return response
        else:
            # GET
            response = jsonify({
                'id': visit.id,
                'name': visit.name,
                'dateCreated': visit.date_created,
                'dateModified': visit.date_modified
            })
            response.status_code = 200
            return response

    @app.route('/metrics', methods=['POST', 'GET'])
    @token_required
    def metric(user):
        if request.method == 'POST':
            category_id = request.data.get('category_id', None)

            metric = Metric(
                name=str(request.data['name']),
                weight=request.data['weight'],
                unit_label=str(request.data['unit_label']),
                total_range_min=request.data['total_range_min'],
                total_range_max=request.data['total_range_max'],
                healthy_range_min=request.data['healthy_range_min'],
                healthy_range_max=request.data['healthy_range_max'],
                gender=str(request.data['gender']),
            )
            try:
                category = Category.query.filter_by(id=category_id).first()
                metric.category = category
            except:
                db.session.rollback()
            metric.save()
            response = jsonify({
                'id': metric.id,
                'name': metric.name,
                'weight': metric.weight,
                'unit_label': metric.unit_label,
                'total_range_min': metric.total_range_min,
                'total_range_max': metric.total_range_max,
                'healthy_range_min': metric.healthy_range_min,
                'healthy_range_max': metric.healthy_range_max,
                'gender': metric.gender,
                'category_id': None if metric.category is None else metric.category.id
            })
            response.status_code = 201
            return response
        else:
            # GET
            metrics = Metric.get_all()
            results = []

            for metric in metrics:
                obj = {
                    'id': metric.id,
                    'name': metric.name,
                    'weight': metric.weight,
                    'unit_label': metric.unit_label,
                    'total_range_min': metric.total_range_min,
                    'total_range_max': metric.total_range_max,
                    'healthy_range_min': metric.healthy_range_min,
                    'healthy_range_max': metric.healthy_range_max,
                    'gender': metric.gender,
                    'category_id': None if metric.category is None else metric.category.id
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/metrics/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def metric_details(id, **kwargs):
        metric = Metric.query.filter_by(id=id).first()
        if not metric:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        if request.method == 'DELETE':
            metric.delete()
            return {
                       "message": "metric {} deleted successfully".format(metric.id)
                   }, 200

        elif request.method == 'PUT':
            metric.name = str(request.data.get('name', metric.name))
            metric.weight = request.data.get('weight', metric.weight)
            metric.unit_label = str(request.data.get('unit_label', metric.unit_label))
            metric.total_range_min = request.data.get('total_range_min', metric.total_range_min)
            metric.total_range_max = request.data.get('total_range_min', metric.total_range_max)
            metric.healthy_range_min = request.data.get('healthy_range_min', metric.healthy_range_min)
            metric.healthy_range_max = request.data.get('healthy_range_max', metric.healthy_range_max)
            metric.gender = request.data.get('gender', metric.gender)
            metric.save()
            response = jsonify({
                'id': metric.id,
                'name': metric.name,
                'weight': metric.weight,
                'unit_label': metric.unit_label,
                'total_range_min': metric.total_range_min,
                'total_range_max': metric.total_range_max,
                'healthy_range_min': metric.healthy_range_min,
                'healthy_range_max': metric.healthy_range_max,
                'gender': metric.gender,
                'category_id': None if metric.category is None else metric.category.id
            })
            response.status_code = 200
            return response
        else:
            # GET
            response = jsonify({
                'id': metric.id,
                'name': metric.name,
                'weight': metric.weight,
                'unit_label': metric.unit_label,
                'total_range_min': metric.total_range_min,
                'total_range_max': metric.total_range_max,
                'healthy_range_min': metric.healthy_range_min,
                'healthy_range_max': metric.healthy_range_max,
                'gender': metric.gender,
                'category_id': None if metric.category is None else metric.category.id
            })
            response.status_code = 200
            return response

    @app.route('/metrics/data', methods=['GET'])
    @token_required
    def metric_data(user):
        results = []
        categories = Category.get_all()
        for category in categories:
            obj_category = {
                'name': category.name,
                'details': []
            }
            for metric in category.metrics:
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
            results.append(obj_category)

        metrics = Metric.query.filter_by(gender=user.gender, category=None)

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
        if request.method == 'POST':
            category = Category(name=str(request.data['name']))
            category.save()
            response = jsonify({
                'id': category.id,
                'name': category.name
            })
            response.status_code = 201
            return response
        else:
            # GET
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
    def category_details(id, **kwargs):
        category = Category.query.filter_by(id=id).first()
        if not category:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

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
            # GET
            response = jsonify({
                'id': category.id,
                'name': category.name,
            })
            response.status_code = 200
            return response

    @app.route('/users', methods=['POST'])
    def new_user():
        try:
            username = request.json['username']
            password = request.json['password']
            gender = request.json['gender']
        except BadRequest:
            return {}, 400

        if User.query.filter_by(username=username).first() is not None:
            return {}, 400
        user = User(username=username, gender=gender)
        user.hash_password(password)
        user.save()
        return jsonify({
            'username': user.username,
            'gender': user.gender,
            'dateCreated': user.date_created,
            'dateModified': user.date_modified
        }), 201

    @app.route('/login', methods=['POST'])
    def login():
        # auth = request.authorization
        try:
            username = request.json['username']
            password = request.json['password']
        except BadRequest:
            return {}, 400

        user = User.query.filter_by(username=username).first()

        if not user:
            return {}, 400

        if user.check_password(password):
            token = jwt.encode(
                payload={
                    'id': user.id,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
                    'admin': user.admin
                },
                key=app.config['SECRET']
            )

            return jsonify({'access_token': token.decode('UTF-8')})

        return {}, 403

    return app


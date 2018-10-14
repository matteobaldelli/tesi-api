import datetime
import jwt
from jwt import DecodeError
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
    from app.models import Medical, Visit, User, Metric

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

            return f(current_user, *args, **kwargs)

        return decorated

    @app.route('/medical', methods=['POST', 'GET'])
    def medical():
        if request.method == 'POST':
            medical = Medical(
                metric=str(request.data.get('metric', '')),
                value=request.data.get('value', 0),
                visit=Visit.query.filter_by(id=request.data['visit_id']).first()
            )
            medical.save()
            response = jsonify({
                'id': medical.id,
                'metric': medical.metric,
                'value': medical.value,
                'date_created': medical.date_created,
                'date_modified': medical.date_modified,
                'visit_id': medical.visit.id
            })
            response.status_code = 201
            return response
        else:
            # GET
            medicals = Medical.query.filter_by(visit_id=request.values.get('visit_id', ''))

            results = []

            for medical in medicals:
                obj = {
                    'id': medical.id,
                    'metric': medical.metric,
                    'value': medical.value,
                    'date_created': medical.date_created,
                    'date_modified': medical.date_modified,
                    'visit_id': medical.visit.id
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/medical/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def medical_details(id, **kwargs):
        medical = Medical.query.filter_by(id=id).first()
        if not medical:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        if request.method == 'DELETE':
            medical.delete()
            return {
                       "message": "medical {} deleted successfully".format(medical.id)
                   }, 200

        elif request.method == 'PUT':
            medical.metric = str(request.data.get('metric', medical.metric))
            medical.value = request.data.get('value', medical.value)
            medical.visit = Visit.query.filter_by(id=request.data.get('visit_id', medical.visit.id)).first()
            medical.save()
            response = jsonify({
                'id': medical.id,
                'metric': medical.metric,
                'value': medical.value,
                'date_created': medical.date_created,
                'date_modified': medical.date_modified,
                'visit_id': medical.visit.id
            })
            response.status_code = 200
            return response
        else:
            # GET
            response = jsonify({
                'id': medical.id,
                'metric': medical.metric,
                'value': medical.value,
                'date_created': medical.date_created,
                'date_modified': medical.date_modified,
                'visit_id': medical.visit.id
            })
            response.status_code = 200
            return response

    @app.route('/visit', methods=['POST', 'GET'])
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
                'date_created': visit.date_created,
                'date_modified': visit.date_modified
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
                    'date_created': visit.date_created,
                    'date_modified': visit.date_modified
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/visit/<int:id>', methods=['GET', 'PUT', 'DELETE'])
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
                'date_created': visit.date_created,
                'date_modified': visit.date_modified
            })
            response.status_code = 200
            return response
        else:
            # GET
            response = jsonify({
                'id': visit.id,
                'name': visit.name,
                'date_created': visit.date_created,
                'date_modified': visit.date_modified
            })
            response.status_code = 200
            return response

    @app.route('/metric', methods=['POST', 'GET'])
    @token_required
    def metric(user):
        if request.method == 'POST':
            metric = Metric(
                name=str(request.data['name']),
                weight=request.data['weight'],
                unit_label=str(request.data['unit_label']),
                total_range_min=request.data['total_range_min'],
                total_range_max=request.data['total_range_max'],
                healthy_range_min=request.data['healthy_range_min'],
                healthy_range_max=request.data['healthy_range_max'],
                gender=request.data['gender']
            )
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
                'gender': metric.gender
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
                    'gender': metric.gender
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/metric/<int:id>', methods=['GET', 'PUT', 'DELETE'])
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
                'gender': metric.gender
            })
            response.status_code = 200
            return response
        else:
            # GET
            response = jsonify({
                'id': metric.id,
                'weight': metric.weight,
                'unit_label': metric.unit_label,
                'total_range_min': metric.total_range_min,
                'total_range_max': metric.total_range_max,
                'healthy_range_min': metric.healthy_range_min,
                'healthy_range_max': metric.healthy_range_max,
                'gender': metric.gender
            })
            response.status_code = 200
            return response

    @app.route('/metric/data', methods=['GET'])
    @token_required
    def metric_data(user):
        metrics = Metric.query.filter_by(gender=user.gender)
        results = []

        for metric in metrics:
            obj = {
                'name': metric.name,
                'weight': metric.weight,
                'unit_label': metric.unit_label,
                'features': {
                    'healthyrange': [
                        metric.total_range_min,
                        metric.total_range_max
                    ],
                    'totalrange': [
                        metric.healthy_range_min,
                        metric.healthy_range_max
                    ]
                }
            }
            results.append(obj)

        response = jsonify(results)
        response.status_code = 200
        return response

    @app.route('/user', methods=['POST'])
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
            'date_created': user.date_created,
            'date_modified': user.date_modified
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
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
                },
                key=app.config['SECRET']
            )

            return jsonify({'access_token': token.decode('UTF-8')})

        return {}, 403

    return app


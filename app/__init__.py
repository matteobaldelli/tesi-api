from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy
from flask import request, jsonify, abort
from flask_cors import CORS


# local import
from instance.config import app_config

db = SQLAlchemy()


def create_app(config_name):
    from app.models import Medical, Visit

    app = FlaskAPI(__name__, instance_relative_config=True)
    cors = CORS(app, resources={r"/*": {"origins": "*"}})
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    @app.route('/medical/', methods=['POST', 'GET'])
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
            # medicals = Medical.get_all()
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

    @app.route('/visit/', methods=['POST', 'GET'])
    def visit():
        if request.method == 'POST':
            visit = Visit(
                name=str(request.data.get('name', 'visit')),
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
            visits = Visit.get_all()
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

    return app


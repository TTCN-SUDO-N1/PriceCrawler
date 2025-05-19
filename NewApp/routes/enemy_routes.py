from flask import request, jsonify
from flask_restx import Namespace,Resource,fields
from NewApp.models import Enemy
from NewApp import db

api = Namespace('enemy',description='Enemy related operations')

enemy_input_model = api.model('EnemyInput', {
    'name': fields.String(required=True, description='Enemy name'),
    'domain': fields.String(required=True, description='Enemy domain'),
})

enemy_output_model = api.model('EnemyOutput', {
    'enemy_id': fields.Integer(readonly=True, description='Enemy unique identifier'),
    'name': fields.String(required=True, description='Enemy name'),
    'domain': fields.String(required=True, description='Enemy domain'),
})

@api.route('/')
class EnemyList(Resource):
    @api.doc('list_enemies')
    @api.marshal_list_with(enemy_output_model)
    def get(self):
        return Enemy.query.all(), 200
    
    @api.expect(enemy_input_model)
    @api.marshal_with(enemy_output_model, code=201)
    def post(self):
        data = request.json
        new_enemy = Enemy(
            name=data['name'],
            domain=data['domain']
        )
        db.session.add(new_enemy)
        db.session.commit()
        return new_enemy, 201
    
@api.route('/<int:enemy_id>')
@api.param('enemy_id', 'Enemy unique identifier')
@api.response(404, 'Enemy not found')
class EnemyResource(Resource):
    @api.doc('get_enemy')
    @api.marshal_with(enemy_output_model)
    def get(self, enemy_id):
        enemy = Enemy.query.get_or_404(enemy_id)
        return enemy, 200
    

    @api.expect(enemy_input_model)
    @api.marshal_with(enemy_output_model)
    def put(self, enemy_id):
        data = request.json
        enemy = Enemy.query.get_or_404(enemy_id)
        enemy.name = data['name']
        enemy.domain = data['domain']
        db.session.commit()
        return enemy, 200
    
    def delete(self, enemy_id):
        enemy = Enemy.query.get_or_404(enemy_id)
        db.session.delete(enemy)
        db.session.commit()
        return '', 204

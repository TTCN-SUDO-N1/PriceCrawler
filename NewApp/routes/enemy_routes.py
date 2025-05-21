from flask import request, jsonify
from flask_restx import Namespace,Resource,fields
from NewApp import db
from NewApp.models import Enemy

api = Namespace('enemy',description='Enemy related operations')

enemy_input_model = api.model('EnemyInput', {
    'name': fields.String(required=True, description='Enemy name'),
    'domain': fields.String(required=True, description='Enemy domain'),
})

enemy_output_model = api.model('EnemyOutput', {
    'id': fields.Integer(readonly=True, description='Enemy unique identifier'),
    'name': fields.String(required=True, description='Enemy name'),
    'domain': fields.String(required=True, description='Enemy domain'),
})

@api.route('/')
class EnemyList(Resource):
    @api.doc('list_enemies', description='Get a list of all enemies')
    @api.marshal_list_with(enemy_output_model)
    def get(self):
        return Enemy.query.all(), 200
    
    @api.expect(enemy_input_model)
    @api.marshal_with(enemy_output_model, code=201)
    @api.doc('create_enemy', description='Create a new enemy')
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
    @api.doc('get_enemy', description='Get an enemy by its ID')
    @api.marshal_with(enemy_output_model)
    def get(self, enemy_id):
        enemy = Enemy.query.get_or_404(enemy_id)
        return enemy, 200
    
    @api.expect(enemy_input_model)
    @api.marshal_with(enemy_output_model)
    @api.doc('update_enemy', description='Update an enemy by its ID')
    def put(self, enemy_id):
        data = request.json
        enemy = Enemy.query.get_or_404(enemy_id)
        enemy.name = data['name']
        enemy.domain = data['domain']
        db.session.commit()
        return enemy, 200
    
    @api.doc('delete_enemy', description='Delete an enemy by its ID')
    def delete(self, enemy_id):
        enemy = Enemy.query.get_or_404(enemy_id)
        db.session.delete(enemy)
        db.session.commit()
        return '', 204

@api.route('/by-domain')
class EnemyByDomainResource(Resource):
    @api.doc('find_enemy_by_domain', description='Find enemy by domain')
    @api.param('domain', 'Domain to search for')
    @api.param('auto_create', 'Automatically create a new enemy if not found', _in='query', type='boolean')
    @api.marshal_with(enemy_output_model)
    def get(self):
        try:
            domain = request.args.get('domain')
            auto_create = request.args.get('auto_create', 'false').lower() == 'true'
            
            if not domain:
                api.abort(400, 'Domain parameter is required')
            
            # Try to find an exact match first
            enemy = Enemy.query.filter(Enemy.domain == domain).first()
            
            if enemy:
                return enemy, 200
            elif auto_create:
                # Auto create enemy
                # Use the domain as the name (first part before any dots)
                if '.' in domain:
                    enemy_name = domain.split('.')[0]
                else:
                    enemy_name = domain
                
                # Capitalize the first letter
                enemy_name = enemy_name.capitalize()
                
                new_enemy = Enemy(
                    name=enemy_name,
                    domain=domain
                )
                db.session.add(new_enemy)
                db.session.commit()
                return new_enemy, 201
            else:
                # Return null response with 204 status code
                # This will ensure the frontend recognizes it as "no match found"
                return None, 204
                
        except Exception as e:
            print(f"Error in by-domain endpoint: {str(e)}")
            api.abort(500, f'Server error: {str(e)}')

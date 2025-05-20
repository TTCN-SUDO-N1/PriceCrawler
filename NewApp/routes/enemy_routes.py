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
        domain = request.args.get('domain')
        auto_create = request.args.get('auto_create', 'false').lower() == 'true'
        
        if not domain:
            api.abort(400, 'Domain parameter is required')
            
        # Remove www. if present
        normalized_domain = domain.replace('www.', '')
        
        # Try to find an exact match first
        enemy = Enemy.query.filter(Enemy.domain == normalized_domain).first()
        
        # If no exact match, try to find a partial match
        if not enemy:
            enemies = Enemy.query.all()
            for e in enemies:
                e_domain = e.domain.replace('www.', '')
                if e_domain in normalized_domain or normalized_domain in e_domain:
                    enemy = e
                    break
        
        # If still no match and auto_create is True, create a new enemy
        if not enemy and auto_create:
            # Generate a name from the domain
            enemy_name = normalized_domain.split('.')[0]
            # Capitalize the first letter
            enemy_name = enemy_name.capitalize()
            
            new_enemy = Enemy(
                name=enemy_name,
                domain=normalized_domain
            )
            db.session.add(new_enemy)
            db.session.commit()
            return new_enemy, 201
            
        if enemy:
            return enemy, 200
        else:
            api.abort(404, 'No enemy found for this domain')

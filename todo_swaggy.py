from flask import Flask, Blueprint
from flask_restx import Api, Resource, fields
from werkzeug.contrib.fixers import ProxyFix

# Initialize App
app = Flask(__name__)
blueprint = Blueprint('api', __name__, url_prefix='/api')
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(blueprint, version='1.0', title='TodoMVC API',
          description='A simple TodoMVC API',
          doc='/doc/'
          )
app.register_blueprint(blueprint)
# Note: Default behavior of SwaggerUI on / is replace above with custom url's
# Swagger is available on url 	: http://127.0.0.1:5000/api/doc/
# Sample API URL 				: http://127.0.0.1:5000/api/todos/

# Configure Swagger parameters
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
app.config.SWAGGER_UI_OPERATION_ID = True
app.config.SWAGGER_UI_REQUEST_DURATION = True

# Define Namespace
ns = api.namespace('todos', description='TODO operations', ordered=True)

# Define the Model
todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details')
})


class TodoDAO(object):
    def __init__(self):
        self.counter = 0
        self.todos = []

    def get(self, id):
        for todo in self.todos:
            if todo['id'] == id:
                return todo
        api.abort(404, "Todo {} doesn't exist".format(id))

    def create(self, data):
        todo = data
        todo['id'] = self.counter = self.counter + 1
        self.todos.append(todo)
        return todo

    def update(self, id, data):
        todo = self.get(id)
        todo.update(data)
        return todo

    def delete(self, id):
        todo = self.get(id)
        self.todos.remove(todo)


# Instantiate the model as datastore
DAO = TodoDAO()

# Define Controller for Todos
@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''
        return DAO.todos

    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload), 201

# Define Controller for Todo
@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)


if __name__ == '__main__':
    # Preload with sample data
    DAO.create({'task': 'Build an API'})
    DAO.create({'task': 'Test the app'})
    DAO.create({'task': 'Deploy to production'})

    app.run(debug=True)

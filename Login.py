from flask import Flask,jsonify,request
import logging
from datetime import datetime
import time

app = Flask(__name__)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Request timer middleware
@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def log_request(response):
    # Calculate request duration
    duration = time.time() - request.start_time

    # Get request details
    now = datetime.utcnow()
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    host = request.host.split(':', 1)[0]
    args = dict(request.args)

    # Get request body for POST/PUT requests
    request_body = None
    if request.method in ['POST', 'PUT'] and request.is_json:
        request_body = request.get_json()

    log_params = {
        'method': request.method,
        'path' : request.path,
        'status' : response.status_code,
        'duration': round(duration * 1000,2),
        'ip': ip,
        'host':host,
        'params':args,
        'body': request_body
    }


    # Log different levels based on status code

    if 200 <= response.status_code < 400:
        logging.info(f'Request completed successfully: {log_params}')
    elif 400 <= response.status_code < 500:
        logging.warning(f'Client error in request: {log_params}')
    else:
        logging.error(f'Sever error in request: {log_params}')
    
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f'Unhandle exception: {str(e)}', exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500

# In-memory storage for our books
books = [
    {"id": 1, "title":"The Great Gatsby", "author":"F. Scott Fitzgerald"},
    {"id": 2, "title": "1984", "author": "George Orwell"},
]

# GET all books

@app.route('/books', methods=['GET'])
def get_books():
    return jsonify({"book" : books})

#GET a specific book by ID
@app.route('/books/<int:book_id>', methods=['GET'])
def get_book_id(book_id):
    book = next((book for book in books if book['id'] == book_id), None)
    if book is None:
        return jsonify({"Error" : "Book not found 404"}), 404
    return jsonify({"book":book})

#POST a new book
@app.route('/books', methods=['POST'])
def create_book():
    if not request.is_json:
        return jsonify({"Error" : "Content-Type must be application/json"}), 400
    
    data = request.get_json()

     # Validate required fields
    if not all(key in data for key in ('title', 'author')):
        return jsonify({'message' : 'Missing title or author'}), 400
    
    # Generate new ID
    new_id = max(book['id'] for book in books) + 1

    new_book = {
        'id': new_id,
        'title':data['title'],
        'author':data['author'],
    }

    books.append(new_book)

    return jsonify({'book': new_book}), 201

#PUT update a book 
@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    if not request.is_json:
        return jsonify({"Error" : "Content-Type must be application/json"}), 400
    
    book = next((book for book in books if book['id']  == book_id ), None)
    if book is None:
        return jsonify({'Error': "Book not found"}),404
    
    data = request.get_json()

    # Update book details
    book['title'] = data.get('title', book['title'])
    book['author'] = data.get('author', book['author'])

    return jsonify({'book': book})

#DELETE a book
@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    global books
    initial_length = len(books)

    books = [book for book in books if book['id'] != book_id]

    if len(books) == initial_length:
        return jsonify({'Error': 'Book not found'}), 404
    
    return jsonify({'message': 'book deleted'}), 200

if __name__ == '__main__':
    logger.info('Starting Flask API sever...')
    app.run(debug=True)
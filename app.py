from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
# Enable Cross-Origin Resource Sharing so the Bolt.diy frontend can call this API
CORS(app)

DATA_FILE = 'courses.json'

# --- Helper Functions for JSON Storage ---

def load_courses():
    """Reads courses from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as file:
        # If the file is empty, return an empty list instead of crashing
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []

def save_courses(courses):
    """Writes the current list of courses back to the JSON file."""
    with open(DATA_FILE, 'w') as file:
        json.dump(courses, file, indent=4)

def get_next_id(courses):
    """Generates the next available integer ID."""
    if not courses:
        return 1
    return max(course['id'] for course in courses) + 1


# --- API Endpoints ---

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Retrieve all courses."""
    return jsonify(load_courses()), 200


@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Retrieve a single course by its ID."""
    courses = load_courses()
    course = next((c for c in courses if c['id'] == course_id), None)
    
    if not course:
        abort(404, description="Course not found.")
        
    return jsonify(course), 200


@app.route('/api/courses', methods=['POST'])
def create_course():
    """Create a new course."""
    data = request.get_json()
    
    # Validation: Check for required fields
    required_fields = ['name', 'description', 'target_date', 'status']
    if not data or any(field not in data for field in required_fields):
        abort(400, description=f"Validation failed: Missing required fields. Must include: {', '.join(required_fields)}")
        
    # Validation: Check status Enum
    valid_statuses = ['Not Started', 'In Progress', 'Completed']
    if data['status'] not in valid_statuses:
        abort(400, description=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    courses = load_courses()
    
    new_course = {
        'id': get_next_id(courses),
        'name': data['name'],
        'description': data['description'],
        'target_date': data['target_date'],
        'status': data['status'],
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    courses.append(new_course)
    save_courses(courses)
    
    return jsonify(new_course), 201


@app.route('/api/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    """Update an existing course."""
    data = request.get_json()
    courses = load_courses()
    
    for course in courses:
        if course['id'] == course_id:
            # Update fields if provided in the payload
            course['name'] = data.get('name', course['name'])
            course['description'] = data.get('description', course['description'])
            course['target_date'] = data.get('target_date', course['target_date'])
            
            # Validate status if it's being updated
            if 'status' in data:
                valid_statuses = ['Not Started', 'In Progress', 'Completed']
                if data['status'] not in valid_statuses:
                    abort(400, description=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
                course['status'] = data['status']
                
            save_courses(courses)
            return jsonify(course), 200
            
    abort(404, description="Course not found.")


@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    """Delete a course."""
    courses = load_courses()
    
    # Filter out the course to be deleted
    updated_courses = [c for c in courses if c['id'] != course_id]
    
    # If the length hasn't changed, the ID wasn't found
    if len(courses) == len(updated_courses):
        abort(404, description="Course not found.")
        
    save_courses(updated_courses)
    return '', 204


# Error handler for cleaner JSON error responses
@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(error):
    return jsonify({"error": error.description}), error.code


if __name__ == '__main__':
    # Run the server
    app.run(debug=True, port=5000)
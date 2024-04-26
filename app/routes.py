from flask import request, render_template
from . import app, db
from .models import User, Post, Comment
from .auth import basic_auth, token_auth

@app.route("/")  # Define a route
def index():
    return render_template('index.html')

# User Endpoints

# Create New User
@app.route('/users', methods=['POST'])
def create_user():
    # Check to make sure that the request body is JSON
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    # Get the data from the request body
    data = request.json

    # Validate that the data has all of the required fields
    required_fields = ['firstName', 'lastName', 'username', 'email', 'password']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return {'error': f"{', '.join(missing_fields)} must be in the request body"}, 400

    # Pull the individual data from the body
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # check to see if any current users already have that username and/or email
    check_users = db.session.execute(db.select(User).where( (User.username == username) | (User.email == email) )).scalars().all()
    if check_users:
        return {'error': "A user with that username and/or email already exists"}, 400
        
    # create a new instance of a user with the data from the request
    new_user = User(first_name=first_name, last_name=last_name,  username=username, email=email, password=password)

    return new_user.to_dict(), 201

#Login to get a token
@app.route('/token')
@basic_auth.login_required
def get_token():
    user = basic_auth.current_user()
    return user.get_token()


@app.route('/users/me')
@token_auth.login_required
def get_me():
    user = token_auth.current_user()
    return user.to_dict()

# Get a user
@app.route('/users/<int:user_id>')
def get_user(user_id):
    user = db.session.get(User, user_id)
    if user:
        return user.to_dict()
    else:
        return {'error': f'User with {user_id} does not exist'}, 404

# Update a user
@app.route('/users/<int:user_id>', methods=['PUT'])
@token_auth.login_required
def edit_user(user_id):
    # Check to see that the request body is JSON
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    # Get the user based on the user id
    user = db.session.get(User, user_id)
    # Check if the user exists
    if user is None:
        return {'error': f'User with {user_id} does not exist'}, 404
    # Get the logged in user based on the token
    current_user = token_auth.current_user()
    # Check if the user to edit is the logged in user
    if user is not current_user:
        return {'error': 'You do not have permission to edit this user'}, 403
    
    data = request.json
    user.update(**data)
    return user.to_dict()

# delete a user
@app.route('/users/<int:user_id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(user_id):
    # Get the user based on the user id
    user = db.session.get(User, user_id)
    # Check if the user exists
    if user is None:
        return {'error': f'User with {user_id} does not exist'}, 404
    # Get the logged in user based on the token
    current_user = token_auth.current_user()
    # Check if the user to edit is the logged in user
    if user is not current_user:
        return {'error': 'You do not have permission to delete this user'}, 403
    # Delete the user
    user.delete()
    return {'success': f"{user.username} has been deleted"}


# Post Endpoints

# Get All Posts
@app.route('/posts') 
def get_posts():
    posts = db.session.execute(db.select(Post).order_by(db.desc(Post.date_created))).scalars().all()
    return [post.to_dict() for post in posts]

# Get a Single Post By ID
@app.route('/posts/<int:post_id>')
def get_post(post_id):
    # Get the posts from database by ID
    post = db.session.get(Post, post_id)
    if post:
        return post.to_dict()
    else:
        return {'error': f"Post with an ID of {post_id} does not exist"}, 404 # If we loop through all of the posts without returning, the post with that ID does not exist

# Create a Post
@app.route('/posts', methods=['POST'])
@token_auth.login_required
def create_post():
    # Check to see if the request body is JSON
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    # Get the data from the request body
    data = request.json
    # Validate the incoming data
    required_fields = ['title', 'body']
    missing_fields = []
    for field in required_fields: # For each of the required fields
        if field not in data: # If the field is not in the request body dictionary
            missing_fields.append(field) # Add that field to the list of missing fields
    if missing_fields: # If there are any missing fields, return 400 status code with the missing fields listed
        return {'error': f"{', '.join(missing_fields)} must be in the request body"}, 400
    
    # Get data values
    title = data.get('title')
    body = data.get('body')

    #get the logged in user
    current_user = token_auth.current_user()

    # Create a new Post instance with data (and get the id from the token authenticated user)
    new_post = Post(title=title, body=body, user_id=current_user.id)
    # Return the newly created post dictionary with a 201 Created Status Code
    return new_post.to_dict(), 201


# Edit/Update Post Endpoint
@app.route('/posts/<int:post_id>', methods=['PUT'])
@token_auth.login_required
def edit_post(post_id):
    # Check to see that they have a JSON body
    if not request.is_json:
        return {'error': 'You content-type must be application/json'}, 400
    # Let's the find post in the db
    post = db.session.get(Post, post_id)
    if post is None:
        return {'error': f"Post with an ID #{post_id} does not exist"}, 404
    # Get the current user based on the token 
    current_user = token_auth.current_user()
    # check if the current user is the author of th post
    if current_user is not post.author:
        return {'error': "This is not your post. You do not have permission to edit"}, 403
    
    # Get the data from the request
    data = request.json
    # Pass that data into the post's update method
    post.update(**data)
    return post.to_dict()


# Delete a Post
@app.route('/posts/<int:post_id>', methods=['DELETE'])
@token_auth.login_required
def delete_post(post_id):
    #based on the post_id parameter check to see Post exists
    post = db.session.get(Post, post_id)

    if post is None:
        return {'error': f'Post with {post_id} does not exist. Please try again.'}, 404
    
    #make sure user tring to delete post, is the user that createdit
    current_user = token_auth.current_user()
    if post.author is not current_user:
        return {'error': 'You do not have permission to delete this post'}, 403
    
    #delete the post
    post.delete()
    return {'success': f"{post.title} was successfully deleted."}, 200


# COMMENT ENDPOINTS

# Create a comment
@app.route('/posts/<int:post_id>/comments', methods=['POST'])
@token_auth.login_required
def create_comment(post_id):
    
    #make sure the request has a body
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    #grab the correct post
    post = db.session.get(Post, post_id)
    if post is None:
        return {'error': f"Post {post_id} does not exist"}, 404
    
    data = request.json
    
    required_fields = ['body']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        return {'error': f"{', '.join(missing_fields)} must be present in the request body"}, 400
    
    body = data.get('body')
    current_user = token_auth.current_user()
    new_comment = Comment(body=body, user_id=current_user.id, post_id=post.id)
    return new_comment.to_dict(), 201


# update a comment
@app.route('/posts/<int:post_id>/comments/<int:comment_id>', methods=['PUT'])
@token_auth.login_required
def edit_comment(post_id, comment_id):
    #check to see if the request body is json
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    #grab post by id
    post = db.session.get(Post, post_id)
    if post is None:
        return {'error': f"Post {post_id} does not exist."}, 404
    
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        return {'error': f'Comment {comment_id} does not exist.'}, 404
    
    if comment.post_id != post.id:
        return {'error' : f"Comment #{comment_id} is not associated with Post #{post_id}"}, 403
    
    current_user = token_auth.current_user()
    
    if comment.user != current_user:
        return {'error': 'You do not have permission to edit this comment.'}, 403
    
    data = request.json
    comment.update(**data)
    return comment.to_dict()

# Delete a comment
@app.route('/posts/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
@token_auth.login_required
def delete_comment(post_id, comment_id):

    #grab post by id
    post = db.session.get(Post, post_id)

    if post is None:
        return {'error': f"Post {post_id} does not exist."}, 404
    
    comment = db.session.get(Comment, comment_id)

    if comment is None:
        return {'error': f'Comment {comment_id} does not exist.'}, 404
    
    if comment.post_id != post.id:
        return {'error' : f"Comment #{comment_id} is not associated with Post #{post_id}"}, 403
    
    current_user = token_auth.current_user()
    
    if comment.user != current_user:
        return {'error': 'You do not have permission to delete this comment.'}, 403
    
    comment.delete()
    return {'success': 'Comment has been successfully banished'}, 200


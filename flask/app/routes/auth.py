import flask
from app.services.user_service import User
from app.logs import log

def auth():
    """Handle user authentication.
    
    Currently implements a simple authentication:
    - Uses URL param if provided
    - Creates random user if no session
    - Uses existing session if available
    
    Returns:
        User: Authenticated user instance
    """

    # Login when user_id is injected as a URL param 
    if flask.request.args.get("user_id"):
        user = User(flask.request.args.get("user_id"))

    # Login as random user (when session cookie is empty)
    elif not flask.session.get("user_id"):
        user = User()

    # Recognizes an existing user (through session cookie)
    else:
        user = User.from_session()

    user.login()
    return user 
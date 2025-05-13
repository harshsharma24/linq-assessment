# app.py
from flask import Flask
from acme import acme_bp, limiter
from integration import integration_bp

app = Flask(__name__)
app.config['RATELIMIT_HEADERS_ENABLED'] = True

# Init limiter for mock CRM
limiter.init_app(app)
# Register mock-CRM routes
app.register_blueprint(acme_bp)
# Register integration routes under /api
app.register_blueprint(integration_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(port=4000, debug=True)
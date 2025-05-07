from flask import Flask
from acme import acme_bp, limiter

app = Flask(__name__)
app.config['RATELIMIT_HEADERS_ENABLED'] = True
limiter.init_app(app)
app.register_blueprint(acme_bp)

if __name__ == "__main__":
    app.run(port=4000, debug=True)

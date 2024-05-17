# ******************************************************************************
#  Copyright (c) 2020 University of Stuttgart
#
#  See the NOTICE file(s) distributed with this work for additional
#  information regarding copyright ownership.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ******************************************************************************

from flask import Flask
import logging

from app.routes_ckt_cutting import blp_ckt_cutting
from app.routes_gate_cutting import blp_gate_cutting
from config import config
from flask_smorest import Api
from app.routes_wire_cutting import blp


def create_app(config_name):
    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    api = Api(app)
    api.register_blueprint(blp)
    api.register_blueprint(blp_gate_cutting)
    api.register_blueprint(blp_ckt_cutting)

    @app.route("/")
    def heartbeat():
        return '<h1>Circuit cutting service is running</h1> <h3>View the API Docs <a href="/api/swagger-ui">here</a></h3>'

    from app import routes_wire_cutting

    return app

# Standard Python
from fastapi import FastAPI, APIRouter

import logging 
import clingo

from pydantic import BaseModel
from typing import Sequence, Any

# Self Defined
from clinguin.server.presentation.endpoints_helper import call_function
from clinguin.server.presentation.solver_dto import SolverDto

from clinguin.utils.logger import Logger
from clinguin.utils.singleton_container import SingletonContainer

from clinguin.server.application.standard_solver import ClingoBackend


class Endpoints:
    def __init__(self, logic_programs : Sequence[str], solver_classes : Sequence[Any], parsed_config) -> None:
        logger = Logger(parsed_config['timestamp'] + '-server', reroute_default = True)

        self._parsed_config = parsed_config
        self._instance = SingletonContainer(logger)
        
        self.router = APIRouter()

        # Definition of endpoints
        self.router.add_api_route("/health", self.health, methods=["GET"])
        self.router.add_api_route("/", self.standardSolver, methods=["GET"])
        self.router.add_api_route("/solver", self.solver, methods=["POST"])

        self._initSolver(logic_programs, solver_classes, self._instance)

        
        
    def _initSolver(self, logic_programs : Sequence[str], solver_classes : Sequence[Any], instance) -> None:
        self._solver = []
        self._solver.append(solver_classes[0](logic_programs))


    async def health(self):
        return {
            "name" : self._parsed_config["name"],
            "version" : self._parsed_config["version"],
            "description" : self._parsed_config["description"]
            }

    async def standardSolver(self):
        return self._solver[0]._get()

    async def solver(self, solver_call_string:SolverDto):

        symbol = clingo.parse_term(solver_call_string.function)
        function_name = symbol.name
        function_arguments = (list(map(lambda symb:str(symb), symbol.arguments)))

        result = call_function(self._solver, function_name, function_arguments, {})
        return result




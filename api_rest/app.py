from itertools import count
from typing import Optional

from flask import Flask, jsonify, request
from flask_pydantic_spec import FlaskPydanticSpec, Request, Response
from pydantic import BaseModel, Field
from tinydb import Query, TinyDB
from tinydb.storages import MemoryStorage

server = Flask(__name__)
spec = FlaskPydanticSpec("flask", title="Live de Python")
spec.register(server)
database = TinyDB(storage=MemoryStorage)
c = count()


class QueryPessoa(BaseModel):
    id: Optional[int]
    nome: Optional[str]
    idade: Optional[int]


class Pessoa(BaseModel):
    id: Optional[int] = Field(default_factory=lambda: next(c))
    nome: str
    idade: int


class Pessoas(BaseModel):
    pessoas: list[Pessoa]
    count: int


@server.get("/pessoa/<int:id>")
@spec.validate(resp=Response(HTTP_200=Pessoa))
def pegar_pessoa(id):
    """Retorna uma Pessoa da base de dados."""
    try:
        pessoa = database.search(Query().id == id)[0]
    except IndexError:
        return {"message": "Pessoa not found"}, 404
    return jsonify(pessoa)


@server.get("/pessoas")
@spec.validate(query=QueryPessoa, resp=Response(HTTP_200=Pessoas))
def pegar_pessoas():
    """Retorna todas as Pessoas da base de dados."""
    query = request.context.query.dict(exclude_none=True)
    todas_as_pessoas = database.search(Query().fragment(query))
    return jsonify(
        Pessoas(pessoas=todas_as_pessoas, count=len(todas_as_pessoas)).dict()
    )


@server.post("/pessoas")
@spec.validate(body=Request(Pessoa), resp=Response(HTTP_201=Pessoa))
def inserir_pessoa():
    """Insere uma Pessoa no banco de dados"""
    body = request.context.body.dict()
    database.insert(body)
    return body


@server.put("/pessoas/<int:id>")
@spec.validate(body=Request(Pessoa), resp=Response(HTTP_201=Pessoa))
def altera_pessoa(id):
    """Altera uma Pessoa no banco de dados"""
    Pessoa = Query()
    body = request.context.body.dict()
    database.update(body, Pessoa.id == id)
    return jsonify(body)


@server.delete("/pessoas/<int:id>")
@spec.validate(resp=Response("HTTP_204"))
def deleta_pessoa(id):
    """Deleta uma Pessoa do banco de dados."""
    Pessoa = Query()
    database.remove(Pessoa.id == id)
    return jsonify({})

import requests
import json


def fetch_openapi(url: str, out_path: str = "openapi.json") -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    try:
        spec = resp.json()
    except ValueError:
        raise ValueError("Document cannot be loaded.")

    # (Optional) quick sanity check
    if not isinstance(spec, dict) or "openapi" not in spec:
        raise ValueError("Document doesn't look like an OpenAPI spec.")

    return spec

sample_spec_string = """
{
  "openapi": "3.0.0",
  "info": {
    "title": "Simple Pet Store API (Mock)",
    "version": "1.0.1",
    "description": "An API to manage pets in a store, using httpbin for responses."
  },
  "servers": [
    {
      "url": "https://httpbin.org",
      "description": "Mock server (httpbin.org)"
    }
  ],
  "paths": {
    "/get": {
      "get": {
        "summary": "List all pets (Simulated)",
        "operationId": "listPets",
        "description": "Simulates returning a list of pets. Uses httpbin's /get endpoint which echoes query parameters.",
        "parameters": [
          {
            "name": "limit",
            "in": "query",
            "description": "Maximum number of pets to return",
            "required": false,
            "schema": { "type": "integer", "format": "int32" }
          },
          {
             "name": "status",
             "in": "query",
             "description": "Filter pets by status",
             "required": false,
             "schema": { "type": "string", "enum": ["available", "pending", "sold"] }
          }
        ],
        "responses": {
          "200": {
            "description": "A list of pets (echoed query params).",
            "content": { "application/json": { "schema": { "type": "object" } } }
          }
        }
      }
    },
    "/post": {
      "post": {
        "summary": "Create a pet (Simulated)",
        "operationId": "createPet",
        "description": "Simulates adding a new pet. Uses httpbin's /post endpoint which echoes the request body.",
        "requestBody": {
          "description": "Pet object to add",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["name"],
                "properties": {
                  "name": {"type": "string", "description": "Name of the pet"},
                  "tag": {"type": "string", "description": "Optional tag for the pet"}
                }
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "Pet created successfully (echoed request body).",
            "content": { "application/json": { "schema": { "type": "object" } } }
          }
        }
      }
    },
    "/get?petId={petId}": {
      "get": {
        "summary": "Info for a specific pet (Simulated)",
        "operationId": "showPetById",
        "description": "Simulates returning info for a pet ID. Uses httpbin's /get endpoint.",
        "parameters": [
          {
            "name": "petId",
            "in": "path",
            "description": "This is actually passed as a query param to httpbin /get",
            "required": true,
            "schema": { "type": "integer", "format": "int64" }
          }
        ],
        "responses": {
          "200": {
            "description": "Information about the pet (echoed query params)",
            "content": { "application/json": { "schema": { "type": "object" } } }
          },
          "404": { "description": "Pet not found (simulated)" }
        }
      }
    }
  }
}
"""



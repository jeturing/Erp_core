
import werkzeug
import textwrap


import logging
_logger = logging.getLogger(__name__)



def generate_docs(server_url):
    # security = generate_security_docs(server_url)
    # tags, paths, components = generate_routing_docs(controllers)

    default_protocall = server_url.split('://')[0]
    default_hostname = server_url.split('://')[1]
                # <div style="background-color: #101010; color: #ffffff;">
                #     <h1>Introduction</h1>
                # </div>
    return {
        'openapi': '3.0.0',
        'info': {
            # 'version': '1.0.0',
            'title': 'Open API',
            'description': textwrap.dedent("""   """),
            'license': {
                'name': 'Other proprietary'
            },
            'contact': {
                'name': 'Webkul Software Pvt Ltd.',
                'url': 'https://store.webkul.com/Odoo-REST-API.html',
            },
        },
        'servers': [{
                        'url': server_url,
                    },
                    {
                        "url": "{protocol}://{hostname}",
                        "description": "Customizable server URL",
                        "variables": {
                                "protocol": {
                                    "default": default_protocall,
                                    "enum": [
                                        "http",
                                        "https"
                                    ]
                                },
                                "hostname": {
                                    "default": default_hostname
                                }
                            }
                    }],
        'tags': [
            {'name' : 'User',
             'description': 'Secured calls'}
             ],
        'paths': {
                    "/api/{model_name}/search": {
                        "get": {
                            "tags": ["User"],
                            "summary": "Search Records",
                            "operationId": "SearchRecords",
                            "description": "By passing in the appropriate options, you can search for available Records in the system",
                            "parameters": [
                                {
                                    "in": "path",
                                    "name": "model_name",
                                    "required": True,
                                    "description": "Model Name",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "header",
                                    "name": "api-key",
                                    "required": True,
                                    "description": "Api Key for authentication",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "header",
                                    "name": "token",
                                    "description": "Token for authentication",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "query",
                                    "name": "domain",
                                    "description": "Domain for filter the records",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "query",
                                    "name": "fields",
                                    "description": "Fields to Show",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "query",
                                    "name": "offset",
                                    "description": "number of records to skip for pagination",
                                    "schema": {"type": "integer", "format": "int32", "minimum": 0}
                                },
                                {
                                    "in": "query",
                                    "name": "order",
                                    "description": "Order of the records i.e accending, descending, etc.",
                                    "schema": {"type": "string", "format": "int32"}
                                },
                                {
                                    "in": "query",
                                    "name": "limit",
                                    "description": "maximum number of records to return",
                                    "schema": {"type": "integer", "format": "int32", "minimum": 0, "maximum": 50}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "search results matching criteria",
                                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SearchRecords"}}}
                                },
                                "400": {
                                    "description": "bad input parameter"
                                }
                            }
                        }
                    },
                    "/api/{model_name}/{id}": {
                        "get": {
                            "tags": ["User"],
                            "summary": "Search a Record",
                            "operationId": "SearchRecord",
                            "description": "By passing in the appropriate options, you can search for available records",
                            "parameters": [
                                {
                                    "in": "path",
                                    "name": "model_name",
                                    "required": True,
                                    "description": "Model Name",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "path",
                                    "name": "id",
                                    "required": True,
                                    "description": "Model Name",
                                    "schema": {"type": "integer"}
                                },
                                {
                                    "in": "header",
                                    "name": "api-key",
                                    "required": True,
                                    "description": "Api Key for authentication",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "header",
                                    "name": "token",
                                    "description": "Token for authentication",
                                    "schema": {"type": "string"}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "search results matching criteria",
                                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SearchRecord"}}}
                                },
                                "400": {
                                    "description": "bad input parameter"
                                }
                            }
                        },
                        "put": {
                            "tags": ["User"],
                            "summary": "Update a Record",
                            "operationId": "updateRecord",
                            "description": "Update a record",
                            "requestBody": {
                                "required": True,
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            },
                            "parameters": [
                                {
                                    "in": "path",
                                    "name": "model_name",
                                    "required": True,
                                    "description": "Model Name",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "path",
                                    "name": "id",
                                    "required": True,
                                    "description": "Model Name",
                                    "schema": {"type": "integer"}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "item created",
                                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UpdateRecord"}}}
                                },
                                "400": {"description": "invalid input, object invalid"},
                                "409": {"description": "an existing item already exists"}
                            }
                        },
                        "delete": {
                            "tags": ["User"],
                            "summary": "Delete a Record",
                            "operationId": "UpdateRecord",
                            "description": "Delete a Record",
                            "parameters": [
                                {
                                    "in": "path",
                                    "name": "model_name",
                                    "required": True,
                                    "description": "Model Name",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "path",
                                    "name": "id",
                                    "required": True,
                                    "description": "Model Name",
                                    "schema": {"type": "integer"}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "item deleted",
                                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/DeleteRecord"}}}
                                },
                                "400": {"description": "invalid input, object invalid"},
                                "409": {"description": "an existing item already exists"}
                            }
                        }
                    },
                    "/api/{model_name}/schema": {
                        "get": {
                            "tags": ["User"],
                            "summary": "Get the schema of a model",
                            "operationId": "GetSchema",
                            "description": "By passing in the appropriate options, you can search for available Records in the system",
                            "parameters": [
                                {
                                    "in": "path",
                                    "name": "model_name",
                                    "required": True,
                                    "description": "Model Name",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "header",
                                    "name": "api-key",
                                    "required": True,
                                    "description": "Api Key for authentication",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "header",
                                    "name": "token",
                                    "description": "Token for authentication",
                                    "schema": {"type": "string"}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "search results matching criteria",
                                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ModelSchema"}}}
                                },
                                "400": {
                                    "description": "bad input parameter"
                                }
                            }
                        }
                    },
                    "/api/{model_name}/create": {
                        "post": {
                            "tags": ["User"],
                            "summary": "Create Record",
                            "operationId": "CreateRecord",
                            "description": "By passing in the appropriate options, you can create the Records in the system",
                            "requestBody": {
                                "required": True,
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            },
                            "parameters": [
                                {
                                    "in": "path",
                                    "name": "model_name",
                                    "required": True,
                                    "description": "Model Name",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "header",
                                    "name": "api-key",
                                    "required": True,
                                    "description": "Api Key for authentication",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "header",
                                    "name": "token",
                                    "description": "Token for authentication",
                                    "schema": {"type": "string"}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Record/Records Created Successfully",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/CreateRecords"}
                                            }
                                        }
                                    }
                                },
                                "400": {"description": "bad input parameter"}
                            }
                        }
                    },
                    "/api/{model_name}/execute_kw": {
                        "post": {
                            "tags": ["User"],
                            "summary": "Execute Function",
                            "operationId": "ExecuteFunction",
                            "description": "By passing in the appropriate options, you can execute a function",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "method": {"type": "string", "description": "The name of the Method"},
                                                "args": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}},
                                                "kw": {"type": "object", "description": "Additional parameters for the methods"}
                                            },
                                            "required": ["method", "args"]
                                        }
                                    }
                                }
                            },
                            "parameters": [
                                {
                                    "in": "path",
                                    "name": "model_name",
                                    "required": True,
                                    "description": "Model Name",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "header",
                                    "name": "api-key",
                                    "required": True,
                                    "description": "Api Key for authentication",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "header",
                                    "name": "token",
                                    "description": "Token for authentication",
                                    "schema": {"type": "string"}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Method Executed Successfully",
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "array", "items": {"$ref": "#/components/schemas/ExecuteFunction"}}
                                        }
                                    }
                                },
                                "400": {"description": "bad input parameter"}
                            }
                        }
                    },
                    "/api/generate_token": {
                        "post": {
                            "tags": ["User"],
                            "summary": "Generate the User-Token",
                            "operationId": "GenerateToken",
                            "description": "By passing in the appropriate options, you can generate the token for the user",
                            "parameters": [
                                {
                                    "in": "header",
                                    "name": "api-key",
                                    "required": True,
                                    "description": "Api Key for authentication",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "in": "header",
                                    "name": "login",
                                    "required": True,
                                    "description": "Token for authentication",
                                    "schema": {"type": "string"}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "search results matching criteria",
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "array", "items": {"$ref": "#/components/schemas/GenerateToken"}}
                                        }
                                    }
                                },
                                "400": {"description": "bad input parameter"}
                            }
                        }
                    }
                },
               
        "components": {
                        "schemas": {
                            "SearchRecords": {
                                "type": "object",
                                "required": ["success", "user_id", "permissions", "data"],
                                "properties": {
                                    "success": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "true"
                                    },
                                    "user_id": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "permissions": {
                                        "type": "object",
                                        "required": ["read"],
                                        "properties": {
                                            "read": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            }
                                        }
                                    },
                                    "data": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {
                                                    "type": "string",
                                                    "format": "uuid",
                                                    "example": "Test"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "SearchRecord": {
                                "type": "object",
                                "required": ["success", "message", "responseCode", "object_name", "record_id", "user_id", "permissions", "data"],
                                "properties": {
                                    "success": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "true"
                                    },
                                    "message": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "Allowed Product Models Permission"
                                    },
                                    "responseCode": {
                                        "type": "integer",
                                        "example": 200
                                    },
                                    "object_name": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "test.model"
                                    },
                                    "record_id": {
                                        "type": "integer",
                                        "example": 23
                                    },
                                    "user_id": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "permissions": {
                                        "type": "object",
                                        "required": ["read"],
                                        "properties": {
                                            "read": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "write": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "create": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "delete": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            }
                                        }
                                    },
                                    "data": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {
                                                    "type": "string",
                                                    "format": "uuid",
                                                    "example": "Test"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "UpdateRecord": {
                                "type": "object",
                                "required": ["success", "message", "responseCode", "object_name", "record_id", "user_id", "permissions"],
                                "properties": {
                                    "success": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "true"
                                    },
                                    "message": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "Allowed Product Models Permission"
                                    },
                                    "responseCode": {
                                        "type": "integer",
                                        "example": 200
                                    },
                                    "object_name": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "test.model"
                                    },
                                    "record_id": {
                                        "type": "integer",
                                        "example": 23
                                    },
                                    "user_id": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "permissions": {
                                        "type": "object",
                                        "required": ["read"],
                                        "properties": {
                                            "read": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "write": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "create": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "delete": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            }
                                        }
                                    }
                                }
                            },
                            "DeleteRecord": {
                                "type": "object",
                                "required": ["success", "message", "responseCode", "object_name", "record_id", "user_id", "permissions"],
                                "properties": {
                                    "success": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "true"
                                    },
                                    "message": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "Allowed Product Models Permission"
                                    },
                                    "responseCode": {
                                        "type": "integer",
                                        "example": 200
                                    },
                                    "object_name": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "test.model"
                                    },
                                    "record_id": {
                                        "type": "integer",
                                        "example": 23
                                    },
                                    "user_id": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "permissions": {
                                        "type": "object",
                                        "required": ["read"],
                                        "properties": {
                                            "read": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "write": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "create": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "delete": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            }
                                        }
                                    }
                                }
                            },
                            "ModelSchema": {
                                "type": "object",
                                "required": ["success", "message", "responseCode", "object_name", "record_id", "user_id", "permissions"],
                                "properties": {
                                    "success": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "true"
                                    },
                                    "message": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "Allowed Product Models Permission"
                                    },
                                    "responseCode": {
                                        "type": "integer",
                                        "example": 200
                                    },
                                    "object_name": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "test.model"
                                    },
                                    "record_id": {
                                        "type": "integer",
                                        "example": 23
                                    },
                                    "user_id": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "permissions": {
                                        "type": "object",
                                        "required": ["read"],
                                        "properties": {
                                            "read": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "write": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "create": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "delete": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            }
                                        }
                                    },
                                    "data": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "field_name": {
                                                    "type": "string",
                                                    "format": "uuid",
                                                    "example": "name"
                                                },
                                                "field_type": {
                                                    "type": "string",
                                                    "format": "uuid",
                                                    "example": "char"
                                                },
                                                "label": {
                                                    "type": "string",
                                                    "format": "uuid",
                                                    "example": "Name"
                                                },
                                                "required": {
                                                    "type": "string",
                                                    "format": "uuid",
                                                    "example": "True"
                                                },
                                                "readonly": {
                                                    "type": "string",
                                                    "format": "uuid",
                                                    "example": "False"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "CreateRecords": {
                                "type": "object",
                                "required": ["success", "message", "responseCode", "object_name", "record_id", "user_id", "permissions"],
                                "properties": {
                                    "success": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "true"
                                    },
                                    "message": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "Allowed Product Models Permission"
                                    },
                                    "responseCode": {
                                        "type": "integer",
                                        "example": 200
                                    },
                                    "object_name": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "test.model"
                                    },
                                    "record_id": {
                                        "type": "integer",
                                        "example": 23
                                    },
                                    "user_id": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "permissions": {
                                        "type": "object",
                                        "required": ["read"],
                                        "properties": {
                                            "read": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "write": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "create": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "delete": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            }
                                        }
                                    }
                                }
                            },
                            "ExecuteFunction": {
                                "type": "object",
                                "required": ["success", "message", "responseCode", "object_name", "model_id", "permissions", "result"],
                                "properties": {
                                    "success": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "true"
                                    },
                                    "message": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "Method Successfully Called"
                                    },
                                    "responseCode": {
                                        "type": "integer",
                                        "example": 200
                                    },
                                    "object_name": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "test.model"
                                    },
                                    "model_id": {
                                        "type": "integer",
                                        "example": 23
                                    },
                                    "permissions": {
                                        "type": "object",
                                        "required": ["read"],
                                        "properties": {
                                            "read": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "write": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "create": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            },
                                            "delete": {
                                                "type": "string",
                                                "format": "uuid",
                                                "example": "true"
                                            }
                                        }
                                    },
                                    "result": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "properties": {
                                                    "name": {
                                                        "type": "string",
                                                        "format": "uuid",
                                                        "example": "Test"
                                                    },
                                                    "id": {
                                                        "type": "integer",
                                                        "format": "uuid",
                                                        "example": 23
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "GenerateToken": {
                                "type": "object",
                                "required": ["success", "message", "responseCode", "user_id", "object_name"],
                                "properties": {
                                    "success": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "true"
                                    },
                                    "message": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "Token Generated"
                                    },
                                    "responseCode": {
                                        "type": "integer",
                                        "example": 200
                                    },
                                    "user_id": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "object_name": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2dpbiI6ImFkbWluIiwidWlkIjoyfQ.bboTKrL02HH0BCdTX5NcH9EXjNUYZyHtHl4EVsL3ZMw"
                                    }
                                }
                            }
                        }
                    }
    }



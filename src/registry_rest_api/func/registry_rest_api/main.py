import azure.functions as func

from shared_code.app import app
from shared_code.http_asgi import AsgiMiddleware


def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    return AsgiMiddleware(app).handle(req, context)

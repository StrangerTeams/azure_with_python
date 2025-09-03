import azure.functions as func
import logging

app = func.FunctionApp()

@app.function_name(name="Function1")
@app.route(route="Function1", auth_level=func.AuthLevel.ANONYMOUS)
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    return func.HttpResponse(
        "Welcome to Azure Functions!",
        status_code=200
    )
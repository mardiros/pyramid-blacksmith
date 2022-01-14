from typing import cast

import uvicorn
from asgiref.typing import ASGI3Application
from starlette.applications import Starlette
from starlette.responses import JSONResponse

app = Starlette(debug=True)

USERS = {
    "naruto": {
        "username": "naruto",
        "firstname": "Naruto",
        "lastname": "Uzumaki",
        "email": "naruto@konoa.city",
        "roles": ["genin"],
    },
    "hinata": {
        "username": "hinata",
        "firstname": "Hinata",
        "lastname": "Hyûga",
        "email": "hinata@konoa.city",
        "roles": ["chunin"],
    },
}


@app.route("/v1/users/{username}", methods=["GET"])
async def show_user(request):
    authorization = request.headers.get("Authorization")
    if not authorization:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    try:
        scheme, value = authorization.split()
    except Exception:
        return JSONResponse({"detail": "Malformed authorization"}, status_code=400)

    if scheme != "Bearer" or value != "kinoe":
        return JSONResponse({"detail": "Forbidden"}, status_code=403)

    username = request.path_params["username"]
    try:
        return JSONResponse(USERS[username])
    except KeyError:
        return JSONResponse({"detail": "user not found"}, status_code=404)


if __name__ == "__main__":
    uvicorn.run(cast(ASGI3Application, app), host="0.0.0.0", port=8000)

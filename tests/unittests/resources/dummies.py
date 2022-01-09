import blacksmith
from blacksmith import PathInfoField, Request, Response


class GetParam(Request):
    name: str = PathInfoField()


class GetReturn(Response):
    pass


blacksmith.register(
    "api",
    "dummy",
    "srv",
    None,
    path="/dummies/{name}",
    contract={"GET": (GetParam, GetReturn)},
)

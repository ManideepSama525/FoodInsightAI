from app.main import app

def walk(routes, prefix=""):
    for r in routes:
        path = getattr(r, "path", None)
        if path is not None:
            print(
                "ROUTE",
                prefix + path,
                getattr(r, "methods", None),
                getattr(r, "name", None),
                getattr(getattr(r, "endpoint", None), "__module__", None),
            )

        nested = getattr(r, "routes", None)
        if nested:
            nested_prefix = prefix + (getattr(r, "prefix", "") or "")
            walk(nested, nested_prefix)

print("=== APP ROUTE TREE ===")
walk(app.routes)

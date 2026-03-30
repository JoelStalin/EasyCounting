from fastapi import APIRouter, FastAPI

from app.application.router_registration import include_router_entries


def test_include_router_entries_applies_prefix_and_routes() -> None:
    app = FastAPI()

    router = APIRouter()

    @router.get('/health')
    def health() -> dict[str, str]:
        return {'status': 'ok'}

    include_router_entries(app, [(router, None)], prefix='/api/v1')

    route_paths = {route.path for route in app.routes}
    assert '/api/v1/health' in route_paths


def test_include_router_entries_applies_optional_tag() -> None:
    app = FastAPI()

    router = APIRouter()

    @router.get('/status')
    def status() -> dict[str, str]:
        return {'status': 'ok'}

    include_router_entries(app, [(router, 'infra')], prefix='/internal')

    openapi = app.openapi()
    get_status = openapi['paths']['/internal/status']['get']
    assert 'infra' in get_status['tags']

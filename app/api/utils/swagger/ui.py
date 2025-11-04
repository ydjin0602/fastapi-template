import json

from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.openapi.docs import swagger_ui_default_parameters
from starlette.responses import HTMLResponse


def get_swagger_ui_html(
    *,
    openapi_url: str = '/openapi.json',
    title: str = 'VPN-PORT',
    swagger_js_url: str = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js',
    swagger_css_url: str = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css',
    swagger_favicon_url: str = 'https://cheers.su/favicon.svg',
    oauth2_redirect_url: str | None = None,
    init_oauth: dict[str, Any] | None = None,
    swagger_ui_parameters: dict[str, Any] | None = None,
    custom_js_url: str
    | None = 'https://unpkg.com/swagger-ui-plugin-hierarchical-tags@1.0.4/build/index.js',
) -> HTMLResponse:
    """Метод для генерации кастомного html сваггера."""
    current_swagger_ui_parameters = swagger_ui_default_parameters.copy()
    if swagger_ui_parameters:
        current_swagger_ui_parameters.update(swagger_ui_parameters)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
    <link rel="shortcut icon" href="{swagger_favicon_url}">
    <title>{title}</title>
    </head>
    <body>
    <div id="swagger-ui">
    </div>
    """

    if custom_js_url:
        html += f"""
        <script src="{custom_js_url}"></script>
        """

    html += f"""
    <script src="{swagger_js_url}"></script>
    <!-- `SwaggerUIBundle` is now available on the page -->
    <script>
    const ui = SwaggerUIBundle({{
        url: '{openapi_url}',
        dom_id: "#swagger",
        plugins: [
          HierarchicalTagsPlugin
        ],
        hierarchicalTagSeparator: /[:|]/,
    """

    for key, value in current_swagger_ui_parameters.items():
        html += f'{json.dumps(key)}: {json.dumps(jsonable_encoder(value))},\n'

    if oauth2_redirect_url:
        html += f"oauth2RedirectUrl: window.location.origin + '{oauth2_redirect_url}',"

    html += """
    presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
    })"""

    if init_oauth:
        html += f"""
        ui.initOAuth({json.dumps(jsonable_encoder(init_oauth))})
    """

    html += """
    </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

import json

from django.utils.translation import gettext_lazy as _
from typing import Any, Optional, Union
from rest_framework.renderers import JSONRenderer


class GenericJSONRenderer(JSONRenderer):
    charset = "utf-8"
    object_label = "object"  # a key which the actual data will be nested in the json

    def render(
        self,
        data: Any,
        accepted_media_type: Optional[str] = None,
        renderer_context: Optional[str] = None,
    ) -> Union[bytes, str]:

        # renderer_context contains info the request, response and how the view is processed.
        if renderer_context is None:
            renderer_context = {}

        view = renderer_context.get("view")
        if hasattr(view, "object_label"):
            object_label = view.object_label
        else:
            object_label = self.object_label

        response = renderer_context.get("response")
        if not response:
            raise ValueError(_("Response not found in the renderer context"))

        status_code = response.status_code
        errors = data.get("errors", None)
        if errors is not None:
            return super(GenericJSONRenderer, self).render(data)

        return json.dumps({"status_code": status_code, object_label: data}).encode(
            self.charset
        )

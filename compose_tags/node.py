from django.template import Node
from django.template.library import InclusionNode
from django.template.loader_tags import construct_relative_path

COMPOSE_CONTEXT_KEY = "_django_compose_context_key"


class ComposeNode(Node):
    def __init__(
        self,
        template,
        nodelist,
        extra_context,
        takes_context,
    ):
        super().__init__()
        self.nodelist = nodelist
        self.template = template
        self.extra_context = extra_context or {}
        self.takes_context = takes_context

    def render(self, context):
        template = self.get_template(context)
        render_context = self.get_render_context(context)
        if self.takes_context:
            with context.push(**render_context):
                return template.render(context)
        return template.render(context.new(render_context))

    def get_template(self, context):
        """Very similar implementation to django.template.loader_tags.IncludeNode"""
        template = self.template.resolve(context)
        # Does this quack like a Template?
        if not callable(getattr(template, "render", None)):
            # If not, try the cache and select_template().
            template_name = template or ()
            if isinstance(template_name, str):
                template_name = (
                    construct_relative_path(
                        self.origin.template_name,
                        template_name,
                    ),
                )
            else:
                template_name = tuple(template_name)
            cache = context.render_context.dicts[0].setdefault(self, {})
            template = cache.get(template_name)
            if template is None:
                template = context.template.engine.select_template(template_name)
                cache[template_name] = template
        # Use the base.Template of a backends.django.Template.
        elif hasattr(template, "template"):
            template = template.template
        return template

    def get_render_context(self, context):
        values = {
            name: var.resolve(context) for name, var in self.extra_context.items()
        }
        values["children"] = self.nodelist.render(context)
        # Copy across the CSRF token, if present, because we need instructions for using CSRF
        # protection to be as simple as possible.
        if not self.takes_context:
            csrf_token = context.get("csrf_token")
            if csrf_token is not None:
                values["csrf_token"] = csrf_token
        return values


class CompositionNode(InclusionNode):
    def __init__(self, func, takes_context, args, kwargs, filename, nodelist):
        super().__init__(func, takes_context, args, kwargs, filename)
        self.nodelist = nodelist

    def get_resolved_arguments(self, context):
        resolved_args, resolved_kwargs = super().get_resolved_arguments(context)
        children = self.nodelist.render(context)
        resolved_args = [children] + resolved_args
        return resolved_args, resolved_kwargs


class DefineNode(Node):
    def __init__(self, target_var, nodelist):
        self.target_var = target_var
        self.nodelist = nodelist

    def render(self, context):
        context[self.target_var] = self.nodelist.render(context)
        return ""

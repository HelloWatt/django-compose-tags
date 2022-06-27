from django.template import Library, Node, TemplateSyntaxError
from django.template.base import token_kwargs
from django.template.library import TagHelperNode
from django.template.loader_tags import construct_relative_path

register = Library()

COMPOSE_CONTEXT_KEY = "_django_compose_context_key"


def kwargs_only(*args, **kwargs):
    return kwargs


def single_or_array_key(is_array):
    if is_array:
        return "array"
    return "single"


class ComposeNode(TagHelperNode):
    child_nodelists = ("nodelist_children", "nodelist_slots")

    def __init__(
        self,
        template,
        takes_context,
        args,
        kwargs,
        nodelist,
        func=kwargs_only,
    ):
        super().__init__(func, takes_context, args, kwargs)
        self.template = template
        self.nodelist = nodelist

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
        resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
        new_context = self.func(*resolved_args, **resolved_kwargs)
        csrf_token = context.get("csrf_token")
        if csrf_token is not None:
            new_context["csrf_token"] = csrf_token
        return new_context

    def get_resolved_arguments(self, context):
        resolved_args, resolved_kwargs = super().get_resolved_arguments(context)
        with context.render_context.push_state(self.nodelist):
            context.render_context[COMPOSE_CONTEXT_KEY] = {"single": [], "array": []}
            resolved_kwargs["children"] = self.nodelist.render(context)
            single_slots = context.render_context[COMPOSE_CONTEXT_KEY]["single"]
            array_slots = context.render_context[COMPOSE_CONTEXT_KEY]["array"]
        single_slot_names = set()
        for slot_name, slot_rendered in single_slots:
            if slot_name in single_slot_names:
                raise TemplateSyntaxError("slot %s already declared" % slot_name)
            if slot_name in resolved_kwargs:
                raise TemplateSyntaxError(
                    "%s is already a keyword argument, hence slot %s is forbidden"
                    % (slot_name, slot_name)
                )
            single_slot_names.add(slot_name)
            resolved_kwargs[slot_name] = slot_rendered
        array_slot_names = set()
        for slot_name, slot_rendered in array_slots:
            if slot_name in single_slot_names:
                raise TemplateSyntaxError(
                    "%s is already a single value slot, hence slot[] %s is forbidden"
                    % (slot_name, slot_name)
                )
            if slot_name in resolved_kwargs and slot_name not in array_slot_names:
                raise TemplateSyntaxError(
                    "%s is already a keyword argument, hence slot[] %s is forbidden"
                    % (slot_name, slot_name)
                )
            array_slot_names.add(slot_name)
            if slot_name in resolved_kwargs:
                resolved_kwargs[slot_name].append(slot_rendered)
            else:
                resolved_kwargs[slot_name] = [slot_rendered]
        return resolved_args, resolved_kwargs


@register.tag("compose")
def do_compose(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "%r tag takes at least one argument: the name of the template to "
            "be included." % bits[0]
        )
    template_name = construct_relative_path(parser.origin.template_name, bits[1])
    remaining_bits = bits[2:]
    takes_context = "takes_context" in remaining_bits
    kwargs = token_kwargs(remaining_bits, parser, support_legacy=False)
    if "children" in kwargs:
        raise TemplateSyntaxError(
            "%r tag must not take children as a keyword argument." % bits[0]
        )
    nodelist = parser.parse(("endcompose",))
    parser.next_token()
    return ComposeNode(
        parser.compile_filter(template_name),
        takes_context,
        [],
        kwargs,
        nodelist,
    )


class SlotNode(Node):
    def __init__(self, name, nodelist, slot_type):
        self.name = name
        self.nodelist = nodelist
        self.slot_type = slot_type

    def render(self, context):
        if COMPOSE_CONTEXT_KEY not in context.render_context:
            raise TemplateSyntaxError(
                "slot must be a descendant of compose or a descendant of a compose component"
            )
        context.render_context[COMPOSE_CONTEXT_KEY][self.slot_type].append(
            (self.name, self.nodelist.render(context))
        )
        return ""


@register.tag("slot")
def do_slot(parser, token, slot_type="single"):
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])
    if bits[1] == "children":
        raise TemplateSyntaxError("'%s' must not be named children." % bits[0])
    nodelist = parser.parse(("endslot",))
    parser.next_token()
    return SlotNode(bits[1], nodelist, slot_type)


@register.tag("slot[]")
def do_slot_array(parser, token):
    return do_slot(parser, token, slot_type="array")

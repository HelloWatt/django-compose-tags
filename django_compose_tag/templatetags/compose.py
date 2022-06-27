from django.template import Library, Node, TemplateSyntaxError
from django.template.base import NodeList, token_kwargs
from django.template.library import TagHelperNode
from django.template.loader_tags import construct_relative_path

register = Library()


def kwargs_only(*args, **kwargs):
    return kwargs


class ComposeNode(TagHelperNode):
    child_nodelists = ("nodelist_children", "nodelist_slots")

    def __init__(
        self,
        template,
        takes_context,
        args,
        kwargs,
        nodelist_children,
        nodelist_slots,
        func=kwargs_only,
    ):
        super().__init__(func, takes_context, args, kwargs)
        self.template = template
        self.nodelist_children = nodelist_children
        self.nodelist_slots = nodelist_slots

    def render(self, context):
        template = self.get_template(context)
        render_context = self.get_render_context(context)
        return template.render(render_context)

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
        return context.new(new_context)

    def get_resolved_arguments(self, context):
        resolved_args, resolved_kwargs = super().get_resolved_arguments(context)
        for slot_node in self.nodelist_slots:
            slot_rendered = slot_node.render(context)
            if slot_node.name in resolved_kwargs:
                if isinstance(resolved_kwargs[slot_node.name], list):
                    resolved_kwargs[slot_node.name].append(slot_rendered)
                else:
                    resolved_kwargs[slot_node.name] = [
                        resolved_kwargs[slot_node.name],
                        slot_rendered,
                    ]
            else:
                resolved_kwargs[slot_node.name] = slot_rendered
        resolved_kwargs["children"] = self.nodelist_children.render(context)
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
    kwargs = token_kwargs(remaining_bits, parser, support_legacy=False)
    takes_context = kwargs.pop("takes_context", False)  # TODO: test
    if "children" in kwargs:
        raise TemplateSyntaxError(
            "%r tag must not take children as a keyword argument." % bits[0]
        )
    nodelist = parser.parse(("endcompose",))
    parser.next_token()
    nodelist_children = NodeList()
    nodelist_slots = NodeList()
    for node in nodelist:
        if isinstance(node, SlotNode):
            if node.name in kwargs:
                raise TemplateSyntaxError(
                    "%r tag received %r both as a keyword argument and a slot."
                    % (bits[0], node.name)
                )
            nodelist_slots.append(node)
            # TODO: handle deep slots
        else:
            nodelist_children.append(node)
    return ComposeNode(
        parser.compile_filter(template_name),
        takes_context,
        [],
        kwargs,
        nodelist_children,
        nodelist_slots,
    )


class SlotNode(Node):
    def __init__(self, name, nodelist):
        self.name = name
        self.nodelist = nodelist

    def render(self, context):
        return self.nodelist.render(context)


@register.tag("slot")
def do_slot(parser, token):
    # TODO: raise if not a descendant of compose
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])
    if bits[1] == "children":
        raise TemplateSyntaxError("'%s' must not be named children." % bits[0])
    nodelist = parser.parse(("endslot",))
    parser.next_token()
    return SlotNode(bits[1], nodelist)

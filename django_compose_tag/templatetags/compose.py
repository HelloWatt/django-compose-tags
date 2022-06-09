from django.template import Library, Node, TemplateSyntaxError
from django.template.base import NodeList, token_kwargs
from django.template.loader_tags import construct_relative_path

register = Library()


class ComposeNode(Node):
    child_nodelists = ("nodelist_children", "nodelist_slots")

    def __init__(self, template, extra_context, nodelist_children, nodelist_slots):
        self.template = template
        self.extra_context = extra_context
        self.nodelist_children = nodelist_children
        self.nodelist_slots = nodelist_slots
        super().__init__()

    def render(self, context):
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
        values = {
            name: var.resolve(context) for name, var in self.extra_context.items()
        }
        values.update({node.name: node.render(context) for node in self.nodelist_slots})
        values["children"] = self.nodelist_children.render(context)
        return template.render(context.new(values))


@register.tag("compose")
def do_compose(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "%r tag takes at least one argument: the name of the template to "
            "be included." % bits[0]
        )
    remaining_bits = bits[2:]
    extra_context = token_kwargs(remaining_bits, parser, support_legacy=False)
    if "children" in extra_context:
        raise TemplateSyntaxError(
            "%r tag must not take children as a keyword argument." % bits[0]
        )
    bits[1] = construct_relative_path(parser.origin.template_name, bits[1])
    nodelist = parser.parse(("endcompose",))
    parser.next_token()
    nodelist_children = NodeList()
    nodelist_slots = NodeList()
    for node in nodelist:
        if isinstance(node, SlotNode):
            if node.name == "children":
                raise TemplateSyntaxError("%r must not be named children." % bits[0])
            if node.name in extra_context:
                raise TemplateSyntaxError(
                    "%r tag received %r both as a keyword argument and a slot."
                    % (bits[0], node.name)
                )
            nodelist_slots.append(node)
        else:
            nodelist_children.append(node)
    return ComposeNode(
        parser.compile_filter(bits[1]), extra_context, nodelist_children, nodelist_slots
    )


class SlotNode(Node):
    def __init__(self, name, nodelist):
        self.name = name
        self.nodelist = nodelist

    def render(self, context):
        return self.nodelist.render(context)


@register.tag("slot")
def do_slot(parser, token):
    # TODO: how do we raise a TemplateSyntaxError if slot is not a direct child of compose?
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])
    nodelist = parser.parse(("endslot",))
    parser.next_token()
    return SlotNode(bits[1], nodelist)

from django.template import Library, TemplateSyntaxError
from django.template.base import token_kwargs
from django.template.loader_tags import construct_relative_path

from compose_tags.node import ComposeNode, DefineNode

register = Library()


@register.tag("compose")
def do_compose(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "%r tag takes at least one argument: the name of the template to "
            "be included." % bits[0]
        )
    template_bit = construct_relative_path(parser.origin.template_name, bits[1])
    remaining_bits = bits[2:]

    takes_context = "takes_context" in remaining_bits
    extra_context = token_kwargs(remaining_bits, parser)
    if "children" in extra_context:
        raise TemplateSyntaxError(
            "%r must not take children as a keyword argument." % bits[0]
        )
    nodelist = parser.parse(('endcompose', ))
    parser.next_token()

    return ComposeNode(
        parser.compile_filter(template_bit),
        nodelist,
        extra_context,
        takes_context,
    )


@register.tag("define")
def do_define(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError(
            "define tag takes exactly one argument: the name of the template variable that should store the result. Eg: {% define myvar %}value{% enddefine %}"
        )
    target_var = bits[1]

    nodelist = parser.parse(('enddefine', ))
    parser.next_token()
    return DefineNode(target_var, nodelist)

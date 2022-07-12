from django.template import Library, TemplateSyntaxError
from django.template.base import token_kwargs
from django.template.loader_tags import construct_relative_path

from django_compose_tag.node import ComposeNode, DefineNode

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
    nodelist = parser.parse((f"endcompose",))
    parser.next_token()

    return ComposeNode(
        parser.compile_filter(template_bit),
        nodelist,
        extra_context,
        takes_context,
    )


# TODO rename templatetags/compose.py or split in to files?
@register.tag("define")
def do_define(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError(
            "%r tag takes one argument: the name of the template variable that should store the result."
            % bits[0]
        )

    nodelist = parser.parse((f"enddefine",))
    parser.next_token()

    return DefineNode(bits[-1], nodelist)

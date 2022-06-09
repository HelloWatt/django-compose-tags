import re

from django.template import Library, TemplateSyntaxError
from django.template.base import FILTER_SEPARATOR, token_kwargs
from django.template.loader_tags import construct_relative_path

from compose_tags.node import ComposeNode, DefineForNode, DefineNode

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


@register.tag("define")
def do_define(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError(
            "define tag takes exactly one argument: the name of the template variable that should store the result. Eg: {% define myvar %}value{% enddefine %}"
        )
    target_var = bits[1]

    nodelist = parser.parse((f"enddefine",))
    parser.next_token()
    return DefineNode(target_var, nodelist)


@register.tag("definelist")
def do_define_list(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "%r tag takes at least one argument: the name of the template variable that should store the result. Eg: {% definelist myvar for x in list %}item is {x}{% enddefinelist %}"
            % bits[0]
        )
    target_var = bits[1]

    if len(bits) == 2 or bits[2] != "for":
        raise TemplateSyntaxError(
            "definelist statements should be formated as {% definelist myvar for x in list %}"
        )

    # Most of this implementation come from django.template.defaulttags.do_for
    for_bits = bits[2:]
    is_reversed = for_bits[-1] == "reversed"
    in_index = -3 if is_reversed else -2
    if for_bits[in_index] != "in":
        raise TemplateSyntaxError(
            "'define myvar for' statements should use the format"
            " 'define myvar for x in y': %s" % token.contents
        )

    invalid_chars = frozenset((" ", '"', "'", FILTER_SEPARATOR))
    loopvars = re.split(r" *, *", " ".join(for_bits[1:in_index]))
    for var in loopvars:
        if not var or not invalid_chars.isdisjoint(var):
            raise TemplateSyntaxError(
                "'define myvar for' received an invalid argument:"
                " %s" % token.contents
            )

    sequence = parser.compile_filter(for_bits[in_index + 1])
    nodelist_loop = parser.parse(
        (
            "empty",
            "enddefinelist",
        )
    )
    token = parser.next_token()
    if token.contents == "empty":
        nodelist_empty = parser.parse(("enddefinelist",))
        parser.delete_first_token()
    else:
        nodelist_empty = None
    return DefineForNode(
        target_var, loopvars, sequence, is_reversed, nodelist_loop, nodelist_empty
    )

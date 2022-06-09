import functools
from inspect import getfullargspec, unwrap

import django.template
from django.template import TemplateSyntaxError
from django.template.library import parse_bits

from compose_tags.node import CompositionNode


def default_composition(children, **kwargs):
    kwargs["children"] = children
    return kwargs


def parse_bits_with_children(
    parser,
    bits,
    params,
    varargs,
    varkw,
    defaults,
    kwonly,
    kwonly_defaults,
    takes_context,
    name,
):
    """
    Do the same as parse_bits, except that context is the second argument, not the first.
    The first one being children.
    """
    if not params or not params[0] == "children":
        raise TemplateSyntaxError(
            "'%s' must have a first argument of 'children'" % name
        )
    params = params[1:]
    if takes_context:
        if params and params[0] == "context":
            params = params[1:]
        else:
            raise TemplateSyntaxError(
                "'%s' is decorated with takes_context=True so it must "
                "have a second argument of 'context'" % name
            )
    return parse_bits(
        parser,
        bits,
        params,
        varargs,
        varkw,
        defaults,
        kwonly,
        kwonly_defaults,
        False,
        name,
    )


def composition_tag(
    filename,
    takes_context=False,
):
    """
    Register a callable as a composition tag:

    @register.tag
    @composition_tag('card.html', takes_context=True)
    def card(children, context, footer):
        return {
            "children": children,
            "footer": footer or default_footer,
        }
    """

    def dec(func_or_parser, token=None):
        func = default_composition if token else func_or_parser
        (
            params,
            varargs,
            varkw,
            defaults,
            kwonly,
            kwonly_defaults,
            _,
        ) = getfullargspec(unwrap(func))

        @functools.wraps(func)
        def compile_func(parser, token):
            name, *bits = token.split_contents()
            args, kwargs = parse_bits_with_children(
                parser,
                bits,
                params,
                varargs,
                varkw,
                defaults,
                kwonly,
                kwonly_defaults,
                takes_context,
                name,
            )
            nodelist = parser.parse((f"end{name}",))
            parser.next_token()

            return CompositionNode(
                func, takes_context, args, kwargs, filename, nodelist
            )

        if token:
            return compile_func(func_or_parser, token)
        return compile_func

    dec.__name__ = ".".join(filename.split("/")[-1].split(".")[:-1])

    return dec

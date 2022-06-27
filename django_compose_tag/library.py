import functools
from inspect import getfullargspec, unwrap

import django.template
from django.template import TemplateSyntaxError
from django.template.library import parse_bits

from django_compose_tag.node import CompositionNode


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
    # TODO: test remove children from params.
    # TODO: ensure it error when children as kwargs
    # TODO: ensure same error when children here and in do_compose
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


class Library(django.template.Library):
    def composition_tag(
        self,
        filename,
        name=None,
        takes_context=False,
    ):
        """
        Register a callable as a composition tag:

        @register.composition_tag('menu.html')
        def show_menu(menu, **kwargs):
            entries = menu.entries_set.all()
            return {
              **kwargs
              'entries': entries
            }
        """

        def dec(func):
            (
                params,
                varargs,
                varkw,
                defaults,
                kwonly,
                kwonly_defaults,
                _,
            ) = getfullargspec(unwrap(func))
            function_name = name or getattr(func, "_decorated_function", func).__name__

            @functools.wraps(func)
            def compile_func(parser, token):
                bits = token.split_contents()[1:]
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
                    function_name,
                )
                nodelist = parser.parse((f"end{function_name}",))
                parser.next_token()

                return CompositionNode(
                    func, takes_context, args, kwargs, filename, nodelist
                )

            self.tag(function_name, compile_func)
            return func

        return dec

from django.template import Library

from compose_tags import composition_tag

register = Library()


register.tag(composition_tag("composition/test_csrf.html"))
register.tag("children", composition_tag("composition/button.html"))


@register.tag
@composition_tag("composition/button.html")
def auto_name(children):
    return {"children": children}


@register.tag
@composition_tag("composition/takes_context.html", takes_context=True)
def takes_context(children, context):
    return {"my_var": context["context_variable"]}


@register.tag
@composition_tag("composition/button.html")
def no_children():
    return


@register.tag
@composition_tag("composition/button.html", takes_context=True)
def no_context(children):
    return


@register.tag
@composition_tag("composition/button.html")
def with_args(children, disabled):
    return {
        "disabled": disabled,
        "children": children,
    }


@register.tag
@composition_tag("composition/button.html")
def with_kwargs(children, disabled):
    return {
        "disabled": disabled,
        "children": children,
    }

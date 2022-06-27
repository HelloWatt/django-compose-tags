from django_compose_tag import Library

register = Library()


def children_only(children):
    return {"children": children}


register.composition_tag("composition/test_csrf.html", "test_csrf")(children_only)
register.composition_tag("composition/button.html", "children")(children_only)


@register.composition_tag("composition/button.html")
def auto_name(children):
    return {"children": children}


@register.composition_tag(
    "composition/takes_context.html", "takes_context", takes_context=True
)
def takes_context(children, context):
    return {"my_var": context["context_variable"]}


@register.composition_tag("composition/button.html", "no_children")
def no_children():
    return


@register.composition_tag("composition/button.html", "no_context", takes_context=True)
def no_context(children):
    return

from django.template import Node, NodeList
from django.template.library import InclusionNode
from django.template.loader_tags import construct_relative_path
from django.utils.safestring import mark_safe

COMPOSE_CONTEXT_KEY = "_django_compose_context_key"


class ComposeNode(Node):
    def __init__(
        self,
        template,
        nodelist,
        extra_context,
        takes_context,
    ):
        super().__init__()
        self.nodelist = nodelist
        self.template = template
        self.extra_context = extra_context or {}
        self.takes_context = takes_context

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
        values = {
            name: var.resolve(context) for name, var in self.extra_context.items()
        }
        values["children"] = self.nodelist.render(context)
        # Copy across the CSRF token, if present, because we need instructions for using CSRF
        # protection to be as simple as possible.
        if not self.takes_context:
            csrf_token = context.get("csrf_token")
            if csrf_token is not None:
                values["csrf_token"] = csrf_token
        return values


class CompositionNode(InclusionNode):
    def __init__(self, func, takes_context, args, kwargs, filename, nodelist):
        super().__init__(func, takes_context, args, kwargs, filename)
        self.nodelist = nodelist

    def get_resolved_arguments(self, context):
        resolved_args, resolved_kwargs = super().get_resolved_arguments(context)
        children = self.nodelist.render(context)
        resolved_args = [children] + resolved_args
        return resolved_args, resolved_kwargs


class DefineNode(Node):
    def __init__(self, target_var, nodelist):
        self.target_var = target_var
        self.nodelist = nodelist

    def render(self, context):
        context[self.target_var] = self.nodelist.render(context)
        return ""


class DefineForNode(Node):
    # copypasta of django.template.defaulttags.ForNode with small modifications for target_var
    child_nodelists = ("nodelist_loop", "nodelist_empty")

    def __init__(
        self,
        target_var,
        loopvars,
        sequence,
        is_reversed,
        nodelist_loop,
        nodelist_empty=None,
    ):
        self.target_var = target_var  # divergence from ForNode
        self.loopvars, self.sequence = loopvars, sequence
        self.is_reversed = is_reversed
        self.nodelist_loop = nodelist_loop
        if nodelist_empty is None:
            self.nodelist_empty = NodeList()
        else:
            self.nodelist_empty = nodelist_empty

    def __repr__(self):
        reversed_text = " reversed" if self.is_reversed else ""
        return "<%s: %s, for %s in %s, tail_len: %d%s>" % (
            self.__class__.__name__,
            self.target_var,  # divergence from ForNode
            ", ".join(self.loopvars),
            self.sequence,
            len(self.nodelist_loop),
            reversed_text,
        )

    def render(self, context):
        list_value = []  # divergence from ForNode

        if "forloop" in context:
            parentloop = context["forloop"]
        else:
            parentloop = {}

        with context.push():
            values = self.sequence.resolve(context, ignore_failures=True)
            if values is None:
                values = []
            if not hasattr(values, "__len__"):
                values = list(values)
            len_values = len(values)
            if len_values < 1:
                list_value = [
                    self.nodelist_empty.render(context)
                ]  # divergence from ForNode
            else:  # divergence from ForNode
                if self.is_reversed:
                    values = reversed(values)
                num_loopvars = len(self.loopvars)
                unpack = num_loopvars > 1
                # Create a forloop value in the context.  We'll update counters on each
                # iteration just below.
                loop_dict = context["forloop"] = {"parentloop": parentloop}
                for i, item in enumerate(values):
                    nodelist = []  # divergence from ForNode
                    # Shortcuts for current loop iteration number.
                    loop_dict["counter0"] = i
                    loop_dict["counter"] = i + 1
                    # Reverse counter iteration numbers.
                    loop_dict["revcounter"] = len_values - i
                    loop_dict["revcounter0"] = len_values - i - 1
                    # Boolean values designating first and last times through loop.
                    loop_dict["first"] = i == 0
                    loop_dict["last"] = i == len_values - 1

                    pop_context = False
                    if unpack:
                        # If there are multiple loop variables, unpack the item into
                        # them.
                        try:
                            len_item = len(item)
                        except TypeError:  # not an iterable
                            len_item = 1
                        # Check loop variable count before unpacking
                        if num_loopvars != len_item:
                            raise ValueError(
                                "Need {} values to unpack in for loop; got {}. ".format(
                                    num_loopvars, len_item
                                ),
                            )
                        unpacked_vars = dict(zip(self.loopvars, item))
                        pop_context = True
                        context.update(unpacked_vars)
                    else:
                        context[self.loopvars[0]] = item

                    for node in self.nodelist_loop:
                        nodelist.append(node.render_annotated(context))

                    if pop_context:
                        # Pop the loop variables pushed on to the context to avoid
                        # the context ending up in an inconsistent state when other
                        # tags (e.g., include and with) push data to context.
                        context.pop()
                    list_value.append(
                        mark_safe("".join(nodelist))
                    )  # divergence from ForNode
        context[self.target_var] = list_value  # divergence from ForNode
        return ""  # divergence from ForNode

import django.template


class Library(django.template.Library):
    def component(self, name=None, compile_function=None):
        if name is None and compile_function is None:
            # @register.component()
            return self.tag_function
        elif name is not None and compile_function is None:
            if callable(name):
                # @register.component
                return self.tag_function(name)
            else:
                # @register.component('somename') or @register.component(name='somename')
                def dec(func):
                    return self.tag(name, func)

                return dec
        elif name is not None and compile_function is not None:
            # register.component('somename', somefunc)
            self.tags[name] = compile_function
            return compile_function
        else:
            raise ValueError(
                "Unsupported arguments to Library.tag: (%r, %r)"
                % (name, compile_function),
            )

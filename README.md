# Django Compose Tag

[![ci-status-image]][ci-status]
[![pypi-version]][pypi]

**Compose templates easily**

Django Compose tag provide a template tag for templates composition, 
with an api close to the `include` template tag.

---

# Overview

Write your template as you would for the include tags:

```jinja
<!-- card.html -->

<article class="card">
    <header class="card-header">{{ header }}</header>
    <div class="card-body">{{ children }}</div>
    <footer class="card-footer">{{ footer }}</footer>
</article>
```

## The `children` tag

`children` has a special meaning, it will be replaced by the content that's between the `{% compose %}` and `{% endcompose %}` tags.

```jinja
{% load compose %}

{% compose "card.html" header="My header" footer="My footer" %}
    <p>In {% now "Y" %} we can even put template tags and {{ variables }} in here.</p>
{% endcompose %}
```

## Similarities to include

card.html is a regular template, so we can use it with a regular include when parameters are simple

```jinja
{% include "card.html" with header="My header" children="My body" footer="My footer" %}
```

Yet there is small differences between `compose` and `include`:

* Like `include`, `compose` accept variables as parameters: `{% compose "card.html" header=var_from_context %}...{% endcompose %}`
* Like `include`, `compose` accept the same kind of parameters for the template, that include variables: `{% compose variable_template %}...{% endcompose %}`
* Unlike `include`, `compose` doesn't prefix its parameters with `with`
* Unlike `include`, `compose` doesn't have an `only` parameter. The parent context is never accessible within the composed template.

----

# Requirements

* Python (3.6, 3.7, 3.8, 3.9, 3.10, 3.11)
* Django (2.2, 3.0, 3.1, 3.2, 4.0, 4.1)

We **highly recommend** and only officially support the latest patch release of
each Python and Django series.

# Installation

Install using `pip`...

    pip install django-compose-tags

Add `'django_compose_tagss'` to your `INSTALLED_APPS` setting.
```python
INSTALLED_APPS = [
    ...
    'django_compose_tagss',
]
```

If you use compose a lot we recommend you add it as to your builtins:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "OPTIONS": {
            # ...
            "builtins": ["django_compose_tagss.templatetags.compose"],
        }
    }
]
```

---

# Alternatives

Django Compose Tag purposely provide a simple api based solely on templates.

If Django Compose Tag doesn't cover your requirements we recommend you take a look at [jinja][jinja-homepage].

[ci-status-image]: https://github.com/HelloWatt/django-compose-tags/actions/workflows/main.yml/badge.svg
[ci-status]: https://github.com/HelloWatt/django-compose-tags/actions/workflows/main.yml
[pypi-version]: https://img.shields.io/pypi/v/django-compose-tags.svg
[pypi]: https://pypi.org/project/django-compose-tags/


[jinja-homepage]: https://jinja.palletsprojects.com

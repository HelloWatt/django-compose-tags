import os

import pytest
from django.template import TemplateSyntaxError
from django.template.loader import get_template, render_to_string

dir_path = os.path.dirname(os.path.realpath(__file__))


def format_html(html):
    """
    Helper function that formats HTML for easier comparison
    :param html: raw HTML text to be formatted
    :return: Cleaned HTML with no newlines. Each line is striped
    """
    return "".join([line.strip() for line in html.split("\n")])


def read_expected(template_name):
    with open(os.path.join(dir_path, "expected", template_name), "r") as f:
        return f.read()


def gather_autotest_templates(autotest_folder: str):
    return [
        (os.path.join(autotest_folder, f), f)
        for f in os.listdir(os.path.join(dir_path, "templates", autotest_folder))
        if f.startswith("test")
    ]


@pytest.mark.parametrize(
    "template_name,template_expected",
    (
        pytest.param(
            template_name, template_name.replace("test_", "expect_"), id=filename
        )
        for template_name, filename in gather_autotest_templates("autotest")
    ),
)
def test_autotest_template(template_name, template_expected):
    rendered = render_to_string(
        template_name,
        context={
            "context_variable": "Context variable value",
            "csrf_token": "test_csrf",
        },
    )
    expected = get_template(template_expected)
    assert format_html(rendered) == format_html(expected.template.source)


# TODO: check error message. Where the exception come from is not tested
@pytest.mark.parametrize(
    "template_name",
    (
        pytest.param(template_name, id=filename)
        for template_name, filename in gather_autotest_templates(
            "autotest_template_syntax_error"
        )
    ),
)
def test_autotest_template_syntax_error(template_name):
    with pytest.raises(TemplateSyntaxError):
        render_to_string(template_name)

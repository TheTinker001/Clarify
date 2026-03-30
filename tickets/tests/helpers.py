from django.urls import reverse
from with_asserts.mixin import AssertHTMLMixin
from tickets.forms import CommentForm


def _reverse_with_next(url_name, next_url):
    """Extended version of reverse to generate URLs with redirects"""
    url = reverse(url_name)
    url += f"?next={next_url}"
    return url


def _valid_comment_post_data(self, text="Test comment"):
    """
    Build POST data for CommentForm without assuming the text field name.
    Uses the first non-attachment field as the comment text field.
    """
    form = CommentForm()
    # Select the first non-attachment field as the comment text field
    field_name = next(name for name in form.fields.keys() if name != "attachments")
    return {"action": "add_comment", field_name: text}


class LogInTester:
    """Class support login in tests."""

    def _is_logged_in(self):
        """Returns True if a user is logged in.  False otherwise."""

        return "_auth_user_id" in self.client.session.keys()


class MenuTesterMixin(AssertHTMLMixin):
    """Class to extend tests with tools to check the presents of menu items."""

    menu_urls = [reverse("password"), reverse("profile"), reverse("log_out")]

    def assert_menu(self, response):
        """Check that menu is present."""

        for url in self.menu_urls:
            with self.assertHTML(response, f'a[href="{url}"]'):
                pass

    def assert_no_menu(self, response):
        """Check that no menu is present."""

        for url in self.menu_urls:
            self.assertNotHTML(response, f'a[href="{url}"]')

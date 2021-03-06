##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2019, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################
import random

from regression.python_test_utils import test_utils
from regression.feature_utils.base_feature_test import BaseFeatureTest


class CheckRoleMembershipControlFeatureTest(BaseFeatureTest):
    """Tests to check role membership control for xss."""

    scenarios = [
        ("Tests to check if Role membership control is vulnerable to XSS",
         dict())
    ]

    role = ""

    def before(self):
        with test_utils.Database(self.server) as (connection, _):
            if connection.server_version < 90100:
                self.skipTest(
                    "Membership is not present in Postgres below PG v9.1")

        # create role
        self.role = "test_role" + str(random.randint(10000, 65535))

        # Some test function is needed for debugger
        test_utils.create_role(self.server, "postgres",
                               self.role)
        test_utils.create_role(self.server, "postgres",
                               "<h1>test</h1>")

    def runTest(self):
        self.page.wait_for_spinner_to_disappear()
        self.page.add_server(self.server)
        self._role_node_expandable(self.role)
        self._check_role_membership_control()

    def after(self):
        self.page.remove_server(self.server)
        test_utils.drop_role(self.server, "postgres",
                             self.role)
        test_utils.drop_role(self.server, "postgres",
                             "<h1>test</h1>")

    def _role_node_expandable(self, role):
        self.page.toggle_open_server(self.server['name'])
        self.page.toggle_open_tree_item('Login/Group Roles')
        self.page.select_tree_item(role)

    def _check_role_membership_control(self):
        self.page.driver.find_element_by_link_text("Object").click()
        self.page.driver.find_element_by_link_text("Properties...").click()
        # self.page.find_by_partial_link_text("Membership").click()
        self.click_membership_tab()
        # Fetch the source code for our custom control
        source_code = self.page.find_by_xpath(
            "//div[contains(@class,'rolmembership')]"
        ).get_attribute('innerHTML')

        self._check_escaped_characters(
            source_code,
            '&lt;h1&gt;test&lt;/h1&gt;',
            'Role Membership Control'
        )
        self.page.find_by_xpath(
            "//button[contains(@type, 'cancel') and "
            "contains(.,'Cancel')]"
        ).click()

    def _check_escaped_characters(self, source_code, string_to_find, source):
        # For XSS we need to search against element's html code
        assert source_code.find(string_to_find) != - \
            1, "{0} might be vulnerable to XSS ".format(source)

    def click_membership_tab(self):
        """This will click and open membership tab of role"""
        success = False
        attempts = 3
        while not success and attempts > 0:
            membership_tab_link = self.page.find_by_xpath(
                "//a[normalize-space(text())='Membership']")
            membership_tab_link.click()
            try:
                self.page.find_by_xpath("//input[@placeholder="
                                        "'Select members']")
                break
            except Exception as e:
                attempts -= 1
                pass

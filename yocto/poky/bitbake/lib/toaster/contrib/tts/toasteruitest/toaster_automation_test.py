#!/usr/bin/python
# Copyright

# DESCRIPTION
# This is toaster automation base class and test cases file

# History:
# 2015.03.09  inital version
# 2015.03.23  adding toaster_test.cfg, run_toastertest.py so we can run case by case from outside

# Briefs:
# This file is comprised of 3 parts:
# I:   common utils like sorting, getting attribute.. etc
# II:  base class part, which complies with unittest frame work and
#      contains class selenium-based functions
# III: test cases
#      to add new case: just implement new test_xxx() function in class toaster_cases

# NOTES for cases:
# case 946:
# step 6 - 8 needs to be observed using screenshots
# case 956:
# step 2 - 3 needs to be run manually

import unittest, time, re, sys, getopt, os, logging, string, errno, exceptions
import shutil, argparse, ConfigParser, platform
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select


###########################################
#                                         #
# PART I: utils stuff                     #
#                                         #
###########################################

class Listattr(object):
    """
    Set of list attribute. This is used to determine what the list content is.
    Later on we may add more attributes here.
    """
    NULL = "null"
    NUMBERS = "numbers"
    STRINGS = "strings"
    PERCENT = "percentage"
    SIZE = "size"
    UNKNOWN = "unknown"


def get_log_root_dir():
    max_depth = 5
    parent_dir = '../'
    for number in range(0, max_depth):
        if os.path.isdir(sys.path[0] + os.sep + (os.pardir + os.sep)*number + 'log'):
            log_root_dir = os.path.abspath(sys.path[0] + os.sep + (os.pardir + os.sep)*number + 'log')
            break

    if number == (max_depth - 1):
        print 'No log dir found. Please check'
        raise Exception

    return log_root_dir


def mkdir_p(dir):
    try:
        os.makedirs(dir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dir):
            pass
        else:
            raise


def get_list_attr(testlist):
    """
    To determine the list content
    """
    if not testlist:
        return Listattr.NULL
    listtest = testlist[:]
    try:
        listtest.remove('')
    except ValueError:
        pass
    pattern_percent = re.compile(r"^([0-9])+(\.)?([0-9])*%$")
    pattern_size = re.compile(r"^([0-9])+(\.)?([0-9])*( )*(K)*(M)*(G)*B$")
    pattern_number = re.compile(r"^([0-9])+(\.)?([0-9])*$")
    def get_patterned_number(pattern, tlist):
        count = 0
        for item in tlist:
            if re.search(pattern, item):
                count += 1
        return count
    if get_patterned_number(pattern_percent, listtest) == len(listtest):
        return Listattr.PERCENT
    elif get_patterned_number(pattern_size, listtest) == len(listtest):
        return Listattr.SIZE
    elif get_patterned_number(pattern_number, listtest) == len(listtest):
        return Listattr.NUMBERS
    else:
        return Listattr.STRINGS


def is_list_sequenced(testlist):
    """
    Function to tell if list is sequenced
    Currently we may have list made up of: Strings ; numbers ; percentage ; time; size
    Each has respective way to determine if it's sequenced.
    """
    test_list = testlist[:]
    try:
        test_list.remove('')
    except ValueError:
        pass

    if get_list_attr(testlist) == Listattr.NULL :
        return True

    elif get_list_attr(testlist) == Listattr.STRINGS :
        return (sorted(test_list) == test_list)

    elif get_list_attr(testlist) == Listattr.NUMBERS :
        list_number = []
        for item in test_list:
            list_number.append(eval(item))
        return (sorted(list_number) == list_number)

    elif get_list_attr(testlist) == Listattr.PERCENT :
        list_number = []
        for item in test_list:
            list_number.append(eval(item.strip('%')))
        return (sorted(list_number) == list_number)

    elif get_list_attr(testlist) == Listattr.SIZE :
        list_number = []
        # currently SIZE is splitted by space
        for item in test_list:
            if item.split()[1].upper() == "KB":
                list_number.append(1024 * eval(item.split()[0]))
            elif item.split()[1].upper() == "MB":
                list_number.append(1024 * 1024 * eval(item.split()[0]))
            elif item.split()[1].upper() == "GB":
                list_number.append(1024 * 1024 * 1024 * eval(item.split()[0]))
            else:
                list_number.append(eval(item.split()[0]))
        return (sorted(list_number) == list_number)

    else:
        print 'Unrecognized list type, please check'
        return False


def is_list_inverted(testlist):
    """
    Function to tell if list is inverted
    Currently we may have list made up of: Strings ; numbers ; percentage ; time; size
    Each has respective way to determine if it's inverted.
    """
    test_list = testlist[:]
    try:
        test_list.remove('')
    except ValueError:
        pass

    if get_list_attr(testlist) == Listattr.NULL :
        return True

    elif get_list_attr(testlist) == Listattr.STRINGS :
        return (sorted(test_list, reverse = True) == test_list)

    elif get_list_attr(testlist) == Listattr.NUMBERS :
        list_number = []
        for item in test_list:
            list_number.append(eval(item))
        return (sorted(list_number, reverse = True) == list_number)

    elif get_list_attr(testlist) == Listattr.PERCENT :
        list_number = []
        for item in test_list:
            list_number.append(eval(item.strip('%')))
        return (sorted(list_number, reverse = True) == list_number)

    elif get_list_attr(testlist) == Listattr.SIZE :
        list_number = []
        # currently SIZE is splitted by space. such as 0 B; 1 KB; 2 MB
        for item in test_list:
            if item.split()[1].upper() == "KB":
                list_number.append(1024 * eval(item.split()[0]))
            elif item.split()[1].upper() == "MB":
                list_number.append(1024 * 1024 * eval(item.split()[0]))
            elif item.split()[1].upper() == "GB":
                list_number.append(1024 * 1024 * 1024 * eval(item.split()[0]))
            else:
                list_number.append(eval(item.split()[0]))
        return (sorted(list_number, reverse = True) == list_number)

    else:
        print 'Unrecognized list type, please check'
        return False

def replace_file_content(filename, item, option):
    f = open(filename)
    lines = f.readlines()
    f.close()
    output = open(filename, 'w')
    for line in lines:
        if line.startswith(item):
            output.write(item + " = '" + option + "'\n")
        else:
            output.write(line)
    output.close()

def extract_number_from_string(s):
    """
    extract the numbers in a string. return type is 'list'
    """
    return re.findall(r'([0-9]+)', s)



###########################################
#                                         #
# PART II: base class                     #
#                                         #
###########################################

class toaster_cases_base(unittest.TestCase):

    def setUp(self):
        self.screenshot_sequence = 1
        self.verificationErrors = []
        self.accept_next_alert = True
        self.host_os = platform.system().lower()
        self.parser = ConfigParser.SafeConfigParser()
        configs = self.parser.read('toaster_test.cfg')
        self.base_url = eval(self.parser.get('toaster_test_' + self.host_os, 'toaster_url'))

        # create log dir . Currently , we put log files in log/tmp. After all
        # test cases are done, move them to log/$datetime dir
        self.log_tmp_dir = os.path.abspath(sys.path[0]) + os.sep + 'log' + os.sep + 'tmp'
        try:
            mkdir_p(self.log_tmp_dir)
        except OSError :
            logging.error("%(asctime)s Cannot create tmp dir under log, please check your privilege")
        self.log = self.logger_create()
        # driver setup
        self.setup_browser()

    def logger_create(self):
        """
        we use root logger for every testcase.
        The reason why we don't use TOASTERXXX_logger is to avoid setting respective level for
        root logger and TOASTERXXX_logger
        To Be Discussed
        """
        log_level_dict = {'CRITICAL':logging.CRITICAL, 'ERROR':logging.ERROR, 'WARNING':logging.WARNING, \
                          'INFO':logging.INFO, 'DEBUG':logging.DEBUG, 'NOTSET':logging.NOTSET}
        log = logging.getLogger()
#        log = logging.getLogger('TOASTER_' + str(self.case_no))
        self.logging_level = eval(self.parser.get('toaster_test_' + self.host_os, 'logging_level'))
        key = self.logging_level.upper()
        log.setLevel(log_level_dict[key])
        fh = logging.FileHandler(filename=self.log_tmp_dir + os.sep + 'case_all' + '.log', mode='a')
        ch = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(pathname)s - %(lineno)d - %(asctime)s \n  \
             %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        log.addHandler(fh)
        log.addHandler(ch)
        return log


    def setup_browser(self, *browser_path):
        self.browser = eval(self.parser.get('toaster_test_' + self.host_os, 'test_browser'))
        print self.browser
        if self.browser == "firefox":
            driver = webdriver.Firefox()
        elif self.browser == "chrome":
            driver = webdriver.Chrome()
        elif self.browser == "ie":
            driver = webdriver.Ie()
        else:
            driver = None
            print "unrecognized browser type, please check"
        self.driver = driver
        self.driver.implicitly_wait(30)
        return self.driver


    def save_screenshot(self,  **log_args):
        """
        This function is used to save screen either by os interface or selenium interface.
        How to use:
        self.save_screenshot(screenshot_type = 'native'/'selenium', log_sub_dir = 'xxx',
                             append_name = 'stepx')
        where native means screenshot func provided by OS,
        selenium means screenshot func provided by selenium webdriver
        """
        types = [log_args.get('screenshot_type')]
        # when no screenshot_type is specified
        if types == [None]:
            types = ['native', 'selenium']
        # normally append_name is used to specify which step..
        add_name = log_args.get('append_name')
        if not add_name:
            add_name = '-'
        # normally there's no need to specify sub_dir
        sub_dir = log_args.get('log_sub_dir')
        if not sub_dir:
            # use casexxx as sub_dir name
            sub_dir = 'case' + str(self.case_no)
        for item in types:
            log_dir = self.log_tmp_dir + os.sep + sub_dir
            mkdir_p(log_dir)
            log_path = log_dir + os.sep +  self.browser + '-' +\
                    item + '-' + add_name + '-' + str(self.screenshot_sequence) + '.png'
            if item == 'native':
                os.system("scrot " + log_path)
            elif item == 'selenium':
                self.driver.get_screenshot_as_file(log_path)
            self.screenshot_sequence += 1

    def browser_delay(self):
        """
        currently this is a workaround for some chrome test.
        Sometimes we need a delay to accomplish some operation.
        But for firefox, mostly we don't need this.
        To be discussed
        """
        if self.browser == "chrome":
            time.sleep(1)
        return


# these functions are not contained in WebDriver class..
    def find_element_by_text(self, string):
        return self.driver.find_element_by_xpath("//*[text()='" + string + "']")


    def find_elements_by_text(self, string):
        return self.driver.find_elements_by_xpath("//*[text()='" + string + "']")


    def find_element_by_text_in_table(self, table_id, text_string):
        """
        This is used to search some certain 'text' in certain table
        """
        try:
            table_element = self.get_table_element(table_id)
            element = table_element.find_element_by_xpath("//*[text()='" + text_string + "']")
        except NoSuchElementException, e:
            print 'no element found'
            raise
        return element


    def find_element_by_link_text_in_table(self, table_id, link_text):
        """
        Assume there're multiple suitable "find_element_by_link_text".
        In this circumstance we need to specify "table".
        """
        try:
            table_element = self.get_table_element(table_id)
            element = table_element.find_element_by_link_text(link_text)
        except NoSuchElementException, e:
            print 'no element found'
            raise
        return element


    def find_elements_by_link_text_in_table(self, table_id, link_text):
        """
        Search link-text in certain table. This helps to narrow down search area.
        """
        try:
            table_element = self.get_table_element(table_id)
            element_list = table_element.find_elements_by_link_text(link_text)
        except NoSuchElementException, e:
            print 'no element found'
            raise
        return element_list


    def find_element_by_partial_link_text_in_table(self, table_id, link_text):
        """
        Search element by partial link text in certain table.
        """
        try:
            table_element = self.get_table_element(table_id)
            element = table_element.find_element_by_partial_link_text(link_text)
            return element
        except NoSuchElementException, e:
            print 'no element found'
            raise


    def find_elements_by_partial_link_text_in_table(self, table_id, link_text):
        """
        Assume there're multiple suitable "find_partial_element_by_link_text".
        """
        try:
            table_element = self.get_table_element(table_id)
            element_list = table_element.find_elements_by_partial_link_text(link_text)
            return element_list
        except NoSuchElementException, e:
            print 'no element found'
            raise


    def find_element_by_xpath_in_table(self, table_id, xpath):
        """
        This helps to narrow down search area. Especially useful when dealing with pop-up form.
        """
        try:
            table_element = self.get_table_element(table_id)
            element = table_element.find_element_by_xpath(xpath)
        except NoSuchElementException, e:
            print 'no element found'
            raise
        return element


    def find_elements_by_xpath_in_table(self, table_id, xpath):
        """
        This helps to narrow down search area. Especially useful when dealing with pop-up form.
        """
        try:
            table_element = self.get_table_element(table_id)
            element_list = table_element.find_elements_by_xpath(xpath)
        except NoSuchElementException, e:
            print 'no elements found'
            raise
        return element_list


    def shortest_xpath(self, pname, pvalue):
        return "//*[@" + pname + "='" + pvalue + "']"


#usually elements in the same column are with same class name. for instance: class="outcome" .TBD
    def get_table_column_text(self, attr_name, attr_value):
        c_xpath = self.shortest_xpath(attr_name, attr_value)
        elements = self.driver.find_elements_by_xpath(c_xpath)
        c_list = []
        for element in elements:
            c_list.append(element.text)
        return c_list


    def get_table_column_text_by_column_number(self, table_id, column_number):
        c_xpath = "//*[@id='" + table_id + "']//td[" + str(column_number) + "]"
        elements = self.driver.find_elements_by_xpath(c_xpath)
        c_list = []
        for element in elements:
            c_list.append(element.text)
        return c_list


    def get_table_head_text(self, *table_id):
#now table_id is a tuple...
        if table_id:
            thead_xpath = "//*[@id='" + table_id[0] + "']//thead//th[text()]"
            elements = self.driver.find_elements_by_xpath(thead_xpath)
            c_list = []
            for element in elements:
                if element.text:
                    c_list.append(element.text)
            return c_list
#default table on page
        else:
            return self.driver.find_element_by_xpath("//*/table/thead").text



    def get_table_element(self, table_id, *coordinate):
        if len(coordinate) == 0:
#return whole-table element
            element_xpath = "//*[@id='" + table_id + "']"
            try:
                element = self.driver.find_element_by_xpath(element_xpath)
            except NoSuchElementException, e:
                raise
            return element
        row = coordinate[0]

        if len(coordinate) == 1:
#return whole-row element
            element_xpath = "//*[@id='" + table_id + "']/tbody/tr[" + str(row) + "]"
            try:
                element = self.driver.find_element_by_xpath(element_xpath)
            except NoSuchElementException, e:
                return False
            return element
#now we are looking for an element with specified X and Y
        column = coordinate[1]

        element_xpath = "//*[@id='" + table_id + "']/tbody/tr[" + str(row) + "]/td[" + str(column) + "]"
        try:
            element = self.driver.find_element_by_xpath(element_xpath)
        except NoSuchElementException, e:
            return False
        return element


    def get_table_data(self, table_id, row_count, column_count):
        row = 1
        Lists = []
        while row <= row_count:
            column = 1
            row_content=[]
            while column <= column_count:
                s= "//*[@id='" + table_id + "']/tbody/tr[" + str(row) +"]/td[" + str(column) + "]"
                v = self.driver.find_element_by_xpath(s).text
                row_content.append(v)
                column = column + 1
                print("row_content=",row_content)
            Lists.extend(row_content)
            print Lists[row-1][0]
            row = row + 1
        return Lists

    # The is_xxx_present functions only returns True/False
    # All the log work is done in test procedure, so we can easily trace back
    # using logging
    def is_text_present (self, patterns):
        for pattern in patterns:
            if str(pattern) not in self.driver.page_source:
                return False
        return True


    def is_element_present(self, how, what):
        try:
            self.driver.find_element(how, what)
        except NoSuchElementException, e:
            return False
        return True


    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True


    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True


    def get_case_number(self):
        """
        what case are we running now
        """
        funcname = sys._getframe(1).f_code.co_name
        caseno_str = funcname.strip('test_')
        try:
            caseno = int(caseno_str)
        except ValueError:
            print "get case number error! please check if func name is test_xxx"
            return False
        return caseno


    def tearDown(self):
        self.log.info(' END: CASE %s log \n\n' % str(self.case_no))
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)


###################################################################
#                                                                 #
# PART III: test cases                                            #
# please refer to                                                 #
# https://bugzilla.yoctoproject.org/tr_show_case.cgi?case_id=xxx  #
#                                                                 #
###################################################################

# Note: to comply with the unittest framework, we call these test_xxx functions
# from run_toastercases.py to avoid calling setUp() and tearDown() multiple times


class toaster_cases(toaster_cases_base):
        ##############
        #  CASE 901  #
        ##############
    def test_901(self):
        # the reason why get_case_number is not in setUp function is that
        # otherwise it returns "setUp" instead of "test_xxx"
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        # open all columns
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # adding explicitly wait for chromedriver..-_-
        self.browser_delay()
        self.driver.find_element_by_id("log").click()
        self.browser_delay()
        self.driver.find_element_by_id("started_on").click()
        self.browser_delay()
        self.driver.find_element_by_id("time").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # dict: {lint text name : actual class name}
        table_head_dict = {'Outcome':'outcome', 'Target':'target', 'Machine':'machine', 'Started on':'started_on', 'Completed on':'completed_on', \
                'Errors':'errors_no', 'Warnings':'warnings_no', 'Time':'time', 'Log':'log'}
        for key in table_head_dict:
            try:
                self.driver.find_element_by_link_text(key).click()
            except Exception, e:
                self.log.error("%s cannot be found on page" % key)
                raise
            column_list = self.get_table_column_text("class", table_head_dict[key])
            # after 1st click, the list should be either sequenced or inverted, but we don't have a "default order" here
            # the point is, after another click, it should be another order
            if is_list_inverted(column_list):
                self.driver.find_element_by_link_text(key).click()
                column_list = self.get_table_column_text("class", table_head_dict[key])
                self.failUnless(is_list_sequenced(column_list))
            else:
                self.failUnless(is_list_sequenced(column_list))
                self.driver.find_element_by_link_text(key).click()
                column_list = self.get_table_column_text("class", table_head_dict[key])
                self.failUnless(is_list_inverted(column_list))
        self.log.info("case passed")


        ##############
        #  CASE 902  #
        ##############
    def test_902(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        # Could add more test patterns here in the future. Also, could search some items other than target column in future..
        patterns = ["minimal", "sato"]
        for pattern in patterns:
            ori_target_column_texts = self.get_table_column_text("class", "target")
            print ori_target_column_texts
            self.driver.find_element_by_id("search").clear()
            self.driver.find_element_by_id("search").send_keys(pattern)
            self.driver.find_element_by_css_selector("button.btn").click()
            new_target_column_texts = self.get_table_column_text("class", "target")
            # if nothing found, we still count it as "pass"
            if new_target_column_texts:
                for text in new_target_column_texts:
                    self.failUnless(text.find(pattern))
            self.driver.find_element_by_css_selector("i.icon-remove").click()
            target_column_texts = self.get_table_column_text("class", "target")
            self.failUnless(ori_target_column_texts == target_column_texts)


        ##############
        #  CASE 903  #
        ##############
    def test_903(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        # when opening a new page, "started_on" is not displayed by default
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # currently all the delay are for chrome driver -_-
        self.browser_delay()
        self.driver.find_element_by_id("started_on").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # step 4
        items = ["Outcome", "Completed on", "Started on", "Failed tasks", "Errors", "Warnings"]
        for item in items:
            try:
                temp_element = self.find_element_by_text_in_table('otable', item)
                # this is how we find "filter icon" in the same level as temp_element(where "a" means clickable, "i" means icon)
                self.failUnless(temp_element.find_element_by_xpath("..//*/a/i[@class='icon-filter filtered']"))
            except Exception,e:
                self.log.error(" %s cannot be found! %s" % (item, e))
                self.failIf(True)
                raise
        # step 5-6
        temp_element = self.find_element_by_link_text_in_table('otable', 'Outcome')
        temp_element.find_element_by_xpath("..//*/a/i[@class='icon-filter filtered']").click()
        self.browser_delay()
        # the 2nd option, whatever it is
        self.driver.find_element_by_xpath("(//input[@name='filter'])[2]").click()
        # click "Apply" button
        self.driver.find_element_by_xpath("//*[@id='filter_outcome']//*[text()='Apply']").click()
        # save screen here
        time.sleep(1)
        self.save_screenshot(screenshot_type='selenium', append_name='step5')
        temp_element = self.find_element_by_link_text_in_table('otable', 'Completed on')
        temp_element.find_element_by_xpath("..//*/a/i[@class='icon-filter filtered']").click()
        self.browser_delay()
        self.driver.find_element_by_xpath("//*[@id='filter_completed_on']//*[text()='Apply']").click()
        # save screen here to compare to previous one
        # please note that for chrome driver, need a little break before saving
        # screen here -_-
        self.browser_delay()
        self.save_screenshot(screenshot_type='selenium', append_name='step6')
        self.driver.find_element_by_id("search").clear()
        self.driver.find_element_by_id("search").send_keys("core-image")
        self.driver.find_element_by_css_selector("button.btn").click()


        ##############
        #  CASE 904  #
        ##############
    def test_904(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_partial_link_text("core-image").click()
        self.driver.find_element_by_link_text("Tasks").click()
#        self.driver.find_element_by_link_text("All builds").click()
#        self.driver.back()
        self.table_name = 'otable'
        # This is how we find the "default" rows-number!
        rows_displayed = int(Select(self.driver.find_element_by_css_selector("select.pagesize")).first_selected_option.text)
        print rows_displayed
        self.failUnless(self.get_table_element(self.table_name, rows_displayed))
        self.failIf(self.get_table_element(self.table_name, rows_displayed + 1))
        # Search text box background text is "Search tasks"
        self.failUnless(self.driver.find_element_by_xpath("//*[@id='searchform']/*[@placeholder='Search tasks']"))

        self.driver.find_element_by_id("search").clear()
        self.driver.find_element_by_id("search").send_keys("busybox")
        self.driver.find_element_by_css_selector("button.btn").click()
        self.browser_delay()
        self.save_screenshot(screenshot_type='selenium', append_name='step5')
        self.driver.find_element_by_css_selector("i.icon-remove").click()
        # Save screen here
        self.save_screenshot(screenshot_type='selenium', append_name='step5_2')
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("cpu_used").click()
        self.driver.find_element_by_id("disk_io").click()
        self.driver.find_element_by_id("task_log").click()
        self.driver.find_element_by_id("recipe_version").click()
        self.driver.find_element_by_id("time_taken").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # The operation is the same as case901
        # dict: {lint text name : actual class name}
        table_head_dict = {'Order':'order', 'Recipe':'recipe_name', 'Task':'task_name', 'Executed':'executed', \
                           'Outcome':'outcome', 'Cache attempt':'cache_attempt', 'Time (secs)':'time_taken', 'CPU usage':'cpu_used', \
                           'Disk I/O (ms)':'disk_io', 'Log':'task_log'}
        for key in table_head_dict:
# This is tricky here: we are doing so because there may be more than 1
# same-name link_text in one page. So we only find element inside the table
            self.find_element_by_link_text_in_table(self.table_name, key).click()
            column_list = self.get_table_column_text("class", table_head_dict[key])
# after 1st click, the list should be either sequenced or inverted, but we don't have a "default order" here
# the point is, after another click, it should be another order
# the fist case is special:this means every item in column_list is the same, so
# after one click, either sequenced or inverted will be fine
            if (is_list_inverted(column_list) and is_list_sequenced(column_list)) \
                or (not column_list) :
                self.find_element_by_link_text_in_table(self.table_name, key).click()
                column_list = self.get_table_column_text("class", table_head_dict[key])
                self.failUnless(is_list_sequenced(column_list) or is_list_inverted(column_list))
            elif is_list_inverted(column_list):
                self.find_element_by_link_text_in_table(self.table_name, key).click()
                column_list = self.get_table_column_text("class", table_head_dict[key])
                self.failUnless(is_list_sequenced(column_list))
            else:
                self.failUnless(is_list_sequenced(column_list))
                self.find_element_by_link_text_in_table(self.table_name, key).click()
                column_list = self.get_table_column_text("class", table_head_dict[key])
                self.failUnless(is_list_inverted(column_list))
# step 8-10
        # filter dict: {link text name : filter table name in xpath}
        filter_dict = {'Executed':'filter_executed', 'Outcome':'filter_outcome', 'Cache attempt':'filter_cache_attempt'}
        for key in filter_dict:
            temp_element = self.find_element_by_link_text_in_table(self.table_name, key)
            # find the filter icon besides it.
            # And here we must have break (1 sec) to get the popup stuff
            temp_element.find_element_by_xpath("..//*[@class='icon-filter filtered']").click()
            self.browser_delay()
            avail_options = self.driver.find_elements_by_xpath("//*[@id='" + filter_dict[key] + "']//*[@name='filter'][not(@disabled)]")
            for number in range(0, len(avail_options)):
                avail_options[number].click()
                self.browser_delay()
                # click "Apply"
                self.driver.find_element_by_xpath("//*[@id='" + filter_dict[key]  + "']//*[@type='submit']").click()
                # insert screen capture here
                self.browser_delay()
                self.save_screenshot(screenshot_type='selenium', append_name='step8')
                # after the last option was clicked, we don't need operation below anymore
                if number < len(avail_options)-1:
                     temp_element = self.find_element_by_link_text_in_table(self.table_name, key)
                     temp_element.find_element_by_xpath("..//*[@class='icon-filter filtered']").click()
                     avail_options = self.driver.find_elements_by_xpath("//*[@id='" + filter_dict[key] + "']//*[@name='filter'][not(@disabled)]")
                     self.browser_delay()
# step 11
        for item in ['order', 'task_name', 'executed', 'outcome', 'recipe_name', 'recipe_version']:
            try:
                self.find_element_by_xpath_in_table(self.table_name, "./tbody/tr[1]/*[@class='" + item + "']/a").click()
            except NoSuchElementException, e:
            # let it go...
                print 'no item in the colum' + item
            # insert screen shot here
            self.save_screenshot(screenshot_type='selenium', append_name='step11')
            self.driver.back()
# step 12-14
        # about test_dict: please refer to testcase 904 requirement step 12-14
        test_dict = {
            'Time':{
                'class':'time_taken',
                'check_head_list':['Recipe', 'Task', 'Executed', 'Outcome', 'Time (secs)'],
                'check_column_list':['cpu_used', 'cache_attempt', 'disk_io', 'task_log', 'order', 'recipe_version']
            },
            'CPU usage':{
                'class':'cpu_used',
                'check_head_list':['Recipe', 'Task', 'Executed', 'Outcome', 'CPU usage'],
                'check_column_list':['cache_attempt', 'disk_io', 'task_log', 'order', 'recipe_version', 'time_taken']
            },
            'Disk I/O':{
                'class':'disk_io',
                'check_head_list':['Recipe', 'Task', 'Executed', 'Outcome', 'Disk I/O (ms)'],
                'check_column_list':['cpu_used', 'cache_attempt', 'task_log', 'order', 'recipe_version', 'time_taken']
            }
        }
        for key in test_dict:
            self.find_element_by_partial_link_text_in_table('nav', 'core-image').click()
            self.find_element_by_link_text_in_table('nav', key).click()
            head_list = self.get_table_head_text('otable')
            for item in test_dict[key]['check_head_list']:
                self.failUnless(item in head_list)
            column_list = self.get_table_column_text('class', test_dict[key]['class'])
            self.failUnless(is_list_inverted(column_list))

            self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
            for item2 in test_dict[key]['check_column_list']:
                self.driver.find_element_by_id(item2).click()
            self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
            # TBD: save screen here


        ##############
        #  CASE 906  #
        ##############
    def test_906(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        self.find_element_by_link_text_in_table('nav', 'Packages').click()
        # find "bash" in first column (Packages)
        self.driver.find_element_by_xpath("//*[@id='otable']//td[1]//*[text()='bash']").click()
        # save sceen here to observe...
# step 6
        self.driver.find_element_by_partial_link_text("Generated files").click()
        head_list = self.get_table_head_text('otable')
        for item in ['File', 'Size']:
            self.failUnless(item in head_list)
        c_list = self.get_table_column_text('class', 'path')
        self.failUnless(is_list_sequenced(c_list))
# step 7
        self.driver.find_element_by_partial_link_text("Runtime dependencies").click()
        # save sceen here to observe...
        # note that here table name is not 'otable'
        head_list = self.get_table_head_text('dependencies')
        for item in ['Package', 'Version', 'Size']:
            self.failUnless(item in head_list)
        c_list = self.get_table_column_text_by_column_number('dependencies', 1)
        self.failUnless(is_list_sequenced(c_list))
        texts = ['Size', 'License', 'Recipe', 'Recipe version', 'Layer', \
                     'Layer branch', 'Layer commit', 'Layer directory']
        self.failUnless(self.is_text_present(texts))


        ##############
        #  CASE 910  #
        ##############
    def test_910(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        image_type="core-image-minimal"
        test_package1="busybox"
        test_package2="lib"
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text(image_type).click()
        self.driver.find_element_by_link_text("Recipes").click()
        self.save_screenshot(screenshot_type='selenium', append_name='step3')

        self.table_name = 'otable'
        # This is how we find the "default" rows-number!
        rows_displayed = int(Select(self.driver.find_element_by_css_selector("select.pagesize")).first_selected_option.text)
        print rows_displayed
        self.failUnless(self.get_table_element(self.table_name, rows_displayed))
        self.failIf(self.get_table_element(self.table_name, rows_displayed + 1))

        # Check the default table is sorted by Recipe
        tasks_column_count = len(self.driver.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div[2]/table/tbody/tr/td[1]"))
        print tasks_column_count
        default_column_list = self.get_table_column_text_by_column_number(self.table_name, 1)
        #print default_column_list

        self.failUnless(is_list_sequenced(default_column_list))

        # Search text box background text is "Search recipes"
        self.failUnless(self.driver.find_element_by_xpath("//*[@id='searchform']/*[@placeholder='Search recipes']"))

        self.driver.find_element_by_id("search").clear()
        self.driver.find_element_by_id("search").send_keys(test_package1)
        self.driver.find_element_by_css_selector("button.btn").click()
        # Save screen here
        self.save_screenshot(screenshot_type='selenium', append_name='step4')
        self.driver.find_element_by_css_selector("i.icon-remove").click()
        self.save_screenshot(screenshot_type='selenium', append_name='step4_2')

        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("depends_on").click()
        self.driver.find_element_by_id("layer_version__branch").click()
        self.driver.find_element_by_id("layer_version__layer__commit").click()
        self.driver.find_element_by_id("layer_version__local_path").click()
        self.driver.find_element_by_id("depends_by").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()

        self.find_element_by_link_text_in_table(self.table_name, 'Recipe').click()
        # Check the inverted table by Recipe
        # Recipe doesn't have class name
        inverted_tasks_column_count = len(self.driver.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div[2]/table/tbody/tr/td[1]"))
        print inverted_tasks_column_count
        inverted_column_list = self.get_table_column_text_by_column_number(self.table_name, 1)
        #print inverted_column_list

        self.driver.find_element_by_xpath("/html/body/div[2]/div/div[2]/div[2]/table/tbody/tr[1]/td[1]/a").click()
        self.driver.back()
        self.failUnless(is_list_inverted(inverted_column_list))
        self.find_element_by_link_text_in_table(self.table_name, 'Recipe').click()

        table_head_dict = {'Recipe file':'recipe_file', 'Section':'recipe_section', \
                'License':'recipe_license', 'Layer':'layer_version__layer__name', \
                'Layer branch':'layer_version__branch', 'Layer directory':'layer_version__local_path'}
        for key in table_head_dict:
            self.find_element_by_link_text_in_table(self.table_name, key).click()
            column_list = self.get_table_column_text("class", table_head_dict[key])
            if (is_list_inverted(column_list) and is_list_sequenced(column_list)) \
                    or (not column_list) :
                self.find_element_by_link_text_in_table(self.table_name, key).click()
                column_list = self.get_table_column_text("class", table_head_dict[key])
                self.failUnless(is_list_sequenced(column_list) or is_list_inverted(column_list))
                self.driver.find_element_by_xpath("/html/body/div[2]/div/div[2]/div[2]/table/tbody/tr[1]/td[1]/a").click()
                self.driver.back()
                self.failUnless(is_list_sequenced(column_list) or is_list_inverted(column_list))
                # Search text box background text is "Search recipes"
                self.failUnless(self.driver.find_element_by_xpath("//*[@id='searchform']/*[@placeholder='Search recipes']"))
                self.driver.find_element_by_id("search").clear()
                self.driver.find_element_by_id("search").send_keys(test_package2)
                self.driver.find_element_by_css_selector("button.btn").click()
                column_search_list = self.get_table_column_text("class", table_head_dict[key])
                self.failUnless(is_list_sequenced(column_search_list) or is_list_inverted(column_search_list))
                self.driver.find_element_by_css_selector("i.icon-remove").click()
            elif is_list_inverted(column_list):
                self.find_element_by_link_text_in_table(self.table_name, key).click()
                column_list = self.get_table_column_text("class", table_head_dict[key])
                self.failUnless(is_list_sequenced(column_list))
                self.driver.find_element_by_xpath("/html/body/div[2]/div/div[2]/div[2]/table/tbody/tr[1]/td[1]/a").click()
                self.driver.back()
                self.failUnless(is_list_sequenced(column_list))
                # Search text box background text is "Search recipes"
                self.failUnless(self.driver.find_element_by_xpath("//*[@id='searchform']/*[@placeholder='Search recipes']"))
                self.driver.find_element_by_id("search").clear()
                self.driver.find_element_by_id("search").send_keys(test_package2)
                self.driver.find_element_by_css_selector("button.btn").click()
                column_search_list = self.get_table_column_text("class", table_head_dict[key])
                self.failUnless(is_list_sequenced(column_search_list))
                self.driver.find_element_by_css_selector("i.icon-remove").click()
            else:
                self.failUnless(is_list_sequenced(column_list))
                self.find_element_by_link_text_in_table(self.table_name, key).click()
                column_list = self.get_table_column_text("class", table_head_dict[key])
                self.failUnless(is_list_inverted(column_list))
                self.driver.find_element_by_xpath("/html/body/div[2]/div/div[2]/div[2]/table/tbody/tr[1]/td[1]/a").click()
                self.driver.back()
                self.failUnless(is_list_inverted(column_list))
                # Search text box background text is "Search recipes"
                self.failUnless(self.driver.find_element_by_xpath("//*[@id='searchform']/*[@placeholder='Search recipes']"))
                self.driver.find_element_by_id("search").clear()
                self.driver.find_element_by_id("search").send_keys(test_package2)
                self.driver.find_element_by_css_selector("button.btn").click()
                column_search_list = self.get_table_column_text("class", table_head_dict[key])
                #print column_search_list
                self.failUnless(is_list_inverted(column_search_list))
                self.driver.find_element_by_css_selector("i.icon-remove").click()

        # Bug 5919
        for key in table_head_dict:
            print key
            self.find_element_by_link_text_in_table(self.table_name, key).click()
            self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
            self.driver.find_element_by_id(table_head_dict[key]).click()
            self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
            self.browser_delay()
            # After hide the column, the default table should be sorted by Recipe
            tasks_column_count = len(self.driver.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div[2]/table/tbody/tr/td[1]"))
            #print tasks_column_count
            default_column_list = self.get_table_column_text_by_column_number(self.table_name, 1)
            #print default_column_list
            self.failUnless(is_list_sequenced(default_column_list))

        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("recipe_file").click()
        self.driver.find_element_by_id("recipe_section").click()
        self.driver.find_element_by_id("recipe_license").click()
        self.driver.find_element_by_id("layer_version__layer__name").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()


        ##############
        #  CASE 911  #
        ##############
    def test_911(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        self.find_element_by_link_text_in_table('nav', 'Recipes').click()
# step 3-5
        self.driver.find_element_by_id("search").clear()
        self.driver.find_element_by_id("search").send_keys("lib")
        self.driver.find_element_by_css_selector("button.btn").click()
        # save screen here for observation
        self.save_screenshot(screenshot_type='selenium', append_name='step5')
# step 6
        self.driver.find_element_by_css_selector("i.icon-remove").click()
        self.driver.find_element_by_id("search").clear()
        # we deliberately want "no result" here
        self.driver.find_element_by_id("search").send_keys("what the hell")
        self.driver.find_element_by_css_selector("button.btn").click()
        self.find_element_by_text("Show all recipes").click()
        self.driver.quit()


        ##############
        #  CASE 912  #
        ##############
    def test_912(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver = self.setup_browser(self)
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        self.find_element_by_link_text_in_table('nav', 'Recipes').click()
        # step 3
        head_list = self.get_table_head_text('otable')
        for item in ['Recipe', 'Recipe version', 'Recipe file', 'Section', 'License', 'Layer']:
            self.failUnless(item in head_list)
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("depends_on").click()
        self.driver.find_element_by_id("layer_version__branch").click()
        self.driver.find_element_by_id("layer_version__layer__commit").click()
        self.driver.find_element_by_id("layer_version__local_path").click()
        self.driver.find_element_by_id("depends_by").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # check if columns selected above is shown
        check_list = ['Dependencies', 'Layer branch', 'Layer commit', 'Layer directory', 'Reverse dependencies']
        head_list = self.get_table_head_text('otable')
        time.sleep(2)
        print head_list
        for item in check_list:
            self.failUnless(item in head_list)
        # un-check 'em all
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("depends_on").click()
        self.driver.find_element_by_id("layer_version__branch").click()
        self.driver.find_element_by_id("layer_version__layer__commit").click()
        self.driver.find_element_by_id("layer_version__local_path").click()
        self.driver.find_element_by_id("depends_by").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # don't exist any more
        head_list = self.get_table_head_text('otable')
        for item in check_list:
            self.failIf(item in head_list)


        ##############
        #  CASE 913  #
        ##############
    def test_913(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        self.find_element_by_link_text_in_table('nav', 'Recipes').click()
        # step 3
        head_list = self.get_table_head_text('otable')
        for item in ['Recipe', 'Recipe version', 'Recipe file', 'Section', 'License', 'Layer']:
            self.failUnless(item in head_list)
        # step 4
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # save screen
        self.browser_delay()
        self.save_screenshot(screenshot_type='selenium', append_name='step4')
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()


        ##############
        #  CASE 914  #
        ##############
    def test_914(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        image_type="core-image-minimal"
        test_package1="busybox"
        test_package2="gdbm"
        test_package3="gettext-native"
        driver = self.driver
        driver.maximize_window()
        driver.get(self.base_url)
        driver.find_element_by_link_text(image_type).click()
        driver.find_element_by_link_text("Recipes").click()
        driver.find_element_by_link_text(test_package1).click()

        self.table_name = 'information'

        tasks_row_count = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[3]/div/div[1]/table/tbody/tr/td[1]"))
        tasks_column_count = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[3]/div/div[1]/table/tbody/tr[1]/td"))
        print tasks_row_count
        print tasks_column_count

        Tasks_column = self.get_table_column_text_by_column_number(self.table_name, 2)
        print ("Tasks_column=", Tasks_column)

        key_tasks=["do_fetch", "do_unpack",  "do_patch", "do_configure", "do_compile", "do_install", "do_package", "do_build"]
        i = 0
        while i < len(key_tasks):
            if key_tasks[i] not in Tasks_column:
                print ("Error! Missing key task: %s" % key_tasks[i])
            else:
                print ("%s is in tasks" % key_tasks[i])
            i = i + 1

        if Tasks_column.index(key_tasks[0]) != 0:
            print ("Error! %s is not in the right position" % key_tasks[0])
        else:
            print ("%s is in right position" % key_tasks[0])

        if Tasks_column[-1] != key_tasks[-1]:
            print ("Error! %s is not in the right position" % key_tasks[-1])
        else:
            print ("%s is in right position" % key_tasks[-1])

        driver.find_element_by_partial_link_text("Packages (").click()
        packages_name = driver.find_element_by_partial_link_text("Packages (").text
        print packages_name
        packages_num = string.atoi(filter(str.isdigit, repr(packages_name)))
        print packages_num

        packages_row_count = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[3]/div/div[2]/table/tbody/tr/td[1]"))
        print packages_row_count

        if packages_num != packages_row_count:
            print ("Error! The packages number is not correct")
        else:
            print ("The pakcages number is correct")

        driver.find_element_by_partial_link_text("Build dependencies (").click()
        depends_name = driver.find_element_by_partial_link_text("Build dependencies (").text
        print depends_name
        depends_num = string.atoi(filter(str.isdigit, repr(depends_name)))
        print depends_num

        if depends_num == 0:
            depends_message = repr(driver.find_element_by_css_selector("div.alert.alert-info").text)
            print depends_message
            if depends_message.find("has no build dependencies.") < 0:
                print ("Error! The message isn't expected.")
            else:
                print ("The message is expected")
        else:
            depends_row_count = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[3]/div/div[3]/table/tbody/tr/td[1]"))
            print depends_row_count
            if depends_num != depends_row_count:
                print ("Error! The dependent packages number is not correct")
            else:
                print ("The dependent packages number is correct")

        driver.find_element_by_partial_link_text("Reverse build dependencies (").click()
        rdepends_name = driver.find_element_by_partial_link_text("Reverse build dependencies (").text
        print rdepends_name
        rdepends_num = string.atoi(filter(str.isdigit, repr(rdepends_name)))
        print rdepends_num

        if rdepends_num == 0:
            rdepends_message = repr(driver.find_element_by_css_selector("#brought-in-by > div.alert.alert-info").text)
            print rdepends_message
            if rdepends_message.find("has no reverse build dependencies.") < 0:
                print ("Error! The message isn't expected.")
            else:
                print ("The message is expected")
        else:
            print ("The reverse dependent packages number is correct")

        driver.find_element_by_link_text("Recipes").click()
        driver.find_element_by_link_text(test_package2).click()
        driver.find_element_by_partial_link_text("Packages (").click()
        driver.find_element_by_partial_link_text("Build dependencies (").click()
        driver.find_element_by_partial_link_text("Reverse build dependencies (").click()


        driver.find_element_by_link_text("Recipes").click()
        driver.find_element_by_link_text(test_package3).click()

        native_tasks_row_count = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[3]/div/div[1]/table/tbody/tr/td[1]"))
        native_tasks_column_count = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[3]/div/div[1]/table/tbody/tr[1]/td"))
        print native_tasks_row_count
        print native_tasks_column_count

        Native_Tasks_column = self.get_table_column_text_by_column_number(self.table_name, 2)
        print ("Native_Tasks_column=", Native_Tasks_column)

        native_key_tasks=["do_fetch", "do_unpack",  "do_patch", "do_configure", "do_compile", "do_install", "do_build"]
        i = 0
        while i < len(native_key_tasks):
            if native_key_tasks[i] not in Native_Tasks_column:
                print ("Error! Missing key task: %s" % native_key_tasks[i])
            else:
                print ("%s is in tasks" % native_key_tasks[i])
            i = i + 1

        if Native_Tasks_column.index(native_key_tasks[0]) != 0:
            print ("Error! %s is not in the right position" % native_key_tasks[0])
        else:
            print ("%s is in right position" % native_key_tasks[0])

        if Native_Tasks_column[-1] != native_key_tasks[-1]:
            print ("Error! %s is not in the right position" % native_key_tasks[-1])
        else:
            print ("%s is in right position" % native_key_tasks[-1])

        driver.find_element_by_partial_link_text("Packages (").click()
        native_packages_name = driver.find_element_by_partial_link_text("Packages (").text
        print native_packages_name
        native_packages_num = string.atoi(filter(str.isdigit, repr(native_packages_name)))
        print native_packages_num

        if native_packages_num != 0:
            print ("Error! Native task shouldn't have any packages.")
        else:
            native_package_message = repr(driver.find_element_by_css_selector("div.alert.alert-info").text)
            print native_package_message
            if native_package_message.find("does not build any packages.") < 0:
                print ("Error! The message for native task isn't expected.")
            else:
                print ("The message for native task is expected.")

        driver.find_element_by_partial_link_text("Build dependencies (").click()
        native_depends_name = driver.find_element_by_partial_link_text("Build dependencies (").text
        print native_depends_name
        native_depends_num = string.atoi(filter(str.isdigit, repr(native_depends_name)))
        print native_depends_num

        native_depends_row_count = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[3]/div/div[3]/table/tbody/tr/td[1]"))
        print native_depends_row_count

        if native_depends_num != native_depends_row_count:
            print ("Error! The dependent packages number is not correct")
        else:
            print ("The dependent packages number is correct")

        driver.find_element_by_partial_link_text("Reverse build dependencies (").click()
        native_rdepends_name = driver.find_element_by_partial_link_text("Reverse build dependencies (").text
        print native_rdepends_name
        native_rdepends_num = string.atoi(filter(str.isdigit, repr(native_rdepends_name)))
        print native_rdepends_num

        native_rdepends_row_count = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[3]/div/div[4]/table/tbody/tr/td[1]"))
        print native_rdepends_row_count

        if native_rdepends_num != native_rdepends_row_count:
            print ("Error! The reverse dependent packages number is not correct")
        else:
            print ("The reverse dependent packages number is correct")

        driver.find_element_by_link_text("Recipes").click()


        ##############
        #  CASE 915  #
        ##############
    def test_915(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
# step 3
        self.find_element_by_link_text_in_table('nav', 'Configuration').click()
        self.driver.find_element_by_link_text("BitBake variables").click()
# step 4
        self.driver.find_element_by_id("search").clear()
        self.driver.find_element_by_id("search").send_keys("lib")
        self.driver.find_element_by_css_selector("button.btn").click()
        # save screen to see result
        self.browser_delay()
        self.save_screenshot(screenshot_type='selenium', append_name='step4')
# step 5
        self.driver.find_element_by_css_selector("i.icon-remove").click()
        head_list = self.get_table_head_text('otable')
        print head_list
        print len(head_list)
        self.failUnless(head_list == ['Variable', 'Value', 'Set in file', 'Description'])
# step 8
        # search other string. and click "Variable" to re-sort, check if table
        # head is still the same
        self.driver.find_element_by_id("search").clear()
        self.driver.find_element_by_id("search").send_keys("poky")
        self.driver.find_element_by_css_selector("button.btn").click()
        self.find_element_by_link_text_in_table('otable', 'Variable').click()
        head_list = self.get_table_head_text('otable')
        self.failUnless(head_list == ['Variable', 'Value', 'Set in file', 'Description'])
        self.find_element_by_link_text_in_table('otable', 'Variable').click()
        head_list = self.get_table_head_text('otable')
        self.failUnless(head_list == ['Variable', 'Value', 'Set in file', 'Description'])


        ##############
        #  CASE 916  #
        ##############
    def test_916(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
# step 2-3
        self.find_element_by_link_text_in_table('nav', 'Configuration').click()
        self.driver.find_element_by_link_text("BitBake variables").click()
        variable_list = self.get_table_column_text('class', 'variable_name')
        self.failUnless(is_list_sequenced(variable_list))
# step 4
        self.find_element_by_link_text_in_table('otable', 'Variable').click()
        variable_list = self.get_table_column_text('class', 'variable_name')
        self.failUnless(is_list_inverted(variable_list))
        self.find_element_by_link_text_in_table('otable', 'Variable').click()
# step 5
        # searching won't change the sequentiality
        self.driver.find_element_by_id("search").clear()
        self.driver.find_element_by_id("search").send_keys("lib")
        self.driver.find_element_by_css_selector("button.btn").click()
        variable_list = self.get_table_column_text('class', 'variable_name')
        self.failUnless(is_list_sequenced(variable_list))


        ##############
        #  CASE 923  #
        ##############
    def test_923(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        # Step 2
        # default sequence in "Completed on" column is inverted
        c_list = self.get_table_column_text('class', 'completed_on')
        self.failUnless(is_list_inverted(c_list))
        # step 3
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("started_on").click()
        self.driver.find_element_by_id("log").click()
        self.driver.find_element_by_id("time").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        head_list = self.get_table_head_text('otable')
        for item in ['Outcome', 'Target', 'Machine', 'Started on', 'Completed on', 'Failed tasks', 'Errors', 'Warnings', 'Warnings', 'Time']:
            self.failUnless(item in head_list)


        ##############
        #  CASE 924  #
        ##############
    def test_924(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        # Please refer to case 924 requirement
        # default sequence in "Completed on" column is inverted
        c_list = self.get_table_column_text('class', 'completed_on')
        self.failUnless(is_list_inverted(c_list))
        # Step 4
        # click Errors , order in "Completed on" should be disturbed. Then hide
        # error column to check if order in "Completed on" can be restored
        self.find_element_by_link_text_in_table('otable', 'Errors').click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("errors_no").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # Note: without time.sleep here, there'll be unpredictable error..TBD
        time.sleep(1)
        c_list = self.get_table_column_text('class', 'completed_on')
        self.failUnless(is_list_inverted(c_list))


        ##############
        #  CASE 940  #
        ##############
    def test_940(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
# Step 2-3
        self.find_element_by_link_text_in_table('nav', 'Packages').click()
        check_head_list = ['Package', 'Package version', 'Size', 'Recipe']
        head_list = self.get_table_head_text('otable')
        self.failUnless(head_list == check_head_list)
# Step 4
        # pulldown menu
        option_ids = ['recipe__layer_version__layer__name', 'recipe__layer_version__branch', \
                      'recipe__layer_version__layer__commit', 'recipe__layer_version__local_path', \
                      'license', 'recipe__version']
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        for item in option_ids:
            if not self.driver.find_element_by_id(item).is_selected():
                self.driver.find_element_by_id(item).click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # save screen here to observe that 'Package' and 'Package version' is
        # not selectable
        self.browser_delay()
        self.save_screenshot(screenshot_type='selenium', append_name='step4')


        ##############
        #  CASE 941  #
        ##############
    def test_941(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        # Step 2-3
        self.find_element_by_link_text_in_table('nav', 'Packages').click()
        # column -- Package
        column_list = self.get_table_column_text_by_column_number('otable', 1)
        self.failUnless(is_list_sequenced(column_list))
        self.find_element_by_link_text_in_table('otable', 'Size').click()


        ##############
        #  CASE 944  #
        ##############
    def test_944(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        # step 1: test Recipes page stuff
        self.driver.find_element_by_link_text("Recipes").click()
        # for these 3 items, default status is not-checked
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("layer_version__branch").click()
        self.driver.find_element_by_id("layer_version__layer__commit").click()
        self.driver.find_element_by_id("layer_version__local_path").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # otable is the recipes table here
        otable_head_text = self.get_table_head_text('otable')
        for item in ["Layer", "Layer branch", "Layer commit", "Layer directory"]:
            self.failIf(item not in otable_head_text)
        # click the fist recipe, whatever it is
        self.get_table_element("otable", 1, 1).click()
        self.failUnless(self.is_text_present(["Layer", "Layer branch", "Layer commit", "Layer directory", "Recipe file"]))

        # step 2: test Packages page stuff. almost same as above
        self.driver.back()
        self.browser_delay()
        self.driver.find_element_by_link_text("Packages").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("recipe__layer_version__layer__name").click()
        self.driver.find_element_by_id("recipe__layer_version__branch").click()
        self.driver.find_element_by_id("recipe__layer_version__layer__commit").click()
        self.driver.find_element_by_id("recipe__layer_version__local_path").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        otable_head_text = self.get_table_head_text("otable")
        for item in ["Layer", "Layer branch", "Layer commit", "Layer directory"]:
            self.failIf(item not in otable_head_text)
        # click the fist recipe, whatever it is
        self.get_table_element("otable", 1, 1).click()
        self.failUnless(self.is_text_present(["Layer", "Layer branch", "Layer commit", "Layer directory"]))

        # step 3: test Packages core-image-minimal(images) stuff. almost same as above. Note when future element-id changes...
        self.driver.back()
        self.driver.find_element_by_link_text("core-image-minimal").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("layer_name").click()
        self.driver.find_element_by_id("layer_branch").click()
        self.driver.find_element_by_id("layer_commit").click()
        self.driver.find_element_by_id("layer_directory").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        otable_head_text = self.get_table_head_text("otable")
        for item in ["Layer", "Layer branch", "Layer commit", "Layer directory"]:
            self.failIf(item not in otable_head_text)
        # click the fist recipe, whatever it is
        self.get_table_element("otable", 1, 1).click()
        self.failUnless(self.is_text_present(["Layer", "Layer branch", "Layer commit", "Layer directory"]))

        # step 4: check Configuration page
        self.driver.back()
        self.driver.find_element_by_link_text("Configuration").click()
        otable_head_text = self.get_table_head_text()
        for item in ["Layer", "Layer branch", "Layer commit", "Layer directory"]:
            self.failIf(item not in otable_head_text)


        ##############
        #  CASE 945  #
        ##############
    def test_945(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        for items in ["Packages", "Recipes", "Tasks"]:
            self.driver.get(self.base_url)
            self.driver.find_element_by_link_text("core-image-minimal").click()
            self.driver.find_element_by_link_text(items).click()

            # this may be page specific. If future page content changes, try to replace it with new xpath
            xpath_showrows = "/html/body/div[2]/div/div[2]/div[2]/div[2]/div/div/div[2]/select"
            xpath_table = "/html/body/div[2]/div/div[2]/div[2]/table/tbody"
            self.driver.find_element_by_xpath(xpath_showrows).click()
            rows_displayed = int(self.driver.find_element_by_xpath(xpath_showrows + "/option[2]").text)

            # not sure if this is a Selenium Select bug: If page is not refreshed here, "select(by visible text)" operation will go back to 100-row page
            # Sure we can use driver.get(url) to refresh page, but since page will vary, we use click link text here
            self.driver.find_element_by_link_text(items).click()
            Select(self.driver.find_element_by_css_selector("select.pagesize")).select_by_visible_text(str(rows_displayed))
            self.failUnless(self.is_element_present(By.XPATH, xpath_table + "/tr[" + str(rows_displayed) +"]"))
            self.failIf(self.is_element_present(By.XPATH, xpath_table + "/tr[" + str(rows_displayed+1) +"]"))

            # click 1st package, then go back to check if it's still those rows shown.
            self.driver.find_element_by_xpath(xpath_table + "/tr[1]/td[1]").click()
            self.driver.find_element_by_link_text(items).click()
            self.failUnless(self.is_element_present(By.XPATH, xpath_table + "/tr[" + str(rows_displayed) +"]"))
            self.failIf(self.is_element_present(By.XPATH, xpath_table + "/tr[" + str(rows_displayed+1) +"]"))


        ##############
        #  CASE 946  #
        ##############
    def test_946(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        self.driver.find_element_by_link_text("Configuration").click()
        # step 3-4
        check_list = ["Summary", "BitBake variables"]
        for item in check_list:
            if not self.is_element_present(how=By.LINK_TEXT, what=item):
                self.log.error("%s not found" %item)
        if not self.is_text_present(['Layers', 'Layer', 'Layer branch', 'Layer commit', 'Layer directory']):
            self.log.error("text not found")
        # step 5
        self.driver.find_element_by_link_text("BitBake variables").click()
        if not self.is_text_present(['Variable', 'Value', 'Set in file', 'Description']):
            self.log.error("text not found")
        # This may be unstable because it's page-specific
        # step 6: this is how we find filter beside "Set in file"
        temp_element = self.find_element_by_text_in_table('otable', "Set in file")
        temp_element.find_element_by_xpath("..//*/a/i[@class='icon-filter filtered']").click()
        self.browser_delay()
        self.driver.find_element_by_xpath("(//input[@name='filter'])[2]").click()
        self.driver.find_element_by_css_selector("button.btn.btn-primary").click()
        # save screen here
        self.browser_delay()
        self.save_screenshot(screenshot_type='selenium', append_name='step6')
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # save screen here
        # step 7
        # we should manually check the step 6-8 result using screenshot
        self.browser_delay()
        self.save_screenshot(screenshot_type='selenium', append_name='step7')
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # step 9
        # click the 1st item, no matter what it is
        self.driver.find_element_by_xpath("//*[@id='otable']/tbody/tr[1]/td[1]/a").click()
        # give it 1 sec so the pop-up becomes the "active_element"
        time.sleep(1)
        element = self.driver.switch_to.active_element
        check_list = ['Order', 'Configuration file', 'Operation', 'Line number']
        for item in check_list:
            if item not in element.text:
                self.log.error("%s not found" %item)
        # any better way to close this pop-up? ... TBD
        element.find_element_by_xpath(".//*[@class='close']").click()
        # step 10 : need to manually check "Yocto Manual" in saved screen
        self.driver.find_element_by_css_selector("i.icon-share.get-info").click()
        # save screen here
        time.sleep(5)
        self.save_screenshot(screenshot_type='native', append_name='step10')


        ##############
        #  CASE 947  #
        ##############
    def test_947(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        self.find_element_by_link_text_in_table('nav', 'Configuration').click()
        # step 2
        self.driver.find_element_by_link_text("BitBake variables").click()
        # step 3
        def xpath_option(column_name):
            # return xpath of options under "Edit columns" button
            return self.shortest_xpath('id', 'navTab') + self.shortest_xpath('id', 'editcol') \
                + self.shortest_xpath('id', column_name)
        self.find_element_by_xpath_in_table('navTab', self.shortest_xpath('class', 'btn dropdown-toggle')).click()
        # by default, option "Description" and "Set in file" were checked
        self.driver.find_element_by_xpath(xpath_option('description')).click()
        self.driver.find_element_by_xpath(xpath_option('file')).click()
        self.find_element_by_xpath_in_table('navTab', self.shortest_xpath('class', 'btn dropdown-toggle')).click()
        check_list = ['Description', 'Set in file']
        head_list = self.get_table_head_text('otable')
        for item in check_list:
            self.failIf(item in head_list)
        # check these 2 options and verify again
        self.find_element_by_xpath_in_table('navTab', self.shortest_xpath('class', 'btn dropdown-toggle')).click()
        self.driver.find_element_by_xpath(xpath_option('description')).click()
        self.driver.find_element_by_xpath(xpath_option('file')).click()
        self.find_element_by_xpath_in_table('navTab', self.shortest_xpath('class', 'btn dropdown-toggle')).click()
        head_list = self.get_table_head_text('otable')
        for item in check_list:
            self.failUnless(item in head_list)


        ##############
        #  CASE 948  #
        ##############
    def test_948(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        self.find_element_by_link_text_in_table('nav', 'Configuration').click()
        self.driver.find_element_by_link_text("BitBake variables").click()
        number_before_search = list()
        number_after_search = list()
        # step 3
        # temp_dict -- filter string : filter name in firepath
        temp_dict = {'Set in file':'filter_vhistory__file_name', 'Description':'filter_description'}
        count = 0
        for key in temp_dict:
            try:
                temp_element = self.find_element_by_text_in_table('otable', key)
                temp_element.find_element_by_xpath("..//*[@class='icon-filter filtered']").click()
                # delay here. otherwise it won't get correct "text" we need.
                # TBD
                time.sleep(1)
                # step 4-5, we need to make sure that "search" manipulation
                # does reduce the number in the filter.
                # in this case, text returned will be "All variables (xxx)"
                temp_text = self.driver.find_element_by_xpath("//*[@id='" + temp_dict[key] + "']//*[@class='radio']").text
                number_list = extract_number_from_string(temp_text)
                print number_list
                # probably we only need the first number. in this case.
                number_before_search.append(eval(number_list[0]))
                count +=1
                # how we locate the close button
                self.driver.find_element_by_xpath("//*[@id='" + temp_dict[key] + "']//*[@class='close']").click()
                self.browser_delay()
            except Exception,e:
                self.log.error(e)
                raise
        # search for a while...
        self.driver.find_element_by_id("search").clear()
        self.driver.find_element_by_id("search").send_keys("BB")
        self.driver.find_element_by_css_selector("button.btn").click()
        # same operation as above, only to get the new numbers in the filter
        count = 0
        for key in temp_dict:
            try:
                temp_element = self.find_element_by_text_in_table('otable', key)
                temp_element.find_element_by_xpath("..//*[@class='icon-filter filtered']").click()
                time.sleep(1)
                # in this case, text returned will be "All variables (xxx)"
                temp_text = self.driver.find_element_by_xpath("//*[@id='" + temp_dict[key] + "']//*[@class='radio']").text
                number_list = extract_number_from_string(temp_text)
                # probably we only need the first number. in this case.
                number_after_search.append(eval(number_list[0]))
                count += 1
                # how we locate the close button
                self.driver.find_element_by_xpath("//*[@id='" + temp_dict[key] + "']//*[@class='close']").click()
                self.browser_delay()
            except Exception,e:
                self.log.error(e)
                raise
        for i in range(0, count):
            print i
            print number_after_search[i]
            print number_before_search[i]
            if number_after_search[i] < number_before_search[i]:
                self.log.info("After search, filter number reduces")
            else:
                self.log.error("Error: After search, filter number doesn't reduce")
                self.failIf(True)


        ##############
        #  CASE 949  #
        ##############
    def test_949(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        self.find_element_by_link_text_in_table('nav', 'core-image-minimal').click()
        # step 3
        try:
            self.driver.find_element_by_partial_link_text("Packages included")
            self.driver.find_element_by_partial_link_text("Directory structure")
        except Exception,e:
            self.log.error(e)
            self.failIf(True)
        # step 4
        head_list = self.get_table_head_text('otable')
        for item in ['Package', 'Package version', 'Size', 'Dependencies', 'Reverse dependencies', 'Recipe']:
            self.failUnless(item in head_list)
        # step 5-6
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        selectable_class = 'checkbox'
        # minimum-table : means unselectable items
        unselectable_class = 'checkbox muted'
        selectable_check_list = ['Dependencies', 'Layer', 'Layer branch', 'Layer commit', 'Layer directory', \
                                 'License', 'Recipe', 'Recipe version', 'Reverse dependencies', \
                                 'Size', 'Size over total (%)']
        unselectable_check_list = ['Package', 'Package version']
        selectable_list = list()
        unselectable_list = list()
        selectable_elements = self.driver.find_elements_by_xpath("//*[@id='editcol']//*[@class='" + selectable_class + "']")
        unselectable_elements = self.driver.find_elements_by_xpath("//*[@id='editcol']//*[@class='" + unselectable_class + "']")
        for element in selectable_elements:
            selectable_list.append(element.text)
        for element in unselectable_elements:
            unselectable_list.append(element.text)
        # check them
        for item in selectable_check_list:
            if item not in selectable_list:
                self.log.error(" %s not found in dropdown menu \n" % item)
                self.failIf(True)
        for item in unselectable_check_list:
            if item not in unselectable_list:
                self.log.error(" %s not found in dropdown menu \n" % item)
                self.failIf(True)
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # step 7
        self.driver.find_element_by_partial_link_text("Directory structure").click()
        head_list = self.get_table_head_text('dirtable')
        for item in ['Directory / File', 'Symbolic link to', 'Source package', 'Size', 'Permissions', 'Owner', 'Group']:
            if item not in head_list:
                self.log.error(" %s not found in Directory structure table head \n" % item)
                self.failIf(True)


        ##############
        #  CASE 950  #
        ##############
    def test_950(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        # step3&4: so far we're not sure if there's "successful build" or "failed
        # build".If either of them doesn't exist, we can still go on other steps
        check_list = ['Configuration', 'Tasks', 'Recipes', 'Packages', 'Time', 'CPU usage', 'Disk I/O']
        has_successful_build = 1
        has_failed_build = 1
        try:
            pass_icon = self.driver.find_element_by_xpath("//*[@class='icon-ok-sign success']")
        except Exception:
            self.log.info("no successful build exists")
            has_successful_build = 0
            pass
        if has_successful_build:
            pass_icon.click()
            # save screen here to check if it matches requirement.
            self.browser_delay()
            self.save_screenshot(screenshot_type='selenium', append_name='step3_1')
            for item in check_list:
                try:
                    self.find_element_by_link_text_in_table('nav', item)
                except Exception:
                    self.log.error("link  %s cannot be found in the page" % item)
                    self.failIf(True)
            # step 6
            check_list_2 = ['Packages included', 'Total package size', \
                      'License manifest', 'Image files']
            self.failUnless(self.is_text_present(check_list_2))
            self.driver.back()
        try:
            fail_icon = self.driver.find_element_by_xpath("//*[@class='icon-minus-sign error']")
        except Exception:
            has_failed_build = 0
            self.log.info("no failed build exists")
            pass
        if has_failed_build:
            fail_icon.click()
            # save screen here to check if it matches requirement.
            self.browser_delay()
            self.save_screenshot(screenshot_type='selenium', append_name='step3_2')
            for item in check_list:
                try:
                    self.find_element_by_link_text_in_table('nav', item)
                except Exception:
                    self.log.error("link  %s cannot be found in the page" % item)
                    self.failIf(True)
            # step 7 involved
            check_list_3 = ['Machine', 'Distro', 'Layers', 'Total number of tasks', 'Tasks executed', \
                      'Tasks not executed', 'Reuse', 'Recipes built', 'Packages built']
            self.failUnless(self.is_text_present(check_list_3))
            self.driver.back()


        ##############
        #  CASE 951  #
        ##############
    def test_951(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        # currently test case itself isn't responsible for creating "1 successful and
        # 1 failed build"
        has_successful_build = 1
        has_failed_build = 1
        try:
            fail_icon = self.driver.find_element_by_xpath("//*[@class='icon-minus-sign error']")
        except Exception:
            has_failed_build = 0
            self.log.info("no failed build exists")
            pass
        # if there's failed build, we can proceed
        if has_failed_build:
            self.driver.find_element_by_partial_link_text("error").click()
            self.driver.back()
        # not sure if there "must be" some warnings, so here save a screen
        self.browser_delay()
        self.save_screenshot(screenshot_type='selenium', append_name='step4')


        ##############
        #  CASE 955  #
        ##############
    def test_955(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.log.info(" You should manually create all images before test starts!")
        # So far the case itself is not responsable for creating all sorts of images.
        # So assuming they are already there
        # step 2
        self.driver.find_element_by_link_text("core-image-minimal").click()
        # save screen here to see the page component


        ##############
        #  CASE 956  #
        ##############
    def test_956(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        # step 2-3 need to run manually
        self.log.info("step 2-3: checking the help message when you hover on help icon of target,\
                       tasks, recipes, packages need to run manually")
        self.driver.find_element_by_partial_link_text("Toaster manual").click()
        if not self.is_text_present("Toaster Manual"):
            self.log.error("please check [Toaster manual] link on page")
            self.failIf(True)


        ##############
        #  CASE 959  #
        ##############
    def test_959(self):
        self.case_no = self.get_case_number()
        self.log.info(' CASE %s log: ' % str(self.case_no))
        self.driver.maximize_window()
        self.driver.get(self.base_url)
        self.driver.find_element_by_link_text("core-image-minimal").click()
        # step 2-3
        self.find_element_by_link_text_in_table('nav', 'Tasks').click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        self.driver.find_element_by_id("task_log").click()
        self.driver.find_element_by_css_selector("button.btn.dropdown-toggle").click()
        # step 4: "Not Executed" tasks have no log. So click "Log"...
        self.find_element_by_link_text_in_table('otable', 'Log').click()
        # save screen to see if there's "absolute path" of logs
        self.browser_delay()
        self.save_screenshot(screenshot_type='selenium', append_name='step4_1')
        self.find_element_by_link_text_in_table('otable', 'Log').click()
        # save screen to see if there's "absolute path" of logs
        self.browser_delay()
        self.save_screenshot(screenshot_type='selenium', append_name='step4_2')





from selenium import webdriver

from selenium.webdriver.common.keys import Keys

import login
import time

driver = webdriver.Chrome(executable_path ="C:\drivers\chromedriver_win32\chromedriver.exe")

driver.get("https://10.225.5.3/")

time.sleep(15)

driver.find_element_by_xpath("//*[@id='apicloginBox']/div/div/div[4]/form/div[2]/div/div/input").click()

dna_user = driver.find_element_by_class_name("form-control")

dna_user.send_keys(login.username)
time.sleep(2)

dna_pwd=driver.find_element_by_xpath("//*[@id='apicloginBox']/div/div/div[4]/form/div[3]/div/div/input").click()

time.sleep(2)

driver.find_element_by_xpath("//*[@id='apicloginBox']/div/div/div[4]/form/div[3]/div/div/input").send_keys(login.password)

driver.find_element_by_xpath("//*[@id='apicloginBox']/div/div/div[4]/form/div[4]/div").click()

time.sleep(20)
try:
    driver.find_element_by_xpath("//*[@id='__defaultPluginBody']/div/div[2]/div/div/div/div[1]").click()
except:
    print ("nothing")

driver.find_element_by_xpath("//*[@id='CriticalIssueCountView']/div/div[3]/a").click()
#
# time.sleep(5)
#
# driver.find_element_by_xpath("//*[@id='DataTables_Table_0_wrapper']/div[2]/div[2]/div/button").click()

time.sleep(4)


# dna_pwd = driver.find_element_by_class_name("form-control")
# time.sleep(2)
# dna_pwd.send_keys(login.password)


#
# driver.find_element_by_xpath("//*[@id='apicloginBox']/div/div/div[4]/form/div[3]/div/div/input").send_keys('Pyth0n@3012')
# time.sleep(4)
#
# driver.find_element_by_xpath("//*[@id='apicloginBox']/div/div/div[4]/form/div[4]/div").click()
#
# print (driver.current_url)


# print (ele.is_displayed())



from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import geocoder

COMPANY_LIST = """0477.143.394
0413 110 231
0416 453 068
0404 621 642
0477 954 038
0441 428 489
0401 927 616
0860 731 973
0473 191 041
0426 492 865
0436 976 486
0827 607 661
0430 037 226
0413 664 814
0474 617 733
0413 830 605
0477 143 394
0458 532 658
0414 041 530
0472 660 610
0422 362 447
0428 252 723
0885 503 991
0457 242 459
0422 454 596

0404 447 933
0480 273 427
0441 928 931
0434 342 145
0454 647 710
0402 459 235
0449 316 668
0405 937 080
0882 544 503
0469 141 488
0415 663 608
0401 029 672
0460 399 711
0465 607 621
0466 712 134
0476 963 945
0407 155 421
0426 586 303
0474 826 975
0446 425 969
0426 702 802
0432 100 455
0473 783 236
0433 460 930
0412 523 479
0441 128 086
0898 937 602
0418 306 164
0440 587 460
0872 733 843
0449 266 188
0472 001 604
0438 251 146
0405 770 992
0465 150 137
0435 148 928
0447 379 341
0470 094 266
0423 039 962
0401 916 530
0478 652 141
0425 109 428
0418 217 577
0604 934 263
?
0475 197 357
0432 618 812
0437 598 573
0438 546 896
0455 123 109
0829 389 590
0401 574 852
0438 592 824
0473 044 848""".split('\n')

profile = webdriver.FirefoxProfile()
profile.set_preference("general.useragent.override", "Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0 %s" % time.time())
driver = webdriver.Firefox()

scrape_geo = False
scrape_vestigingen = False

for company in COMPANY_LIST:
    success = False
    while not success:
        try:
            driver.get("http://kbopub.economie.fgov.be/kbopub/zoeknummerform.html")
            assert "Opzoeking" in driver.title
            elem = driver.find_element_by_id("nummer")
            elem.send_keys(company)
            elem.send_keys(Keys.RETURN)
            assert "No results found." not in driver.page_source
            time.sleep(0.5)
            if "captchaform" in driver.current_url:
                time.sleep(5.0)
                continue
            elem = driver.find_element_by_xpath("//*[contains(text(), 'Adres van de maatschappelijke zetel')]/following-sibling::td")
            adres = elem.text.replace('\n','\t').split('Sinds')[0].strip().split('Extra')[0].strip()
            print adres
            g = geocoder.google(adres)
            print g.latlng[0],",",g.latlng[1]
            elems = driver.find_elements_by_xpath("//*[contains(text(), 'Functies')]/parent")
            print len(elems)
            for elem in elems:
                print elem.text


            company_name = driver.find_element_by_xpath("//*[contains(text(), 'Maatschappelijke Naam:')]/following-sibling::td").text.split('\n')[0]

            if scrape_vestigingen:
                vestigingen_link = driver.find_element_by_xpath("//a[contains(text(), 'Gegevens en activiteiten per VE')]")
                driver.get(vestigingen_link.get_attribute("href"))
                if "Vestigingseenheidsgegevens" in driver.title:
                    # Pagina van 1 vestiging
                    number = driver.find_element_by_xpath("//*[contains(text(), 'Ondernemingsnummer')]/following-sibling::td").text
                    name = driver.find_element_by_xpath("//*[contains(text(), 'Naam van de vestigingseenheid')]/following-sibling::td").text
                    name = name.split('\n')[0]
                    if name == "Geen gegevens opgenomen in KBO.":
                        name = ""
                    address = driver.find_element_by_xpath("//*[contains(text(), 'Adres van de vestigingseenheid')]/following-sibling::td").text
                    address = address.split('\n')
                    street = address[0].replace('   ', ' ')
                    city = address[2].replace('   ', ' ')
                    print company, '\t', company_name, '\t', number, '\t', name, '\t', street, '\t', city
                else:
                    # Tabel met meerdere vestigingen
                    rows = driver.find_elements_by_xpath("//table[@id='vestiginglist']/tbody/tr")
                    for row in rows:
                        cells = row.find_elements_by_xpath('.//td')
                        address = cells[5].text.split('\n')
                        name = cells[4].text
                        if name == "Geen gegevens opgenomen in KBO.":
                            name = ""
                        number = cells[2].text
                        print company, '\t', company_name, '\t', name, '\t', name, '\t', address[0], '\t', address[1]
            time.sleep(2.0)
            success = True
        except:
            import traceback

            traceback.print_exc()
            time.sleep(1.0)
            print "NOT FOUND:", company, "->", driver.current_url
            success = True

driver.close()
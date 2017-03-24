#!/usr/bin/env python
# -*- coding: utf-8 -*

import os,scrapy,re,json,gc,requests,ast
from lxml import html
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from scrapy.http import Request
import unicodedata


from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
from twisted.internet.error import ConnectError

from ..inteligence.utility.logic import apply_schema_to_url
from ..inteligence.utility.logic import remove_urls
from ..inteligence.utility.logic import get_text
from ..inteligence.utility.logic import make_up_url
from ..inteligence.utility.logic import parse_site_variable
from ..inteligence.utility.logic import mail
from ..inteligence.phone_number.logic import PhoneParser

class BaseSpider(scrapy.Spider):
    """
    Base spider that help you crawl all data
    through out the domain given in start urls
    """

    name = "auto"
    total_item=[]

    allowed_domains = []
    banned_responses = [404, 500]
    def __init__(self,link='',mail_to='',*args, **kwargs):
        """
        initializing the spider
        :param inital set of values link:

        """
        self.url_link = link
        self.start_urls = []
        self.urls_seen = set()
        self.mail_id=mail_to
        print"mail",mail
        response = requests.get(url=link)
        self.list_link(link,response.text)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def __avoid_unwanted_responses(self, status):
        """
        Checks for valid responses
        :param status:
        :return: Boolean
        """
        if status in self.banned_responses:
            return False
        return True

    def start_requests(self):
        """
        Get domain and item of websites
        :return:
        """
        for req_url in self.start_urls:
         print"URL:", req_url
         yield Request(url = req_url, meta = {'domain': self.url_link},callback = self.parse,errback = self.errback_httpbin)

    def errback_httpbin(self, failure):
        # log all errback failures,
        # in case you want to do something special for some errors,
        # you may need the failure's type
        self.logger.error(repr(failure))

        #if isinstance(failure.value, HttpError):
        if failure.check(HttpError):
            # you can get the response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        #elif isinstance(failure.value, DNSLookupError):
        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        #elif isinstance(failure.value, TimeoutError):
        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error('ConnectonError on %s', request.url)


    def parse(self, response):
        """
        Parses the main html response
        :param response:
        :return:
        """
        final_data = {}

        item = {}

        if self.__avoid_unwanted_responses(response.status):
            doc = html.fromstring(response.body)
            domain = response.meta['domain']
            site_variable, site_name = parse_site_variable(response.url)
            final_data[self.get_domain(domain)] = []
            
       
            #phone Number only 
            phone_logic = PhoneParser(response)
            phone_number = phone_logic.process_response(response)
            if phone_number:
                phone_no = phone_number
            else:
                phone_no = []
            self.total_item.append(phone_no)
            




    def spider_closed(self, spider):
        """
        Write data to the file after closing the spider
        :param spider:
        :return:
        """
        final_data = []
        if spider is not self:
            return
        
        for data in self.total_item:
            if data:
               final_data.append(data)
        with open("./result.json","w") as f:
         f.write(json.dumps(final_data,indent=4, sort_keys=True))
        mail(self.mail_id)

        print"COLLECT GARBAGE...."
        gc.collect
        print"REMOVING GARBAGE...."
        del gc.garbage

    def get_domain(self, url):
        """
        Parses domain name from url
        :param url:
        :return name:
        """
        name = re.search(r'\.(.+?)\.', url)
        if name is not None:
            name = name.group(1).replace('-','_')
        else:
            name = re.search(r'\/\/(.+?)\.', url)
            if name:
                name = name.group(1).replace('-','_')
        return name





    def list_link(self,link,response):
        """

        :param link:
        :param response:
        :return list of valid url:
        """
        doc = html.fromstring(response)
        next_urls = doc.xpath('.//a/@href') + doc.xpath('.//A/@HREF')
        if next_urls:
              urls = remove_urls(next_urls)
              urls = list(set(urls))
              for url in urls:
                  url = make_up_url(url, link)
                  if not url:
                      continue
                  next_url = apply_schema_to_url(url)

                  if link in  next_url and  link != next_url:
                         self.start_urls.append(next_url)


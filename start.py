import sys,os.path
os.chdir('./AIspider')
print("PWD:",os.getcwd())
url='http://www.glahe-fliesen.de/'
mail_to='jithin.sayone@gmail.com'
cmd="scrapy crawl auto -a link="+str(url)+" -a mail_to="+str(mail_to)
os.system(cmd)

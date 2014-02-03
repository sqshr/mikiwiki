import markdown
import os
import cgi
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urllib
import operator
import urlparse
import fnmatch
import re
import inspect

sitedir = "."
wikiname="miki"
global actions

def page(self,content,info):
	files = sorted(os.listdir(os.path.abspath(sitedir)), key=str.lower)
	categories=""
	if self.client_address[0]!="127.0.0.1":
		global actions
		actions=""
	for file in files:
		if os.path.isdir(file):
			categories=categories+"<li><a href=\"/"+file+"\">"+file+"</a></li>"
	head="""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>"""+wikiname+" - "+info['title']+"""</title><link rel="stylesheet" href="/bootstrap.min.css" type="text/css"></head>"""
	bodyprenav="""<body><div id="wrap">"""
	navbar="""
<div class="navbar navbar-fixed-top">
	<div class="navbar-inner">
		<div class="container">
			<a class="brand" href="/">"""+wikiname+"""</a>
			<ul class="nav">
				"""+categories+"""
				<li><a href="http://daringfireball.net/projects/markdown/syntax">Markdown Help</a></li>
			</ul>
			<form class="navbar-form pull-right" method="POST" action="/search">
				<input class="search-query" type="search" id="search" name="search" placeholder="search here...">
			</form>  
				"""+actions+"""
		</div>
	</div>
</div>"""

	bodypostnav="""<div class="container">"""
	footer= "</div></div></body></html>"
	self.wfile.write(head+bodyprenav+navbar+bodypostnav+content+footer)

def request(self):
	info = {'path':sitedir+urllib.url2pathname(self.path) , 'title':urllib.url2pathname(os.path.basename(urlparse.urlparse(self.path).path)), 'urlparsed':urlparse.urlparse(self.path)}
	#info = {urlparse.urlparse(self.path)}
	return info

def directory(self,info):
	global actions
	actions="""<form class="navbar-form pull-right" method="POST" action="new"><input type="hidden" name="dir" value="""+urllib.url2pathname(info['path'])+"""><button class="btn btn-primary">New</button></form>"""
	tittle=title(self,info)
	bc=breadcrumbs(self,info)
	listing=""
	dirs=[]
	files=[]
	ls = sorted(os.listdir(info['path']), key=str.lower)
	for item in ls:
		if not item.startswith('.'):
			filepath=os.path.join(info['path'],item)
			listitem=(filepath,item)
			if os.path.isdir(filepath):
				dirs.append(listitem)
			elif os.path.isfile(filepath) and not ".css" in item and not item==inspect.getfile(inspect.currentframe()):
				files.append(listitem)
	if dirs:
		listing=listing+"<h2>Directories</h2>"
		for filepath,file in dirs:
			listing=listing+"<ul><a href=\"/"+filepath+"\">"+file+"</a></ul>"
	if files:
		listing=listing+"<h2>Files</h2>"
		for filepath,file in files:
			listing=listing+"<ul><a href=\"/"+filepath+"\">"+file+"</a></ul>"
	if not dirs and not files:
		listing="<h1>Empty Directory</h1>"
	page(self,tittle+bc+listing,info)

def title(self,info):
	if not info['title']:
		title="<h1>"+wikiname+"</h1>"
	else:
		title="<h1>"+info['title']+"</h1>"
	return title

def css(self,info):
	if info['path'].endswith('bootstrap.min.css'):
		file=open("cerulean.css", "r")
		css = file.read()
	self.wfile.write(css)

def search(self,form,info):
	query = str.lower(form['search'].value)
	content="<h1>Search results for '"+cgi.escape(query)+"'</h1>"
	dirss="<h2>Directories</h2>"
	filess="<h2>Files</h2>"
	grep="<h2>Files containing...</h2>"
	for root, dirs, files in os.walk(os.path.abspath(sitedir)):
## Directories
		for basename in dirs:
			if not basename.startswith('.'):
				if fnmatch.fnmatch(str.lower(basename), "*"+query+"*"):
					filename = os.path.relpath(os.path.join(root, basename),os.path.abspath(sitedir))
					dirss=dirss+"<ul><a href=\"/"+filename+"\">"+basename+"</a></ul>"
## Files
		for basename in files:
			if not basename.startswith('.') and not basename.endswith('.css') and not basename.endswith('.py') and not basename.endswith('.backup'):
				if fnmatch.fnmatch(str.lower(basename), "*"+query+"*"):
					filename = os.path.relpath(os.path.join(root, basename),os.path.abspath(sitedir))
					filess=filess+"<ul><a href=\"/"+filename+"\">"+basename+"</a></ul>"
## Grep in Files
		for basename in files:
			if not basename.startswith('.') and not basename.endswith('.css') and not basename.endswith('.py') and not basename.endswith('.backup'):
				filename = os.path.relpath(os.path.join(root, basename),os.path.abspath(sitedir))
				result=[]
				for line in open(filename):
 					if query in str.lower(line):
   						result.append(line)
   				if result:
   					grep=grep+"<h5><a href=\"/"+filename+"\">"+basename+"</a></h5>"
   					grep=grep+"<ul>"
   					for match in result:
						grep=grep+"<li>"+cgi.escape(match)+"</li>"
					grep=grep+"</ul>"


	page(self,content+dirss+filess+grep,info)

def savepage(self,form,info):
##EDIT
	if form['type'].value=="edit":
		try:
			f=open(urllib.url2pathname(form['file'].value), 'w')
			f.write(form['content'].value)
			f.close
			#page(self,"<h1>Page Saved</h1><a href=\""+form['file'].value+"\">Go back to page.</a>",info)
		except KeyError:
			os.remove(urllib.url2pathname(form['file'].value))
##NEW	
	if form['type'].value=="new":
		try:
			f=open(urllib.url2pathname(os.path.join(form['dir'].value,form['file'].value)), 'w')
			f.write(form['content'].value)
			f.close
			#page(self,"new file created",info)
		except KeyError:
			os.remove(urllib.url2pathname(os.path.join(form['dir'].value,form['file'].value)))
			os.makedirs(urllib.url2pathname(os.path.join(form['dir'].value,form['file'].value)))
		
def editpage(self,form,info):
	f = open(form['path'].value)
	content="""<h1>"""+os.path.basename(form['path'].value)+""" - Edit Mode</h1><form class="form" method="POST" action="/save"><input type="hidden" name="type" value="edit"><input type="hidden" name="file" value="""+urllib.pathname2url(form['path'].value)+""" /><div class="controls"><textarea class="input-xxlarge" rows="30" name="content" id="editcontent">"""+f.read()+"""</textarea></div><div class="form-actions"><button class="btn btn-primary">Save</button></div></form>"""
	page(self,content,info)
	
def newpage(self, form, info):
	content="""<h1>"""+os.path.basename(form['dir'].value)+""" - New Page</h1><form class="form" method="POST" action="/save"><input type="hidden" name="type" value="new"><input type="hidden" name="dir" value="""+form['dir'].value+""" /><div class="controls"><div class="row-fluid"><input type="text" name="file" placeholder="Page Title"></div><div class="row-fluid"><textarea class="input-xxlarge" rows="30" cols="300" name="content"></textarea></div></div><div class="form-actions"><button class="btn btn-primary">Save</button></div></form>"""
	page(self,content,info)

def file(self,info):
	global actions
	actions="""<form class="navbar-form pull-right" method="POST" action="/edit"><input type="hidden" name="path" value=\""""+urllib.url2pathname(info['path'])+"""\"><button class="btn btn-primary">Edit</button></form>"""
	f = open(urllib.url2pathname(info['path']))
	try:
		crumbtrail=breadcrumbs(self,info)
		content=title(self,info)+crumbtrail+markdown.markdown(f.read(),['tables'])
		content=content.replace("<table>","<table class=\"table table-bordered table-striped table-hover\">")
	except UnicodeDecodeError:
		content="<h1>Error</h1>"+breadcrumbs(self,info)+"<p>A unicode decode error was encountered. This page will not display, but can still be edited to remove the offending characters.</p>"
	f.close()
	page(self,content,info)

def breadcrumbs(self,info):
	crumbtrail="<ul class=\"breadcrumb\">"
	breadcrumb=""
	crumbs=re.split("/",info['path'])
	for count, crumb in enumerate( crumbs[0:len(crumbs)], start = 1 ):
		breadcrumb=breadcrumb+'/'+crumb
		if (crumb=="."):
			crumb=wikiname
		if crumb:
			crumbtrail=crumbtrail+"<span class=\"divider\">/</span>  <li><a href=\""+breadcrumb+"\">"+crumb+"</a></li> "
	crumbtrail=crumbtrail+"</ul>"
	return crumbtrail
	
class RequestHandler(BaseHTTPRequestHandler):
	def _writeheaders(self):
		if not self.path.endswith('/save'):
			self.send_response(200)
			if self.path.endswith('.css'):
				self.send_header('Content-type', 'text/css')
				self.send_header('Cache-Control', 'public, max-age=0')
			else:
				self.send_header('Content-type', 'text/html')
			self.end_headers()
		
	def do_HEAD(self):
		self._writeheaders()
		
	def do_GET(self):
		self._writeheaders()
		info=request(self)
		global actions
		actions=""
	
	##CSS
		if info['path'].endswith('.css'):
			css(self,info)
	##Directory
		elif os.path.isdir(info['path']):
			directory(self,info)
	##File
		elif os.path.isfile(info['path']):
			file(self,info)
		else:
			page(self,"<h1>Not Found</h1>"+breadcrumbs(self,info)+"<p>It looks like this page doesn't exist</p>",info)
		
	def do_POST(self):
		self._writeheaders()
		info=request(self)
		global actions
		actions=""
		form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':self.headers['Content-Type'],})
	##Search
		if info['path'].endswith('/search'):
			search(self,form,info)
	##Deny Remote POSTS
		elif self.client_address[0]!="127.0.0.1":
			page(self,"<h2>Not permitted</h2>",info)
	##Edit Page
		elif info['path'].endswith('/edit'):
			editpage(self,form,info)
	##Save Page
		elif info['path'].endswith('/save'):
			savepage(self,form,info)
			if form['type'].value=="new":
				self.send_response(302)
				self.send_header('Location',os.path.join(form['dir'].value,form['file'].value))
				self.end_headers()	
			else:
				if os.path.isfile(urllib.url2pathname(form['file'].value)):
					self.send_response(302)
					self.send_header('Location', form['file'].value)
					self.end_headers()	
				else:
					self.send_response(200)
					self.end_headers()	
					page(self,"<h1>Page Deleted</h1>"+breadcrumbs(self,info),info)	
	##New Page
		elif info['path'].endswith('/new'):
			newpage(self,form,info)	
		

serveraddr = ('localhost', 8080)
srvr = HTTPServer(serveraddr, RequestHandler)
print("Server online and active")
srvr.serve_forever()

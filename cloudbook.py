# -*- coding: utf-8 -*- 

import base64
import cStringIO
import jinja2
import os
import StringIO
import zipfile
import re
import webapp2

from google.appengine.api import users, images
from google.appengine.ext import db
from google.appengine.ext.webapp.util import login_required
from xml.sax import handler, parseString, saxutils
from xml.dom import minidom

# Set to true if we want to have our webapp print stack traces, etc
_DEBUG = True

_MESSAGE_LOGIN = 'login required'
_MESSAGE_INVALID_KEY = 'invalid key'

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Book(db.Model):
    user_id = db.UserProperty()
    title = db.StringProperty()
    author = db.StringProperty()
    isbn = db.StringProperty()
    cover = db.TextProperty()
    last_chapter = db.IntegerProperty(default=0)
    last_percent = db.FloatProperty(default=0.0)
    
class Toc(db.Model):
    book = db.ReferenceProperty(Book, collection_name='tocs')
    seq = db.IntegerProperty()
    title = db.StringProperty()
    html = db.TextProperty()
    
class BaseRequestHandler(webapp2.RequestHandler):
    def generate(self, template_name, template_values={}):
        values = {
                  'request': self.request,
                  'user': users.get_current_user(),
                  'login_url': users.create_login_url(self.request.uri),
                  'logout_url': users.create_logout_url('http://%s/' % (self.request.host,)),
                  'debug': self.request.get('deb'),
                  'application_name': 'Task Manager', }
        values.update(template_values)
        template = jinja_environment.get_template(os.path.join('templates', template_name))
        self.response.out.write(template.render(values))
    
class MainPage(BaseRequestHandler):
    """Not yet defined how main page will be designed.
    Maybe this would be bookstore page and has links to go bookshelf.
    """
    def get(self):
        self.redirect('/bookshelf')
        
class BookshelfPage(BaseRequestHandler):
    @login_required
    def get(self):
        self.generate('bookshelf.html', {})

class BookReaderPage(BaseRequestHandler):
    def get(self):
        book_key = self.request.get('key')
        book = db.get(book_key)
        tocs = []
        for toc_key in book.tocs:
            toc = db.get(toc_key.key())
            tocs.append(toc)
        self.generate('reader.html', { 'book': book, 'tocs': tocs })

class UploadBook(BaseRequestHandler):
    def post(self):
        try:
            # 1. unzip epub
            epub_file = self.request.POST.get('epub').file
            buffer = cStringIO.StringIO(epub_file.read())
            zobj = zipfile.ZipFile(buffer)
            
            # 2. find opf file path
            container_file = zobj.read('META-INF/container.xml')
            container_dom = minidom.parseString(container_file)
            rootfile = container_dom.getElementsByTagName('rootfile')
            opf_path = rootfile[0].getAttribute('full-path')
            root_path = opf_path[:opf_path.rfind('/') + 1]
            
            # 3. parse book info
            opf_file = zobj.read(opf_path)
            opf_dom = minidom.parseString(opf_file)
            book = Book()
            book.user_id = users.get_current_user()
            book.title = opf_dom.getElementsByTagName('dc:title')[0].firstChild.nodeValue
            book.author = opf_dom.getElementsByTagName('dc:creator')[0].firstChild.nodeValue
            book.isbn = opf_dom.getElementsByTagName('dc:identifier')[0].firstChild.nodeValue
            book.put()
            
            # 4. parse toable of content
            item_list = opf_dom.getElementsByTagName('item')
            for item in item_list:
                if item.getAttribute('id') == 'ncx':
                    ncx_path = item.getAttribute('href')
                    break
                raise Exception('Wrong opf file. There is no ncx file.')
            ncx_file = zobj.read(root_path + ncx_path)
            p = re.compile(r'<!DOCTYPE[\s]+?[^>]*>', re.I)
            ncx_file = p.sub('', ncx_file)
            handler = self.TocHandler(zobj, root_path, book)
            parseString(ncx_file, handler)
            
            # 5. clean up
            zobj.close()
            
            # 6. response
            self.redirect('/bookshelf')
        except Exception, err:
            self.generate('exception.html', { 'error': err })

    class TocHandler(handler.ContentHandler):
        def __init__(self, zobj, root_path, book):
            handler.ContentHandler.__init__(self)
            self.zobj = zobj
            self.root_path = root_path
            self.book = book
            self.toc = Toc()
            self.seq = 0
            self.start_tag = ''
            self.prev_url = ''
            
        def startElement(self, name, attrs):
            self.start_tag = saxutils.escape(name)
            
            if saxutils.escape(name) == 'content':
                src = saxutils.escape(attrs['src'])
                url = src
                #print url
                
                # save this if first chapter
                if self.seq == 0:
                    html_file = self.zobj.read(self.root_path + url)
                    dom = minidom.parseString(html_file)
                    img_tag = dom.getElementsByTagName("img")[0]
                    img_src = img_tag.attributes["src"].value
                    img_file = self.zobj.read(self.root_path + img_src)
                    cover = img_file
                    #cover = images.resize(img_file, 120, 160)
                    b64 = "data:image/png;base64," + base64.encodestring(cover)
                    self.book.cover = b64
                    self.book.put()
            	
                if url != self.prev_url:
                    self.toc.seq = self.seq
                    self.seq += 1
                    html = self._compact(url)
                    self.toc.html = html
                    self.toc.book = self.book
                    self.toc.put()
    
                self.prev_url = url
                self.toc = Toc()
        
        def characters(self, content):
            if self.start_tag == 'text':
                self.toc.title = saxutils.escape(content)
        
        def endElement(self, name):
            if self.start_tag == name:
                self.start_tag = ''
        
        def _compact(self, url):
            html_file = self.zobj.read(self.root_path + url)
            dom = minidom.parseString(html_file)
            
            # 1. handle link tag
            links = dom.getElementsByTagName("link")
            for link in links:
                if link.attributes["rel"].value == "stylesheet":
                    href = link.attributes["href"].value
                else:
                    continue
                
                output = StringIO.StringIO()
				#f = open(root_path + href)
                output.write(self.zobj.read(self.root_path + href))
                css = output.getvalue()
                output.close()
                
                style = dom.createElement("style");
                style.appendChild(dom.createTextNode(css))
                link.parentNode.appendChild(style)
                link.parentNode.removeChild(link)
            
            # 2. handle img tag
            imgs = dom.getElementsByTagName("img")
            for img in imgs:
                src = img.attributes["src"].value
                img_file = self.zobj.read(self.root_path + src)
                b64 = "data:image/png;base64," + base64.encodestring(img_file)
                img.attributes["src"].value = b64
                
            # 3. to string
            return dom.toprettyxml()

class DeleteBook(BaseRequestHandler):
    def get(self):
        book_key = self.request.get('key')
        book = db.get(book_key)
        if book != None:
            # delete tocs
            tocs = book.tocs
            for toc in tocs:
                db.delete(toc)
            # delete book
            db.delete(book)
        
        self.redirect('/bookshelf')

class BookListAjax(webapp2.RequestHandler):
    def get(self):
        result = ''
        books = db.GqlQuery('SELECT * FROM Book ORDER BY title')
        if users.get_current_user():
            if books:
                i = 0
                result += '{"status": "success", "books": ['
                for book in books:
                    book_result = '{"key": "' + str(book.key()) + \
                                    '", "title": "' + book.title + \
                                    '", "author": "' + book.author + \
                                    '", "isbn": "' + book.isbn + \
                                    '", "cover": "' + (book.cover.replace('\n', '') if book.cover else '') + \
                                    '", "last_chapter": "' + str(book.last_chapter) + \
                                    '", "last_percent": "' + str(book.last_percent) + \
                                    '", "tocs": ' + str([str(toc.key()) for toc in book.tocs]).replace('\'', '"') + \
                                    '}'
                    result += book_result
                    i += 1
                    if i < books.count():
                        result += ', '
                result += ']}'
            else:
                result = '{"status": "fail", "message": "book does not exist."}'
        else:
            result = '{"status": "fail", "message": "' + _MESSAGE_LOGIN + '"}'
        
        self.response.headers['Content-Type'] = "application/json; charset=utf-8"
        self.response.out.write(result)

class BookInfoAjax(webapp2.RequestHandler):
    def get(self):
        result = ''
        if users.get_current_user():
            book_key = self.request.get('key')
            if book_key == '':
                result = '{"status": "fail", "message": "' + _MESSAGE_INVALID_KEY + '"}'
            else:
                book = db.get(book_key)
                result = '{"status": "success' + \
                                    '", "title": "' + book.title + \
                                    '", "author": "' + book.author + \
                                    '", "isbn": "' + book.isbn + \
                                    '", "last_chapter": "' + str(book.last_chapter) + \
                                    '", "last_percent": "' + str(book.last_percent) + \
                                    '"}'
        else:
            result = '{"status": "fail", "message": "' + _MESSAGE_LOGIN + '"}'
        
        self.response.headers['Content-Type'] = "application/json; charset=utf-8"
        self.response.out.write(result)

class BookContentAjax(webapp2.RequestHandler):
    def get(self):
        book_key = self.request.get('key')
        book_chapter = self.request.get('chapter')
        book = db.get(book_key)
        if book_chapter == '':
            chapter = book.last_chapter
        else:
            chapter = int(book_chapter)
        toc_key = book.tocs[chapter]
        toc = db.get(toc_key.key())
        self.response.headers['Content-Type'] = "application/xhtml+xml; charset=utf-8"
        self.response.out.write(toc.html)

app = webapp2.WSGIApplication([
                                      ('/', MainPage),
                                      ('/bookshelf', BookshelfPage),
                                      ('/reader', BookReaderPage),
                                      ('/upload', UploadBook),
                                      ('/delete', DeleteBook),
                                      ('/booklist', BookListAjax),
                                      ('/bookinfo', BookInfoAjax),
                                      ('/bookcontent', BookContentAjax)],
                                      debug=True)

'''def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()'''

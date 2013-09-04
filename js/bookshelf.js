/**
 * Displays Bookshelf
 *
 * @param xhr
 */
function displayBookshelfCallback(xhr) {
    if(xhr.readyState == 1) {
        console.log(1);
    }
    if(xhr.readyState == 2) {
        console.log(2);
    }
    if(xhr.readyState == 3) {
        console.log(3);
    }
    if(xhr.readyState == 4) {
        console.log(4);
        if(xhr.status == 200) {
            var result = xhr.responseText;

            if((result != null) && (result != "")) {
                result = JSON.parse(result);

                if(result.status == "success") {
                    var books = result.books;

                    if(books.length > 0) {
                        for(var i = 0; i < books.length; ++i) {
                            var book = books[i];

                            var bookitem = '<li>';
                            bookitem += '  <div>';
                            bookitem += '    <a href="/reader?key=' + book.key + '">';
                            bookitem += '      <img width="150" height="200" src="' + book.cover + '" alt="' + book.title + '">';
                            bookitem += '    </a>';
                            bookitem += '    <span id="' + book.key + '_info"></span>';
                            bookitem += '  </div>';
                            bookitem += '</li>';

                            if(i == 0) {
                                $("ul.booklist").html(bookitem);
                            } else {
                                $("ul.booklist").append(bookitem);
                            }

                            /*
                             var chapterList = "";
                             for (var j=0 ; j<book.tocs.length ; ++j) {
                             chapterList += "<a href=\"/bookcontent?key=" + book.key + "&chapter=" + j + "\">" + j + "</a>&nbsp;";
                             }

                             $("#" + book.key + "_info").append(chapterList);
                             */
                        }
                    } else {
                        $("ul.booklist").html("<p>No book.</p>");
                    }
                } else if(result.status == "fail") {
                    console.log(result);
                    $("ul.booklist").html("<p>" + result.message + "</p>");
                }
            }
        }
    }
}

/**
 * Checks Form
 *
 * @param form
 * @returns {Boolean}
 */
function checkform(form) {
    if(form.epub.value == "") {
        toast('error', 'Please select epub file.');
        return false;
    }
    return true;
}
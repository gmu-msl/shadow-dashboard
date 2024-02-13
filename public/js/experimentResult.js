searchButtonClicked = function () {
  // Get the search text
  var searchField = document.getElementById('searchInputField');
  var searchText = searchField.value;

  var url = window.location.href;

  // strip the query string
  var index = url.indexOf('?');
  if (index > -1) {
    url = url.substring(0, index);
  }

  var newUrl = url + '?username=' + searchText;

  // Redirect to the new url
  window.location.href = newUrl;
};

// This function is called when the document is loaded
document.addEventListener('DOMContentLoaded', function () {
  // collapsible code
  var coll = document.getElementsByClassName('collapsible');
  var i;

  for (i = 0; i < coll.length; i++) {
    coll[i].addEventListener('click', function () {
      this.classList.toggle('active');
      var content = this.nextElementSibling;
      if (content.style.maxHeight) {
        content.style.maxHeight = null;
      } else {
        content.style.maxHeight = content.scrollHeight + 'px';
      }
    });
  }
});

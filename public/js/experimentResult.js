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

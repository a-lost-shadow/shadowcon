function makeMenu(list, submenu, stateDict) {
  return function() {
    stateDict[list + "_last_click"] = false;

    $(list).click(function() {
      if ($(submenu).is(':visible') && stateDict[list + "_last_click"]) {
        $(submenu).hide();
      } else if(!$(submenu).is(':visible')) {
        $(submenu).show();
      }
      stateDict[list + "_last_click"] = true;
      return false;
    });
    $(list).hover(function() {
      $(submenu).show();
      stateDict[list + "_last_click"] = false;
    }, function() {
      stateDict[list + "_last_click"] = false;
    });
  }
}

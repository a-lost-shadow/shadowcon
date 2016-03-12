function dummyData() {
  return {
    "locations": ["Boiler Room", "Dance Floor", "Dungeon"],
    "games": [
      {
        "title": "First Game",
        "location": 1,
        "start": 0,
        "width": 8
      },
      {
        "title": "2nd Game",
        "location": 0,
        "start": 40,
        "width": 7
      },
      {
        "title": "Down with the Sun",
        "location": 2,
        "start": 24,
        "width": 6
      }
    ]
  }
}

// constants used by locations
var textOffset = 4;
var rowHeight = 30;


function locationY(row) {
  return 61 + rowHeight * row;
}

function drawSchedule(svgId, data) {
  $(svgId).svg('destroy');
  $(svgId).svg();
  var svg = $(svgId).svg('get');
  var width = Math.max($(svgId)[0].getBoundingClientRect().width, 500);

  // draw the locations first so we can determine how much space they need
  var maxLocationWidth = 0;
  for (i = 0; i < data.locations.length; i++) {
    var text = svg.text(textOffset, locationY(i), data.locations[i], {class:"location"});
    maxLocationWidth = Math.max(maxLocationWidth, text.clientWidth);
  }


  // constants used by the rest of the table
  var gameHeight = rowHeight - 3;
  var gridStart = maxLocationWidth + textOffset + 10
  var hour = { width: (width - gridStart) / 48, offset: 14};
  hour.blockWidth = hour.width * 4;
  var grid = {x: gridStart, y:40, width: hour.width * 46};
  grid.light = {x: 0, y:0};
  grid.bold = {x: grid.x % (4 * hour.width) - 2 * hour.width - 1,
               y: grid.y % rowHeight};
  var days = {x: grid.x + 6 * hour.width - 1, y: 10, height: 20, width: hour.blockWidth * 6};
  var hourHeader = {y: 35, offset: 11}
  var dayHeader = {y: 15,
                friday: grid.x + 6 * hour.width -76,
                saturday: grid.x + 18 * hour.width - hourHeader.offset - 20,
                sunday: grid.x + 36 * hour.width - hourHeader.offset + 30};

  var hourHeaders = ["12am", "4am", "8am", "Noon", "4pm", "8pm"];


  // Definitions used to create the repeating elements
  var defs = svg.defs();

  svg.configure({height:41 + data.locations.length * rowHeight, width: width});
  // pattern(parent, id, x, y, width, height, vx, vy, vwidth, vheight, settings)
  var pattern = svg.pattern(defs, "smallGrid", grid.light.x, grid.light.y, hour.width, rowHeight, {patternUnits:"userSpaceOnUse"});
  var path = svg.createPath()
  svg.path(pattern, path.move(hour.width, 0).line(0,0).line(0, rowHeight), {class:"light"});

  var pattern = svg.pattern(defs, "grid", grid.bold.x, grid.bold.y, hour.blockWidth, rowHeight, {patternUnits:"userSpaceOnUse"});
  //rect(parent, x, y, width, height, rx, ry, settings)
  svg.rect(pattern, 0, 0, hour.blockWidth, rowHeight, {fill:"url(#smallGrid)"});
  var path = svg.createPath()
  svg.path(pattern, path.move(hour.blockWidth, 0).line(0,0).line(0, rowHeight), {class:"heavy"});

  var pattern = svg.pattern(defs, "label_bars", 0, 11, grid.x, rowHeight, {patternUnits:"userSpaceOnUse"});
  svg.polyline(pattern, [[0, rowHeight], [grid.x, rowHeight], [grid.x, 0]], {class:"heavy"});

  var pattern = svg.pattern(defs, "days", days.x, days.y, days.width, days.height, {patternUnits:"userSpaceOnUse", class:"heavy"});
  svg.polyline(pattern, [[0, 0], [0, days.height]]);

  // draw the repeated elements
  svg.rect(grid.x, grid.y, grid.width, "100%", {fill:"url(#grid)"});
  svg.rect(0, grid.y, grid.x, "100%", {fill:"url(#label_bars)"});
  svg.rect(0, 0, grid.width, days.height, {fill:"url(#days)"});

  // Create the text for the days
  var text = svg.createText();
  text.span("Friday", {x: dayHeader.friday});
  text.span("Saturday", {x: dayHeader.saturday});
  text.span("Sunday", {x: dayHeader.sunday});
  svg.text(0, dayHeader.y, text, {class: "header"});

  // create the text for the hour labels
  var text = svg.createText();
  for (i = 0; i < 12; i++) {
    header = hourHeaders[(i + 5) % hourHeaders.length];
    x = grid.x - hourHeader.offset + hour.width * (2 + i * 4);
    text.span(header, {x: x});
  }
  svg.text(0, hourHeader.y, text, {class: "header"});

  // create the game objects
  for (i = 0; i < data.games.length; i++) {
    x = grid.x + hour.width * data.games[i].start
    y = locationY(data.games[i].location) - 19
    width = data.games[i].width * hour.width

    if (0 === width) { continue; }

    var subSvg = svg.svg(x, y, width, gameHeight, {"data-toggle": "tooltip", title: data.games[i].title});
    svg.rect(subSvg, 1, 0, width - 2, gameHeight, {class: "game"});
    svg.text(subSvg, textOffset, 19, data.games[i].title, {class: "game_title", clip:"rect(0,0,10,20)"});
  }

  $('[data-toggle="tooltip"]').tooltip({
    'container': 'body',
    'placement': 'bottom'
  });
}
